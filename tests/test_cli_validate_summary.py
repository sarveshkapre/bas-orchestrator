from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from bas_orchestrator.cli import app


def test_validate_summary_ok(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "ok": True,
                "campaign_name": "test",
                "run_id": "run-1",
                "started_at": "1970-01-01T00:00:00+00:00",
                "finished_at": "1970-01-01T00:00:00+00:00",
                "score": 1.0,
                "summary": {"total": 1, "passed": 1, "failed": 0, "errored": 0, "skipped": 0},
                "results": [
                    {
                        "module_id": "noop-1",
                        "status": "pass",
                        "notes": None,
                        "duration_ms": 0,
                        "evidence_ref": "$.results[0].evidence",
                    }
                ],
            }
        )
    )

    runner = CliRunner()
    result = runner.invoke(app, ["validate-summary", str(summary_path), "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {"errors": [], "ok": True}


def test_validate_summary_invalid_json(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text("{not json")

    runner = CliRunner()
    result = runner.invoke(app, ["validate-summary", str(summary_path), "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout.strip()) == {"ok": False, "reason": "invalid_json"}


def test_validate_summary_missing_fields(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps({"ok": True}))

    runner = CliRunner()
    result = runner.invoke(app, ["validate-summary", str(summary_path), "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout.strip())
    assert payload["ok"] is False
    assert any("missing field" in error for error in payload["errors"])
