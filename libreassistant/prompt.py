"""Shared user-prompt utility for tool approval dialogs.

Centralizes the spinner-prompt interaction so individual tools don't need to
know about spinner state.  The CLI registers a hook that pauses the spinner
before showing the prompt; tools just call ``user_prompt()``.
"""

from __future__ import annotations

import builtins

# Module-level hook set by the CLI (cli.py) to pause the spinner during prompts.
# When set, user_prompt() calls _hook(text) instead of builtins.input().
# The hook is responsible for stopping the spinner, showing the prompt,
# reading input, and restarting the spinner.
_hook = None  # type: callable | None


def set_prompt_hook(hook) -> None:
    """Register (or clear) the prompt hook.  Called once by cli.py at startup."""
    global _hook
    _hook = hook


def user_prompt(text: str) -> str:
    """Prompt the user and return their input stripped and lowered.

    If a hook is registered (CLI mode), it handles spinner pausing and I/O.
    Otherwise falls back to plain ``builtins.input()`` — safe for tests and
    non-interactive contexts where no spinner is running.
    """
    if _hook:
        return _hook(text)
    return builtins.input(text).strip().lower()
