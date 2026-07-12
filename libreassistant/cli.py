"""Entry point for LibreAssistant REPL. Handles CLI argument parsing, the interactive command loop, session lifecycle, MCP OAuth flow, and background task management."""

import argparse, itertools, json, os, queue, sys, threading, time

from openai import OpenAI

from .config import get_api_key, load_config, strip_control_chars
from .session import (
    is_valid_session_name,
    save_session,
    load_session,
    list_sessions,
    delete_session,
    auto_save,
    auto_load,
    sanitize,
    trim,
    AUTO_SESSION_PATH,
    Session,
    Message,
)
from .agent import Agent
from .profiles import get_profile, list_profiles, load_profiles, UnknownProfileError
from .task_pool import TaskPool, task_dict
from .tool_registry import ToolRegistry
from .tools import register_all
from .mcp import MCPManager
from .mcp.oauth import set_log_callback
from .skills import (
    load_skills,
    get_skill_names_descriptions,
    get_skill_content,
    install_bundled_skills,
    SKILLS_DIR,
)

MODEL = os.environ.get(
    "LIBRE_MODEL", "big-pickle"
)  # Default model override via env var
MAX_TOOL_ROUNDS = 10  # Max tool-call rounds per turn (overridden by profile)

SPINNER = itertools.cycle(
    r"-\|/"
)  # Animated spinner characters for the "Thinking..." indicator

# Why if/elif instead of a dict dispatch? Slash commands have prefix-matching
# semantics (e.g. "/save foo" starts with "/save") that a flat dict lookup
# can't express.  The chain also lets us short-circuit: session lifecycle
# commands skip agent.turn() entirely, which matters for /new and /quit.


def _status(msg: str, round_n: int = 0) -> None:
    """Write an in-place status line with optional round counter."""
    prefix = f"  [{round_n}] " if round_n else "  "
    sys.stdout.write("\r" + prefix + msg + " " * 40)
    sys.stdout.flush()


def _clear_status() -> None:
    """Clear the in-place status line from the terminal."""
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()


def _show_reasoning(text: str) -> None:
    """Print model reasoning content in dimmed text."""
    for line in text.splitlines():
        line = line.strip()
        if line:
            print(f"\n  \033[2m{line}\033[0m")


# Command-reference table shown by /help
COMMANDS = {
    "/agent": "/agent <name>       Switch to a different agent profile",
    "/steer": "/steer <msg>        Inject a message between tool rounds",
    "/tasks": "/tasks              List all background tasks",
    "/task": "/task <id> [stop|output]  Task details and control",
    "/save": "/save <name>         Save the current session",
    "/load": "/load <name>         Load a saved session",
    "/rm": "/rm <name>           Delete a saved session",
    "/sessions": "/sessions            List saved sessions",
    "/new": "/new                 Start a new session (auto-saves current)",
    "/setup": "/setup [server]        List servers or trigger OAuth for one",
    "/auth": "/auth <server>         Alias for /setup <server>",
    "/deauth": "/deauth <server>       Clear cached tokens for a server",
    "/skills": "/skills              List installed skill modules",
    "/mcp": "/mcp                 List connected MCP servers",
    "/compact": "/compact             Compress context window (summarize + trim)",
    "/help": "/help                Show this help",
    "/quit": "/quit, /exit         Quit (auto-saves)",
}

# Note: /<skill-name> is also valid — loads a skill into context (e.g. /tutorial)


def print_help():
    print("\nCommands:")
    for cmd in [
        "/agent",
        "/steer",
        "/tasks",
        "/task",
        "/save",
        "/load",
        "/rm",
        "/sessions",
        "/new",
        "/setup",
        "/auth",
        "/deauth",
        "/skills",
        "/mcp",
        "/compact",
        "/help",
        "/quit",
    ]:
        print(f"  {COMMANDS[cmd]}")
    print(f"\n  /<skill-name>          Load a skill into context (e.g. /tutorial)")


# ---- CLI entry point ----
# ---- CLI entry point ----
# cli.py is the "composition root" of LibreAssistant: it creates every
# subsystem (ToolRegistry, TaskPool, MCPManager, Session, Agent) and
# wires them together via constructor injection.  None of the subsystems
# know about each other — they communicate through the shared _context
# dict in ToolRegistry and the backlog queue between TaskPool and Session.
# This single-function design keeps testability in the subsystems while
# concentrating wiring complexity in one place.
def main():
    parser = argparse.ArgumentParser(
        prog="libreassistant",
        description="CLI assistant with tool calling and MCP support",
    )
    parser.add_argument(
        "--kms",
        action="store_true",
        help="Unrestricted terminal mode — skip all command confirmations",
    )
    parser.add_argument("--agent", default="default", help="Starting agent profile")
    parser.add_argument(
        "--list-agents", action="store_true", help="List available profiles and exit"
    )  # --kms: skip all confirmations; --agent: initial profile; --list-agents: enumerate profiles
    parser.add_argument(
        "--no-terminal",
        action="store_true",
        help="Disable the terminal/shell tool entirely",
    )
    parser.add_argument(
        "--sandbox-root",
        type=str,
        default=None,
        help="Restrict file/terminal access to this directory (default: home directory)",
    )
    parser.add_argument(
        "--tutorial",
        action="store_true",
        help="Start with the interactive tutorial loaded into context",
    )
    parser.add_argument(
        "--exec",
        type=str,
        default=None,
        metavar="MESSAGE",
        help="Execute one turn with MESSAGE, print result, and exit (non-interactive)",
    )
    parser.add_argument(
        "--exec-task",
        type=str,
        default=None,
        metavar="MESSAGE",
        help="Submit MESSAGE as a background task, wait for result, and exit",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Seconds to wait for --exec-task to complete (default: 120)",
    )
    args = parser.parse_args()

    if args.exec and args.exec_task:
        parser.error(
            "--exec and --exec-task are mutually exclusive. Use --exec for direct turns, --exec-task for background delegation."
        )

    if args.kms:
        if args.exec or args.exec_task:
            # In exec mode, skip interactive confirmation — there's no terminal to prompt on.
            # The user explicitly chose both --kms and --exec, so they know the risks.
            print("  --kms mode: command confirmations disabled (non-interactive)")
        else:
            print("\n  ⚠️  WARNING: --kms mode disables ALL safety confirmations.")
            print("  The agent will execute commands, modify files, and access")
            print("  your filesystem without asking permission.\n")
            print("  This includes commands that could modify or delete files,\n")
            print("  access sensitive data, or execute arbitrary code.\n")
            answer = (
                input("  Type 'yes' to confirm, anything else to abort: ")
                .strip()
                .lower()
            )
            if (
                answer != "yes"
            ):  # Full word "yes" required — prevents accidental single-key confirms
                print("  Aborted.")
                sys.exit(0)

    if args.list_agents:
        for name in list_profiles():
            prof = get_profile(name)
            print(f"  {name:20s} {prof.description}")
        return

    api_key = get_api_key()
    config = load_config()
    client = OpenAI(
        api_key=api_key,
        base_url="https://opencode.ai/zen/v1",
        timeout=60,
        max_retries=2,
    )  # OpenAI-compatible client pointing at the OpenCode Zen endpoint

    profile = get_profile(args.agent)

    # Build global (unfiltered) tool registry, then filter by profile
    global_registry = ToolRegistry()
    # Cross-reference: kms_mode flows from here → config.py:kms_mode() reads sys.argv
    # → terminal.py:confirm_command() uses it to skip user prompts
    # → file_ops.py:_resolve_path() uses it to bypass sandbox, delete_file() to skip confirmation.
    # Note: terminal.py and file_ops.py import config.kms_mode() directly (reads sys.argv),
    # while the registry.kms_mode property is a separate copy used by other code paths.
    global_registry.kms_mode = getattr(args, "kms", False)
    from .tools.file_ops import set_sandbox_root as set_file_sandbox
    from .tools.terminal import set_sandbox_root as set_terminal_sandbox

    set_file_sandbox(args.sandbox_root)
    set_terminal_sandbox(args.sandbox_root)
    global_registry.sandbox_root = args.sandbox_root
    register_all(global_registry)

    # Cross-reference: --no-terminal unregisters the terminal tool from the GLOBAL registry
    # BEFORE filtering.  This means no profile (including "code") will have terminal access
    # when this flag is set.  The unregister happens before filter() so the tool is gone
    # from all profile views.
    if args.no_terminal:
        global_registry.unregister("terminal")

    # Cross-reference: filter() creates a new ToolRegistry containing only tools whose
    # names match the profile's tool_patterns globs.  The filtered registry shares the
    # global's _context dict (see tool_registry.py:89), so task_pool, mcp_manager, etc.
    # remain accessible.  profile.tool_patterns=["*"] means "all tools" (profiles.py:22).
    registry = global_registry.filter(profile.tool_patterns or ["*"])

    profiles = load_profiles()
    task_pool = TaskPool(
        registry_factory=lambda: global_registry,
        client_factory=lambda: OpenAI(
            api_key=api_key,
            base_url="https://opencode.ai/zen/v1",
            timeout=60,
            max_retries=2,
        ),
        profile_registry=profiles,
    )
    global_registry.task_pool = task_pool  # TaskPool runs background tasks; inject its ref into the global registry for tool-side access

    # OAuth log callback — renders auth URLs and success messages inline
    def oauth_log(msg: str):
        if msg.startswith("__AUTH_BOX__"):
            parts = msg.split("\n", 2)
            name = parts[1] if len(parts) > 1 else "Service"
            url = parts[2] if len(parts) > 2 else ""
            print()
            print(f"  {'=' * 50}")
            print(f"  {name} Authorization")
            print(f"  {'=' * 50}")
            print(f"  Open this URL in your browser:")
            print(f"    {url}")
            print(f"  {'=' * 50}")
        elif msg.startswith("__AUTH_OK__"):
            name = msg.split("\n", 1)[1] if "\n" in msg else "Service"
            print(f"  {name} connected \u2713")
        else:
            sys.stdout.write("\r" + " " * 80 + "\r")
            print(f"  {msg}")

    set_log_callback(
        oauth_log
    )  # Register the OAuth log callback so MCPManager can write UI lines

    if registry.kms_mode:
        print(
            "  --kms mode: command confirmations disabled"
        )  # --kms mode: all tool calls proceed without interactive confirmation

    # Connect all configured MCP servers and report status.
    # In --exec mode, suppress the startup banner (only the result matters).
    mcp_manager = MCPManager(registry)
    connected = mcp_manager.connect_all()
    if not args.exec:
        for line in connected:
            if "failed" in line:
                print(f"  {line}")
            else:
                print(f"  {line}")
        tool_count = len(registry.schemas)
        print(f"\n  {tool_count} tools available")
        print(f"\n  Type /help for commands, or just start typing.")

    session = Session(profile=profile, backlog=task_pool.backlog)
    session.add_system_message(profile.system_prompt, agent=profile.name)

    # Install bundled skills (tutorial, skill-creator) to user's skills dir on first run.
    # This ensures built-in skills are available when LibreAssistant is distributed
    # as an executable or appimage where ~/.libreassistant/skills/ won't exist yet.
    installed = install_bundled_skills()
    if installed and not args.exec:
        print(f"  Installed built-in skills: {', '.join(installed)}")

    # Inject available skill names+descriptions into the system prompt (lazy loading).
    # Only names and descriptions are included here — full skill content is loaded
    # on demand via /<skill-name> to save context window space.
    skill_listing = get_skill_names_descriptions(profile.tool_patterns, profile.name)
    if skill_listing:
        session.add_system_message(skill_listing, agent=profile.name)

    agent = Agent(
        session=session,
        client=client,
        registry=registry,
        task_pool=task_pool,
        model=MODEL,
    )  # Seed the session with the profile's system prompt, then wrap in an Agent

    # Auto-resume: prompt user to restore the last unsaved session.
    # Skipped in --exec mode because there's no terminal to prompt on.
    if not args.exec:
        resumed = auto_load()
        if resumed:
            answer = input("Resume last session? [Y/n]: ").strip().lower()
            if answer not in ("n", "no"):
                for d in resumed:
                    msg = Message(
                        id=d.get("id", ""),
                        session_id=session.id,
                        role=d["role"],
                        content=d.get("content", None),
                        tool_calls=d.get("tool_calls", None),
                        tool_call_id=d.get("tool_call_id", None),
                        agent=d.get("agent", "default"),
                        mode=d.get("mode", "primary"),
                        parent_id=d.get("parent_id", None),
                        timestamp=d.get("timestamp", 0.0),
                    )
                    agent.session.add_message(msg)
                # Deduplicate system messages — startup already injected the
                # profile's system prompt and skill listing, and the loaded
                # session may contain copies of those same messages.  Keep
                # only the first system message (the primary instruction).
                seen_system = False
                deduped = []
                for msg in agent.session.messages:
                    if msg.role == "system":
                        if seen_system:
                            continue
                        seen_system = True
                    deduped.append(msg)
                agent.session.messages = deduped
            # Delete the auto-save after resume (or decline) to prevent double-resume
            # on next startup.  The session is now live in memory; re-saving happens
            # on /quit or Ctrl+C via auto_save().  If we didn't delete here, a crash
            # mid-session would restore stale messages from the old auto-save on top
            # of the (potentially different) live session.
            AUTO_SESSION_PATH.unlink(missing_ok=True)

    # Tutorial mode: load the tutorial skill into context as the first user message.
    # This triggers the agent to respond with guided walkthrough behavior.
    if args.tutorial:
        tutorial_content = get_skill_content(
            "tutorial", profile.tool_patterns, profile.name
        )
        if tutorial_content:
            result = agent.turn(
                f"[User loaded the 'tutorial' skill. Follow its instructions and guide the user through LibreAssistant.]\n\n{tutorial_content}"
            )
            if result is not None:
                print(f"\n{strip_control_chars(result)}")
            else:
                print(
                    "\n  Tutorial loaded! I'll guide you through using LibreAssistant."
                )
        else:
            print("\n  No tutorial skill found.")

    # ---- Non-interactive exec mode: run one turn or one task, print result, exit ----
    if args.exec_task:
        # Task-based exec: submit to TaskPool, wait for result, print it.
        # This exercises the full delegation pipeline end-to-end:
        # submit → task profile → run_tool_loop → verification → backlog → absorb.
        task = task_pool.submit(
            specialist=profile.name,
            input=args.exec_task,
            parent_session_id=session.id,
        )
        print(f"  Task {task.id} submitted ({profile.name} profile)")

        deadline = time.time() + args.timeout
        while time.time() < deadline:
            time.sleep(0.5)
            if task.status in ("completed", "failed", "stopped"):
                break

        if task.status == "running":
            print(f"  Task {task.id} timed out after {args.timeout}s")
            task_pool.stop(task.id)
        elif task.status == "failed":
            print(f"  Task failed: {task.error}")
        elif task.output:
            print(f"\n{task.output}")
        else:
            print("\n(no output)")

        agent.session.absorb_completed_tasks()
        mcp_manager.shutdown()
        task_pool.shutdown(wait=False)
        sys.exit(0)

    if args.exec:
        # Direct exec: run one agent.turn(), print result, exit.
        # Useful for quick one-shot questions from the terminal.
        result = agent.turn(args.exec)
        if result is not None:
            print(f"\n{strip_control_chars(result)}")
        else:
            print("\n(no response)")

        mcp_manager.shutdown()
        task_pool.shutdown(wait=False)
        sys.exit(0)

    # ---- Spinner state (shared across iterations and the prompt hook) ----
    spinner_event = threading.Event()
    spinner_msg = [
        "Thinking..."
    ]  # Mutable container: callback updates this, spinner reads it
    _spinner_thread = [None]  # Container for the current spinner thread

    # ---- Interrupt / steer state ----
    abort_event = threading.Event()
    steer_queue: queue.Queue[str] = queue.Queue()

    def _spin():
        while not spinner_event.is_set():
            _status(f"{spinner_msg[0]} {next(SPINNER)}")
            time.sleep(0.1)
        _clear_status()

    def _start_spinner():
        spinner_event.clear()
        spinner_msg[0] = "Thinking..."
        t = threading.Thread(target=_spin, daemon=True)
        t.start()
        _spinner_thread[0] = t

    def _stop_spinner():
        spinner_event.set()
        t = _spinner_thread[0]
        if t is not None:
            t.join(timeout=1)
            _spinner_thread[0] = None

    def on_status(msg: str, round_n: int = 0) -> None:
        spinner_msg[0] = msg

    def on_tool_call(name: str, args: dict, result: str) -> None:
        """Display a tool call and its result in real-time."""
        _stop_spinner()
        try:
            args_summary = json.dumps(args, ensure_ascii=False)
            if len(args_summary) > 120:
                args_summary = args_summary[:120] + "..."
            result_summary = result[:200] + "..." if len(result) > 200 else result
            print(f"\n  \033[2m[{name}] {args_summary}\033[0m")
            for line in result_summary.splitlines()[:8]:
                print(f"  \033[2m  {line}\033[0m")
        finally:
            _start_spinner()

    # Register the prompt hook so tools can pause the spinner during user prompts.
    # The hook handles spinner pausing and I/O; tools handle their own prompt logic.
    from .prompt import set_prompt_hook

    def _pause_spinner_for_prompt(prompt_text: str) -> str:
        _stop_spinner()
        try:
            return input(prompt_text).strip().lower()
        finally:
            _start_spinner()

    set_prompt_hook(_pause_spinner_for_prompt)

    # ---- Main REPL loop ----
    try:
        while True:
            try:
                raw = input(f"\n({agent.session.profile.name}) > ").strip()
            except KeyboardInterrupt:
                print()
                continue  # Ctrl-C at the prompt just shows a new line, doesn't exit
            if not raw:
                continue

            # --- Session lifecycle commands ---
            if raw in ("/quit", "/exit"):
                auto_save(agent.session.messages)
                agent.active = False
                print("Goodbye!")
                break

            if raw in ("/new", "/reset"):
                # Save the old session first, then reset to just the system prompt.
                # Keeping only messages[0] (the system prompt) preserves the agent's
                # identity and instructions while discarding all conversation history.
                auto_save(agent.session.messages)
                agent.session.messages = [agent.session.messages[0]]
                print("\n(new session)")
                continue

            if raw in (
                "/save",
                "/load",
                "/rm",
            ):  # Handle bare /save, /load, /rm without a name argument
                print(f"Usage: {raw} <name>")
                continue

            if raw.startswith("/save "):
                name = raw.removeprefix("/save ").strip()
                if not name or not is_valid_session_name(name):
                    print("Invalid name. Use letters, numbers, hyphens, underscores.")
                    continue
                save_session(name, agent.session.messages)
                print(f"\n(session '{name}' saved)")
                continue

            if raw.startswith("/load "):
                name = raw.removeprefix("/load ").strip()
                if not name or not is_valid_session_name(name):
                    print("Invalid session name.")
                    continue
                loaded = load_session(name)
                if loaded is not None:
                    agent.session.messages = loaded
                    # Restore session.id from the loaded messages so new messages
                    # get the correct session_id (not the fresh UUID from startup).
                    if loaded:
                        agent.session.id = loaded[0].session_id
                    agent.registry.session_id = agent.session.id
                    # Deduplicate system messages — keep only the first one.
                    # Loaded sessions may contain multiple system messages from
                    # prior runs (startup injects system prompts, and they get
                    # saved with the session).  The model treats the first system
                    # message as the primary instruction, so extras just waste
                    # context and can confuse the model.
                    seen_system = False
                    deduped = []
                    for msg in agent.session.messages:
                        if msg.role == "system":
                            if seen_system:
                                continue
                            seen_system = True
                        deduped.append(msg)
                    agent.session.messages = deduped
                    print(f"\n(session '{name}' loaded)")
                else:
                    print(f"\n(session '{name}' not found)")
                continue

            if raw.startswith("/rm "):
                name = raw.removeprefix("/rm ").strip()
                if not name or not is_valid_session_name(name):
                    print("Invalid session name.")
                    continue
                if delete_session(name):
                    print(f"\n(session '{name}' deleted)")
                else:
                    print(f"\n(session '{name}' not found)")
                continue

            # --- Session listing and navigation ---
            if raw == "/sessions":
                names = list_sessions()
                if names:
                    print("\n" + "\n".join(f"  {n}" for n in names))
                else:
                    print("\n(no saved sessions)")
                continue

            # --- MCP / OAuth commands ---
            if raw == "/setup":
                statuses = mcp_manager.get_status()
                if not statuses:
                    print("\n(no MCP servers configured)")
                else:
                    print()
                    for s in statuses:
                        label = s["status"]
                        if "expires_in" in s:
                            hours = s["expires_in"] // 3600
                            mins = (s["expires_in"] % 3600) // 60
                            label = f"{s['tools']} tools (expires in {hours}h{mins}m)"
                        print(f"  {s['name']:20s}  {label}")
                continue

            if raw.startswith("/setup ") or raw.startswith(
                "/auth "
            ):  # /setup <name> and /auth <name> both trigger OAuth re-authentication
                cmd, _, name = raw.partition(" ")
                name = name.strip()
                if not name:
                    print(f"Usage: {cmd} <server_name>")
                    continue
                if not mcp_manager._find_client(
                    name
                ):  # Guard: ensure the server name exists in config before attempting OAuth
                    print(f"No server named '{name}' configured")
                    continue
                statuses = mcp_manager.get_status()
                status_map = {s["name"]: s for s in statuses}
                entry = status_map.get(name, {})
                if entry and not entry.get("needs_auth", True):
                    print(f"  {name} is already connected")
                    continue
                print(f"\n  Starting OAuth for {name}...")
                try:
                    mcp_manager.retry_server(name)
                    print(f"  {name} authentication complete")
                    tool_count = len(
                        [t for t in registry.tool_names if t.startswith(name)]
                    )  # Count tools contributed by this specific server
                    if tool_count:
                        print(f"  {tool_count} tools now available")
                except Exception as e:
                    print(f"  {name} authentication failed: {e}")
                continue

            # --- Profile switching ---
            if raw.startswith("/deauth "):
                name = raw.removeprefix("/deauth ").strip()
                if not name:
                    print("Usage: /deauth <server_name>")
                    continue
                if mcp_manager.deauth_server(name):
                    print(f"\n  Tokens cleared for {name}")
                    print(f"  Use /setup {name} to re-authenticate")
                else:
                    print(f"\n  No server named '{name}'")
                continue

            if raw.startswith(
                "/agent "
            ):  # /agent <name> — hot-swap the active profile on the current session
                name = raw.removeprefix("/agent ").strip()
                print(agent.switch_profile(name))
                continue

            if raw.startswith(
                "/steer "
            ):  # /steer <msg> — inject a message between tool rounds
                steer_text = raw.removeprefix("/steer ").strip()
                if steer_text:
                    steer_queue.put(steer_text)
                    print("\n(steer message queued)")
                else:
                    print("\nUsage: /steer <message>")
                continue

            # --- Background task commands ---
            if raw == "/tasks":
                if not task_pool.tasks:
                    print("\n(no background tasks)")
                else:
                    print()
                    for task in task_pool.tasks.values():
                        print(f"  {task.id}  {task.specialist:20s}  {task.status}")
                continue

            if raw.startswith(
                "/task "
            ):  # /task <id> [stop|output] — inspect or control a background task
                parts = raw.removeprefix("/task ").strip().split(maxsplit=1)
                if not parts:
                    print("Usage: /task <id> [stop|output]")
                    continue
                task_id = parts[0]
                action = parts[1] if len(parts) > 1 else None
                task = task_pool.get(task_id)
                if task is None:
                    print(f"\nNo task with id '{task_id}'")
                    continue
                if action == "stop":
                    task_pool.stop(task_id)
                    print(f"\nTask {task_id} stopped")
                elif action == "output":
                    if task.output:
                        print(f"\n{task.output}")
                    else:
                        print(f"\n(no output yet)")
                else:
                    print(f"\n  Task: {task.id}")
                    print(f"  Specialist: {task.specialist}")
                    print(f"  Status: {task.status}")
                    print(f"  Input: {task.input[:200]}")
                    if task.output:
                        print(f"  Output: {task.output[:200]}")
                    if task.error:
                        print(f"  Error: {task.error}")
                continue

            # --- Help fallback ---
            if raw == "/skills":
                skills = load_skills()
                if not skills:
                    print("\n  No skills installed.")
                    print(f"  Place skill directories in {SKILLS_DIR}")
                else:
                    print()
                    for skill in skills:
                        tools_str = (
                            f" (tools: {', '.join(skill.tools)})" if skill.tools else ""
                        )
                        profiles_str = (
                            f" (profiles: {', '.join(skill.profiles)})"
                            if skill.profiles
                            else ""
                        )
                        print(
                            f"  {skill.name}: {skill.description}{tools_str}{profiles_str}"
                        )
                continue

            if raw == "/mcp":
                if mcp_manager:
                    statuses = mcp_manager.get_status()
                    if not statuses:
                        print("\n  No MCP servers configured.")
                    else:
                        print()
                        for s in statuses:
                            tools_count = s.get("tools", 0)
                            status_str = s.get("status", "unknown")
                            print(f"  {s['name']}: {status_str} ({tools_count} tools)")
                else:
                    print("\n  MCP not available.")
                continue

            if raw.startswith("/mcp add "):
                url = raw.removeprefix("/mcp add ").strip()
                if not url:
                    print("Usage: /mcp add <url>")
                    continue
                print(f"\n  Adding MCP server: {url}")
                print("  (Use /setup to authenticate after adding)")
                continue

            if raw.startswith("/mcp remove "):
                name = raw.removeprefix("/mcp remove ").strip()
                if not name:
                    print("Usage: /mcp remove <name>")
                    continue
                if mcp_manager:
                    try:
                        mcp_manager.deauth_server(name)
                        print(f"\n  Removed server '{name}'")
                    except Exception as e:
                        print(f"\n  Error removing '{name}': {e}")
                else:
                    print("\n  MCP not available.")
                continue

            if raw.startswith("/mcp tools "):
                name = raw.removeprefix("/mcp tools ").strip()
                if not name:
                    print("Usage: /mcp tools <name>")
                    continue
                if mcp_manager:
                    statuses = mcp_manager.get_status()
                    status_map = {s["name"]: s for s in statuses}
                    if name in status_map:
                        tools = [t for t in registry.tool_names if t.startswith(name)]
                        if tools:
                            print(f"\n  Tools from {name}:")
                            for t in tools:
                                print(f"    - {t}")
                        else:
                            print(f"\n  No tools from {name}")
                    else:
                        print(f"\n  Server '{name}' not found")
                else:
                    print("\n  MCP not available.")
                continue

            if raw.startswith("/mcp auth "):
                name = raw.removeprefix("/mcp auth ").strip()
                if not name:
                    print("Usage: /mcp auth <name>")
                    continue
                if not mcp_manager._find_client(name):
                    print(f"No server named '{name}' configured")
                    continue
                statuses = mcp_manager.get_status()
                status_map = {s["name"]: s for s in statuses}
                entry = status_map.get(name, {})
                if entry and not entry.get("needs_auth", True):
                    print(f"  {name} is already connected")
                    continue
                print(f"\n  Starting OAuth for {name}...")
                try:
                    mcp_manager.retry_server(name)
                    print(f"  {name} authentication complete")
                    tool_count = len(
                        [t for t in registry.tool_names if t.startswith(name)]
                    )
                    if tool_count:
                        print(f"  {tool_count} tools now available")
                except Exception as e:
                    print(f"  {name} authentication failed: {e}")
                continue

            if raw == "/compact":
                api_dicts = session.api_messages()
                if len(api_dicts) <= 1:
                    print("\nNothing to compact")
                    continue
                before_count = len(api_dicts)
                before_chars = sum(len(m.get("content", "") or "") for m in api_dicts)
                sanitize(api_dicts)
                trim(
                    api_dicts,
                    session.profile.max_context_chars,
                    compaction_mode=getattr(session.profile, "compaction_mode", "trim"),
                    client=client,
                    model=MODEL,
                )
                after_count = len(api_dicts)
                after_chars = sum(len(m.get("content", "") or "") for m in api_dicts)
                reduced = before_count - after_count
                print(
                    f"\nCompacted: {before_count} \u2192 {after_count} messages "
                    f"({reduced} removed), {before_chars} \u2192 {after_chars} chars"
                )
                session.auto_save()
                continue

            # --- Skill loading: /<skill-name> injects full skill content into context ---
            if raw.startswith("/") and not raw.startswith(
                "/" + "/".join(COMMANDS.keys()).replace("/", "", 1)
            ):
                # Check if this is a skill name (not a built-in command)
                skill_name = raw.lstrip("/")
                # Skip if it matches a built-in command
                builtin_commands = {cmd.lstrip("/") for cmd in COMMANDS}
                if skill_name not in builtin_commands:
                    skill_content = get_skill_content(
                        skill_name, profile.tool_patterns, profile.name
                    )
                    if skill_content:
                        result = agent.turn(
                            f"[User loaded the '{skill_name}' skill. Follow its instructions.]\n\n{skill_content}"
                        )
                        if result is not None:
                            print(f"\n{strip_control_chars(result)}")
                        else:
                            print(f"\n  Skill '{skill_name}' loaded.")
                    else:
                        print(f"\n  Unknown command or skill: {raw}")
                        print_help()
                    continue

            if raw == "/help":
                print_help()
                continue

            if raw.startswith("/"):  # Unrecognized slash command — show help
                print(f"Unknown command: {raw}")
                print_help()
                continue

            if (
                len(raw) > 10000
            ):  # Hard character limit to prevent context-window overflow
                print("\n(message too long — 10 000 char limit)")
                continue

            # Start spinner for this turn (reuses shared state from outside the loop)
            abort_event.clear()
            _start_spinner()

            try:
                result = agent.turn(
                    raw,
                    reasoning_callback=_show_reasoning,
                    status_callback=on_status,
                    tool_call_callback=on_tool_call,
                    abort_event=abort_event,
                    steer_queue=steer_queue,
                )
                if result is not None:
                    safe = strip_control_chars(
                        result
                    )  # Strip control characters from final output before display
                    _clear_status()
                    print(f"\n{safe}")
                else:
                    _clear_status()
                    print("\n(no response)")
            except KeyboardInterrupt:
                # Ctrl-C during a turn: abort the turn and all background tasks
                _stop_spinner()
                abort_event.set()
                stopped = task_pool.stop_all()
                _clear_status()
                label = f", {stopped} task(s) stopped" if stopped else ""
                print(f"\n(aborted{label})")
            except Exception as e:  # Catch and display errors without crashing the REPL
                _clear_status()
                print(f"\nError: {e}")
            finally:  # Ensure spinner stops even on error
                _stop_spinner()

    except EOFError:  # Ctrl+D: save session and exit gracefully
        auto_save(agent.session.messages)
        print("Goodbye!")
    # Cleanup: shut down MCP connections, task pool, and mark agent inactive
    finally:
        mcp_manager.shutdown()
        task_pool.shutdown(wait=False)
        agent.active = False


if __name__ == "__main__":
    main()
