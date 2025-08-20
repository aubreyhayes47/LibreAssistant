# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for the personal data vault and consent endpoints."""
from __future__ import annotations

import pytest

from libreassistant.vault import DataVault


def test_vault_crud_and_export(client):
    user_id = "alice"
    payload = {"favorite": "cats"}

    resp = client.post(f"/api/v1/consent/{user_id}", json={"consent": True})
    assert resp.status_code == 200

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

    resp = client.post(f"/api/v1/consent/{user_id}", json={"consent": True})
    assert resp.status_code == 200

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


def test_vault_requires_consent(client):
    user_id = "eve"
    payload = {"pet": "parrot"}

    resp = client.post(f"/api/v1/vault/{user_id}", json={"data": payload})
    assert resp.status_code == 403

    resp = client.get(f"/api/v1/vault/{user_id}")
    assert resp.status_code == 403

    resp = client.post(f"/api/v1/consent/{user_id}", json={"consent": True})
    assert resp.status_code == 200

    resp = client.post(f"/api/v1/vault/{user_id}", json={"data": payload})
    assert resp.status_code == 200

    resp = client.get(f"/api/v1/vault/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["data"] == payload


def test_vault_rejects_non_serializable_data():
    vault = DataVault()
    user_id = "charlie"
    vault.set_consent(user_id, True)
    with pytest.raises(ValueError, match="JSON-serializable"):
        vault.store(user_id, {"bad": object()})
    assert vault.retrieve(user_id) == {}
