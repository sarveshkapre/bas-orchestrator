# Update — 2026-02-01

## Shipped
- Added `bas report` to summarize evidence packs (human or JSON) with CI-friendly exit codes.
- Hardened `bas verify` to fail cleanly on invalid evidence pack schemas.
- Packaging + repo hygiene: SPDX license metadata and ignore `build/` + `dist/`.

## Verification
```bash
make check
make build
```

## PR
- Pending (will be created via `gh pr create`).
