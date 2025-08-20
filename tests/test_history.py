# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for recording and retrieving past requests."""

from __future__ import annotations


def test_history_tracks_invocations(client) -> None:
    payload1 = {"message": "hi"}
    payload2 = {"message": "bye"}
    client.post(
        "/api/v1/invoke",
        json={"plugin": "echo", "payload": payload1, "user_id": "alice"},
    )
    client.post(
        "/api/v1/invoke",
        json={"plugin": "echo", "payload": payload2, "user_id": "alice"},
    )
    response = client.get("/api/v1/history/alice")
    assert response.status_code == 200
    assert response.json()["history"] == [
        {"plugin": "echo", "payload": payload1},
        {"plugin": "echo", "payload": payload2},
    ]
