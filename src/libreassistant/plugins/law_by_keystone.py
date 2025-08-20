# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Law by Keystone plugin stub integrating with File I/O."""

from __future__ import annotations

from ..kernel import kernel
from ..mcp_adapter import MCPPluginAdapter
from . import file_io


class LawByKeystonePlugin(MCPPluginAdapter):
    """Export legal research results via the MCP law server."""

    def __init__(self) -> None:
        env = {"MCP_FS_BASE_DIR": file_io.ALLOWED_BASE_DIR}
        super().__init__(
            "servers/law_by_keystone/index.ts",
            "generate_legal_summary",
            env,
        )


def register() -> None:
    """Register the Law by Keystone plugin with the microkernel."""
    kernel.register_plugin("law_by_keystone", LawByKeystonePlugin())
