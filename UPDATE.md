# Update — 2026-02-01

## Shipped
- Added `bas report` to summarize evidence packs (human or JSON) with CI-friendly exit codes.
- Added `bas validate-campaign` for preflight checks in CI (campaign + optional policy).
- Hardened `bas verify` to fail cleanly on invalid evidence pack schemas.
- Packaging + repo hygiene: SPDX license metadata and ignore `build/` + `dist/`.

## Verification
```bash
make check
make build
```

## PR
- https://github.com/sarveshkapre/bas-orchestrator/pull/1
