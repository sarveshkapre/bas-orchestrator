from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from bas_orchestrator.cli import app


def _write_summary(path: Path, *, score: float, run_id: str) -> None:
    path.write_text(
        json.dumps(
            {
                "ok": True,
                "campaign_name": "test",
                "run_id": run_id,
                "started_at": "1970-01-01T00:00:00+00:00",
                "finished_at": "1970-01-01T00:00:00+00:00",
                "score": score,
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


def test_diff_summary_matches(tmp_path: Path) -> None:
    golden = tmp_path / "golden.json"
    candidate = tmp_path / "candidate.json"
    _write_summary(golden, score=1.0, run_id="run-1")
    _write_summary(candidate, score=1.0, run_id="run-1")

    runner = CliRunner()
    result = runner.invoke(app, ["diff-summary", str(golden), str(candidate), "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {"diffs": [], "ok": True}


def test_diff_summary_detects_drift(tmp_path: Path) -> None:
    golden = tmp_path / "golden.json"
    candidate = tmp_path / "candidate.json"
    _write_summary(golden, score=1.0, run_id="run-1")
    _write_summary(candidate, score=0.5, run_id="run-2")

    runner = CliRunner()
    result = runner.invoke(app, ["diff-summary", str(golden), str(candidate), "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout.strip())
    assert payload["ok"] is False
    assert payload["diffs"]


def test_diff_summary_ignore_field(tmp_path: Path) -> None:
    golden = tmp_path / "golden.json"
    candidate = tmp_path / "candidate.json"
    _write_summary(golden, score=1.0, run_id="run-1")
    _write_summary(candidate, score=1.0, run_id="run-2")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "diff-summary",
            str(golden),
            str(candidate),
            "--json",
            "--ignore-field",
            "run_id",
        ],
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {"diffs": [], "ok": True}
