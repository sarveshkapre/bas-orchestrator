# PLAN

## Goal
Ship a local-first BAS campaign orchestrator that runs bounded modules, collects evidence, and scores control coverage with repeatable outputs.

## Scope (MVP)
- Campaign spec (YAML) with targets, modules, schedules, and expected outcomes.
- Local agent runner with bounded modules (simulated safe actions only).
- Evidence pack JSON output with timestamps, inputs, results, and score.
- Deterministic run mode for reproducible results.

## Non-goals (MVP)
- Multi-tenant auth, user accounts, SaaS features.
- Live exploit tooling or unsafe attack behaviors.
- Cloud scale scheduling or dynamic agent pools.

## Architecture
- CLI (`bas`) handles init and run workflows.
- Core engine loads campaign spec → validates → dispatches modules.
- Module registry contains safe, bounded module implementations.
- Evidence pack writer appends module results and scoring summary.

## Stack
- Python 3.11, Typer CLI, Pydantic for validation, PyYAML for campaign files.
- Ruff for lint/format, mypy for types, pytest for tests.

## Data contracts
- `CampaignSpec`: name, targets, modules, schedule, expectations.
- `ModuleResult`: status, evidence, duration, notes.
- `EvidencePack`: campaign metadata, run config, module results, score.

## Milestones
1. Scaffold repo + CLI skeleton + example campaign.
2. Validate campaign specs with Pydantic.
3. Implement local runner + module registry.
4. Evidence pack writer + scoring rules.
5. Add tests, CI, and docs polish.

## Risks
- Scope creep into unsafe behaviors. Mitigation: strict module interface and safe defaults.
- Ambiguous scoring. Mitigation: explicit expectations per module.
- Evidence format churn. Mitigation: versioned schema.
