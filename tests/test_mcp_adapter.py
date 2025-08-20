import subprocess
import sys
import textwrap
import queue
import threading

import pytest

from libreassistant.mcp_adapter import MCPClient


@pytest.fixture
def mock_mcp_server():
    """Provide a minimal stand-in MCP server implemented in Python.

    This avoids requiring a Node.js environment during tests while still
    exercising the JSON-RPC plumbing used by :class:`MCPClient`.
    """

    script = textwrap.dedent(
        """
        import sys

        for line in sys.stdin:
            if '"listTools"' in line:
                res = '{"jsonrpc": "2.0", "id": 1, "result": {"tools": []}}'
            else:
                res = (
                    '{"jsonrpc": "2.0", "id": 1, '
                    '"error": {"message": "unknown method"}}'
                )
            print(res)
            sys.stdout.flush()
        """
    )

    proc = subprocess.Popen(
        [sys.executable, "-u", "-c", script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        yield proc
    finally:
        if proc.poll() is None:
            proc.kill()


def _setup_client(client: MCPClient) -> None:
    client._queue = queue.Queue()

    def _reader() -> None:
        if client.proc.stdout is None:
            raise RuntimeError("MCPClient process has no stdout")
        for line in client.proc.stdout:
            client._queue.put(line)
        client._queue.put(None)

    client._reader = threading.Thread(target=_reader, daemon=True)
    client._reader.start()


def test_request_times_out():
    client = MCPClient.__new__(MCPClient)
    client.proc = subprocess.Popen(
        ["sleep", "100"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    client.next_id = 1
    client.timeout = None
    _setup_client(client)
    try:
        with pytest.raises(TimeoutError):
            client.request("listTools", timeout=0.1)
    finally:
        client.close()


def test_list_tools_mock_server(mock_mcp_server):
    client = MCPClient.__new__(MCPClient)
    client.proc = mock_mcp_server
    client.next_id = 1
    client.timeout = None
    _setup_client(client)
    try:
        assert client.request("listTools") == {"tools": []}
    finally:
        client.close()


def test_request_no_stdin():
    client = MCPClient.__new__(MCPClient)
    client.proc = subprocess.Popen(
        ["sleep", "100"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    client.proc.stdin.close()
    client.proc.stdin = None
    client.next_id = 1
    client.timeout = None
    try:
        with pytest.raises(RuntimeError, match="no stdin"):
            client.request("listTools")
    finally:
        client.close()


def test_reader_no_stdout():
    client = MCPClient.__new__(MCPClient)
    client.proc = subprocess.Popen(
        ["sleep", "100"], stdin=subprocess.PIPE, stdout=None, text=True
    )
    client._queue = queue.Queue()

    def _reader() -> None:
        if client.proc.stdout is None:
            raise RuntimeError("MCPClient process has no stdout")
        for line in client.proc.stdout:
            client._queue.put(line)
        client._queue.put(None)

    try:
        with pytest.raises(RuntimeError, match="no stdout"):
            _reader()
    finally:
        client.close()
