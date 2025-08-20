<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# MCP Configuration

LibreAssistant's Model Context Protocol (MCP) client uses configuration files to
control which servers are available and what network access they have.

## Registry file (`mcp.registry.json`)

The registry enumerates all MCP servers and optional network policies.

```json
{
  "defaultNetwork": { "allow": ["localhost"] },
  "servers": [
    {
      "name": "files",
      "module": "./servers/files/index.ts",
      "network": {
        "allow": ["localhost"],
        "deny": ["example.com"],
        "protocols": ["https"]
      }
    }
  ]
}
```

- **defaultNetwork** – optional object that sets global `allow`, `deny`, and
  `protocols` lists applied to every server that does not provide its own rules.
- **servers** – array where each entry defines:
  - **name** – unique identifier for the server.
  - **module** – path to the server implementation.
  - **network** – optional object overriding the default policy with `allow`,
    `deny`, and `protocols` lists of hosts and URL schemes the server may reach.

## Consent file (`mcp.consent.json`)

Consent information is stored separately:

```json
{ "files": true, "law_by_keystone": false }
```

The file is a simple mapping from server name to a boolean indicating whether the
user or administrator has granted permission for the client to load that server.

## Interaction of consent and network policies

When the MCP client starts it reads `mcp.registry.json` and `mcp.consent.json`.
Only servers with a `true` flag in the consent file are registered. For each
registered server the client's network policy is set to the server's `network`
configuration (or `defaultNetwork` if none is provided). Both the client and the
spawned server process enforce these rules, ensuring non‑consented servers are
never started and consented servers can only access allowed hosts using
permitted protocols.

See [network-policy.md](./network-policy.md) for more details on network
restrictions.
