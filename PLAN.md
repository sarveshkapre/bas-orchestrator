# BAS Orchestrator — Plan

Local-first campaign orchestrator for bounded BAS simulations that produces reproducible, auditable evidence packs and scoring.

## Features
- Campaign spec (`.yaml`) with targets + modules + expectations.
- Local module runner (safe, bounded modules only).
- Deterministic run mode for reproducible evidence packs.
- Evidence pack JSON output with scoring summary.
- Optional evidence signing + verification.
- Optional remote agent execution with policy allowlists.
- JSON schema export for core data contracts.

## Top risks / unknowns
- Safety boundaries: keeping modules strictly bounded, reversible, and auditable.
- Evidence contract stability: versioning and backwards compatibility as schemas evolve.
- Remote agent trust model: transport security, capability validation, and policy enforcement.
- Scoring semantics: keeping “pass/fail/skip/error” aligned with operator expectations.

## Commands
See `docs/PROJECT.md` for the canonical command list.

```bash
make setup
make check
make build
```

## Shipped (most recent first)
- 2026-02-01: Added `bas diff-summary` for golden comparison.
- 2026-02-01: Added `bas policy-hash` helper for CI usage.
- 2026-02-01: Added TLS client auth validation for agent handshake.
- 2026-02-01: Added `bas validate-summary` for CI checks of report output.
- 2026-02-01: Added evidence summary schema export.
- 2026-02-01: Hardened remote agent trust checks (reject insecure http by default, validate handshake caps).
- 2026-02-01: Added schema compatibility tests for core contracts.
- 2026-02-01: Enhanced `bas report` with per-module durations and evidence pointers.
- 2026-02-01: Added `bas validate-campaign` for preflight validation (campaign + policy).
- 2026-02-01: Added `bas report` for human/JSON evidence summaries and CI-friendly exit codes; hardened `bas verify` on invalid schemas; fixed packaging license metadata.

## Next to ship
- Extend `bas report` output polish (durations, per-module evidence pointers).
