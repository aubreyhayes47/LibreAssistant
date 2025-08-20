# Model Context Protocol Overview

Model Context Protocol (MCP) defines a neutral interface between AI clients and external capability providers. It addresses the classic N×M integration problem by standardising how models discover and use tools, resources and prompts.

## Architecture
MCP adopts a client–server model built on JSON‑RPC 2.0 transported over stdio or HTTP/SSE. Clients initiate a capability discovery handshake where each server advertises its tools, resources and prompts. Once registered, the client issues JSON‑RPC calls to invoke tools and receive structured responses.

### Primitives
* **Tools** – callable functions with JSON‑Schema validated parameters and return values.
* **Resources** – read‑only URIs exposing data such as files or status objects.
* **Prompts** – templated text the client may render before tool invocation.

## Threat Model & Mitigations
Threats include prompt injection, tool poisoning and malicious servers. Without RBAC the system mitigates risk through:
* explicit server allow‑lists
* consent prompts for destructive operations
* a deny‑by‑default network policy
* filesystem jails for file tools
* exhaustive audit logging of JSON‑RPC frames
