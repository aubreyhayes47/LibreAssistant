"""Tests for the personal data vault and consent endpoints."""
from __future__ import annotations


def test_vault_crud_and_export(client):
    user_id = "alice"
    payload = {"favorite": "cats"}

    resp = client.post(f"/api/v1/vault/{user_id}", json={"data": payload})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    resp = client.get(f"/api/v1/vault/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["data"] == payload

    resp = client.get(f"/api/v1/vault/{user_id}/export")
    assert resp.status_code == 200
    assert resp.json()["data"] == payload

    resp = client.delete(f"/api/v1/vault/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"

    resp = client.get(f"/api/v1/vault/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["data"] == {}


def test_consent_toggle(client):
    user_id = "bob"
    resp = client.get(f"/api/v1/consent/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["consent"] is False

    resp = client.post(f"/api/v1/consent/{user_id}", json={"consent": True})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    resp = client.get(f"/api/v1/consent/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["consent"] is True
