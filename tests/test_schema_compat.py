from __future__ import annotations

from bas_orchestrator.models import CampaignSpec, EvidencePack


def test_campaign_schema_contract() -> None:
    schema = CampaignSpec.model_json_schema()

    assert schema["type"] == "object"
    assert set(schema["required"]) == {"name", "targets", "modules"}
    assert schema["properties"]["version"]["default"] == "v1"

    target = schema["$defs"]["Target"]
    assert {"id", "name", "tags"} <= set(target["properties"].keys())


def test_evidence_schema_contract() -> None:
    schema = EvidencePack.model_json_schema()

    required = {
        "campaign_name",
        "run_id",
        "started_at",
        "finished_at",
        "results",
        "score",
        "summary",
    }
    assert required <= set(schema["required"])
    assert schema["properties"]["schema_version"]["default"] == "v1"

    module_result = schema["$defs"]["ModuleResult"]
    assert set(module_result["properties"]["status"]["enum"]) == {
        "pass",
        "fail",
        "skipped",
        "error",
    }
