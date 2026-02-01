# Policy Allowlist

Policy files provide default allowlists for large campaigns.

## Format
```yaml
version: v1
allowlist:
  - "local"
modules:
  noop-1:
    allowlist:
      - "local"
targets:
  local-host:
    allowlist:
      - "local"
```

## Resolution order
1. `modules.<module_id>.allowlist`
2. `targets.<target_id>.allowlist`
3. `allowlist` (global)
4. `module.scope_allowlist`

If the resolved allowlist is empty, the module is rejected.
