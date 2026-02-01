from __future__ import annotations

import json
from pathlib import Path

from bas_orchestrator.agent_client import AgentClient, AgentClientConfig, AgentClientError


def test_agent_client_disabled_raises() -> None:
    client = AgentClient(AgentClientConfig(base_url="https://example", enabled=False))
    try:
        client.execute_module({"module_id": "noop"})
    except AgentClientError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("expected AgentClientError")


def test_agent_payload_roundtrip(tmp_path: Path) -> None:
    payload = {"run_id": "det-123", "module_id": "noop"}
    path = tmp_path / "payload.json"
    path.write_text(json.dumps(payload))
    assert json.loads(path.read_text()) == payload


def test_mock_handshake_and_execute() -> None:
    client = AgentClient(
        AgentClientConfig(
            base_url="mock://agent",
            enabled=True,
            mock_capabilities=["noop"],
            mock_policy_hash="abc",
        )
    )
    result = client.handshake(
        agent_id="agent-1",
        capabilities=["noop"],
        version="v1",
        expected_policy_hash="abc",
    )
    assert result.agent_id == "agent-1"
    assert "noop" in result.capabilities
    module = client.execute_module(
        {
            "module_id": "noop-1",
            "module": "noop",
            "scope": {"expires_at": "1970-01-01T00:00:00+00:00"},
        }
    )
    assert module.status == "pass"
