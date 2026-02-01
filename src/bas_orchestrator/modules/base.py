from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from bas_orchestrator.models import ModuleResult


@dataclass(frozen=True)
class ModuleContext:
    module_id: str
    target_id: str
    params: dict[str, Any]
    expectations: dict[str, Any]
    scope_allowlist: list[str]


class Module:
    name: str = "base"

    def run(self, context: ModuleContext) -> ModuleResult:
        started_at = datetime.now(UTC)
        finished_at = datetime.now(UTC)
        return ModuleResult(
            module_id=context.module_id,
            status="skipped",
            started_at=started_at,
            finished_at=finished_at,
            evidence={"reason": "base module"},
        )
