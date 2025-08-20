# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Encrypted data vault for user data with persistent storage."""

from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable

from cryptography.fernet import Fernet


class DataVault:
    """Store user data encrypted with a symmetric key.

    Data and consent flags may be stored in an on-disk SQLite database. The
    encryption key is persisted to a file so that data survives process
    restarts. The class is thread-safe; access to internal state is serialized
    using a :class:`threading.Lock`.
    """

    def __init__(
        self,
        *,
        key_file: str | Path | None = None,
        db_path: str | Path | None = None,
        key: bytes | None = None,
    ) -> None:
        self._lock = Lock()
        self._conn: sqlite3.Connection | None = None

        # Key management -------------------------------------------------
        self._key_file = Path(key_file) if key_file else None
        if key is not None:
            self._fernet = Fernet(key)
        elif self._key_file and self._key_file.exists():
            self._fernet = Fernet(self._key_file.read_bytes())
        else:
            new_key = Fernet.generate_key()
            self._fernet = Fernet(new_key)
            if self._key_file:
                self._key_file.parent.mkdir(parents=True, exist_ok=True)
                self._key_file.write_bytes(new_key)

        # Storage --------------------------------------------------------
        self._db_path = Path(db_path) if db_path else None
        if self._db_path:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            cur = self._conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS data (user_id TEXT PRIMARY KEY, token BLOB)"
            )
            cur.execute(
                "CREATE TABLE IF NOT EXISTS consent (user_id TEXT PRIMARY KEY, consent INTEGER NOT NULL)"
            )
            self._conn.commit()
        else:
            self._data: Dict[str, bytes] = {}
            self._consent: Dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Consent helpers
    def _get_consent(self, user_id: str) -> bool:
        if self._conn:
            cur = self._conn.cursor()
            cur.execute("SELECT consent FROM consent WHERE user_id=?", (user_id,))
            row = cur.fetchone()
            return bool(row[0]) if row else False
        return self._consent.get(user_id, False)

    def _set_consent(self, user_id: str, consent: bool) -> None:
        if self._conn:
            cur = self._conn.cursor()
            cur.execute(
                "REPLACE INTO consent (user_id, consent) VALUES (?, ?)",
                (user_id, int(consent)),
            )
            self._conn.commit()
        else:
            self._consent[user_id] = consent

    def _require_consent(self, user_id: str) -> None:
        """Raise ``PermissionError`` if the user has not granted consent."""
        if not self._get_consent(user_id):
            raise PermissionError("Consent required")

    # ------------------------------------------------------------------
    # Public API
    def store(self, user_id: str, data: Dict[str, Any]) -> None:
        try:
            payload = json.dumps(data).encode()
        except (TypeError, ValueError) as exc:
            raise ValueError("Vault data must be JSON-serializable") from exc
        token = self._fernet.encrypt(payload)
        with self._lock:
            self._require_consent(user_id)
            if self._conn:
                cur = self._conn.cursor()
                cur.execute(
                    "REPLACE INTO data (user_id, token) VALUES (?, ?)",
                    (user_id, token),
                )
                self._conn.commit()
            else:
                self._data[user_id] = token

    def retrieve(self, user_id: str) -> Dict[str, Any]:
        with self._lock:
            self._require_consent(user_id)
            if self._conn:
                cur = self._conn.cursor()
                cur.execute("SELECT token FROM data WHERE user_id=?", (user_id,))
                row = cur.fetchone()
                token = row[0] if row else None
            else:
                token = self._data.get(user_id)
        if not token:
            return {}
        payload = self._fernet.decrypt(token)
        return json.loads(payload.decode())

    def delete(self, user_id: str) -> None:
        with self._lock:
            self._require_consent(user_id)
            if self._conn:
                cur = self._conn.cursor()
                cur.execute("DELETE FROM data WHERE user_id=?", (user_id,))
                cur.execute("DELETE FROM consent WHERE user_id=?", (user_id,))
                self._conn.commit()
            else:
                self._data.pop(user_id, None)
                self._consent.pop(user_id, None)

    def export(self, user_id: str) -> Dict[str, Any]:
        return self.retrieve(user_id)

    def set_consent(self, user_id: str, consent: bool) -> None:
        with self._lock:
            self._set_consent(user_id, consent)

    def get_consent(self, user_id: str) -> bool:
        with self._lock:
            return self._get_consent(user_id)

    # ------------------------------------------------------------------
    # Key rotation
    def rotate_key(
        self,
        *,
        new_key: bytes | None = None,
        backup_path: str | Path | None = None,
    ) -> None:
        """Rotate the encryption key and re-encrypt stored entries.

        If ``backup_path`` is provided (or a key file is configured), the
        previous key is written there before replacement. Existing entries are
        decrypted with the old key and re-encrypted with the new key.
        """

        with self._lock:
            old_fernet = self._fernet
            new_key = new_key or Fernet.generate_key()
            self._fernet = Fernet(new_key)

            if self._key_file:
                dest = Path(backup_path) if backup_path else self._key_file.with_suffix(
                    self._key_file.suffix + ".bak"
                )
                if self._key_file.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(self._key_file, dest)
                self._key_file.write_bytes(new_key)

            # Re-encrypt existing entries
            if self._conn:
                cur = self._conn.cursor()
                cur.execute("SELECT user_id, token FROM data")
                rows: Iterable[tuple[str, bytes]] = cur.fetchall()
                for user_id, token in rows:
                    payload = old_fernet.decrypt(token)
                    new_token = self._fernet.encrypt(payload)
                    cur.execute(
                        "REPLACE INTO data (user_id, token) VALUES (?, ?)",
                        (user_id, new_token),
                    )
                self._conn.commit()
            else:
                for user_id, token in list(self._data.items()):
                    payload = old_fernet.decrypt(token)
                    self._data[user_id] = self._fernet.encrypt(payload)

