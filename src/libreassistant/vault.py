# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Encrypted in-memory data vault for user data."""
from __future__ import annotations

import json
from threading import Lock
from typing import Any, Dict

from cryptography.fernet import Fernet


class DataVault:
    """Store user data encrypted with a symmetric key.

    This class is thread-safe; access to internal state is serialized using a
    :class:`threading.Lock`.
    """

    def __init__(self, key: bytes | None = None) -> None:
        self._fernet = Fernet(key or Fernet.generate_key())
        self._data: Dict[str, bytes] = {}
        self._consent: Dict[str, bool] = {}
        self._lock = Lock()

    def _require_consent(self, user_id: str) -> None:
        """Raise ``PermissionError`` if the user has not granted consent.

        The caller must hold ``self._lock`` to ensure a consistent view of the
        consent registry.
        """
        if not self._consent.get(user_id, False):
            raise PermissionError("Consent required")

    def store(self, user_id: str, data: Dict[str, Any]) -> None:
        payload = json.dumps(data).encode()
        token = self._fernet.encrypt(payload)
        with self._lock:
            self._require_consent(user_id)
            self._data[user_id] = token

    def retrieve(self, user_id: str) -> Dict[str, Any]:
        with self._lock:
            self._require_consent(user_id)
            token = self._data.get(user_id)
        if not token:
            return {}
        payload = self._fernet.decrypt(token)
        return json.loads(payload.decode())

    def delete(self, user_id: str) -> None:
        with self._lock:
            self._require_consent(user_id)
            self._data.pop(user_id, None)
            self._consent.pop(user_id, None)

    def export(self, user_id: str) -> Dict[str, Any]:
        return self.retrieve(user_id)

    def set_consent(self, user_id: str, consent: bool) -> None:
        with self._lock:
            self._consent[user_id] = consent

    def get_consent(self, user_id: str) -> bool:
        with self._lock:
            return self._consent.get(user_id, False)
