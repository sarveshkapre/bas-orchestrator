from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from bas_orchestrator.cli import app


def test_validate_module_command(tmp_path: Path) -> None:
    spec = tmp_path / "module_spec.yaml"
    result_path = tmp_path / "module_result.json"

    spec.write_text(
        """
id: "echo-1"
module: "echo_expectation"
target_id: "local-host"
scope_allowlist:
  - "local"
expectations:
  expected_value: "ok"
params:
  value: "ok"
"""
    )
    result_path.write_text(
        """
{
  "module_id": "echo-1",
  "status": "pass",
  "started_at": "1970-01-01T00:00:00+00:00",
  "finished_at": "1970-01-01T00:00:00+00:00",
  "evidence": {"expected": "ok", "observed": "ok"},
  "notes": null
}
"""
    )

    runner = CliRunner()
    run = runner.invoke(
        app,
        [
            "validate-module",
            "--spec",
            str(spec),
            "--result",
            str(result_path),
        ],
    )
    assert run.exit_code == 0
    assert "module spec ok" in run.stdout
