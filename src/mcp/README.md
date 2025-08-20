# MCP Module

This directory contains the core pieces for running and connecting to Model Context Protocol (MCP) servers.

## Files

- **client.ts** – Implements `MCPClient`, a client capable of registering multiple remote MCP servers, enforcing network policies, and recording an audit log of tool invocations.
- **transport.ts** – Provides transport implementations (`StdioTransport`, `HTTPTransport`) and `serveStdio` to expose a server over JSON-RPC.
- **registry.ts** – Loads MCP servers from a registry configuration file, applying per-server consent and optional network policies.
- **server-runner.js** – Helper script that launches a server module and serves it over stdio while applying network policy restrictions.

## Generating TypeDoc

TypeDoc can be used to build API documentation from the TSDoc comments:

```bash
npm install --save-dev typedoc
npx typedoc --out docs/mcp src/mcp
```

The generated documentation will appear in `docs/mcp/`.

