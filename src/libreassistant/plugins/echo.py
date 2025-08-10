# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Simple echo plugin used as a reference implementation."""

from __future__ import annotations

from typing import Any, Dict

from ..kernel import kernel


class EchoPlugin:
    """Echo back a message while updating user state."""

    def run(self, user_state: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        message = payload.get("message", "")
        user_state["last_message"] = message
        return {"echo": message}


def register() -> None:
    """Register the echo plugin with the microkernel."""
    kernel.register_plugin("echo", EchoPlugin())
