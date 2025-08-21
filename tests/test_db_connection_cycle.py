# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for repeatedly opening and closing the database connection."""

from libreassistant import db


def test_get_close_reopen_cycles() -> None:
    conn1 = db.get_conn()
    db.close_conn()
    conn2 = db.get_conn()
    assert conn2 is not conn1
    db.close_conn()
    conn3 = db.get_conn()
    assert conn3 is not conn2
    db.close_conn()
