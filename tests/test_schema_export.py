from __future__ import annotations

import json
from pathlib import Path

from bas_orchestrator.schema import dump_schemas


def test_dump_schemas(tmp_path: Path) -> None:
    dump_schemas(tmp_path)
    campaign = tmp_path / "campaign.schema.json"
    evidence = tmp_path / "evidence.schema.json"

    assert campaign.exists()
    assert evidence.exists()
    assert json.loads(campaign.read_text())["title"] == "CampaignSpec"
    assert json.loads(evidence.read_text())["title"] == "EvidencePack"
