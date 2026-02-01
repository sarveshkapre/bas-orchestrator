# Module SDK (Draft)

## Contract
A module is a bounded, safe behavior with explicit inputs, expectations, and evidence output.

### Required fields
- `id`: unique module instance id.
- `module`: module name from registry.
- `target_id`: target identifier.
- `params`: execution parameters (safe, bounded).
- `expectations`: expected outcome for scoring.
- `scope_allowlist`: required allowlist entries (may be provided by policy file).

### Result fields
- `status`: pass|fail|skipped|error.
- `started_at` / `finished_at`: RFC3339 UTC timestamps.
- `evidence`: structured data with minimal secrets.

## Safety rules
- No destructive actions.
- Must respect allowlists and scopes.
- Evidence must avoid sensitive payloads.

## Fixtures
See `tests/fixtures/module_spec.yaml` and `tests/fixtures/module_result.json` for canonical examples.
