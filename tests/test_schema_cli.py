from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from bas_orchestrator.cli import app


def test_export_schemas_cli(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["export-schemas", "--out", str(tmp_path)])
    assert result.exit_code == 0
    campaign = tmp_path / "campaign.schema.json"
    evidence = tmp_path / "evidence.schema.json"
    assert campaign.exists()
    assert evidence.exists()
    assert json.loads(campaign.read_text())["title"] == "CampaignSpec"
