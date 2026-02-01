from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from bas_orchestrator.models import ModuleResult
from bas_orchestrator.modules.base import Module, ModuleContext


class NoopModule(Module):
    name = "noop"

    def run(self, context: ModuleContext) -> ModuleResult:
        if not context.scope_allowlist:
            started_at = datetime.now(UTC)
            finished_at = datetime.now(UTC)
            return ModuleResult(
                module_id=context.module_id,
                status="error",
                started_at=started_at,
                finished_at=finished_at,
                evidence={"error": "empty allowlist"},
                notes="scope_allowlist must not be empty",
            )
        started_at = datetime.now(UTC)
        finished_at = datetime.now(UTC)
        return ModuleResult(
            module_id=context.module_id,
            status="pass",
            started_at=started_at,
            finished_at=finished_at,
            evidence={"message": "noop completed"},
        )


class EchoExpectationModule(Module):
    name = "echo_expectation"

    def run(self, context: ModuleContext) -> ModuleResult:
        if not context.scope_allowlist:
            started_at = datetime.now(UTC)
            finished_at = datetime.now(UTC)
            return ModuleResult(
                module_id=context.module_id,
                status="error",
                started_at=started_at,
                finished_at=finished_at,
                evidence={"error": "empty allowlist"},
                notes="scope_allowlist must not be empty",
            )
        started_at = datetime.now(UTC)
        expected = context.expectations.get("expected_value")
        observed = context.params.get("value")
        status: Literal["pass", "fail"] = "pass" if expected == observed else "fail"
        finished_at = datetime.now(UTC)
        return ModuleResult(
            module_id=context.module_id,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            evidence={"expected": expected, "observed": observed},
        )


_REGISTRY: dict[str, Module] = {
    NoopModule.name: NoopModule(),
    EchoExpectationModule.name: EchoExpectationModule(),
}


def get_module(name: str) -> Module:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown module: {name}")
    return _REGISTRY[name]


def list_modules() -> list[str]:
    return sorted(_REGISTRY.keys())
