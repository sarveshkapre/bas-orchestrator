# AGENTS

## Working agreements
- Follow `docs/PLAN.md` and `docs/PROJECT.md` for architecture and commands.
- Keep changes minimal and focused; update tests and `docs/CHANGELOG.md` for user-facing changes.
- Preserve the safety model: modules must be bounded, reversible, and auditable.
- Avoid adding heavy dependencies; prefer standard library or existing deps.

## Commands
- Setup: `make setup`
- Dev: `make dev`
- Test: `make test`
- Lint: `make lint`
- Typecheck: `make typecheck`
- Build: `make build`
- Quality gate: `make check`

## Conventions
- Python 3.11+
- Ruff for lint/format, mypy for types, pytest for tests.
- Evidence packs are append-only JSON objects with stable field names.
