<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Security Notes

## Consent Model
Dangerous tools such as `fs_update` and `fs_delete` require an explicit `confirm: true` parameter. The UI should display a modal explaining the risk before submission.

## Audit Schema
Every invocation records `{server, tool, params, result, timestamp, beforeHash?, afterHash?}`. File operations hash contents before and after mutation.

## Network Rules
Servers operate under a deny‑by‑default egress policy. Administrators define a
`defaultNetwork` policy and may supply per-server `network` entries in
`config/mcp.registry.json` with `allow`, `deny`, and `protocols` lists. The MCP
client and spawned server processes both enforce these restrictions. For
stronger guarantees, consider running servers in isolated containers or
processes with restricted network access.

## File Jail
The file server resolves paths within `mcp_fs/` and rejects attempts to escape the directory, providing a simple sandbox for local CRUD operations.
