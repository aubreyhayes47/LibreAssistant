"""Lightweight SQLite database for history and audit logs."""

from __future__ import annotations

import json
import os
import pysqlcipher3.dbapi2 as sqlite3
from pathlib import Path
from typing import Any, Dict, List

DB_PATH = Path(os.getenv("LIBRE_DB_PATH", "config/app.db"))
DB_KEY = os.getenv("LIBRE_DB_KEY")
HISTORY_RETENTION_DAYS = int(os.getenv("HISTORY_RETENTION_DAYS", "30"))
AUDIT_RETENTION_DAYS = int(os.getenv("AUDIT_RETENTION_DAYS", "30"))

_conn: sqlite3.Connection | None = None


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        if not DB_KEY:
            raise RuntimeError("LIBRE_DB_KEY environment variable must be set for encrypted database access")
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.execute(f"PRAGMA key='{DB_KEY}'")
        _initialize(_conn)
    return _conn


def _initialize(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            plugin TEXT NOT NULL,
            payload TEXT NOT NULL,
            granted INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS file_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            action TEXT,
            path TEXT
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_user_time ON history(user_id, timestamp)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_user_time ON file_audit(user_id, timestamp)"
    )
    conn.commit()


def clear() -> None:
    """Remove all entries (used in tests)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM history")
    cur.execute("DELETE FROM file_audit")
    conn.commit()


def prune_history() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM history WHERE timestamp < datetime('now', ?)",
        (f'-{HISTORY_RETENTION_DAYS} days',),
    )
    conn.commit()


def prune_audit() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM file_audit WHERE timestamp < datetime('now', ?)",
        (f'-{AUDIT_RETENTION_DAYS} days',),
    )
    conn.commit()


def add_history(user_id: str, plugin: str, payload: Dict[str, Any], granted: bool | None) -> None:
    conn = get_conn()
    prune_history()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO history (user_id, plugin, payload, granted) VALUES (?, ?, ?, ?)",
        (
            user_id,
            plugin,
            json.dumps(payload),
            int(granted) if granted is not None else None,
        ),
    )
    conn.commit()


def get_history(user_id: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT plugin, payload, granted FROM history WHERE user_id=? ORDER BY timestamp",
        (user_id,),
    )
    rows = cur.fetchall()
    result: List[Dict[str, Any]] = []
    for plugin, payload, granted in rows:
        entry: Dict[str, Any] = {
            "plugin": plugin,
            "payload": json.loads(payload),
        }
        if granted is not None:
            entry["granted"] = bool(granted)
        result.append(entry)
    return result


def add_file_audit(user_id: str | None, action: str | None, path: str | None) -> None:
    conn = get_conn()
    prune_audit()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO file_audit (user_id, action, path) VALUES (?, ?, ?)",
        (user_id, action, path),
    )
    conn.commit()


def get_file_audit(user_id: str | None = None) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    if user_id is None:
        cur.execute(
            "SELECT user_id, action, path, timestamp FROM file_audit ORDER BY timestamp"
        )
    else:
        cur.execute(
            "SELECT user_id, action, path, timestamp FROM file_audit WHERE user_id=? ORDER BY timestamp",
            (user_id,),
        )
    rows = cur.fetchall()
    return [
        {"user_id": u, "action": a, "path": p, "timestamp": t} for u, a, p, t in rows
    ]
