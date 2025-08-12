# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Law by Keystone plugin stub integrating with File I/O."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from ..kernel import kernel
from . import file_io


class LawByKeystonePlugin:
    """Export legal research results to the local filesystem."""

    def run(self, user_state: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        query = payload.get("query")
        fmt = payload.get("output_format", "md")
        output_path = payload.get("output_path")
        if not query or not output_path:
            return {"error": "query and output_path required"}

        if fmt not in {"md", "json", "html"}:
            return {"error": "unsupported format"}

        allowed_dir = os.path.realpath(os.path.expanduser(file_io.ALLOWED_BASE_DIR))
        user_path = os.path.expanduser(output_path)
        if not os.path.isabs(user_path):
            user_path = os.path.join(allowed_dir, user_path)
        output_dir = os.path.realpath(user_path)

        if not (output_dir == allowed_dir or output_dir.startswith(allowed_dir + os.sep)):
            return {"error": "path outside allowed directory"}

        os.makedirs(output_dir, exist_ok=True)

        summary = {
            "query": query,
            "results": [
                {"title": "Example Case", "summary": "No real data fetched"}
            ],
        }

        if fmt == "md":
            content = f"# Research Summary\n\nQuery: {query}\n"
            ext = "md"
        elif fmt == "json":
            content = json.dumps(summary, indent=2)
            ext = "json"
        else:  # html
            content = (
                "<html><body><h1>Research Summary</h1>"
                f"<p>Query: {query}</p></body></html>"
            )
            ext = "html"

        file_path = os.path.join(output_dir, f"summary.{ext}")
        file_plugin = file_io.FileIOPlugin()
        result = file_plugin.run(
            user_state,
            {"operation": "create", "path": file_path, "content": content},
        )
        if "error" in result:
            return result
        return {"status": "exported", "path": file_path}


def register() -> None:
    """Register the Law by Keystone plugin with the microkernel."""
    kernel.register_plugin("law_by_keystone", LawByKeystonePlugin())
