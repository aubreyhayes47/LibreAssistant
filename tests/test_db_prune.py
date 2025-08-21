# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for database pruning functions."""

from __future__ import annotations

from libreassistant import db


def test_prune_history_removes_old_entries() -> None:
    conn = db.get_conn()
    cur = conn.cursor()
    # Insert a history entry older than the retention window and a recent one
    cur.execute(
        "INSERT INTO history (user_id, plugin, payload, granted, timestamp) "
        "VALUES (?, ?, ?, ?, datetime('now', '-40 days'))",
        ("alice", "plugin", "{}", 1),
    )
    cur.execute(
        "INSERT INTO history (user_id, plugin, payload, granted) VALUES (?, ?, ?, ?)",
        ("alice", "plugin", "{}", 1),
    )
    conn.commit()
    # Ensure both entries are present before pruning
    cur.execute("SELECT COUNT(*) FROM history")
    assert cur.fetchone()[0] == 2
    db.prune_history()
    # Only the recent entry should remain
    cur.execute("SELECT COUNT(*) FROM history")
    assert cur.fetchone()[0] == 1


def test_prune_audit_removes_old_entries() -> None:
    conn = db.get_conn()
    cur = conn.cursor()
    # Insert an audit entry older than the retention window and a recent one
    cur.execute(
        "INSERT INTO file_audit (user_id, action, path, timestamp) "
        "VALUES (?, ?, ?, datetime('now', '-40 days'))",
        ("alice", "read", "/old"),
    )
    cur.execute(
        "INSERT INTO file_audit (user_id, action, path) VALUES (?, ?, ?)",
        ("alice", "read", "/new"),
    )
    conn.commit()
    # Ensure both entries are present before pruning
    cur.execute("SELECT COUNT(*) FROM file_audit")
    assert cur.fetchone()[0] == 2
    db.prune_audit()
    # Only the recent entry should remain
    cur.execute("SELECT COUNT(*) FROM file_audit")
    assert cur.fetchone()[0] == 1
