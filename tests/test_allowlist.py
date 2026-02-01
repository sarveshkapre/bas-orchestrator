from __future__ import annotations

from datetime import UTC, datetime

from bas_orchestrator.modules.base import ModuleContext
from bas_orchestrator.modules.registry import NoopModule


def test_allowlist_required() -> None:
    module = NoopModule()
    context = ModuleContext(
        module_id="noop-1",
        target_id="local-host",
        params={},
        expectations={},
        scope_allowlist=[],
    )
    result = module.run(context)
    assert result.status == "error"
    assert result.evidence["error"] == "empty allowlist"
    assert result.started_at.tzinfo is not None
    assert result.finished_at.tzinfo is not None
    assert result.started_at <= datetime.now(UTC)
