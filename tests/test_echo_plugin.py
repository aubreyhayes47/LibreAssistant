# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Unit and integration tests for the built-in echo plugin."""

from __future__ import annotations


from typing import Any

from libreassistant.plugins.echo import EchoPlugin


def test_echo_plugin_unit() -> None:
    plugin = EchoPlugin()
    state: dict[str, Any] = {}
    result = plugin.run(state, {"message": "hi"})
    assert result == {"echo": "hi"}
    assert state["last_message"] == "hi"


def test_echo_plugin_integration(client) -> None:
    response = client.post(
        "/api/v1/invoke",
        json={"plugin": "echo", "payload": {"message": "hi"}, "user_id": "alice"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "result": {"echo": "hi"},
        "state": {
            "last_message": "hi",
            "history": [{"plugin": "echo", "payload": {"message": "hi"}}],
        },
    }

