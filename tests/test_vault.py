# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for the personal data vault and consent endpoints."""
from __future__ import annotations

import shutil
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


def test_vault_persistence(tmp_path):
    key_file = tmp_path / "vault.key"
    db_path = tmp_path / "vault.db"
    user_id = "frank"

    vault1 = DataVault(key_file=key_file, db_path=db_path)
    vault1.set_consent(user_id, True)
    vault1.store(user_id, {"note": "hello"})

    vault2 = DataVault(key_file=key_file, db_path=db_path)
    assert vault2.get_consent(user_id) is True
    assert vault2.retrieve(user_id) == {"note": "hello"}


def test_vault_key_rotation(tmp_path):
    key_file = tmp_path / "vault.key"
    db_path = tmp_path / "vault.db"
    user_id = "george"

    vault = DataVault(key_file=key_file, db_path=db_path)
    vault.set_consent(user_id, True)
    vault.store(user_id, {"x": 1})

    old_key = key_file.read_bytes()
    vault.rotate_key()
    new_key = key_file.read_bytes()

    assert old_key != new_key
    assert (tmp_path / "vault.key.bak").exists()
    assert vault.retrieve(user_id) == {"x": 1}


def test_vault_key_rotation_custom_backup(tmp_path):
    key_file = tmp_path / "vault.key"
    db_path = tmp_path / "vault.db"
    backup_file = tmp_path / "backup" / "old.key"
    user_id = "henry"

    vault = DataVault(key_file=key_file, db_path=db_path)
    vault.set_consent(user_id, True)
    vault.store(user_id, {"v": 1})

    old_key = key_file.read_bytes()
    vault.rotate_key(backup_path=backup_file)
    assert backup_file.read_bytes() == old_key
    assert key_file.read_bytes() != old_key
    assert vault.retrieve(user_id) == {"v": 1}


def test_vault_key_rotation_restore(tmp_path):
    key_file = tmp_path / "vault.key"
    db_path = tmp_path / "vault.db"
    user_id = "isabella"
    payload = {"secret": "value"}

    vault = DataVault(key_file=key_file, db_path=db_path)
    vault.set_consent(user_id, True)
    vault.store(user_id, payload)

    db_backup = tmp_path / "backup" / "vault.db"
    db_backup.parent.mkdir()
    shutil.copy2(db_path, db_backup)

    vault.rotate_key()
    assert vault.retrieve(user_id) == payload

    backup_key = tmp_path / "vault.key.bak"
    restored = DataVault(key_file=backup_key, db_path=db_backup)
    assert restored.retrieve(user_id) == payload
