"""Tests for recording history entries explicitly."""


def test_record_history_endpoint(client) -> None:
    response = client.post(
        "/api/v1/history/alice",
        json={"plugin": "echo", "payload": {"message": "hi"}, "granted": True},
    )
    assert response.status_code == 200
    hist = client.get("/api/v1/history/alice").json()["history"]
    assert hist[-1] == {"plugin": "echo", "payload": {"message": "hi"}, "granted": True}
