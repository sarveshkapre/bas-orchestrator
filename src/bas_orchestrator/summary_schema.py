from __future__ import annotations

from typing import Any


def build_summary_schema() -> dict[str, Any]:
    return {
        "title": "EvidenceSummary",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "ok",
            "campaign_name",
            "run_id",
            "started_at",
            "finished_at",
            "score",
            "summary",
            "results",
        ],
        "properties": {
            "ok": {"type": "boolean"},
            "campaign_name": {"type": "string"},
            "run_id": {"type": "string"},
            "started_at": {"type": "string"},
            "finished_at": {"type": "string"},
            "score": {"type": "number"},
            "summary": {
                "type": "object",
                "additionalProperties": False,
                "required": ["total", "passed", "failed", "errored", "skipped"],
                "properties": {
                    "total": {"type": "integer", "minimum": 0},
                    "passed": {"type": "integer", "minimum": 0},
                    "failed": {"type": "integer", "minimum": 0},
                    "errored": {"type": "integer", "minimum": 0},
                    "skipped": {"type": "integer", "minimum": 0},
                },
            },
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["module_id", "status", "duration_ms", "evidence_ref"],
                    "properties": {
                        "module_id": {"type": "string"},
                        "status": {"type": "string"},
                        "notes": {"type": ["string", "null"]},
                        "duration_ms": {"type": "integer", "minimum": 0},
                        "evidence_ref": {"type": "string"},
                    },
                },
            },
        },
    }
