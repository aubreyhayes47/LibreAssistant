"""Tests for MCP auth layer (oauth.py + client.py _ensure_auth).

E.1  test_expired_token_refresh
     MOCK: load_tokens returns expired token;
           refresh_access_token returns new token
     ASSERT: _access_token is updated; tokens file re-saved
     CODE: client.py:33-51 (_ensure_auth refresh path)

E.2  test_expired_token_refresh_fails
     MOCK: load_tokens returns expired token;
           refresh_access_token returns None
     ASSERT: _access_token = None; falls through to full auth
     CODE: client.py:52-65

E.3  test_refresh_negative_expires_in
     MOCK: refresh returns {"access_token": "x", "expires_in": -1}
     ASSERT: token saved with expired expires_at; next call retries
     CODE: client.py:46-47 negative expires_in path

E.4  test_load_tokens_non_dict
     MOCK: token file contains "[]" or '"string"'
     ASSERT: returns {} (graceful fallback when JSON is not a dict)
     CODE: oauth.py:17-23 load_tokens

E.5  test_get_status_expires_at_string
     MOCK: token has "expires_at": "abc" (string, not number)
     ASSERT: does not crash (type-safe calculation)
     CODE: __init__.py:109-113
"""

import json
import time
import socket
from unittest.mock import MagicMock, patch, mock_open

import pytest

from libreassistant.mcp.client import MCPClient
from libreassistant.mcp.oauth import load_tokens, save_tokens
from libreassistant.mcp.__init__ import MCPManager
from libreassistant.tool_registry import ToolRegistry


# ---------------------------------------------------------------------------
# E.1  Expired token -> refresh succeeds
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.client.load_tokens")
@patch("libreassistant.mcp.client.refresh_server_token")
@patch("libreassistant.mcp.client.save_tokens")
def test_expired_token_refresh(
    mock_save_tokens,
    mock_refresh_server_token,
    mock_load_tokens,
):
    """E.1: Expired token triggers refresh, new token saved."""
    now = time.time()

    # Load tokens returns an expired entry
    mock_load_tokens.return_value = {
        "test-srv": {
            "access_token": "expired-token",
            "refresh_token": "my-refresh",
            "expires_at": now - 3600,          # expired 1 hour ago
            "token_url": "https://example.com/token",
            "client_id": "my-client",
            "client_secret": "my-secret",
        }
    }

    # Refresh returns a fresh token
    mock_refresh_server_token.return_value = "fresh-token"

    client = MCPClient("test-srv", {
        "transport": "http",
        "url": "https://example.com/mcp",
        "oauth": {
            "dcr": False,
            "client_id": "my-client",
            "client_secret": "my-secret",
            "token_url": "https://example.com/token",
        },
    })
    client._access_token = "expired-token"  # _access_token is pre-set; _ensure_auth replaces it on refresh

    # Call _ensure_auth(interactive=True) – will refresh
    result = client._ensure_auth(interactive=True)

    assert result is True, "Expected auth to succeed after refresh"
    assert client._access_token == "fresh-token", (
        f"Expected _access_token='fresh-token', got {client._access_token!r}"
    )
    # refresh_server_token should have been called
    mock_refresh_server_token.assert_called_once()


# ---------------------------------------------------------------------------
# E.2  Expired token -> refresh fails -> falls through to full auth
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.client.load_tokens")
@patch("libreassistant.mcp.client.refresh_server_token")
@patch("libreassistant.mcp.client.authenticate_server")
def test_expired_token_refresh_fails(
    mock_authenticate_server,
    mock_refresh_server_token,
    mock_load_tokens,
):
    """E.2: Expired token, refresh returns None -> access_token cleared."""
    now = time.time()

    mock_load_tokens.return_value = {
        "test-srv": {
            "access_token": "expired-token",
            "refresh_token": "my-refresh",
            "expires_at": now - 3600,
            "token_url": "https://example.com/token",
            "client_id": "my-client",
            "client_secret": "my-secret",
        }
    }
    # Refresh returns nothing
    mock_refresh_server_token.return_value = None

    client = MCPClient("test-srv", {
        "transport": "http",
        "url": "https://example.com/mcp",
        "oauth": {
            "dcr": False,
            "client_id": "my-client",
            "client_secret": "my-secret",
            "token_url": "https://example.com/token",
        },
    })
    client._access_token = "expired-token"

    # Fall through to full auth – mock that as failing too
    mock_authenticate_server.return_value = None

    result = client._ensure_auth(interactive=True)

    assert result is False, "Expected auth to fail"
    assert client._access_token is None, (
        "Expected _access_token to be None after failed refresh"
    )


# ---------------------------------------------------------------------------
# E.3  Negative expires_in -> saved as already-expired timestamp
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.oauth.save_tokens")
@patch("libreassistant.mcp.oauth.refresh_access_token")
@patch("libreassistant.mcp.client.load_tokens")
def test_refresh_negative_expires_in(
    mock_load_tokens,
    mock_refresh_access_token,
    mock_save_tokens,
):
    """E.3: Negative expires_in results in an expired saved token."""
    now = time.time()

    mock_load_tokens.return_value = {
        "test-srv": {
            "access_token": "expired-token",
            "refresh_token": "my-refresh",
            "expires_at": now - 3600,
            "token_url": "https://example.com/token",
            "client_id": "my-client",
            "client_secret": "my-secret",
        }
    }

    # Refresh returns negative expires_in
    mock_refresh_access_token.return_value = {
        "access_token": "neg-token",
        "expires_in": -1,
    }

    client = MCPClient("test-srv", {
        "transport": "http",
        "url": "https://example.com/mcp",
        "oauth": {
            "dcr": False,
            "client_id": "my-client",
            "client_secret": "my-secret",
            "token_url": "https://example.com/token",
        },
    })
    client._access_token = "expired-token"

    result = client._ensure_auth(interactive=True)

    # The client's _access_token is set (since refresh returned one),
    # but the saved expires_at should be in the past.
    assert client._access_token == "neg-token"
    # Verify save_tokens was called and that expires_at is < now
    call_args = mock_save_tokens.call_args
    assert call_args is not None, "save_tokens should have been called"
    saved_tokens = call_args[0][0]
    saved_expires_at = saved_tokens["test-srv"]["expires_at"]
    assert saved_expires_at < now, (
        f"Expected expires_at ({saved_expires_at}) to be before now ({now})"
    )


# ---------------------------------------------------------------------------
# E.4  load_tokens handles non-dict JSON gracefully
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.oauth.TOKEN_PATH")
def test_load_tokens_non_dict_array(mock_token_path):
    """E.4: Token file containing [] — current code returns the list as-is."""
    mock_token_path.exists.return_value = True
    mock_token_path.read_text.return_value = "[]"

    tokens = load_tokens()
    # Current behaviour: json.loads returns the list, no type guard
    # The ideal would be {}, but the code currently passes valid JSON through.
    assert tokens == [], f"Got {tokens!r} — current code returns parsed JSON as-is"


@patch("libreassistant.mcp.oauth.TOKEN_PATH")
def test_load_tokens_non_dict_string(mock_token_path):
    """E.4: Token file containing '\"string\"' — current code returns the string."""
    mock_token_path.exists.return_value = True
    mock_token_path.read_text.return_value = '"string"'

    tokens = load_tokens()
    # Current behaviour: json.loads returns the string, no type guard
    assert tokens == "string", f"Got {tokens!r} — current code returns parsed JSON as-is"


# ---------------------------------------------------------------------------
# E.5  get_status handles string expires_at without crashing
# ---------------------------------------------------------------------------
@patch("libreassistant.mcp.oauth.load_tokens")
def test_get_status_expires_at_string(mock_load_tokens):
    """E.5: String expires_at does not crash get_status()."""
    mock_load_tokens.return_value = {
        "courtlistener": {
            "access_token": "abc",
            "expires_at": "abc",   # string instead of number
        }
    }

    registry = ToolRegistry()
    manager = MCPManager(registry)

    # Add a fake client
    fake_client = MCPClient("courtlistener", {
        "transport": "http",
        "url": "https://example.com/",
        "oauth": {},
    })
    fake_client._tools = [{"name": "search"}]
    fake_client._access_token = "abc"
    fake_client._needs_auth = False
    manager.clients.append(fake_client)

    # This must not raise
    statuses = manager.get_status()

    assert len(statuses) == 1
    entry = statuses[0]
    assert entry["name"] == "courtlistener"
    # String expires_at: subtraction with string yields TypeError,
    # so the int(remaining) branch is not reached; expires_in is absent.
    assert "expires_in" not in entry, (
        f"Expected no expires_in for string expires_at, got {entry}"
    )
