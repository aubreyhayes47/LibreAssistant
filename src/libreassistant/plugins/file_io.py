# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""File I/O plugin providing basic filesystem operations."""

from __future__ import annotations

import os
from typing import Any, Dict, Literal, Tuple

from pydantic import BaseModel, model_validator

from ..kernel import kernel
from ..mcp_adapter import MCPPluginAdapter
from .. import db

# Filesystem operations are restricted to this base directory. Paths
# provided by users will be resolved relative to this directory and
# rejected if they escape it. The default uses a "desktop" directory in
# the user's home folder.
ALLOWED_BASE_DIR = os.path.join(os.path.expanduser("~"), "desktop")


def _resolver(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    op = payload.get("operation")
    mapping = {
        "read": "fs_read",
        "create": "fs_create",
        "update": "fs_update",
        "delete": "fs_delete",
        "list": "fs_list",
    }
    if op not in mapping:
        raise ValueError("unknown operation")
    params = dict(payload)
    params.pop("operation")
    return mapping[op], params


class FileIOInput(BaseModel):
    """Schema for payloads accepted by :class:`FileIOPlugin`."""

    operation: Literal["read", "create", "update", "delete", "list"]
    path: str
    content: str | None = None
    confirm: bool | None = None

    @model_validator(mode="after")
    def _check_requirements(self) -> "FileIOInput":
        if self.operation in {"create", "update"} and self.content is None:
            raise ValueError("content required")
        if self.operation in {"update", "delete"} and not self.confirm:
            raise ValueError("confirm required")
        return self


class FileIOPlugin(MCPPluginAdapter):
    """Perform basic file operations through the MCP file server."""

    InputModel = FileIOInput

    def __init__(self) -> None:
        if not os.path.isdir(ALLOWED_BASE_DIR):
            os.makedirs(ALLOWED_BASE_DIR, exist_ok=True)
        env = {"MCP_FS_BASE_DIR": ALLOWED_BASE_DIR}
        super().__init__("servers/files/index.ts", _resolver, env)

    def run(
        self, user_state: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        user_id = user_state.get("user_id")
        if "path" in payload:
            # Resolve the path to its canonical form and ensure it remains
            # within the allowed base directory. The resolved path is stored
            # in ``user_state`` and passed on to the server to prevent path
            # traversal attacks. ``os.path.commonpath`` raises ``ValueError``
            # for paths on different drives; such requests are rejected.
            resolved_path = os.path.realpath(payload["path"])
            base_dir = os.path.realpath(ALLOWED_BASE_DIR)
            try:
                # ``commonpath`` may raise ``ValueError`` on cross-drive inputs
                common = os.path.commonpath([resolved_path, base_dir])
            except ValueError:
                return {"error": "path outside allowed directory"}
            if common != base_dir:
                return {"error": "path outside allowed directory"}
            user_state["last_file_path"] = resolved_path
            payload["path"] = resolved_path
            payload["user_id"] = user_id
            db.add_file_audit(user_id, payload.get("operation"), resolved_path)
        return super().run(user_state, payload)


def register() -> None:
    """Register the file I/O plugin with the microkernel."""
    kernel.register_plugin("file_io", FileIOPlugin())
