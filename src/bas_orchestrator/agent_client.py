from __future__ import annotations

import json
import ssl
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from bas_orchestrator.models import ModuleResult


@dataclass(frozen=True)
class AgentClientConfig:
    base_url: str
    cert_path: str | None = None
    key_path: str | None = None
    ca_path: str | None = None
    enabled: bool = False
    timeout_seconds: float = 10.0
    agent_id: str | None = None
    expected_policy_hash: str | None = None
    allow_insecure_http: bool = False
    mock_capabilities: list[str] | None = None
    mock_policy_hash: str | None = None


class AgentClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class HandshakeResult:
    agent_id: str
    capabilities: list[str]
    policy_hash: str | None


class AgentClient:
    def __init__(self, config: AgentClientConfig) -> None:
        self._config = config
        self._handshake: HandshakeResult | None = None

    def handshake(
        self,
        *,
        agent_id: str | None,
        capabilities: list[str],
        version: str,
        expected_policy_hash: str | None,
    ) -> HandshakeResult:
        if not self._config.enabled:
            raise AgentClientError("Agent client disabled")
        if self._config.base_url.startswith("http://") and not self._config.allow_insecure_http:
            raise AgentClientError("Insecure agent URL; use https:// or allow_insecure_http")
        if (self._config.cert_path and not self._config.key_path) or (
            self._config.key_path and not self._config.cert_path
        ):
            raise AgentClientError("Both cert_path and key_path are required for TLS client auth")

        if self._config.base_url.startswith("mock://"):
            result = HandshakeResult(
                agent_id=agent_id or "mock-agent",
                capabilities=self._config.mock_capabilities or capabilities,
                policy_hash=self._config.mock_policy_hash,
            )
            self._validate_handshake(result, capabilities)
            self._validate_policy_hash(result, expected_policy_hash)
            self._handshake = result
            return result

        payload = {
            "agent_id": agent_id or "orchestrator",
            "capabilities": capabilities,
            "version": version,
        }
        response = self._post_json("/v1/agent/handshake", payload)
        result = HandshakeResult(
            agent_id=str(response.get("agent_id", "")),
            capabilities=list(response.get("capabilities", [])),
            policy_hash=response.get("policy_hash"),
        )
        self._validate_handshake(result, capabilities)
        self._validate_policy_hash(result, expected_policy_hash)
        self._handshake = result
        return result

    def execute_module(self, payload: dict[str, Any]) -> ModuleResult:
        if not self._config.enabled:
            raise AgentClientError("Agent client disabled")
        if self._handshake is None:
            raise AgentClientError("Agent handshake required before execution")
        if payload.get("module") not in self._handshake.capabilities:
            raise AgentClientError("Agent missing capability for module")
        if self._config.base_url.startswith("mock://"):
            now = datetime.now(UTC).isoformat()
            timestamp = payload.get("scope", {}).get("expires_at") or now
            return ModuleResult.model_validate(
                {
                    "module_id": payload.get("module_id", "unknown"),
                    "status": "pass",
                    "started_at": timestamp,
                    "finished_at": timestamp,
                    "evidence": {"mock": True},
                    "notes": "mock agent result",
                }
            )
        response = self._post_json("/v1/agent/modules/execute", payload)
        return ModuleResult.model_validate(response)

    def _ssl_context(self) -> ssl.SSLContext:
        context = ssl.create_default_context()
        if self._config.ca_path:
            context.load_verify_locations(self._config.ca_path)
        if self._config.cert_path and self._config.key_path:
            context.load_cert_chain(self._config.cert_path, self._config.key_path)
        return context

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._config.base_url.rstrip('/')}{path}"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        context = self._ssl_context()
        try:
            with urllib.request.urlopen(
                request, timeout=self._config.timeout_seconds, context=context
            ) as res:
                body = res.read().decode("utf-8")
        except Exception as exc:  # pragma: no cover - network path
            raise AgentClientError(f"Agent request failed: {exc}") from exc

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:  # pragma: no cover - network path
            raise AgentClientError("Agent returned invalid JSON") from exc

        if not isinstance(payload, dict):
            raise AgentClientError("Agent returned invalid payload")
        return payload

    def _validate_policy_hash(
        self, result: HandshakeResult, expected_policy_hash: str | None
    ) -> None:
        if expected_policy_hash and expected_policy_hash != result.policy_hash:
            raise AgentClientError("Agent policy hash mismatch")

    def _validate_handshake(self, result: HandshakeResult, requested: list[str]) -> None:
        if not result.agent_id:
            raise AgentClientError("Agent handshake missing agent_id")
        if not result.capabilities:
            raise AgentClientError("Agent handshake missing capabilities")
        if any(
            not isinstance(capability, str) or not capability for capability in result.capabilities
        ):
            raise AgentClientError("Agent handshake returned invalid capability")
        missing = set(requested) - set(result.capabilities)
        if missing:
            raise AgentClientError("Agent missing requested capabilities")
