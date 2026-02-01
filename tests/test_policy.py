from __future__ import annotations

from pathlib import Path

from bas_orchestrator.engine import load_campaign, load_policy, run_campaign


def write_campaign(path: Path) -> None:
    path.write_text(
        """
version: v1
name: "policy-campaign"
targets:
  - id: "local-host"
    name: "Local Host"
modules:
  - id: "noop-1"
    module: "noop"
    target_id: "local-host"
    scope_allowlist: []
    expectations: {}
    params: {}
"""
    )


def write_policy(path: Path) -> None:
    path.write_text(
        """
version: v1
allowlist:
  - "local"
"""
    )


def test_policy_allowlist_applies(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    policy_path = tmp_path / "policy.yaml"
    write_campaign(campaign_path)
    write_policy(policy_path)

    spec = load_campaign(campaign_path)
    policy = load_policy(policy_path)
    evidence = run_campaign(spec, deterministic=True, policy=policy)

    assert evidence.summary["passed"] == 1
