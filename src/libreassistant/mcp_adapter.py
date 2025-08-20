from __future__ import annotations

"""Adapters allowing MCP servers to appear as legacy Plugin objects."""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "src" / "mcp" / "server-runner.js"


class MCPClient:
    """Minimal JSON-RPC client speaking to an MCP server over stdio."""

    def __init__(self, module: str, env: Dict[str, str] | None = None) -> None:
        mod_path = Path(module)
        if not mod_path.is_absolute():
            mod_path = (ROOT / mod_path).resolve()
        env_vars = os.environ.copy()
        if env:
            env_vars.update(env)
        self.proc = subprocess.Popen(
            [
                "node",
                "--loader",
                "ts-node/esm",
                str(RUNNER),
                str(mod_path),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            cwd=str(ROOT),
            env=env_vars,
        )
        self.next_id = 1

        # Perform a basic handshake to ensure the server is ready
        self.request("listTools")

    def request(self, method: str, params: Any | None = None) -> Any:
        req = {"jsonrpc": "2.0", "id": self.next_id, "method": method}
        self.next_id += 1
        if params is not None:
            req["params"] = params
        assert self.proc.stdin and self.proc.stdout
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("no response from MCP server")
        res = json.loads(line)
        if "error" in res:
            raise RuntimeError(res["error"]["message"])
        return res["result"]

    def invoke(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self.request("invoke", {"tool": tool, "params": params})

    def close(self) -> None:
        self.proc.kill()


Resolver = Callable[[Dict[str, Any]], Tuple[str, Dict[str, Any]]]


class MCPPluginAdapter:
    """Expose an MCP server as a legacy Plugin object."""

    def __init__(
        self,
        module: str,
        resolver: str | Resolver,
        env: Dict[str, str] | None = None,
    ) -> None:
        self.client = MCPClient(module, env)
        self.resolver = resolver

    def close(self) -> None:
        """Release resources held by the underlying MCP client."""
        self.client.close()

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        try:
            self.close()
        except Exception:
            pass

    def _resolve(self, payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        if callable(self.resolver):
            return self.resolver(payload)
        return self.resolver, payload

    def run(
        self, user_state: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            tool, params = self._resolve(payload)
        except Exception as exc:  # pragma: no cover - defensive
            return {"error": str(exc)}
        try:
            return self.client.invoke(tool, params)
        except Exception as exc:
            return {"error": str(exc)}
