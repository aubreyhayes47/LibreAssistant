# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Simple echo plugin used as a reference implementation."""

from __future__ import annotations

from typing import Any, Dict

from ..kernel import kernel
from ..mcp_adapter import MCPPluginAdapter


class EchoPlugin(MCPPluginAdapter):
    """Echo back a message while updating user state via MCP server."""

    def __init__(self) -> None:
        super().__init__("servers/echo/index.ts", "echo_message")

    def run(
        self, user_state: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = super().run(user_state, payload)
        user_state["last_message"] = payload.get("message", "")
        return result


def register() -> None:
    """Register the echo plugin with the microkernel."""
    kernel.register_plugin("echo", EchoPlugin())
