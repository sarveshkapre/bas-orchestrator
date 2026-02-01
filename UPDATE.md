# Update — 2026-02-01

## Shipped
- Added `bas report` to summarize evidence packs (human or JSON) with CI-friendly exit codes.
- Expanded `bas report` with per-module duration and evidence pointers.
- Added `bas validate-campaign` for preflight checks in CI (campaign + optional policy).
- Added schema compatibility tests for campaign/evidence contracts.
- Hardened remote agent trust checks (reject insecure http by default, validate handshake caps).
- Hardened `bas verify` to fail cleanly on invalid evidence pack schemas.
- Packaging + repo hygiene: SPDX license metadata and ignore `build/` + `dist/`.

## Verification
```bash
make check
make build
```

## PR
- https://github.com/sarveshkapre/bas-orchestrator/pull/1
