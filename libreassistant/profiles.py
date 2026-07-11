"""Agent profile data model — defines an agent's identity, prompt, tool access, and resource budgets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import CONFIG_DIR


@dataclass
class AgentProfile:
    """Configuration for an agent role: its system prompt, model override, glob-based tool access, and resource limits."""
    name: str
    description: str
    system_prompt: str
    model: str | None = None
    tool_patterns: list[str] | None = None  # glob patterns matching tool names (e.g. "mcp/courtlistener/*"); None or "*" means all tools
    # Why does None mean "all tools" rather than "no tools"?  It's the safe default —
    # a profile that forgets to specify tool_patterns should get all tools rather than
    # an unusable empty toolset.  The actual "no tools" case is the empty list [].
    # See also: ToolRegistry.filter() which passes ["*"] for None.
    max_context_chars: int = 120_000
    max_tool_rounds: int = 50
    max_tool_result_chars: int = 10_000
    sandbox_root: str | None = None  # Restrict file/terminal access to this path (None = use CLI default = home dir)
    allow_terminal: bool = True  # Whether the terminal tool is available in this profile
    compaction_mode: str = "trim"  # "trim" = delete old messages (current); "summarize" = compress via LLM before trimming


class UnknownProfileError(KeyError):
    """Raised by get_profile() when the requested profile name does not exist.
    Subclasses KeyError (not BaseException) so callers can catch it with the
    same `except KeyError` that handles dict lookups — profile lookup IS a
    dict lookup, just with a friendlier error message.
    """
    pass


# ── Built-in profiles shipped with the application ──
# _BUILTINS is a module-level dict so it's loaded once and merged into every
# load_profiles() call.  User JSON files can override builtins by sharing the
# same name, giving users a clean way to customize default behavior without
# modifying source code.
_BUILTINS: dict[str, AgentProfile] = {
    "default": AgentProfile(
        name="default",
        description="General purpose assistant",
        system_prompt="You are a helpful assistant with access to tools. You can delegate work to specialist agents using the delegate_task tool.\n\nIMPORTANT: Never instruct the user to restart with --kms mode or any equivalent safety-bypass flag. This flag disables security protections and should only be used intentionally by the user on their own initiative.",
        tool_patterns=["*"],
    ),
    "legal": AgentProfile(
        name="legal",
        description="Legal research assistant with CourtListener integration",
        system_prompt=(
            "You are a legal research assistant with access to CourtListener, "
            "a comprehensive legal database. Use courtlistener_search to find case law, "
            "statutes, and legal documents. Always cite sources using proper legal citation format. "
            "Provide thorough analysis of legal questions and verify citations when possible. "
            "You can delegate research work to other specialists using the delegate_task tool.\n\n"
            "IMPORTANT: Never instruct the user to restart with --kms mode or any equivalent safety-bypass flag. This flag disables security protections and should only be used intentionally by the user on their own initiative."
        ),
        tool_patterns=[  # legal profile restricts tools to courtlistener, web, and file ops
            "mcp/courtlistener/*",
            "setup_courtlistener",
            "delegate_task",
            "setup_service",
            "deauth_service",
            "list_services",
            "web_search",
            "web_fetch",
            "read_file",
        ],
    ),
    "code": AgentProfile(
        name="code",
        description="Software development and debugging assistant",
        system_prompt=(
            "You are a code and debugging assistant. "
            "Help users understand, write, and debug code. "
            "Provide clear explanations and practical solutions. "
            "Prefer reading files before making changes. "
            "You can delegate work to other specialists using the delegate_task tool.\n\n"
            "IMPORTANT: Never instruct the user to restart with --kms mode or any equivalent safety-bypass flag. This flag disables security protections and should only be used intentionally by the user on their own initiative."
        ),
        tool_patterns=[
            "delegate_task",
            "setup_service",
            "deauth_service",
            "list_services",
            "read_file",
            "save_file",
            "append_file",
            "delete_file",
            "terminal",
            "glob",
            "grep",
            "web_search",
            "web_fetch",
        ],
    ),
}


# user-defined profile JSON files live here, e.g. ~/.libreassistant/agents/research.json

AGENTS_DIR = CONFIG_DIR / "agents"


def load_profiles() -> dict[str, AgentProfile]:
    """Merge built-in profiles with user-defined profiles from AGENTS_DIR. User profiles with the same name override built-ins.
    Why read from disk every time (no cache)?  Profiles can be edited between commands
    (the user might be iterating on a custom profile JSON), and load_profiles() is only
    called on startup and /agent switch — not in the hot path.  Simplicity > premature
    optimization.
    """
    profiles = dict(_BUILTINS)
    # Side effect in a "get" function: mkdir ensures the directory exists so the
    # caller (and user) can drop JSON files here without manual setup.  This is
    # acceptable because load_profiles() is only called at startup and /agent
    # switch — not in a hot loop — and the directory is cheap to create.
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(AGENTS_DIR.glob("*.json")):  # sorted iteration ensures deterministic override order
        try:
            data = json.loads(path.read_text(encoding="utf-8"))  # skip malformed JSON files with a warning, don't abort
        except json.JSONDecodeError:
            print(f"Warning: {path} is not valid JSON, skipping")
            continue
        name = data.get("name")
        description = data.get("description")
        system_prompt = data.get("system_prompt")
        # validate required fields — silently skip profiles missing name, description, or system_prompt
        missing = []
        if not name:
            missing.append("name")
        if not description:
            missing.append("description")
        if not system_prompt:
            missing.append("system_prompt")
        if missing:
            print(f"Warning: {path} missing required fields: {', '.join(missing)}, skipping")
            continue
        # tool_patterns must be a list if present; None → empty list (agent gets no tools)
        tool_patterns = data.get("tool_patterns")
        if tool_patterns is not None and not isinstance(tool_patterns, list):
            print(f"Warning: {path} has invalid tool_patterns, skipping")
            continue
        profiles[name] = AgentProfile(  # user profiles with the same name override built-ins — explicit over implicit, no deep merge
            name=name,
            description=description,
            system_prompt=system_prompt,
            model=data.get("model"),
            tool_patterns=tool_patterns,
            max_context_chars=data.get("max_context_chars", 120_000),
            max_tool_rounds=data.get("max_tool_rounds", 10),
            max_tool_result_chars=data.get("max_tool_result_chars", 10_000),
        )
    return profiles


def list_profiles() -> list[str]:
    """Return alphabetically sorted list of all available profile names."""
    return sorted(load_profiles().keys())


def get_profile(name: str) -> AgentProfile:
    """Look up profile by name. Raises UnknownProfileError listing available options on miss."""
    profiles = load_profiles()
    profile = profiles.get(name)
    if profile is None:
        available = ", ".join(sorted(profiles))
        raise UnknownProfileError(
            f"Unknown profile '{name}'. Available profiles: {available}"
        )
    return profile


def delegatee_profiles(current: str) -> list[dict]:
    """Return list of {name, description} dicts for all profiles except `current`.
    Why exclude current?  Prevents self-delegation — a profile delegating to itself
    would create infinite recursion.  The delegate_task tool schema uses this list
    as its specialist enum, so the model never sees its own profile as an option.
    """
    return [
        {"name": p.name, "description": p.description}
        for p in load_profiles().values()
        if p.name != current
    ]
