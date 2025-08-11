# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for the FastAPI application and microkernel endpoint."""

from __future__ import annotations

from libreassistant.kernel import kernel


def test_read_root(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "LibreAssistant API"}


def test_user_state_persists(client) -> None:
    class CounterPlugin:
        def run(self, state, payload):
            state["count"] = state.get("count", 0) + 1
            return {"count": state["count"]}

    kernel.register_plugin("counter", CounterPlugin())
    first = client.post(
        "/api/v1/invoke", json={"plugin": "counter", "payload": {}, "user_id": "bob"}
    )
    second = client.post(
        "/api/v1/invoke", json={"plugin": "counter", "payload": {}, "user_id": "bob"}
    )
    assert first.json()["result"] == {"count": 1}
    assert second.json()["result"] == {"count": 2}
    assert second.json()["state"]["count"] == 2

