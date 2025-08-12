# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""File I/O plugin providing basic filesystem operations."""

from __future__ import annotations

import os
from typing import Any, Dict

from ..kernel import kernel

# Filesystem operations are restricted to this base directory. Paths provided by
# users will be resolved relative to this directory and rejected if they escape
# it. The default uses a "desktop" directory in the user's home folder.
ALLOWED_BASE_DIR = os.path.join(os.path.expanduser("~"), "desktop")


class FileIOPlugin:
    """Perform basic file operations with explicit confirmation for risky actions."""

    def run(self, user_state: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        operation = payload.get("operation")
        raw_path = payload.get("path")
        if not operation or not raw_path:
            return {"error": "operation and path required"}

        allowed_dir = os.path.realpath(os.path.expanduser(ALLOWED_BASE_DIR))

        user_path = os.path.expanduser(raw_path)
        if not os.path.isabs(user_path):
            user_path = os.path.join(allowed_dir, user_path)
        path = os.path.realpath(user_path)

        if not (path == allowed_dir or path.startswith(allowed_dir + os.sep)):
            return {"error": "path outside allowed directory"}

        user_state["last_file_path"] = path

        confirm = payload.get("confirm", False)
        content = payload.get("content", "")

        try:
            if operation == "read":
                with open(path, "r", encoding="utf-8") as fh:
                    data = fh.read()
                return {"content": data}
            if operation == "create":
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(content)
                return {"status": "created"}
            if operation == "update":
                if not confirm:
                    return {"error": "explicit confirmation required"}
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(content)
                return {"status": "updated"}
            if operation == "delete":
                if not confirm:
                    return {"error": "explicit confirmation required"}
                os.remove(path)
                return {"status": "deleted"}
            return {"error": "unknown operation"}
        except OSError as exc:  # pragma: no cover - error branch
            return {"error": str(exc)}


def register() -> None:
    """Register the file I/O plugin with the microkernel."""
    kernel.register_plugin("file_io", FileIOPlugin())
