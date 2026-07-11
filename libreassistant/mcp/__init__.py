"""MCP manager — orchestrates MCP client lifecycle, tool registration, and auth-aware stubs."""
from ..tool_registry import ToolRegistry
from .client import MCPClient
from .servers import get_servers

# Schema used for stub tools while a server is unauthenticated (no params needed).
STUB_SCHEMA = {
    "type": "object",
    "properties": {},
    "required": [],
}

class MCPManager:
    """Manages a pool of MCPClient instances, registers their tools with a ToolRegistry, and handles auth state transitions (stub -> live)."""
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        registry.mcp_manager = self  # Register back-reference so registry can reach the manager without circular imports
        self.clients: list[MCPClient] = []

    def connect_all(self) -> list[str]:
        """Discover servers from config, connect each (lazy auth), and register tools or stubs. Returns status strings for CLI display.
        Why idempotent (early return if self.clients is non-empty)?  connect_all() is
        called at startup and also after profile-switch re-registration.  Guarding on
        self.clients prevents double-connecting and duplicating tool registrations.
        """
        if self.clients:
            return [f"  already connected ({len(self.clients)} clients)"]
        servers = get_servers()  # get_servers() merges built-in, Google (from env), and user-defined
        connected = []
        for s in servers:
            try:
                client = MCPClient(s["name"], s)
                tools = client.lazy_connect()
                if tools:
                    # Server connected and returned tools — register them live
                    self._register_tools(client, tools)
                # Server supports OAuth but has no cached token yet — register a stub tool instead
                elif client._needs_auth:
                    self._register_stub(client)
                else:
                    raise RuntimeError(f"Could not connect and auth not applicable")
                self.clients.append(client)
                tool_count = len(tools) if tools else 1
                status = "setup tool" if not tools else f"{tool_count} tools"
                connected.append(f"  {s['name']} ({status})")  # Count stub as "1 tool" for status display consistency
            except Exception as e:
                connected.append(f"  {s['name']} — failed ({e})")
        return connected

    def _register_tools(self, client: MCPClient, tools: list[dict]) -> None:
        """Register every tool from a connected server, namespaced under server name via closure.

        Cross-reference: The tool name format is "{server}_{toolname}" (e.g.
        "courtlistener_search").  This namespace convention lets profile tool_patterns
        filter MCP tools by server — the "legal" profile uses "mcp/courtlistener/*"
        to include only CourtListener tools, while excluding stdio tools from other
        servers.  The ToolRegistry.filter() method matches these names against glob
        patterns, so the underscore-separated naming is load-bearing.
        """
        # Stub-to-real lifecycle: when a server first loads without a cached token,
        # _register_stub() installs a "setup_<name>" placeholder tool.  Once the user
        # calls that stub (triggering OAuth), _handle_stub() unregisters it and calls
        # _register_tools() to swap in the real tools.  This gives the LLM a discoverable
        # on-ramp for authentication without pre-emptively blocking startup.
        prefix = client.name
        for t in tools:
            name = t["name"]
            description = t.get("description", "")
            schema = t.get("inputSchema", t.get("parameters", {}))
            c = client
            n = name

            # Capture loop vars as default args so closures capture by value, not by reference
            def make_handler(c=c, n=n):  # Factory returns a handler closure that captures the current client and tool name
                def handler(args: dict) -> str:
                    return c.call_tool(n, args)
                return handler

            self.registry.register(
                f"{prefix}_{name}",
                f"[{prefix}] {description}",
                schema,
                make_handler(),
            )

    def _register_stub(self, client: MCPClient) -> None:
        """Register a placeholder "setup_<name>" tool that triggers OAuth when called.

        Why register a stub *before* authentication?  The LLM needs to know that
        a server exists and how to activate it — but without a valid token we can't
        discover its real tools yet.  The stub gives the model a single, discoverable
        entry point ("call setup_courtlistener to authenticate") that kicks off the
        full OAuth flow via _handle_stub(), which then swaps the stub for live tools.
        """
        name = client.name

        def make_stub(c=client, n=name):
            def handler(args: dict) -> str:
                return self._handle_stub(n, c)
            return handler

        self.registry.register(
            f"setup_{name}",
            f"[{name}] Not authenticated yet. Call this tool to start OAuth setup.",
            STUB_SCHEMA,
            make_stub(),
        )

    def _handle_stub(self, server_name: str, client: MCPClient, force: bool = False) -> str:
        """Complete OAuth flow, swap stub for real tools, return success message with tool list.

        Why unregister everything then re-register (not just update)?
        The number and names of tools may have changed since the stub was created
        (e.g. server added or removed tools between versions).  A clean unregister
        + register avoids leaving stale tool entries that the server no longer exposes.
        """
        try:
            tools = client.finish_connect(force=force)
        except Exception as e:
            return f"Authentication failed: {e}"
        self.registry.unregister_prefix(f"setup_{server_name}")
        self.registry.unregister_prefix(server_name)  # Remove both the stub and any previously registered tools for this server before re-registering
        self._register_tools(client, tools)
        tool_names = [f"{server_name}_{t['name']}" for t in tools]
        return (
            f"Authentication successful for {server_name}. "
            f"{len(tools)} tools now available: {', '.join(tool_names)}"
        )

    def retry_server(self, name: str, force: bool = False) -> bool:
        """Re-run auth for a single server; returns False if server name is unknown."""
        client = self._find_client(name)
        if client is None:
            return False
        if not force and not client._needs_auth:
            return True
        self._handle_stub(name, client, force=force)
        return True

    def get_status(self) -> list[dict]:
        """Return per-server status dicts including auth state, tool count, and token expiry."""
        results = []
        for c in self.clients:
            entry = {"name": c.name, "needs_auth": c._needs_auth, "tools": len(c._tools)}
            if c._needs_auth:
                entry["status"] = "not authenticated"
            else:
                entry["status"] = f"{len(c._tools)} tools"
                from .oauth import load_tokens  # Lazy-import to avoid circular dependency at module level
                import time
                tokens = load_tokens()
                tok = tokens.get(c.name, {})
                expires_at = tok.get("expires_at", 0)
                # Guard against non-numeric expires_at (e.g. string)
                if isinstance(expires_at, (int, float)) and expires_at:
                    remaining = expires_at - time.time()
                    if remaining > 0:
                        entry["expires_in"] = int(remaining)
                    else:
                        entry["status"] = "token expired"
            results.append(entry)
        return results

    def deauth_server(self, name: str) -> bool:
        """Revoke OAuth tokens for a server, reset to stub, and unregister all its tools.

        The full deauth dance (why all three steps?):
        1. Delete tokens from disk — prevents stale credentials being reused on restart.
        2. Unregister all tools prefixed with `name` — removes live tools from the registry
           so the LLM stops seeing them immediately.
        3. Re-register a stub (`setup_{name}`) — gives the LLM an on-ramp to re-authenticate
           via the same OAuth flow that worked the first time.

        Skipping step 2 or 3 would leave the registry in an inconsistent state: either
        dead tools that silently fail, or a stub without the live tools being cleaned up first.
        """
        from .oauth import load_tokens, save_tokens
        tokens = load_tokens()
        if name in tokens:
            del tokens[name]
            save_tokens(tokens)
        client = self._find_client(name)
        if client:
            client._access_token = None
            client._needs_auth = True
            client._tools = []
            self.registry.unregister_prefix(name)
            self._register_stub(client)
        return True

    def _find_client(self, name: str) -> MCPClient | None:
        """Look up a connected client by server name."""
        for c in self.clients:
            if c.name == name:
                return c
        return None

    def find_client(self, name: str) -> MCPClient | None:
        return self._find_client(name)

    def update_registry(self, registry):
        """Swap the target ToolRegistry (e.g. after /agent re-filters the global registry).

        Why is this needed?  Profile switching calls global_registry.filter() which
        produces a *new* ToolRegistry.  The manager must point at the new registry so
        that subsequent _register_tools() / _register_stub() calls land in the right
        place.  The shared _context dict keeps mcp_manager reachable from both the
        old and new registries, but the manager's own self.registry field still
        needs updating so its own writes go to the active registry.
        """
        self.registry = registry

    def shutdown(self):
        """Disconnect all clients gracefully and clear the pool.

        Why disconnect *before* clearing self.clients?  Each MCPClient may hold a
        live stdio subprocess (with stdin/stdout pipes).  disconnect() sends SIGTERM
        → wait → SIGKILL to the subprocess, ensuring the OS releases the file
        descriptors and process table entry.  Clearing without disconnecting would
        orphan those processes.
        """
        for c in self.clients:
            try:
                c.disconnect()
            except Exception:
                pass
        self.clients.clear()

    def reconnect_all(self) -> list[str]:
        """Full reset — disconnect everything then reconnect from scratch."""
        self.shutdown()
        return self.connect_all()
