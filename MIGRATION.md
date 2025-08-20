# MCP Migration Plan

## Phase 1 – Client & Registry
* Add TypeScript MCP client and registry loader
* Ship reference servers and unit tests

## Phase 2 – Plugin Conversion
* Re‑implement Echo, File I/O, Law by Keystone and ThinkTank as MCP servers
* Expose tools, resources and prompts per server

## Phase 3 – Switchboard Integration
* Wrap MCP client with adapter for UI
* Enable server discovery and tool execution from switchboard

## Phase 4 – Security & CI
* Prompt for destructive file operations
* Capture audit logs and enforce per‑server network policies with allow/deny
  lists and protocol restrictions
* Add tests to CI pipeline
