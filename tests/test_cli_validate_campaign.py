from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from bas_orchestrator.cli import app


def test_validate_campaign_ok(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    campaign_path.write_text(
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
"""
    )

    runner = CliRunner()
    result = runner.invoke(app, ["validate-campaign", str(campaign_path), "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {"errors": [], "ok": True}


def test_validate_campaign_reports_errors(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    campaign_path.write_text(
        """
version: v1
name: "test-campaign"
targets:
  - id: "local-host"
    name: "Local Host"
modules:
  - id: "bad-1"
    module: "does_not_exist"
    target_id: "nope"
    scope_allowlist: []
    expectations: {}
    params: {}
"""
    )

    runner = CliRunner()
    result = runner.invoke(app, ["validate-campaign", str(campaign_path), "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout.strip())
    assert payload["ok"] is False
    codes = {error["code"] for error in payload["errors"]}
    assert codes == {"unknown_module", "unknown_target", "empty_allowlist"}


def test_validate_campaign_invalid_policy(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    campaign_path.write_text(
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
"""
    )
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text("this is: [not valid: yaml")

    runner = CliRunner()
    result = runner.invoke(
        app, ["validate-campaign", str(campaign_path), "--policy", str(policy_path), "--json"]
    )
    assert result.exit_code == 2
    assert json.loads(result.stdout.strip()) == {"ok": False, "reason": "invalid_policy"}
