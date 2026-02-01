from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml
from pydantic import ValidationError

from bas_orchestrator.agent_client import AgentClientConfig
from bas_orchestrator.engine import (
    CampaignLoadError,
    compute_policy_hash,
    effective_allowlist,
    load_campaign,
    load_policy,
    run_campaign,
    sign_evidence,
    verify_evidence,
)
from bas_orchestrator.models import EvidencePack, ModuleResult, ModuleSpec
from bas_orchestrator.modules.registry import get_module, list_modules
from bas_orchestrator.schema import dump_schemas
from bas_orchestrator.summary_validate import (
    diff_summary as diff_summary_payload,
)
from bas_orchestrator.summary_validate import (
    validate_summary as validate_summary_payload,
)

app = typer.Typer(no_args_is_help=True)

INIT_PATH_ARG = typer.Argument(..., help="Path to write a sample campaign YAML")
CAMPAIGN_ARG = typer.Argument(..., help="Path to campaign YAML")
OUT_OPT = typer.Option(..., "--out", help="Path to write evidence pack JSON")
DETERMINISTIC_OPT = typer.Option(
    False, "--deterministic", help="Use stable timestamps and run id for reproducibility"
)
SIGN_KEY_OPT = typer.Option(None, "--sign-key", help="HMAC key for signing evidence pack")
AGENT_URL_OPT = typer.Option(None, "--agent-url", help="Remote agent base URL")
AGENT_ENABLED_OPT = typer.Option(False, "--agent-enabled", help="Enable remote agent execution")
AGENT_CERT_OPT = typer.Option(None, "--agent-cert", help="Client TLS cert path")
AGENT_KEY_OPT = typer.Option(None, "--agent-key", help="Client TLS key path")
AGENT_CA_OPT = typer.Option(None, "--agent-ca", help="CA bundle path for agent TLS")
AGENT_INSECURE_OPT = typer.Option(
    False, "--agent-insecure", help="Allow insecure http:// agent URLs (not recommended)"
)
POLICY_OPT = typer.Option(None, "--policy", help="Policy YAML/JSON path with allowlists")
AGENT_ID_OPT = typer.Option(None, "--agent-id", help="Agent id used during handshake")
AGENT_POLICY_HASH_OPT = typer.Option(
    None, "--agent-policy-hash", help="Expected agent policy hash for validation"
)
VERIFY_EVIDENCE_ARG = typer.Argument(..., help="Path to evidence pack JSON")
VERIFY_KEY_OPT = typer.Option(..., "--sign-key", help="HMAC key used to sign evidence")
VERIFY_JSON_OPT = typer.Option(False, "--json", help="Emit machine-readable JSON output")
VALIDATE_SPEC_OPT = typer.Option(..., "--spec", help="Path to module spec YAML/JSON")
VALIDATE_RESULT_OPT = typer.Option(None, "--result", help="Path to module result JSON")
SCHEMA_OUT_OPT = typer.Option(..., "--out", help="Output directory for JSON schemas")
REPORT_EVIDENCE_ARG = typer.Argument(..., help="Path to evidence pack JSON")
REPORT_JSON_OPT = typer.Option(False, "--json", help="Emit machine-readable JSON output")
REPORT_EXIT_NONZERO_OPT = typer.Option(
    False,
    "--exit-nonzero",
    help="Exit with code 1 if any module failed/errored (code 2 is reserved for invalid inputs)",
)
VALIDATE_SUMMARY_ARG = typer.Argument(..., help="Path to summary JSON")
VALIDATE_SUMMARY_JSON_OPT = typer.Option(False, "--json", help="Emit machine-readable JSON output")
DIFF_SUMMARY_GOLDEN_ARG = typer.Argument(..., help="Path to golden summary JSON")
DIFF_SUMMARY_CANDIDATE_ARG = typer.Argument(..., help="Path to candidate summary JSON")
DIFF_SUMMARY_JSON_OPT = typer.Option(False, "--json", help="Emit machine-readable JSON output")
DIFF_SUMMARY_IGNORE_OPT = typer.Option(
    None,
    "--ignore-field",
    help="Top-level fields to ignore (repeatable)",
)
POLICY_HASH_ARG = typer.Argument(..., help="Path to policy YAML/JSON")
POLICY_HASH_JSON_OPT = typer.Option(False, "--json", help="Emit machine-readable JSON output")
VALIDATE_CAMPAIGN_ARG = typer.Argument(..., help="Path to campaign YAML")
VALIDATE_CAMPAIGN_POLICY_OPT = typer.Option(
    None, "--policy", help="Policy YAML/JSON path with allowlists"
)
VALIDATE_CAMPAIGN_JSON_OPT = typer.Option(False, "--json", help="Emit machine-readable JSON output")

EXAMPLE_CAMPAIGN = """version: v1
name: "basic-campaign"
targets:
  - id: "local-host"
    name: "Local Host"
    tags: ["dev"]
modules:
  - id: "noop-1"
    module: "noop"
    target_id: "local-host"
    scope_allowlist: ["local"]
    expectations: {}
    params: {}
  - id: "echo-1"
    module: "echo_expectation"
    target_id: "local-host"
    scope_allowlist: ["local"]
    expectations:
      expected_value: "ok"
    params:
      value: "ok"
"""


@app.command()
def init(path: Path = INIT_PATH_ARG) -> None:
    if path.exists():
        raise typer.BadParameter(f"File already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(EXAMPLE_CAMPAIGN)
    typer.echo(f"Wrote example campaign to {path}")


@app.command()
def run(
    campaign: Path = CAMPAIGN_ARG,
    out: Path = OUT_OPT,
    deterministic: bool = DETERMINISTIC_OPT,
    sign_key: str | None = SIGN_KEY_OPT,
    agent_url: str | None = AGENT_URL_OPT,
    agent_enabled: bool = AGENT_ENABLED_OPT,
    agent_cert: str | None = AGENT_CERT_OPT,
    agent_key: str | None = AGENT_KEY_OPT,
    agent_ca: str | None = AGENT_CA_OPT,
    agent_insecure: bool = AGENT_INSECURE_OPT,
    policy_path: Path | None = POLICY_OPT,
    agent_id: str | None = AGENT_ID_OPT,
    agent_policy_hash: str | None = AGENT_POLICY_HASH_OPT,
) -> None:
    try:
        spec = load_campaign(campaign)
    except CampaignLoadError as exc:
        raise typer.BadParameter(str(exc)) from exc

    policy = None
    if policy_path is not None:
        try:
            policy = load_policy(policy_path)
        except CampaignLoadError as exc:
            raise typer.BadParameter(str(exc)) from exc

    agent_config = None
    if agent_enabled:
        if not agent_url:
            raise typer.BadParameter("--agent-url is required when --agent-enabled is set")
        agent_config = AgentClientConfig(
            base_url=agent_url,
            cert_path=agent_cert,
            key_path=agent_key,
            ca_path=agent_ca,
            enabled=True,
            agent_id=agent_id,
            expected_policy_hash=agent_policy_hash,
            allow_insecure_http=agent_insecure,
        )
    evidence = run_campaign(
        spec,
        deterministic=deterministic,
        agent_config=agent_config,
        policy=policy,
    )
    if sign_key:
        evidence = sign_evidence(evidence, sign_key)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence.model_dump(mode="json"), indent=2, sort_keys=True))
    typer.echo(f"Wrote evidence pack to {out}")


@app.command()
def modules() -> None:
    for name in list_modules():
        typer.echo(name)


@app.command()
def verify(
    evidence_path: Path = VERIFY_EVIDENCE_ARG,
    sign_key: str = VERIFY_KEY_OPT,
    json_output: bool = VERIFY_JSON_OPT,
) -> None:
    if not evidence_path.exists():
        raise typer.BadParameter(f"Evidence file not found: {evidence_path}")
    try:
        payload = json.loads(evidence_path.read_text())
    except json.JSONDecodeError as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "reason": "invalid_json"}))
        raise typer.Exit(code=2) from exc
    try:
        evidence = EvidencePack.model_validate(payload)
    except ValidationError as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "reason": "invalid_schema"}))
        raise typer.Exit(code=2) from exc
    if not evidence.signature or not evidence.signature_alg:
        if json_output:
            typer.echo(json.dumps({"ok": False, "reason": "missing_signature"}))
        raise typer.Exit(code=1)
    ok = verify_evidence(evidence, sign_key)
    if not ok:
        if json_output:
            typer.echo(json.dumps({"ok": False, "reason": "invalid_signature"}))
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(json.dumps({"ok": True}))
    else:
        typer.echo("evidence signature ok")


@app.command()
def validate_module(
    spec_path: Path = VALIDATE_SPEC_OPT,
    result_path: Path | None = VALIDATE_RESULT_OPT,
) -> None:
    if not spec_path.exists():
        raise typer.BadParameter(f"Spec file not found: {spec_path}")
    try:
        raw_spec = _load_payload(spec_path)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    ModuleSpec.model_validate(raw_spec)

    if result_path is not None:
        if not result_path.exists():
            raise typer.BadParameter(f"Result file not found: {result_path}")
        try:
            raw_result = _load_payload(result_path)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        ModuleResult.model_validate(raw_result)

    typer.echo("module spec ok")


def _load_payload(path: Path) -> object:
    content = path.read_text()
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(content)
    if path.suffix.lower() == ".json":
        return json.loads(content)
    raise ValueError(f"Unsupported file type: {path}")


@app.command()
def export_schemas(out: Path = SCHEMA_OUT_OPT) -> None:
    dump_schemas(out)
    typer.echo(f"wrote schemas to {out}")


@app.command()
def report(
    evidence_path: Path = REPORT_EVIDENCE_ARG,
    json_output: bool = REPORT_JSON_OPT,
    exit_nonzero: bool = REPORT_EXIT_NONZERO_OPT,
) -> None:
    if not evidence_path.exists():
        raise typer.BadParameter(f"Evidence file not found: {evidence_path}")
    try:
        payload = json.loads(evidence_path.read_text())
    except json.JSONDecodeError as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "reason": "invalid_json"}))
        raise typer.Exit(code=2) from exc

    try:
        evidence = EvidencePack.model_validate(payload)
    except ValidationError as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "reason": "invalid_schema"}))
        raise typer.Exit(code=2) from exc

    counts = {"total": 0, "passed": 0, "failed": 0, "errored": 0, "skipped": 0}
    for result in evidence.results:
        counts["total"] += 1
        if result.status == "pass":
            counts["passed"] += 1
        elif result.status == "fail":
            counts["failed"] += 1
        elif result.status == "error":
            counts["errored"] += 1
        else:
            counts["skipped"] += 1

    ok = counts["failed"] == 0 and counts["errored"] == 0

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "ok": ok,
                    "campaign_name": evidence.campaign_name,
                    "run_id": evidence.run_id,
                    "started_at": evidence.started_at.isoformat(),
                    "finished_at": evidence.finished_at.isoformat(),
                    "score": evidence.score,
                    "summary": counts,
                    "results": [
                        {
                            "module_id": result.module_id,
                            "status": result.status,
                            "notes": result.notes,
                            "duration_ms": int(
                                (result.finished_at - result.started_at).total_seconds() * 1000
                            ),
                            "evidence_ref": f"$.results[{index}].evidence",
                        }
                        for index, result in enumerate(evidence.results)
                    ],
                },
                sort_keys=True,
            )
        )
        if exit_nonzero and not ok:
            raise typer.Exit(code=1)
        return

    typer.echo(f"Campaign: {evidence.campaign_name}")
    typer.echo(f"Run ID:   {evidence.run_id}")
    typer.echo(f"Started:  {evidence.started_at.isoformat()}")
    typer.echo(f"Finished: {evidence.finished_at.isoformat()}")
    typer.echo(
        "Score:    "
        f"{evidence.score:.2f} (passed {counts['passed']}/{counts['total']}; "
        f"failed {counts['failed']}; errored {counts['errored']}; skipped {counts['skipped']})"
    )
    typer.echo("")
    typer.echo("Modules")

    module_col = max(len("module_id"), max((len(r.module_id) for r in evidence.results), default=0))
    status_col = max(len("status"), max((len(r.status) for r in evidence.results), default=0))
    duration_col = len("duration_ms")

    typer.echo(
        f"{'module_id'.ljust(module_col)}  "
        f"{'status'.ljust(status_col)}  "
        f"{'duration_ms'.ljust(duration_col)}  "
        "notes"
    )
    typer.echo(f"{'-' * module_col}  {'-' * status_col}  {'-' * duration_col}  -----")
    for result in evidence.results:
        notes = result.notes or ""
        duration_ms = int((result.finished_at - result.started_at).total_seconds() * 1000)
        typer.echo(
            f"{result.module_id.ljust(module_col)}  "
            f"{result.status.ljust(status_col)}  "
            f"{str(duration_ms).ljust(duration_col)}  "
            f"{notes}"
        )

    if exit_nonzero and not ok:
        raise typer.Exit(code=1)


@app.command()
def validate_summary(
    summary_path: Path = VALIDATE_SUMMARY_ARG,
    json_output: bool = VALIDATE_SUMMARY_JSON_OPT,
) -> None:
    if not summary_path.exists():
        raise typer.BadParameter(f"Summary file not found: {summary_path}")
    try:
        payload = json.loads(summary_path.read_text())
    except json.JSONDecodeError as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "reason": "invalid_json"}))
        raise typer.Exit(code=2) from exc

    errors = validate_summary_payload(payload)
    ok = not errors
    if json_output:
        typer.echo(json.dumps({"ok": ok, "errors": errors}, sort_keys=True))
        if not ok:
            raise typer.Exit(code=1)
        return

    if ok:
        typer.echo("summary ok")
        return
    typer.echo("summary invalid")
    for error in errors:
        typer.echo(f"- {error}")
    raise typer.Exit(code=1)


@app.command()
def diff_summary(
    golden_path: Path = DIFF_SUMMARY_GOLDEN_ARG,
    candidate_path: Path = DIFF_SUMMARY_CANDIDATE_ARG,
    json_output: bool = DIFF_SUMMARY_JSON_OPT,
    ignore_field: list[str] | None = DIFF_SUMMARY_IGNORE_OPT,
) -> None:
    if not golden_path.exists():
        raise typer.BadParameter(f"Golden summary not found: {golden_path}")
    if not candidate_path.exists():
        raise typer.BadParameter(f"Candidate summary not found: {candidate_path}")

    try:
        golden_payload = json.loads(golden_path.read_text())
        candidate_payload = json.loads(candidate_path.read_text())
    except json.JSONDecodeError as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "reason": "invalid_json"}))
        raise typer.Exit(code=2) from exc

    diffs = diff_summary_payload(
        golden_payload,
        candidate_payload,
        ignore_fields=ignore_field or [],
    )
    ok = not diffs
    if json_output:
        typer.echo(json.dumps({"ok": ok, "diffs": diffs}, sort_keys=True))
        if not ok:
            raise typer.Exit(code=1)
        return

    if ok:
        typer.echo("summary matches golden")
        return
    typer.echo("summary drift detected")
    for diff in diffs:
        typer.echo(f"- {diff}")
    raise typer.Exit(code=1)


@app.command()
def policy_hash(
    policy_path: Path = POLICY_HASH_ARG,
    json_output: bool = POLICY_HASH_JSON_OPT,
) -> None:
    try:
        policy = load_policy(policy_path)
    except CampaignLoadError as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "reason": "invalid_policy"}))
        raise typer.Exit(code=2) from exc

    digest = compute_policy_hash(policy)
    if json_output:
        typer.echo(json.dumps({"ok": True, "policy_hash": digest}, sort_keys=True))
        return
    typer.echo(digest)


@app.command()
def validate_campaign(
    campaign: Path = VALIDATE_CAMPAIGN_ARG,
    policy_path: Path | None = VALIDATE_CAMPAIGN_POLICY_OPT,
    json_output: bool = VALIDATE_CAMPAIGN_JSON_OPT,
) -> None:
    policy = None
    if policy_path is not None:
        try:
            policy = load_policy(policy_path)
        except CampaignLoadError as exc:
            if json_output:
                typer.echo(json.dumps({"ok": False, "reason": "invalid_policy"}))
            raise typer.Exit(code=2) from exc

    try:
        spec = load_campaign(campaign)
    except CampaignLoadError as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "reason": "invalid_campaign"}))
        raise typer.Exit(code=2) from exc
    except ValidationError as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "reason": "invalid_campaign_schema"}))
        raise typer.Exit(code=2) from exc

    target_ids = {target.id for target in spec.targets}
    errors: list[dict[str, str]] = []

    for module_spec in spec.modules:
        if module_spec.target_id not in target_ids:
            errors.append(
                {
                    "code": "unknown_target",
                    "module_id": module_spec.id,
                    "message": f"Unknown target_id: {module_spec.target_id}",
                }
            )

        try:
            get_module(module_spec.module)
        except KeyError:
            errors.append(
                {
                    "code": "unknown_module",
                    "module_id": module_spec.id,
                    "message": f"Unknown module: {module_spec.module}",
                }
            )

        allowlist = effective_allowlist(module_spec, policy)
        if not allowlist:
            errors.append(
                {
                    "code": "empty_allowlist",
                    "module_id": module_spec.id,
                    "message": "Effective scope allowlist is empty",
                }
            )

    ok = not errors

    if json_output:
        typer.echo(json.dumps({"ok": ok, "errors": errors}, sort_keys=True))
        if not ok:
            raise typer.Exit(code=1)
        return

    if ok:
        typer.echo("campaign ok")
        return

    typer.echo("campaign invalid")
    for error in errors:
        module_id = error.get("module_id", "?")
        typer.echo(f"- [{error['code']}] {module_id}: {error['message']}")
    raise typer.Exit(code=1)
