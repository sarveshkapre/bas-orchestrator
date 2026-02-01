from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml

from bas_orchestrator.agent_client import AgentClientConfig
from bas_orchestrator.engine import (
    CampaignLoadError,
    load_campaign,
    load_policy,
    run_campaign,
    sign_evidence,
    verify_evidence,
)
from bas_orchestrator.models import EvidencePack, ModuleResult, ModuleSpec
from bas_orchestrator.modules.registry import list_modules
from bas_orchestrator.schema import dump_schemas

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
    evidence = EvidencePack.model_validate(payload)
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
