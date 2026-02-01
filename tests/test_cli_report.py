from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from bas_orchestrator.cli import app
from bas_orchestrator.engine import load_campaign, run_campaign


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
      value: "nope"
"""
    )


def test_report_command_text_output(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    write_campaign(campaign_path)

    spec = load_campaign(campaign_path)
    evidence = run_campaign(spec, deterministic=True)

    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(evidence.model_dump_json())

    runner = CliRunner()
    result = runner.invoke(app, ["report", str(evidence_path)])
    assert result.exit_code == 0
    assert "Campaign: test-campaign" in result.stdout
    assert "Modules" in result.stdout
    assert "noop-1" in result.stdout
    assert "echo-1" in result.stdout


def test_report_command_json_and_exit_code(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    write_campaign(campaign_path)

    spec = load_campaign(campaign_path)
    evidence = run_campaign(spec, deterministic=True)

    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(evidence.model_dump_json())

    runner = CliRunner()
    result = runner.invoke(app, ["report", str(evidence_path), "--json", "--exit-nonzero"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout.strip())
    assert payload["ok"] is False
    assert payload["summary"]["failed"] == 1
