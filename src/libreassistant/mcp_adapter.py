# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Adapters allowing MCP servers to appear as legacy Plugin objects."""
from __future__ import annotations

import json
import logging
import os
import queue
import subprocess
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Tuple, Literal

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "src" / "mcp" / "server-runner.js"


class MCPClient:
    """Minimal JSON-RPC client speaking to an MCP server over stdio.

    The client manages a subprocess running an MCP server and provides a
    blocking ``request`` API.  It implements the context manager protocol so
    that resources are always released::

        with MCPClient("servers/echo/index.ts") as client:
            client.request("listTools")

    Exiting the ``with`` block automatically terminates the subprocess.
    """

    def __init__(
        self,
        module: str,
        env: Dict[str, str] | None = None,
        timeout: float | None = 30.0,
    ) -> None:
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
        self.timeout = timeout

        # Queue of raw lines from the server's stdout and structures for
        # matching responses to their request ``id``.
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._responses: Dict[int, queue.Queue[Dict[str, Any] | None]] = {}
        self._lock = threading.Lock()

        def _reader() -> None:
            """Background thread streaming raw server responses into ``_queue``."""
            if self.proc.stdout is None:
                raise RuntimeError("MCPClient process has no stdout")
            for line in self.proc.stdout:
                self._queue.put(line)
            self._queue.put(None)

        self._reader = threading.Thread(target=_reader, daemon=True)
        self._reader.start()

        def _dispatcher() -> None:
            """Parse queued lines and dispatch them to waiting callers."""
            while True:
                line = self._queue.get()
                if line is None:
                    with self._lock:
                        for resp_queue in self._responses.values():
                            resp_queue.put(None)
                    break
                res = json.loads(line)
                req_id = res.get("id")
                with self._lock:
                    q: queue.Queue[dict[str, Any] | None] | None = (
                        self._responses.get(req_id) if req_id is not None else None
                    )
                if q is not None:
                    q.put(res)

        self._dispatcher = threading.Thread(target=_dispatcher, daemon=True)
        self._dispatcher.start()

        # Perform a basic handshake to ensure the server is ready
        self.request("listTools")

    def request(
        self,
        method: str,
        params: Any | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send a JSON-RPC request and return the ``result`` field.

        Parameters are encoded in the standard JSON-RPC 2.0 shape containing
        ``jsonrpc``, ``id`` and ``method`` keys plus an optional ``params``
        object. A response is awaited for ``timeout`` seconds (defaulting to
        ``self.timeout``); if no response arrives a :class:`TimeoutError` is
        raised. The server may report failures by including an ``error`` member
        in its response, which is surfaced here as ``RuntimeError``.
        """
        # Lazily initialise concurrency primitives when constructed via ``__new__``.
        if not hasattr(self, "_lock"):
            self._lock = threading.Lock()
        if not hasattr(self, "_responses"):
            self._responses = {}
        if not hasattr(self, "_queue"):
            self._queue = queue.Queue()
        if not hasattr(self, "_dispatcher"):
            def _dispatcher() -> None:
                while True:
                    line = self._queue.get()
                    if line is None:
                        with self._lock:
                            for resp_queue in self._responses.values():
                                resp_queue.put(None)
                        break
                    res = json.loads(line)
                    req_id = res.get("id")
                    with self._lock:
                        q: queue.Queue[dict[str, Any] | None] | None = (
                            self._responses.get(req_id) if req_id is not None else None
                        )
                    if q is not None:
                        q.put(res)
            self._dispatcher = threading.Thread(target=_dispatcher, daemon=True)
            self._dispatcher.start()

        with self._lock:
            req_id = self.next_id
            self.next_id += 1
            resp_queue: queue.Queue[Dict[str, Any] | None] = queue.Queue()
            self._responses[req_id] = resp_queue

        req = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            req["params"] = params
        if self.proc.stdin is None:
            raise RuntimeError("MCPClient process has no stdin")
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        wait = self.timeout if timeout is None else timeout
        try:
            res = (
                resp_queue.get(timeout=wait)
                if wait is not None
                else resp_queue.get()
            )
        except queue.Empty:
            raise TimeoutError(
                f"MCP server did not respond within {wait} seconds",
            ) from None
        finally:
            with self._lock:
                self._responses.pop(req_id, None)
        if res is None:
            raise RuntimeError("no response from MCP server")
        if "error" in res:
            raise RuntimeError(res["error"]["message"])
        return res["result"]

    def invoke(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a remote tool via JSON-RPC.

        This is a thin wrapper over :meth:`request` that always calls the
        ``invoke`` method on the MCP server, passing the tool name and
        arguments as parameters.
        """
        return self.request("invoke", {"tool": tool, "params": params})

    def close(self) -> None:
        try:
            self.proc.terminate()
            self.proc.wait()
        except Exception as exc:  # pragma: no cover - best effort
            logging.debug("Exception while terminating MCPClient process: %s", exc)
        finally:
            if getattr(self, "_reader", None) and self._reader.is_alive():
                self._reader.join(timeout=0.1)

    # -- context manager -------------------------------------------------

    def __enter__(self) -> "MCPClient":
        """Return ``self`` when entering a ``with`` block."""

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> Literal[False]:
        """Ensure the subprocess is terminated on context exit."""

        self.close()
        # Propagate any exception that occurred inside the with block.
        return False


Resolver = Callable[[Dict[str, Any]], Tuple[str, Dict[str, Any]]]


class MCPPluginAdapter:
    """Expose an MCP server as a legacy Plugin object."""

    def __init__(
        self,
        module: str,
        resolver: str | Resolver,
        env: Dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> None:
        self.client = MCPClient(module, env, timeout=timeout)
        self.resolver = resolver

    def close(self) -> None:
        """Release resources held by the underlying MCP client."""
        self.client.close()

    # Allow adapters to be used as context managers for automatic cleanup.
    def __enter__(self) -> "MCPPluginAdapter":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> Literal[False]:
        self.close()
        return False

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        try:
            self.close()
        except Exception:
            pass

    def _resolve(self, payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Map an incoming payload to a tool name and parameters.

        ``resolver`` may be a callable that produces a ``(tool, params)`` pair
        or a fixed tool name, in which case the raw payload is used as the
        parameter dictionary.
        """
        if callable(self.resolver):
            return self.resolver(payload)
        return self.resolver, payload

    def run(
        self, user_state: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the resolved tool against the MCP server.

        The payload is first translated into a target tool and parameter set
        using :meth:`_resolve`. Invocation errors or resolver failures are
        caught and returned as ``{"error": <message>}`` dictionaries so that
        callers receive structured failure information instead of exceptions.
        """
        try:
            tool, params = self._resolve(payload)
        except Exception as exc:  # pragma: no cover - defensive
            return {"error": str(exc)}
        try:
            return self.client.invoke(tool, params)
        except Exception as exc:
            return {"error": str(exc)}

