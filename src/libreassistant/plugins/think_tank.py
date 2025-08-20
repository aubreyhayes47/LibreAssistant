# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""ThinkTank plugin coordinating multiple internal experts."""

from __future__ import annotations

from typing import Any, Dict

from ..kernel import kernel
from ..mcp_adapter import MCPPluginAdapter


class ThinkTankPlugin(MCPPluginAdapter):
    """Orchestrate specialist agents via the MCP ThinkTank server."""

    def __init__(self) -> None:
        super().__init__("servers/think_tank/index.ts", "analyze_goal")

    def run(
        self, user_state: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = super().run(user_state, payload)
        if "analysis" in result:
            dossier = user_state.setdefault("thinktank_dossier", [])
            dossier.append(result["analysis"])
        return result


def register() -> None:
    """Register the ThinkTank plugin with the microkernel."""
    kernel.register_plugin("think_tank", ThinkTankPlugin())
