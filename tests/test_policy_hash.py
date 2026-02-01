from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from bas_orchestrator.cli import app
from bas_orchestrator.engine import compute_policy_hash, load_policy


def test_policy_hash_stable(tmp_path: Path) -> None:
    path = tmp_path / "policy.yaml"
    path.write_text(
        """
version: v1
allowlist: ["local"]
targets:
  local-host:
    allowlist: ["local"]
"""
    )
    policy = load_policy(path)
    digest_a = compute_policy_hash(policy)
    digest_b = compute_policy_hash(policy)
    assert digest_a == digest_b


def test_policy_hash_changes_with_content(tmp_path: Path) -> None:
    path_a = tmp_path / "policy_a.yaml"
    path_b = tmp_path / "policy_b.yaml"
    path_a.write_text(
        """
version: v1
allowlist: ["local"]
"""
    )
    path_b.write_text(
        """
version: v1
allowlist: ["prod"]
"""
    )
    digest_a = compute_policy_hash(load_policy(path_a))
    digest_b = compute_policy_hash(load_policy(path_b))
    assert digest_a != digest_b


def test_policy_hash_cli_json(tmp_path: Path) -> None:
    path = tmp_path / "policy.yaml"
    path.write_text(
        """
version: v1
allowlist: ["local"]
"""
    )
    runner = CliRunner()
    result = runner.invoke(app, ["policy-hash", str(path), "--json"])
    assert result.exit_code == 0
    assert "policy_hash" in result.stdout
