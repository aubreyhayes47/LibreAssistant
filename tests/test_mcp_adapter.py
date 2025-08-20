import subprocess
import pytest
from libreassistant.mcp_adapter import MCPClient


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
