"""Tests for MCP recovery/resilience behaviours (client.py + __init__.py).

G.1  test_send_http_429_parseable_body
     MOCK: urlopen raises HTTPError(429) with JSON body
     ASSERT: _parse_response returns body dict; _session_id cleared
     CODE: client.py:134 (Fix C, non-401 URLError path)

G.2  test_send_http_429_nonparseable_body
     MOCK: urlopen raises HTTPError(429) with empty body
     ASSERT: _session_id cleared; returns {} (empty body is parseable as empty)
     CODE: client.py:134-140

G.3  test_connect_all_twice
     CALL: manager.connect_all() twice
     ASSERT: no crash; clients accumulate (known resource leak)
     CODE: __init__.py:17-36

G.4  test_shutdown_hang
     MOCK: subprocess ignores SIGTERM + SIGKILL (zombie)
     ASSERT: disconnect second wait() should also have timeout
             (currently blocks forever — known bug)
     CODE: client.py:271-279
"""

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from libreassistant.mcp.client import MCPClient
from libreassistant.mcp.__init__ import MCPManager
from libreassistant.tool_registry import ToolRegistry


# Import URLError for type checking and exception handling
from urllib.error import URLError, HTTPError


def _make_http_error(status_code: int, body: str):  # helper: builds an HTTPError with a synthetic body for testing error handling
    """Build an HTTPError-like exception with .read() and .code."""
    import io
    fp = io.BytesIO(body.encode())
    exc = HTTPError(
        url="http://localhost/",
        code=status_code,
        msg="Too Many Requests",
        hdrs={},
        fp=fp,
    )
    return exc


# ---------------------------------------------------------------------------
# G.1  HTTP 429 with parseable JSON body
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.client.urlopen")
def test_send_http_429_parseable_body(mock_urlopen):
    """G.1: 429 with JSON body returns parsed dict; _session_id cleared."""
    client = MCPClient("test-srv", {
        "transport": "http",
        "url": "http://localhost:9999/",
    })
    client._session_id = "old-session"

    body = json.dumps({"detail": "Rate limit exceeded", "retry_after": 5})
    mock_urlopen.side_effect = _make_http_error(429, body)

    result = client._send_http({
        "jsonrpc": "2.0", "id": 1, "method": "tools/list",
    })

    # The parsed body should be returned
    assert result == {"detail": "Rate limit exceeded", "retry_after": 5}, (
        f"Expected parsed body dict, got {result!r}"
    )
    # Session must be cleared on error
    assert client._session_id is None, (
        f"Expected _session_id cleared after 429, got {client._session_id!r}"
    )


# ---------------------------------------------------------------------------
# G.2  HTTP 429 with non-parseable (empty) body
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.client.urlopen")
def test_send_http_429_nonparseable_body(mock_urlopen):
    """G.2: 429 with empty body clears _session_id and returns {}.

    The _parse_response function strips whitespace and returns {}
    for an empty string, so the URLError path's try/except returns
    the empty dict rather than re-raising.
    """
    client = MCPClient("test-srv", {
        "transport": "http",
        "url": "http://localhost:9999/",
    })
    client._session_id = "old-session"

    mock_urlopen.side_effect = _make_http_error(429, "")

    # Empty body -> _parse_response("") -> {} (the empty guard at line 84)
    result = client._send_http({
        "jsonrpc": "2.0", "id": 1, "method": "tools/list",
    })

    assert result == {}, (
        f"Expected empty dict from non-parseable 429 body, got {result!r}"
    )
    # Session must be cleared
    assert client._session_id is None, (
        f"Expected _session_id cleared after non-parseable 429, got {client._session_id!r}"
    )


# ---------------------------------------------------------------------------
# G.3  connect_all() called twice — no crash, clients accumulate
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.__init__.MCPClient")
@patch("libreassistant.mcp.__init__.get_servers")
def test_connect_all_twice(mock_get_servers, mock_mcpclient_cls):
    """G.3: Double connect_all does not crash (known: clients accumulate)."""
    mock_get_servers.return_value = [
        {"name": "srv-a", "transport": "http", "url": "http://a/"},
        {"name": "srv-b", "transport": "http", "url": "http://b/"},
    ]

    def make_fake_client(**kwargs):
        c = MagicMock()
        c.name = kwargs.get("name", "srv-a")
        c._needs_auth = False
        c.lazy_connect.return_value = [
            {"name": "ping", "description": "", "inputSchema": {"type": "object"}}
        ]
        c.tools = []
        return c

    mock_mcpclient_cls.side_effect = lambda name, cfg: make_fake_client(name=name)

    registry = ToolRegistry()
    manager = MCPManager(registry)

    # First call
    r1 = manager.connect_all()
    assert len(r1) == 2, f"Expected 2 results on first connect, got {r1}"
    assert len(manager.clients) == 2, (
        f"Expected 2 clients after first connect, got {len(manager.clients)}"
    )

    # Second call — guard returns early
    r2 = manager.connect_all()
    assert len(r2) == 1, f"Expected 1 result on second connect, got {r2}"
    assert "already connected" in r2[0], f"Expected 'already connected' message, got {r2}"


# ---------------------------------------------------------------------------
# G.4  shutdown — subprocess ignores SIGTERM and SIGKILL (zombie scenario)
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.client.subprocess.Popen")
def test_shutdown_hang(mock_popen):
    """G.4: Subprocess that ignores signals should not cause disconnect to hang forever.

    Tests the code path where the process ignores SIGTERM and then SIGKILL.
    The second wait() may still block; this test documents the known limitation.
    """
    client = MCPClient("test-srv", {
        "transport": "stdio",
        "command": "stubborn-binary",
    })

    # Build a fake process that ignores SIGTERM but eventually dies on SIGKILL
    fake_proc = MagicMock()

    # First wait (after SIGTERM) raises TimeoutExpired
    import subprocess as sp
    fake_proc.wait.side_effect = [
        sp.TimeoutExpired(cmd="stubborn-binary", timeout=5),
        None,  # second wait (after SIGKILL) succeeds
    ]
    fake_proc.poll.return_value = None
    client._proc = fake_proc

    # This must not hang or crash
    try:
        client.disconnect()
    except Exception as exc:
        pytest.fail(f"disconnect() raised unexpectedly: {exc}")

    # Verify the kill path was reached
    assert fake_proc.terminate.called, "terminate() should have been called"
    assert fake_proc.kill.called, "kill() should have been called"
    # wait() should have been called twice (terminate wait + kill wait)
    assert fake_proc.wait.call_count >= 2, (
        f"Expected wait() called at least twice, got {fake_proc.wait.call_count}"
    )


def test_stub_live_deauth_tool_lifecycle():
    registry = ToolRegistry()
    manager = MCPManager(registry)

    client = MagicMock()
    client.name = "courtlistener"
    client._needs_auth = True
    client._tools = []
    client.finish_connect.return_value = [
        {"name": "search", "description": "Search", "inputSchema": {"type": "object", "properties": {}}}
    ]
    manager.clients.append(client)

    manager._register_stub(client)
    assert "setup_courtlistener" in registry.tool_names

    result = registry.dispatch("setup_courtlistener", {})
    assert "Authentication successful" in result
    assert "setup_courtlistener" not in registry.tool_names
    assert "courtlistener_search" in registry.tool_names

    with patch("libreassistant.mcp.oauth.load_tokens", return_value={"courtlistener": {"access_token": "x"}}), \
         patch("libreassistant.mcp.oauth.save_tokens") as save_tokens:
        assert manager.deauth_server("courtlistener") is True

    save_tokens.assert_called_once_with({})
    assert "courtlistener_search" not in registry.tool_names
    assert "setup_courtlistener" in registry.tool_names
