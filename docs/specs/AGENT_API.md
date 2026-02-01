# Agent API (Draft)

This is the contract for a future remote BAS agent. MVP uses local modules only.

## Goals
- Mutual TLS for transport authentication.
- Explicit allowlists to prevent unsafe scopes.
- Deterministic request/response payloads for audit.

## Transport
- HTTPS + mTLS required.
- Agents must reject plaintext HTTP.
- Client presents orchestrator cert; agent cert pinned via allowlist.

## Endpoints
### POST /v1/agent/handshake
Request:
```json
{"agent_id":"string","capabilities":["module-name"],"version":"v1"}
```
Response:
```json
{"agent_id":"string","status":"ok","policy_hash":"sha256","capabilities":["module-name"]}
```

### POST /v1/agent/modules/execute
Request:
```json
{
  "run_id":"string",
  "module_id":"string",
  "module":"string",
  "target_id":"string",
  "params":{},
  "expectations":{},
  "scope":{"allowlist":["string"],"expires_at":"RFC3339"}
}
```
Response:
```json
{
  "module_id":"string",
  "status":"pass|fail|skipped|error",
  "started_at":"RFC3339",
  "finished_at":"RFC3339",
  "evidence":{},
  "notes":"string"
}
```

## Policies
- `scope.allowlist` must be non-empty.
- `scope.expires_at` must be in the future.
- Agents enforce allowlists locally and report denials.
- Orchestrator may reject agents if `policy_hash` does not match expected.

## Errors
- Use HTTP 400 for invalid payloads.
- Use HTTP 403 for policy violations.
- Use HTTP 409 for stale policy hash.
