# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

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
    """Return a shared connection to the encrypted database.

    Initializes the database on first use, creating the directory and tables
    as needed. The connection is cached globally so subsequent calls reuse the
    same handle.

    Returns:
        sqlite3.Connection: Active connection to the SQLite database.

    Side Effects:
        Creates the database file and schema if they do not already exist and
        sets the global connection.
    """
    global _conn
    if _conn is None:
        if not DB_KEY:
            raise RuntimeError("LIBRE_DB_KEY environment variable must be set for encrypted database access")
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        try:
            _conn.execute("PRAGMA key=?", (DB_KEY,))
        except sqlite3.OperationalError:
            quoted_key = _conn.execute("SELECT quote(?)", (DB_KEY,)).fetchone()[0]
            _conn.execute(f"PRAGMA key={quoted_key}")
        _initialize(_conn)
    return _conn


def close_conn() -> None:
    """Close the global database connection if it exists."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def _initialize(conn: sqlite3.Connection) -> None:
    """Create required tables and indexes in the database.

    Parameters:
        conn: Connection on which schema creation statements are executed.

    Returns:
        None.

    Side Effects:
        Executes SQL statements that create tables and indexes if they do not
        exist and commits the transaction.
    """
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
    """Remove stale entries from the history table.

    Deletes rows older than the retention period defined by
    ``HISTORY_RETENTION_DAYS`` and commits the change.

    Returns:
        None.

    Side Effects:
        Modifies the ``history`` table by removing expired records.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM history WHERE timestamp < datetime('now', ?)",
        (f'-{HISTORY_RETENTION_DAYS} days',),
    )
    conn.commit()


def prune_audit() -> None:
    """Remove stale entries from the file audit table.

    Deletes rows older than the retention period defined by
    ``AUDIT_RETENTION_DAYS`` and commits the change.

    Returns:
        None.

    Side Effects:
        Modifies the ``file_audit`` table by removing expired records.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM file_audit WHERE timestamp < datetime('now', ?)",
        (f'-{AUDIT_RETENTION_DAYS} days',),
    )
    conn.commit()


def add_history(user_id: str, plugin: str, payload: Dict[str, Any], granted: bool | None) -> None:
    """Record a plugin invocation for a user.

    Parameters:
        user_id: Identifier of the user initiating the action.
        plugin: Name of the plugin invoked.
        payload: Data passed to the plugin; stored as JSON.
        granted: Whether consent was granted; ``None`` if unspecified.

    Returns:
        None.

    Side Effects:
        Prunes outdated history entries and commits the new record to the
        database.
    """
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
    """Retrieve all history entries for a user.

    Parameters:
        user_id: Identifier of the user whose history is requested.

    Returns:
        A list of dictionaries containing the plugin name, payload, and
        optional consent flag.

    Side Effects:
        None beyond reading from the database.
    """
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
    """Record a file system action in the audit log.

    Parameters:
        user_id: Identifier of the user performing the action, if known.
        action: The type of file operation performed.
        path: The file path involved in the operation.

    Returns:
        None.

    Side Effects:
        Prunes outdated audit entries and commits the new record to the
        database.
    """
    conn = get_conn()
    prune_audit()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO file_audit (user_id, action, path) VALUES (?, ?, ?)",
        (user_id, action, path),
    )
    conn.commit()


def get_file_audit(user_id: str | None = None) -> List[Dict[str, Any]]:
    """Retrieve file audit records, optionally filtering by user.

    Parameters:
        user_id: If provided, only records for this user are returned.

    Returns:
        A list of dictionaries with ``user_id``, ``action``, ``path``, and
        ``timestamp`` keys.

    Side Effects:
        None beyond reading from the database.
    """
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
