from __future__ import annotations

import json
from pathlib import Path

from bas_orchestrator.models import CampaignSpec, EvidencePack


def dump_schemas(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    campaign = CampaignSpec.model_json_schema()
    evidence = EvidencePack.model_json_schema()
    (out_dir / "campaign.schema.json").write_text(json.dumps(campaign, indent=2, sort_keys=True))
    (out_dir / "evidence.schema.json").write_text(json.dumps(evidence, indent=2, sort_keys=True))
