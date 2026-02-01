from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from bas_orchestrator.cli import app
from bas_orchestrator.engine import load_campaign, run_campaign, sign_evidence


def write_campaign(path: Path) -> None:
    path.write_text(
        """
version: v1
name: "test-campaign"
targets:
  - id: "local-host"
    name: "Local Host"
modules:
  - id: "noop-1"
    module: "noop"
    target_id: "local-host"
    expectations: {}
    params: {}
"""
    )


def test_sign_and_verify_json_roundtrip(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    write_campaign(campaign_path)

    spec = load_campaign(campaign_path)
    evidence = run_campaign(spec, deterministic=True)
    signed = sign_evidence(evidence, "test-key")

    payload = json.loads(signed.model_dump_json())
    assert payload["signature_alg"] == "hmac-sha256"
    assert payload["signature"]


def test_verify_command_json_output(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    write_campaign(campaign_path)

    spec = load_campaign(campaign_path)
    evidence = run_campaign(spec, deterministic=True)
    signed = sign_evidence(evidence, "test-key")

    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(signed.model_dump_json())

    runner = CliRunner()
    result = runner.invoke(app, ["verify", str(evidence_path), "--sign-key", "test-key", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {"ok": True}
