"""Thread-safe registry of tool schemas and handler functions. Supports glob-filtering per agent profile and JSON-string dispatch."""

from __future__ import annotations

import fnmatch, json, threading

class ToolRegistry:
    """Central registry that maps tool names to JSON schemas and handler callbacks. Each AgentProfile gets a filtered view via .filter(patterns)."""
    def __init__(self):
        # _tools is a list (not a dict) because the OpenAI API expects a list-of-dicts
        # format [{type, function: {name, description, parameters}}, ...].  The list
        # order determines tool presentation order in the API payload.
        self._tools = []
        # _handlers maps tool name → callable.  Separate from _tools so dispatch()
        # can do a fast dict lookup without scanning the schema list.
        self._handlers = {}
        self._lock = threading.Lock()
        # Why a _context dict instead of direct instance attributes (task_pool, mcp_manager, etc.)?
        # When filter() creates a new ToolRegistry for a profile, it assigns the SAME _context
        # dict reference (line 89).  This means writes to any key — task_pool, mcp_manager,
        # kms_mode — on the original registry are immediately visible to all filtered copies,
        # and vice versa.  This shared-reference pattern is the mechanism that lets
        # profile-switched registries see MCP tools and the task pool without re-injection.
        #
        # Why is _context NOT protected by _lock?  All _context keys are set once during
        # single-threaded CLI startup (cli.py:130-167) before any worker threads exist.
        # After that point, only current_profile and session_id are mutated (by Agent.__init__
        # and switch_profile), and those are always written from the main REPL thread.
        # Adding a lock here would complicate the property API for no real safety gain.
        self._context = {
            "task_pool": None,  # injected post-construction by app bootstrap; None means delegation disabled
            "mcp_manager": None,  # injected post-construction; None means no MCP services available
            "kms_mode": False,  # when True, destructive operations skip user confirmation
            "current_profile": "default",  # used to prevent self-delegation in delegate_task_handler
            "session_id": None,  # propagated to delegated tasks for parent-session tracking
            "sandbox_root": None,  # configurable filesystem sandbox root
        }

    @property
    def task_pool(self):
        return self._context["task_pool"]

    @task_pool.setter
    def task_pool(self, value) -> None:
        self._context["task_pool"] = value

    @property
    def mcp_manager(self):
        return self._context["mcp_manager"]

    @mcp_manager.setter
    def mcp_manager(self, value) -> None:
        self._context["mcp_manager"] = value

    @property
    def kms_mode(self) -> bool:
        return self._context["kms_mode"]

    @kms_mode.setter
    def kms_mode(self, value: bool) -> None:
        self._context["kms_mode"] = value

    @property
    def current_profile(self) -> str:
        return self._context["current_profile"]

    @current_profile.setter
    def current_profile(self, value: str) -> None:
        self._context["current_profile"] = value

    @property
    def session_id(self):
        return self._context["session_id"]

    @session_id.setter
    def session_id(self, value) -> None:
        self._context["session_id"] = value

    @property
    def sandbox_root(self):
        return self._context["sandbox_root"]

    @sandbox_root.setter
    def sandbox_root(self, value) -> None:
        self._context["sandbox_root"] = value

    def filter(self, patterns: list[str]) -> ToolRegistry:
        """Return a new ToolRegistry containing only tools whose names match at least one of the given glob patterns.
        Why a new registry (not mutating self)?  The original "global" registry holds all tools;
        each profile needs its own subset.  A new object lets multiple profiles coexist without
        interfering with each other.  Shared _context ensures the filtered registry remains functional.
        """
        filtered = ToolRegistry()
        with self._lock:
            for tool in self._tools:
                name = tool["function"]["name"]
                if any(fnmatch.fnmatch(name, p) for p in patterns):
                    filtered._tools.append(tool)
                    filtered._handlers[name] = self._handlers[name]
        # Share the context dict by reference (not copy).  This is deliberate:
        # the filtered registry must see live updates to task_pool, mcp_manager,
        # kms_mode, etc. that are set on the global registry after filtering.
        # A copy would snapshot the context at filter-time and go stale.
        filtered._context = self._context
        return filtered

    def register(self, name: str, description: str, parameters: dict, handler) -> None:
        """Register a tool with its JSON Schema and handler. Thread-safe via self._lock."""
        with self._lock:
            self._tools = [t for t in self._tools if t["function"]["name"] != name]
            self._tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            })
            self._handlers[name] = handler

    def unregister_prefix(self, prefix: str) -> None:
        """Unregister all tools whose names start with the given prefix. The trailing underscore on MCP prefixes (e.g. "mcp_") is stripped for normalization."""
        prefix = prefix.rstrip("_")  # normalize: "mcp_" and "mcp" both match "mcp/..." tool names
        with self._lock:
            self._tools = [t for t in self._tools if not t["function"]["name"].startswith(prefix)]
            for name in list(self._handlers.keys()):
                if name.startswith(prefix):
                    del self._handlers[name]

    def unregister(self, name: str) -> None:
        """Unregister a single tool by exact name. Thread-safe."""
        with self._lock:
            self._tools = [t for t in self._tools if t["function"]["name"] != name]
            self._handlers.pop(name, None)

    @property
    def schemas(self) -> list[dict]:
        """List of OpenAI-compatible tool definition dicts (type + function schema).
        Returns a shallow copy (list(self._tools)), not the live internal list.
        Why?  Without the copy, callers (e.g. MCPManager.get_status, the API payload
        builder) could accidentally mutate _tools — appending, removing, or reordering
        entries — corrupting the registry.  This was a real bug (FIXED: B10) where
        external mutation caused duplicate or missing tool schemas.
        """
        return list(self._tools)

    @property
    def tool_names(self) -> list[str]:
        """List of registered handler names."""
        return list(self._handlers.keys())

    def dispatch(self, name: str, args: dict) -> str:
        """Look up handler by name and call it with `args`. Returns a JSON string on success, or an error string prefixed with "Error: " on failure.
        Lock scope: we lock only for the dict lookup, NOT for the handler call itself.
        Tool handlers may block on network I/O or user input — holding the lock during
        execution would serialize all tool calls and freeze the UI during confirmations.
        """
        with self._lock:
            handler = self._handlers.get(name)
        if handler is None:
            return f"Error: unknown tool '{name}'"
        try:
            result = handler(args)
            if isinstance(result, str):
                return result
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return f"Error calling {name}: {e}"
