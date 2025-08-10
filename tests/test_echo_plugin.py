# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Integration test for the built-in echo plugin."""

from __future__ import annotations


def test_echo_plugin_integration(client) -> None:
    response = client.post(
        "/api/v1/invoke",
        json={"plugin": "echo", "payload": {"message": "hi"}, "user_id": "alice"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "result": {"echo": "hi"},
        "state": {"last_message": "hi"},
    }

