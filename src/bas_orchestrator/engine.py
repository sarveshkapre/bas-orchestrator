from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from bas_orchestrator.agent_client import AgentClient, AgentClientConfig, AgentClientError
from bas_orchestrator.models import CampaignSpec, EvidencePack, ModuleResult, ModuleSpec, PolicySpec
from bas_orchestrator.modules.base import ModuleContext
from bas_orchestrator.modules.registry import get_module


class CampaignLoadError(Exception):
    pass


SUPPORTED_CAMPAIGN_VERSIONS = {"v1"}
SUPPORTED_POLICY_VERSIONS = {"v1"}


def load_campaign(path: Path) -> CampaignSpec:
    try:
        raw = yaml.safe_load(path.read_text())
    except FileNotFoundError as exc:
        raise CampaignLoadError(f"Campaign file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise CampaignLoadError(f"Invalid YAML in campaign file: {path}") from exc

    if not isinstance(raw, dict):
        raise CampaignLoadError("Campaign file must be a YAML object")

    spec = CampaignSpec.model_validate(raw)
    if spec.version not in SUPPORTED_CAMPAIGN_VERSIONS:
        raise CampaignLoadError(f"Unsupported campaign version: {spec.version}")
    return spec


def load_policy(path: Path) -> PolicySpec:
    try:
        raw = yaml.safe_load(path.read_text())
    except FileNotFoundError as exc:
        raise CampaignLoadError(f"Policy file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise CampaignLoadError(f"Invalid YAML in policy file: {path}") from exc

    if not isinstance(raw, dict):
        raise CampaignLoadError("Policy file must be a YAML object")

    policy = PolicySpec.model_validate(raw)
    if policy.version not in SUPPORTED_POLICY_VERSIONS:
        raise CampaignLoadError(f"Unsupported policy version: {policy.version}")
    return policy


def _deterministic_run_id(spec: CampaignSpec) -> str:
    payload = json.dumps(spec.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"det-{digest[:16]}"


def _normalized_result(result: ModuleResult, *, fixed_time: datetime | None) -> ModuleResult:
    if fixed_time is None:
        return result
    return result.model_copy(
        update={
            "started_at": fixed_time,
            "finished_at": fixed_time,
        }
    )


def run_campaign(
    spec: CampaignSpec,
    *,
    deterministic: bool = False,
    agent_config: AgentClientConfig | None = None,
    policy: PolicySpec | None = None,
) -> EvidencePack:
    fixed_time = datetime(1970, 1, 1, tzinfo=UTC) if deterministic else None
    run_id = _deterministic_run_id(spec) if deterministic else str(uuid4())
    started_at = fixed_time or datetime.now(UTC)
    results: list[ModuleResult] = []

    target_lookup = {target.id: target for target in spec.targets}
    agent = AgentClient(agent_config) if agent_config else None
    agent_caps = None
    if agent is not None:
        try:
            agent_caps = agent.handshake(
                agent_id=agent_config.agent_id if agent_config else None,
                capabilities=sorted({module.module for module in spec.modules}),
                version=spec.version,
                expected_policy_hash=agent_config.expected_policy_hash if agent_config else None,
            )
        except AgentClientError as exc:
            for module_spec in spec.modules:
                results.append(
                    ModuleResult(
                        module_id=module_spec.id,
                        status="error",
                        started_at=fixed_time or datetime.now(UTC),
                        finished_at=fixed_time or datetime.now(UTC),
                        evidence={"error": "agent handshake failed", "message": str(exc)},
                    )
                )
            finished_at = fixed_time or datetime.now(UTC)
            score, summary = score_results(results)
            return EvidencePack(
                campaign_name=spec.name,
                run_id=run_id,
                started_at=started_at,
                finished_at=finished_at,
                results=results,
                score=score,
                summary=summary,
            )

    for module_spec in spec.modules:
        if module_spec.target_id not in target_lookup:
            results.append(
                ModuleResult(
                    module_id=module_spec.id,
                    status="error",
                    started_at=fixed_time or datetime.now(UTC),
                    finished_at=fixed_time or datetime.now(UTC),
                    evidence={"error": "unknown target"},
                    notes=f"Unknown target: {module_spec.target_id}",
                )
            )
            continue

        try:
            module = get_module(module_spec.module)
        except KeyError as exc:
            results.append(
                ModuleResult(
                    module_id=module_spec.id,
                    status="error",
                    started_at=fixed_time or datetime.now(UTC),
                    finished_at=fixed_time or datetime.now(UTC),
                    evidence={"error": "unknown module"},
                    notes=str(exc),
                )
            )
            continue

        effective_allowlist = _effective_allowlist(module_spec, policy)
        context = ModuleContext(
            module_id=module_spec.id,
            target_id=module_spec.target_id,
            params=module_spec.params,
            expectations=module_spec.expectations,
            scope_allowlist=effective_allowlist,
        )

        if agent is not None:
            if agent_caps is not None and module_spec.module not in agent_caps.capabilities:
                results.append(
                    ModuleResult(
                        module_id=module_spec.id,
                        status="error",
                        started_at=fixed_time or datetime.now(UTC),
                        finished_at=fixed_time or datetime.now(UTC),
                        evidence={"error": "module not supported by agent"},
                        notes=f"missing capability: {module_spec.module}",
                    )
                )
                continue
            payload = {
                "run_id": run_id,
                "module_id": module_spec.id,
                "module": module_spec.module,
                "target_id": module_spec.target_id,
                "params": module_spec.params,
                "expectations": module_spec.expectations,
                "scope": {
                    "allowlist": effective_allowlist,
                    "expires_at": (fixed_time or datetime.now(UTC)).isoformat(),
                },
            }
            try:
                result = agent.execute_module(payload)
            except AgentClientError as exc:
                results.append(
                    ModuleResult(
                        module_id=module_spec.id,
                        status="error",
                        started_at=fixed_time or datetime.now(UTC),
                        finished_at=fixed_time or datetime.now(UTC),
                        evidence={"error": "agent failure", "message": str(exc)},
                    )
                )
                continue
        else:
            try:
                result = module.run(context)
            except Exception as exc:  # pragma: no cover - defensive
                results.append(
                    ModuleResult(
                        module_id=module_spec.id,
                        status="error",
                        started_at=fixed_time or datetime.now(UTC),
                        finished_at=fixed_time or datetime.now(UTC),
                        evidence={"error": "module exception", "message": str(exc)},
                    )
                )
                continue

        results.append(_normalized_result(result, fixed_time=fixed_time))

    finished_at = fixed_time or datetime.now(UTC)
    score, summary = score_results(results)

    return EvidencePack(
        campaign_name=spec.name,
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        results=results,
        score=score,
        summary=summary,
    )


def sign_evidence(evidence: EvidencePack, key: str) -> EvidencePack:
    digest = _sign_payload(evidence, key)
    return evidence.model_copy(update={"signature_alg": "hmac-sha256", "signature": digest})


def verify_evidence(evidence: EvidencePack, key: str) -> bool:
    if evidence.signature_alg != "hmac-sha256" or not evidence.signature:
        return False
    digest = _sign_payload(evidence, key)
    return hmac.compare_digest(digest, evidence.signature)


def _sign_payload(evidence: EvidencePack, key: str) -> str:
    payload = evidence.model_dump(mode="json", exclude={"signature", "signature_alg"})
    message = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(key.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _effective_allowlist(module_spec: ModuleSpec, policy: PolicySpec | None) -> list[str]:
    if policy is None:
        return module_spec.scope_allowlist

    if module_spec.id in policy.modules and policy.modules[module_spec.id].allowlist:
        return policy.modules[module_spec.id].allowlist
    if module_spec.target_id in policy.targets and policy.targets[module_spec.target_id].allowlist:
        return policy.targets[module_spec.target_id].allowlist
    if policy.allowlist:
        return policy.allowlist
    return module_spec.scope_allowlist


def score_results(results: list[ModuleResult]) -> tuple[float, dict[str, Any]]:
    total = len(results)
    passed = sum(1 for result in results if result.status == "pass")
    failed = sum(1 for result in results if result.status == "fail")
    errored = sum(1 for result in results if result.status == "error")
    skipped = sum(1 for result in results if result.status == "skipped")

    score = 0.0 if total == 0 else passed / total
    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errored": errored,
        "skipped": skipped,
    }
    return score, summary
