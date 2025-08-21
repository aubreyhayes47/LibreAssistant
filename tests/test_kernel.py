# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Unit tests for the Microkernel core components."""

from __future__ import annotations

from libreassistant.kernel import Microkernel


class EchoPlugin:
    """Simple plugin used for testing."""

    def run(self, state, payload):
        state["echo"] = payload["msg"]
        return {"echo": payload["msg"]}


def test_register_and_invoke_updates_state() -> None:
    kernel = Microkernel()
    kernel.register_plugin("echo", EchoPlugin())
    result = kernel.invoke("echo", "user", {"msg": "hi"})
    assert result == {"echo": "hi"}
    assert kernel.get_state("user") == {"echo": "hi", "user_id": "user"}


def test_get_state_returns_same_dict() -> None:
    kernel = Microkernel()
    first = kernel.get_state("alice")
    first["x"] = 1
    second = kernel.get_state("alice")
    assert first is second
    assert second["x"] == 1


def test_invoke_missing_plugin_returns_error() -> None:
    kernel = Microkernel()
    result = kernel.invoke("missing", "user", {})
    assert result == {"error": "unknown_plugin", "plugin": "missing"}


def test_reset_clears_plugins_and_state() -> None:
    kernel = Microkernel()
    kernel.register_plugin("echo", EchoPlugin())
    kernel.invoke("echo", "user", {"msg": "hi"})
    kernel.reset()
    assert kernel.get_state("user") == {"user_id": "user"}
    assert kernel.invoke("echo", "user", {"msg": "hi"}) == {
        "error": "unknown_plugin",
        "plugin": "echo",
    }
