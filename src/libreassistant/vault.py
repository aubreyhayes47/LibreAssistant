"""Encrypted in-memory data vault for user data."""
from __future__ import annotations

import json
from typing import Any, Dict

from cryptography.fernet import Fernet


class DataVault:
    """Store user data encrypted with a symmetric key."""

    def __init__(self, key: bytes | None = None) -> None:
        self._fernet = Fernet(key or Fernet.generate_key())
        self._data: Dict[str, bytes] = {}
        self._consent: Dict[str, bool] = {}

    def store(self, user_id: str, data: Dict[str, Any]) -> None:
        payload = json.dumps(data).encode()
        token = self._fernet.encrypt(payload)
        self._data[user_id] = token

    def retrieve(self, user_id: str) -> Dict[str, Any]:
        token = self._data.get(user_id)
        if not token:
            return {}
        payload = self._fernet.decrypt(token)
        return json.loads(payload.decode())

    def delete(self, user_id: str) -> None:
        self._data.pop(user_id, None)
        self._consent.pop(user_id, None)

    def export(self, user_id: str) -> Dict[str, Any]:
        return self.retrieve(user_id)

    def set_consent(self, user_id: str, consent: bool) -> None:
        self._consent[user_id] = consent

    def get_consent(self, user_id: str) -> bool:
        return self._consent.get(user_id, False)
