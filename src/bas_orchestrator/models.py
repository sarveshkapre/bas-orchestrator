from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Target(BaseModel):
    id: str
    name: str
    tags: list[str] = Field(default_factory=list)


class ModuleSpec(BaseModel):
    id: str
    module: str
    target_id: str
    expectations: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    scope_allowlist: list[str] = Field(default_factory=list)


class CampaignSpec(BaseModel):
    version: str = "v1"
    name: str
    targets: list[Target]
    modules: list[ModuleSpec]


class ModuleResult(BaseModel):
    module_id: str
    status: Literal["pass", "fail", "skipped", "error"]
    started_at: datetime
    finished_at: datetime
    evidence: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class EvidencePack(BaseModel):
    schema_version: str = "v1"
    campaign_name: str
    run_id: str
    started_at: datetime
    finished_at: datetime
    results: list[ModuleResult]
    score: float
    summary: dict[str, Any]
    signature_alg: str | None = None
    signature: str | None = None


class PolicyRule(BaseModel):
    allowlist: list[str] = Field(default_factory=list)


class PolicySpec(BaseModel):
    version: str = "v1"
    allowlist: list[str] = Field(default_factory=list)
    targets: dict[str, PolicyRule] = Field(default_factory=dict)
    modules: dict[str, PolicyRule] = Field(default_factory=dict)
