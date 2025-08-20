# Security Notes

## Consent Model
Dangerous tools such as `fs_update` and `fs_delete` require an explicit `confirm: true` parameter. The UI should display a modal explaining the risk before submission.

## Audit Schema
Every invocation records `{server, tool, params, result, timestamp, beforeHash?, afterHash?}`. File operations hash contents before and after mutation.

## Network Rules
Servers operate under a deny‑by‑default egress policy. Only hosts listed in
`config/mcp.registry.json` under the `allowedHosts` array may be contacted.

## File Jail
The file server resolves paths within `mcp_fs/` and rejects attempts to escape the directory, providing a simple sandbox for local CRUD operations.
