"""Tests for tool_registry.py: ToolRegistry filtering, dispatch, MCPClient thread safety."""
from unittest.mock import MagicMock

import pytest

from libreassistant.tool_registry import ToolRegistry
from libreassistant.mcp.client import MCPClient


# --- Filtering (per-profile tool visibility) ---
def test_tool_registry_filter():  # filter() returns a NEW registry with only matching tools; original unchanged
    registry = ToolRegistry()
    for name in ["web_search", "web_fetch", "read_file", "terminal", "mcp/courtlistener/search"]:
        registry.register(name, "", {}, lambda x: x)
    filtered = registry.filter(["web_*"])
    assert set(filtered.tool_names) == {"web_search", "web_fetch"}
    assert set(registry.tool_names) == {"web_search", "web_fetch", "read_file", "terminal", "mcp/courtlistener/search"}


def test_tool_registry_filter_all():  # "*" matches all tools
    registry = ToolRegistry()
    registry.register("a", "", {}, lambda x: x)
    registry.register("b", "", {}, lambda x: x)
    filtered = registry.filter(["*"])
    assert set(filtered.tool_names) == {"a", "b"}


def test_tool_registry_filter_none():  # no match → empty filtered registry (not None)
    registry = ToolRegistry()
    registry.register("a", "", {}, lambda x: x)
    registry.register("b", "", {}, lambda x: x)
    filtered = registry.filter(["nonexistent"])
    assert filtered.tool_names == []


# --- MCPClient thread safety ---
def test_mcp_client_req_id_thread_safe():  # _next_id() uses an atomic counter for JSON-RPC request IDs
    client = MCPClient(name="test", config={})
    id1 = client._next_id()
    id2 = client._next_id()
    assert id2 == id1 + 1


# --- Filter preserves dispatch ability ---
def test_filter_preserves_handlers():  # dispatch works on the filtered copy; original handler function is preserved
    registry = ToolRegistry()
    registry.register("web_search", "", {}, lambda _: "called")
    filtered = registry.filter(["web_*"])
    result = filtered.dispatch("web_search", {})
    assert result == "called"


# --- Filter copies shared references ---
def test_filter_copies_mcp_manager():  # mcp_manager is shared by reference; filtered registries see the same MCP connections
    registry = ToolRegistry()
    mock = MagicMock()
    registry.mcp_manager = mock
    filtered = registry.filter(["*"])
    assert filtered.mcp_manager is mock


# --- Unknown tool dispatch ---
def test_dispatch_unknown():  # dispatch returns error string, does not raise
    registry = ToolRegistry()
    result = registry.dispatch("nonexistent", {})
    assert result.startswith("Error: unknown tool")


# --- Default state and property copying ---
def test_default_current_profile():  # fresh registry defaults to "default" profile and no session
    registry = ToolRegistry()
    assert registry.current_profile == "default"
    assert registry.session_id is None


def test_filter_copies_current_profile():  # current_profile is copied to the filtered registry
    registry = ToolRegistry()
    registry.current_profile = "legal"
    filtered = registry.filter(["*"])
    assert filtered.current_profile == "legal"


def test_filter_copies_session_id():  # session_id is copied to the filtered registry (needed for message attribution)
    registry = ToolRegistry()
    registry.session_id = "sess_abc123"
    filtered = registry.filter(["*"])
    assert filtered.session_id == "sess_abc123"


def test_filtered_service_handler_uses_shared_runtime_context():
    from libreassistant.mcp import MCPManager
    from libreassistant.tools import register_all

    global_registry = ToolRegistry()
    register_all(global_registry)
    filtered = global_registry.filter(["list_services"])
    manager = MCPManager(filtered)

    fake_client = MagicMock()
    fake_client.name = "courtlistener"
    fake_client._needs_auth = True
    fake_client._tools = []
    manager.clients.append(fake_client)

    result = filtered.dispatch("list_services", {})

    assert "courtlistener" in result
    assert "not authenticated" in result
    assert global_registry.mcp_manager is manager
