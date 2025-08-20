import json
import subprocess
import sys
import textwrap

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
        import json
        import sys

        for line in sys.stdin:
            req = json.loads(line)
            if req["method"] == "listTools":
                res = {"jsonrpc": "2.0", "id": req["id"], "result": {"tools": []}}
            else:
                res = {
                    "jsonrpc": "2.0",
                    "id": req["id"],
                    "error": {"message": "unknown method"},
                }
            print(json.dumps(res))
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


def test_request_times_out():
    client = MCPClient.__new__(MCPClient)
    client.proc = subprocess.Popen(
        ["sleep", "100"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    client.next_id = 1
    client.timeout = None
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
    try:
        assert client.request("listTools") == {"tools": []}
    finally:
        client.close()
