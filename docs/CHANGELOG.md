# CHANGELOG

## [Unreleased]
- Expanded `bas report` output with per-module duration and evidence pointers.
- Added `bas validate-campaign` for CI-friendly preflight validation of campaigns and policy allowlists.
- Added `bas report` to summarize evidence packs (human-readable or JSON) with CI-friendly exit codes.
- Hardened `bas verify` to fail cleanly on invalid evidence pack schemas.
- Updated packaging metadata to use SPDX license expression (removes setuptools deprecation warning).
- Scaffolded repository structure.
- Added CLI skeleton, campaign spec validation, and evidence pack output.
- Added deterministic run mode for reproducible evidence packs.
- Added optional evidence pack signing (HMAC-SHA256).
- Added evidence signature verification command and remote agent/module SDK drafts.
- Added module spec validation command and agent client stub.
- Added remote agent integration hooks, scope allowlists, and schema export command.
- Added allowlist fixtures/tests, schema export docs, and agent integration options.
- Added policy allowlist files, agent handshake/capability checks, and schema version validation.
