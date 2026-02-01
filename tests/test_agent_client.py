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


def test_handshake_rejects_insecure_http() -> None:
    client = AgentClient(AgentClientConfig(base_url="http://agent", enabled=True))
    try:
        client.handshake(
            agent_id="agent-1",
            capabilities=["noop"],
            version="v1",
            expected_policy_hash=None,
        )
    except AgentClientError as exc:
        assert "Insecure" in str(exc)
    else:
        raise AssertionError("expected AgentClientError")


def test_handshake_requires_capabilities() -> None:
    client = AgentClient(AgentClientConfig(base_url="mock://agent", enabled=True))
    try:
        client.handshake(
            agent_id="agent-1",
            capabilities=[],
            version="v1",
            expected_policy_hash=None,
        )
    except AgentClientError as exc:
        assert "capabilities" in str(exc)
    else:
        raise AssertionError("expected AgentClientError")


def test_handshake_rejects_missing_requested_capability() -> None:
    client = AgentClient(
        AgentClientConfig(base_url="mock://agent", enabled=True, mock_capabilities=["noop"])
    )
    try:
        client.handshake(
            agent_id="agent-1",
            capabilities=["noop", "echo_expectation"],
            version="v1",
            expected_policy_hash=None,
        )
    except AgentClientError as exc:
        assert "requested capabilities" in str(exc)
    else:
        raise AssertionError("expected AgentClientError")


def test_handshake_requires_cert_and_key_pair() -> None:
    client = AgentClient(
        AgentClientConfig(base_url="mock://agent", enabled=True, cert_path="cert.pem")
    )
    try:
        client.handshake(
            agent_id="agent-1",
            capabilities=["noop"],
            version="v1",
            expected_policy_hash=None,
        )
    except AgentClientError as exc:
        assert "cert_path and key_path" in str(exc)
    else:
        raise AssertionError("expected AgentClientError")


def test_ca_bundle_error_message(tmp_path: Path) -> None:
    bad_ca = tmp_path / "missing.pem"
    client = AgentClient(
        AgentClientConfig(
            base_url="https://agent",
            enabled=True,
            ca_path=str(bad_ca),
            mock_capabilities=["noop"],
        )
    )
    try:
        client.handshake(
            agent_id="agent-1",
            capabilities=["noop"],
            version="v1",
            expected_policy_hash=None,
        )
    except AgentClientError as exc:
        assert "CA bundle" in str(exc)
    else:
        raise AssertionError("expected AgentClientError")
