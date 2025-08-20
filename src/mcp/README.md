# MCP subsystem

This directory contains a minimal implementation of components that speak the Model Context Protocol (MCP).

## Files

### client.ts
Wraps remote MCP servers and exposes a high level `MCPClient` class. The client caches server capabilities, enforces network policies, and records an audit log of tool invocations.

### transport.ts
Defines the `Transport` interface along with implementations:
`StdioTransport` for child processes, `HTTPTransport` for HTTP endpoints, and the `serveStdio` helper that exposes a server over stdio.

### registry.ts
Loads a JSON registry configuration and registers servers with an `MCPClient` when consent is granted. Optional network policies are applied per server or as defaults.

### server-runner.js
Helper script used by the registry to spawn a server module in its own process. It applies network policy restrictions and exposes the module via stdio using `serveStdio`.

## Generating TypeDoc

TypeDoc can generate HTML API documentation from the TypeScript sources.

1. Install TypeDoc:

   ```bash
   npm install --save-dev typedoc
   ```

2. Generate documentation for the MCP module:

   ```bash
   npx typedoc src/mcp --out docs/mcp
   ```

The generated files will appear under `docs/mcp`.
