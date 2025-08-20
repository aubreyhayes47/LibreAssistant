<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# MCP Network Policy

LibreAssistant's Model Context Protocol (MCP) client can enforce network
policies on a per‑server basis. Administrators may configure allow/deny lists
for hostnames and restrict which protocols a server may access.

## Configuration

Network rules are defined in `config/mcp.registry.json`.

```json
{
  "defaultNetwork": { "allow": ["localhost"] },
  "servers": [
    {
      "name": "law_by_keystone",
      "module": "./servers/law_by_keystone/index.ts",
      "network": {
        "allow": [
          "localhost",
          "api.govinfo.gov",
          "api.ecfr.gov"
        ],
        "deny": ["example.com"],
        "protocols": ["https"]
      }
    }
  ]
}
```

- `defaultNetwork` applies to all servers that do not specify their own
  rules.
- Each server may supply a `network` object with `allow`, `deny` and
  `protocols` lists.
- During invocation the client and the spawned server process both enforce
  these policies, rejecting disallowed requests.

## Isolation

For heightened security, run MCP servers in isolated containers or processes
with restricted network access in addition to the client‑side policy. Container
firewalls or sandbox tools can provide defense in depth.
