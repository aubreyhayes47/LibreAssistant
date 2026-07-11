"""Built-in tool schemas, handlers, and registration. This is the integration point where all standard tools (web, file, terminal, service auth, delegation) are registered with the ToolRegistry."""

import json

from ..tool_registry import ToolRegistry
from ..profiles import delegatee_profiles
from .web_fetch import fetch_url
from .web_search import handle_web_search
from .terminal import handle_terminal
from .file_ops import read_file, save_file, append_file, delete_file

WEB_FETCH_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {
            "type": "string",
            "description": "The URL to fetch",
            "minLength": 1,
            "pattern": "^https?://",
        },
        "format": {
            "type": "string",
            "enum": ["text", "html"],
            "description": "Output format: 'text' (stripped, default) or 'html' (raw)",
            "default": "text",
        },
    },
    "required": ["url"],
    "additionalProperties": False,
}

WEB_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Search query",
            "minLength": 1,
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results (1-10)",
            "default": 5,
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}

TERMINAL_SCHEMA = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "description": "Shell command to run",
            "minLength": 1,
        },
        "shell": {
            "type": "boolean",
            "description": "Use shell interpreter (enables pipes, redirects, globs, chaining). Defaults to true.",
            "default": True,
        },
    },
    "required": ["command"],
    "additionalProperties": False,
}

READ_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "Path to the file (absolute or expanded). Must be under the sandbox directory for safety unless --kms.",
            "minLength": 1,
        },
    },
    "required": ["path"],
    "additionalProperties": False,
}

SAVE_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "Path where to save (absolute or expanded). Must be under the sandbox directory unless --kms.",
            "minLength": 1,
        },
        "content": {
            "type": "string",
            "description": "Full text content to write to the file",
            "minLength": 0,
        },
    },
    "required": ["path", "content"],
    "additionalProperties": False,
}

APPEND_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "Path to the existing file",
            "minLength": 1,
        },
        "content": {
            "type": "string",
            "description": "Text to append to the file",
        },
    },
    "required": ["path", "content"],
    "additionalProperties": False,
}

DELETE_FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "Path to the file to delete",
            "minLength": 1,
        },
    },
    "required": ["path"],
    "additionalProperties": False,
}

SETUP_SERVICE_SCHEMA = {
    "type": "object",
    "properties": {
        "service_name": {
            "type": "string",
            "description": "Name of the service to set up (e.g. courtlistener, google-gmail, google-drive, google-calendar)",
            "minLength": 1,
        },
        "force": {
            "type": "boolean",
            "description": "Force re-authentication even if token appears valid",
            "default": False,
        },
    },
    "required": ["service_name"],
    "additionalProperties": False,
}

DEAUTH_SERVICE_SCHEMA = {
    "type": "object",
    "properties": {
        "service_name": {
            "type": "string",
            "description": "Name of the service to deauthorize",
            "minLength": 1,
        },
    },
    "required": ["service_name"],
    "additionalProperties": False,
}

LIST_SERVICES_SCHEMA = {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": False,
}


def register_all(registry: ToolRegistry) -> None:
    """Register every built-in tool on the given registry: web fetch, web search, terminal, file ops (read/save/append/delete), service auth (setup/deauth/list), and task delegation."""
    registry.register(
        "web_fetch",
        "Fetch the content of a URL. Returns the page text (capped at 2 MB). "
        "Use format='html' for raw HTML. "
        "PDFs and images return a message suggesting the terminal tool.",
        WEB_FETCH_SCHEMA,
        fetch_url,
    )
    registry.register(
        "web_search",
        "Search the web for a query. Returns title, URL, and snippet per result.",
        WEB_SEARCH_SCHEMA,
        handle_web_search,
    )
    registry.register(
        "terminal",
        "Run a shell command through /bin/sh. Supports pipes (|), redirects (>), "
        "chaining (&&, ||), variable expansion ($HOME), and globs (*). "
        "Read-only commands (ls, cat, grep, pwd, etc.) are auto-approved. "
        "Other commands require user confirmation. "
        "Commands with absolute paths outside the sandbox are blocked. "
        "Use --kms flag to skip confirmations and sandbox restrictions.",
        TERMINAL_SCHEMA,
        handle_terminal,
    )
    registry.register(
        "read_file",
        "Read a text file from disk. Also handles PDFs (via pdftotext). "
        "Path must be under your home directory for safety (unless --kms is active).",
        READ_FILE_SCHEMA,
        read_file,
    )
    registry.register(
        "save_file",
        "Write text content to a file. Creates parent directories if needed. "
        "Path must be under your home directory for safety (unless --kms is active).",
        SAVE_FILE_SCHEMA,
        save_file,
    )
    registry.register(
        "append_file",
        "Append text content to an existing file. "
        "Path must be under your home directory for safety (unless --kms is active).",
        APPEND_FILE_SCHEMA,
        append_file,
    )
    registry.register(
        "delete_file",
        "Delete a file. User must confirm in normal mode. Skipped in --kms mode. "
        "Path must be under your home directory for safety (unless --kms is active).",
        DELETE_FILE_SCHEMA,
        delete_file,
    )

    # ── Service auth handler (closure capturing registry by reference) ──
    # Why a closure?  The handler needs access to registry.mcp_manager, which isn't
    # injected until AFTER registration (MCPManager is created later in cli.py).
    # The closure captures `registry` by reference — it resolves mcp_manager at call
    # time, not registration time.  This works because all closures share the same
    # `registry` object (the global unfiltered registry), and the shared _context dict
    # ensures mcp_manager is visible even through filtered registry copies.
    #
    # Cross-reference: This handler is invoked by two paths:
    # (1) The LLM calling the setup_service tool (tool_call in run_tool_loop).
    # (2) The /setup and /auth CLI commands in cli.py, which call
    #     mgr.retry_server() directly — bypassing this handler but performing
    #     the same OAuth flow via MCPManager._handle_stub().
    def setup_service_handler(args: dict) -> str:
        mgr = registry.mcp_manager
        if mgr is None:
            return "Error: no MCP manager available"
        name = args.get("service_name", "")
        force = args.get("force", False)
        if not mgr._find_client(
            name
        ):  # uses private _find_client — coupling to MCPManager internals
            return f"Error: no service named '{name}' configured"
        try:
            # skip auth if token is already valid and force is False
            if not force:
                statuses = mgr.get_status()
                status_map = {s["name"]: s for s in statuses}
                entry = status_map.get(name, {})
                if entry and not entry.get("needs_auth", True):
                    return f"Service '{name}' is already connected."
            mgr.retry_server(
                name, force=force
            )  # refresh tool list — successful auth may expose new MCP tools
            tool_names = [t for t in mgr.registry.tool_names if t.startswith(name)]
            if tool_names:
                return (
                    f"Service '{name}' authenticated successfully. "
                    f"Available tools: {', '.join(tool_names)}"
                )
            return f"Service '{name}' authenticated but no tools were returned."
        except Exception as e:
            return f"Authentication failed for '{name}': {e}"

    # ── Deauth handler ──
    def deauth_service_handler(args: dict) -> str:
        mgr = registry.mcp_manager
        if mgr is None:
            return "Error: no MCP manager available"
        name = args.get("service_name", "")
        if not mgr._find_client(name):
            return f"Error: no service named '{name}' configured"
        if mgr.deauth_server(name):
            return (
                f"Service '{name}' deauthorized. Use setup_service to re-authenticate."
            )
        return f"Failed to deauthorize '{name}'."

    # ── List-services handler with human-readable status table ──
    def list_services_handler(args: dict) -> str:
        mgr = registry.mcp_manager
        if mgr is None:
            return "No MCP services configured."
        statuses = mgr.get_status()
        if not statuses:
            return "No MCP services configured."
        # build a Markdown table with status, tool count, and expiration info
        lines = ["| Service | Status |", "|---------|--------|"]
        for s in statuses:
            label = s["status"]
            if "expires_in" in s:
                hours = s["expires_in"] // 3600
                mins = (s["expires_in"] % 3600) // 60
                label = f"{s['tools']} tools (expires in {hours}h{mins}m)"  # convert seconds to hours/minutes for human readability
            elif s["needs_auth"]:
                label = "not authenticated — use setup_service tool"
            lines.append(f"| {s['name']} | {label} |")
        return "\n".join(lines)

    # ── Register service auth tools ──
    registry.register(
        "setup_service",
        "Start OAuth setup for an MCP service like courtlistener. "
        "Call this when the user wants to connect a service that requires browser-based authentication. "
        "Opens a URL for the user to authorize in their browser. "
        "Use force=true to force re-authentication even if token appears valid.",
        SETUP_SERVICE_SCHEMA,
        setup_service_handler,
    )
    registry.register(
        "deauth_service",
        "Deauthorize an MCP service. Clears stored tokens and disconnects. "
        "Use this when tokens are invalid or the user wants to re-authenticate "
        "with a different account.",
        DEAUTH_SERVICE_SCHEMA,
        deauth_service_handler,
    )
    registry.register(
        "list_services",
        "List all configured MCP services and their authentication status.",
        LIST_SERVICES_SCHEMA,
        list_services_handler,
    )

    DELEGATE_TASK_SCHEMA = {
        "type": "object",
        "properties": {
            "specialist": {
                "type": "string",
                "description": "Which specialist profile to delegate to. Valid options depend on your current profile and are listed in the system prompt.",
            },
            "input": {
                "type": "string",
                "description": "What to do. Be specific and include all necessary context.",
            },
            "needs_verification": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional criteria to verify (hidden from the specialist).",
            },
        },
        "required": ["specialist", "input"],
        "additionalProperties": False,
    }

    # ── Delegate-task handler: submits to TaskPool and returns task id ──
    def delegate_task_handler(args: dict) -> str:
        task_pool = registry.task_pool
        if task_pool is None:
            return "Error: task delegation not available"
        current = getattr(registry, "current_profile", "default")
        if (
            args["specialist"] == current
        ):  # prevent self-delegation: check current_profile (not session_id) because the guard is about identity, not conversation — an agent must not delegate to itself even across sessions
            return "Error: cannot delegate tasks to yourself"
        valid = [p["name"] for p in delegatee_profiles(current)]
        if args["specialist"] not in valid:
            return f"Error: unknown specialist '{args['specialist']}'. Available: {', '.join(valid)}"
        task = task_pool.submit(
            args["specialist"],
            args["input"],
            args.get("needs_verification", []),
            parent_session_id=getattr(
                registry, "session_id", None
            ),  # propagate session_id for parent-session tracking in Task
        )
        return json.dumps(
            {
                "task_id": task.id,
                "specialist": task.specialist,
                "status": task.status,
            },
            ensure_ascii=False,
        )

    # ── Register the delegate_task tool (last so schema sees all profiles) ──
    # Why build the schema at registration time?  The specialist enum is derived from
    # delegatee_profiles(), which reads the current profile set.  Building it here
    # ensures the LLM always sees the latest profile list — if we built it lazily in
    # the handler, the tool schema sent to the API would be stale after /agent switch.
    registry.register(
        "delegate_task",
        "Delegate a task to a specialist agent. "
        "The specialist runs in the background with its own tool access. "
        "Results are injected into the conversation when complete. "
        "Use this for work that benefits from a different toolset or perspective.",
        DELEGATE_TASK_SCHEMA,
        delegate_task_handler,
    )

    # ── Docs tool: search LibreAssistant's own ARCHITECTURE.md ──
    # Why a self-documenting tool?  It lets the model look up its own architecture
    # without polluting the system prompt with the full doc.  The tool does a
    # section-level grep against ARCHITECTURE.md and returns only the relevant
    # slices — keeping context usage minimal while enabling genuine self-reference.
    DOCS_SCHEMA = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "What to look up in the LibreAssistant documentation (e.g. 'task pool', 'MCP authentication', 'compaction')",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    def handle_docs(args: dict) -> str:
        """Search LibreAssistant's documentation for information about how the system works."""
        query = args.get("query", "").lower()
        if not query:
            return "Error: query is required"

        try:
            import re
            from pathlib import Path

            # Look for ARCHITECTURE.md in the project root (development) or package root (installed)
            candidates = [
                Path(__file__).parent.parent.parent
                / "ARCHITECTURE.md",  # Project root during development
                Path(__file__).parent.parent
                / "ARCHITECTURE.md",  # Package root if bundled
            ]
            arch_path = next((p for p in candidates if p.exists()), None)
            if arch_path is None:
                return "Error: ARCHITECTURE.md not found"

            text = arch_path.read_text(encoding="utf-8")

            # Split into sections and find relevant ones
            sections = re.split(r"\n## ", text)
            matches = []
            for section in sections:
                if query in section.lower():
                    # Truncate to reasonable size
                    content = section[:2000]
                    if len(section) > 2000:
                        content += "\n... [truncated]"
                    matches.append(content)

            if not matches:
                return f"No documentation found for '{query}'. Try different keywords."

            result = f"Documentation for '{query}':\n\n" + "\n\n---\n\n".join(
                matches[:3]
            )
            if len(result) > 6000:
                result = result[:6000] + "\n\n[truncated]"
            return result
        except Exception as e:
            return f"Error reading docs: {e}"

    registry.register(
        "docs",
        "Search LibreAssistant's own documentation about how the system works",
        DOCS_SCHEMA,
        handle_docs,
    )

    # ── Skills tool: list available skills or read a specific skill's content ──
    # Why a tool (not just the system prompt listing)?  It lets the agent proactively
    # load skills when it recognizes a relevant task — e.g. reading the skill-creator
    # when asked to build a new skill.  The system prompt only shows names+descriptions;
    # this tool returns full content on demand.
    SKILLS_SCHEMA = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Skill name to read (e.g. 'tutorial', 'skill-creator'). Omit to list all available skills.",
            },
        },
        "additionalProperties": False,
    }

    def handle_skills(args: dict) -> str:
        """List available skills or read a specific skill's full content."""
        from ..skills import load_skills, _skill_matches_profile

        current_profile = getattr(registry, "current_profile", "default")
        # Get the profile's tool_patterns for filtering
        from ..profiles import get_profile

        try:
            prof = get_profile(current_profile)
            tool_patterns = prof.tool_patterns
        except Exception:
            tool_patterns = None

        skills = load_skills()
        matching = [
            s
            for s in skills
            if _skill_matches_profile(s, tool_patterns, current_profile)
        ]

        skill_name = args.get("name", "")
        if not skill_name:
            # List mode: return names + descriptions
            if not matching:
                return "No skills installed. Place skill directories in ~/.libreassistant/skills/"
            lines = ["Available skills:"]
            for s in matching:
                tools_str = f" (tools: {', '.join(s.tools)})" if s.tools else ""
                lines.append(f"- {s.name}: {s.description}{tools_str}")
            return "\n".join(lines)

        # Read mode: return full content for the requested skill
        for s in matching:
            if s.name == skill_name:
                return f"## Skill: {s.name}\n\n{s.content}"
        available = ", ".join(s.name for s in matching)
        return (
            f"Skill '{skill_name}' not found. Available: {available}"
            if available
            else f"Skill '{skill_name}' not found. No skills installed."
        )

    registry.register(
        "skills",
        "List available skills or read a specific skill's full instructions. "
        "Use this to discover what skills are installed, or to load a skill's "
        "content when you recognize a task that matches a skill's description.",
        SKILLS_SCHEMA,
        handle_skills,
    )
