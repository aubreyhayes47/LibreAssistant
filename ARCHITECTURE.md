<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Architecture Review

## Current Flow

```text
User → Switchboard → Plugin → User State → History
```

Plugins are Python objects registered in a microkernel. Each invocation mutates per‑user state and the API logs history entries.

## Target MCP Flow

```text
User → Switchboard → MCP Client → MCP Server Tool → Audit Log
```

The switchboard embeds an MCP client which discovers servers via registry
allow‑list and enforces per‑server network policies. Tools perform work and
return JSON results while the client records audit entries. Legacy plugins remain
available during migration.

### Integration Gaps
- No schema validation for plugin inputs
- Transport is tightly coupled to in‑process calls
- File operation audit trail is incomplete
