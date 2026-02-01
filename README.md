# BAS Orchestrator

SafeBreach-style campaign orchestrator for running bounded, reproducible BAS simulations, collecting evidence, and scoring control coverage.

Status: **backlog → scaffolded (in progress)**

## What it does
- Loads campaign specs (YAML) describing targets, modules, schedules, and success criteria.
- Dispatches modules to agents (local runner in MVP; remote agents later).
- Produces a signed evidence pack (JSON) with timestamps, module results, and scoring.

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

bas init examples/basic-campaign.yaml
bas run examples/basic-campaign.yaml --out evidence.json
bas run examples/basic-campaign.yaml --out evidence.json --deterministic
bas run examples/basic-campaign.yaml --out evidence.json --sign-key "dev-key"
bas verify evidence.json --sign-key "dev-key"
bas verify evidence.json --sign-key "dev-key" --json
bas report evidence.json
bas report evidence.json --exit-nonzero
bas validate-campaign examples/basic-campaign.yaml
bas validate-campaign examples/basic-campaign.yaml --json
bas validate-module --spec tests/fixtures/module_spec.yaml --result tests/fixtures/module_result.json
bas export-schemas --out schemas
bas run examples/basic-campaign.yaml --out evidence.json --agent-enabled --agent-url https://agent.local --agent-id agent-1
bas run examples/basic-campaign.yaml --out evidence.json --agent-enabled --agent-url http://agent.local --agent-insecure
bas run examples/basic-campaign.yaml --out evidence.json --policy tests/fixtures/policy.yaml
```

Schema export outputs: `campaign.schema.json`, `evidence.schema.json`, `summary.schema.json`.

## Example campaign
See `examples/basic-campaign.yaml` for a minimal end-to-end campaign spec.

## Docker
```bash
docker build -t bas-orchestrator .
```

## Security notes
- No authentication yet (local-first, single-operator MVP).
- Modules are strictly bounded and must declare prerequisites and safe scopes.
- Evidence packs are append-only and intended for audit workflows.
- Optional HMAC signing can be used for integrity verification in transit.

## Project docs
- `docs/PLAN.md`
- `docs/PROJECT.md`
- `docs/ROADMAP.md`
- `docs/specs/AGENT_API.md`
- `docs/specs/MODULE_SDK.md`
- `docs/specs/SCHEMA_EXPORT.md`
- `docs/specs/POLICY.md`
