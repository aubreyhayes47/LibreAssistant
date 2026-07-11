"""Tests for MCP transport layer (client.py).

D.1  test_send_http_timeout_recovers_session
     MOCK: urlopen returns response with mcp-session-id header,
           then resp.read() raises socket.timeout
     ASSERT: client._session_id is None after exception
     CODE: client.py:110-114 (Fix A inner try/except)

D.2  test_send_http_empty_body
     MOCK: urlopen returns 200 with empty body
     ASSERT: returns {} from _send_http
     CODE: client.py:83-85 (_parse_response empty guard)

D.3  test_send_http_non_json_response
     MOCK: resp.read() returns b"null" or b"[]"
     ASSERT: call_tool raises TypeError (null) or AttributeError ([]) or returns gracefully
     CODE: client.py:254-258 (caller expects dict)

D.4  test_send_http_connection_reset
     MOCK: urlopen raises ConnectionResetError
     ASSERT: exception propagates; _session_id is cleared
     CODE: client.py:110-114 (Fix A catches all Exception)

D.5  test_send_stdio_empty_line
     MOCK: subprocess stdout returns "  \n"
     ASSERT: returns {} (not JSONDecodeError)
     CODE: client.py:151 _send_stdio → _parse_response (Fix B)
"""

import json
import socket
import subprocess
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from libreassistant.mcp.client import MCPClient


# ---------------------------------------------------------------------------
# Helper: build a minimal client configured for HTTP transport
# ---------------------------------------------------------------------------
def _http_client() -> MCPClient:
    return MCPClient("test-srv", {
        "transport": "http",
        "url": "http://localhost:9999/",
    })


# ---------------------------------------------------------------------------
# D.1  socket.timeout during read clears _session_id
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.client.urlopen")
def test_send_http_timeout_recovers_session(mock_urlopen):
    """D.1: socket.timeout during read clears session ID and re-raises."""
    client = _http_client()  # reuses _http_client() then overrides transport/command to stdio
    client._session_id = "old-session-id"

    # urlopen returns a response with a session header; read raises timeout
    fake_resp = MagicMock()
    fake_resp.headers.get.return_value = "new-session-id"
    fake_resp.read.side_effect = socket.timeout("timed out")
    mock_urlopen.return_value = fake_resp

    with pytest.raises(socket.timeout):
        client._send_http({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
        })

    # Session must be cleared after a read failure
    assert client._session_id is None, (
        f"Expected _session_id to be None after timeout, got {client._session_id!r}"
    )


# ---------------------------------------------------------------------------
# D.2  Empty response body -> {}
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.client.urlopen")
def test_send_http_empty_body(mock_urlopen):
    """D.2: Empty body returns {} without crashing."""
    client = _http_client()

    fake_resp = MagicMock()
    fake_resp.headers.get.return_value = None
    fake_resp.read.return_value = b"   \n\n  "
    mock_urlopen.return_value = fake_resp

    result = client._send_http({
        "jsonrpc": "2.0", "id": 1, "method": "ping",
    })

    assert result == {}, f"Expected empty dict, got {result!r}"


# ---------------------------------------------------------------------------
# D.3  Non-dict JSON response (null / array) — call_tool must not crash
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.client.urlopen")
def test_send_http_non_json_response_null(mock_urlopen):
    """D.3: 'null' body — call_tool raises TypeError ('in' on None)."""
    client = _http_client()

    fake_resp = MagicMock()
    fake_resp.headers.get.return_value = None
    fake_resp.read.return_value = b"null"
    mock_urlopen.return_value = fake_resp

    # The parsed response is None (JSON null).
    # call_tool does `if "error" in result` — TypeError on None.
    with pytest.raises(TypeError):
        client.call_tool("some_tool", {"arg": 1})


@patch("libreassistant.mcp.client.urlopen")
def test_send_http_non_json_response_array(mock_urlopen):
    """D.3: '[]' body — call_tool raises AttributeError (.get on list)."""
    client = _http_client()

    fake_resp = MagicMock()
    fake_resp.headers.get.return_value = None
    fake_resp.read.return_value = b"[]"
    mock_urlopen.return_value = fake_resp

    # The parsed response is [].
    # `"error" in []` is False (checks list elements), then
    # `[].get("result", ...)` raises AttributeError.
    with pytest.raises(AttributeError):
        client.call_tool("some_tool", {"arg": 1})


# ---------------------------------------------------------------------------
# D.4  ConnectionResetError propagates and clears _session_id
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.client.urlopen")
def test_send_http_connection_reset(mock_urlopen):
    """D.4: ConnectionResetError propagates; _session_id cleared."""
    client = _http_client()
    client._session_id = "session-to-clear"

    # Simulate: urlopen succeeds, but read raises ConnectionResetError
    fake_resp = MagicMock()
    fake_resp.headers.get.return_value = "new-session"
    fake_resp.read.side_effect = ConnectionResetError("reset")
    mock_urlopen.return_value = fake_resp

    with pytest.raises(ConnectionResetError):
        client._send_http({
            "jsonrpc": "2.0", "id": 1, "method": "tools/list",
        })

    assert client._session_id is None, (
        f"Expected _session_id to be None after reset, got {client._session_id!r}"
    )


# ---------------------------------------------------------------------------
# D.5  stdio empty whitespace-only line -> {} (no JSONDecodeError)
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.client.MCPClient._read_stderr")
@patch("libreassistant.mcp.client.subprocess.Popen")
def test_send_stdio_empty_line(mock_popen, mock_read_stderr):
    """D.5: Whitespace-only stdout line returns {}."""
    client = _http_client()
    # Switch transport to stdio and set up a fake subprocess
    client.transport = "stdio"
    client.command = "some-binary"

    # Build a fake process
    fake_proc = MagicMock()
    fake_proc.poll.return_value = None
    fake_proc.stdin = MagicMock()
    fake_proc.stdout.readline.return_value = "  \n"
    mock_popen.return_value = fake_proc

    client._proc = fake_proc
    client._stdout_lock = MagicMock()

    result = client._send_stdio({
        "jsonrpc": "2.0", "id": 1, "method": "ping",
    })

    assert result == {}, f"Expected empty dict, got {result!r}"


def test_call_tool_retries_rate_limit_once():
    client = _http_client()
    throttled = {
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": "Rate limit exceeded: HTTP 429: {'detail': 'Request was throttled. Rate limit exceeded: 5/min. Expected available in 2 seconds.'}",
                }
            ]
        }
    }
    ok = {"result": {"content": [{"type": "text", "text": "ok"}]}}
    client._send_request = MagicMock(side_effect=[throttled, ok])

    with patch("libreassistant.mcp.client.time.sleep") as sleep:
        result = client.call_tool("search", {"q": "roe"})

    assert result == "ok"
    sleep.assert_called_once_with(3)
    assert client._send_request.call_count == 2


def test_call_tool_retries_incomplete_read_once():
    import http.client

    client = _http_client()
    ok = {"result": {"content": [{"type": "text", "text": "ok"}]}}
    client._send_request = MagicMock(side_effect=[http.client.IncompleteRead(b""), ok])

    with patch("libreassistant.mcp.client.time.sleep") as sleep:
        result = client.call_tool("resume_citation_analysis", {"job_id": "abc"})

    assert result == "ok"
    sleep.assert_called_once_with(1)
    assert client._send_request.call_count == 2
