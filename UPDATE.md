# Update — 2026-02-01

## Shipped
- Added `bas report` to summarize evidence packs (human or JSON) with CI-friendly exit codes.
- Expanded `bas report` with per-module duration and evidence pointers.
- Added `bas validate-campaign` for preflight checks in CI (campaign + optional policy).
- Added schema compatibility tests for campaign/evidence contracts.
- Hardened remote agent trust checks (reject insecure http by default, validate handshake caps).
- Added evidence summary schema export for downstream tooling.
- Added `bas validate-summary` for CI validation of report output.
- Added TLS client auth validation for agent handshake (cert/key pairing).
- Added `bas policy-hash` helper for CI usage.
- Added `bas diff-summary` for golden summary drift detection.
- Documented policy hash derivation in Agent API spec.
- Hardened `bas verify` to fail cleanly on invalid evidence pack schemas.
- Packaging + repo hygiene: SPDX license metadata and ignore `build/` + `dist/`.

## Verification
```bash
make check
make build
```

## PR
- https://github.com/sarveshkapre/bas-orchestrator/pull/1
