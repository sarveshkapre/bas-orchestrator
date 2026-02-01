from __future__ import annotations

from pathlib import Path

from bas_orchestrator.agent_client import AgentClientConfig
from bas_orchestrator.engine import load_campaign, run_campaign


def write_campaign(path: Path) -> None:
    path.write_text(
        """
version: v1
name: "agent-campaign"
targets:
  - id: "local-host"
    name: "Local Host"
modules:
  - id: "noop-1"
    module: "noop"
    target_id: "local-host"
    scope_allowlist: ["local"]
    expectations: {}
    params: {}
"""
    )


def test_agent_capability_missing(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    write_campaign(campaign_path)

    spec = load_campaign(campaign_path)
    agent_config = AgentClientConfig(
        base_url="mock://agent",
        enabled=True,
        mock_capabilities=["other"],
    )
    evidence = run_campaign(spec, deterministic=True, agent_config=agent_config)

    assert evidence.summary["errored"] == 1


def test_agent_policy_hash_mismatch(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    write_campaign(campaign_path)

    spec = load_campaign(campaign_path)
    agent_config = AgentClientConfig(
        base_url="mock://agent",
        enabled=True,
        mock_capabilities=["noop"],
        mock_policy_hash="abc",
        expected_policy_hash="def",
    )
    evidence = run_campaign(spec, deterministic=True, agent_config=agent_config)

    assert evidence.summary["errored"] == 1
