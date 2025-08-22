# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

import importlib
import os
import sys
import sqlite3

import pytest

from libreassistant import db as app_db


def test_falls_back_to_plain_sqlite_without_key(tmp_path, monkeypatch):
    """When ``LIBRE_DB_KEY`` is unset a plain SQLite connection is returned."""
    db_file = tmp_path / "plain.db"
    monkeypatch.setenv("LIBRE_DB_PATH", str(db_file))
    monkeypatch.delenv("LIBRE_DB_KEY", raising=False)
    importlib.reload(app_db)

    try:
        conn = app_db.get_conn()
        assert not app_db.SQLCIPHER_AVAILABLE
        assert isinstance(conn, sqlite3.Connection)
        app_db.add_history("bob", "test", {"data": "value"}, True)
        app_db.get_history("bob")
        data = db_file.read_bytes()
        assert b"bob" in data
        assert b"value" in data
    finally:
        app_db.close_conn()
        importlib.reload(app_db)


def test_plain_sqlite_fallback(tmp_path):
    """When SQLCipher is missing, the module falls back to plain SQLite."""
    db_file = tmp_path / "plain.db"
    orig_db_path = os.environ.get("LIBRE_DB_PATH")
    orig_db_key = os.environ.get("LIBRE_DB_KEY")

    os.environ["LIBRE_DB_PATH"] = str(db_file)
    os.environ["LIBRE_DB_KEY"] = "unused-key"

    orig_mod = sys.modules.pop("pysqlcipher3", None)
    orig_mod_dbapi = sys.modules.pop("pysqlcipher3.dbapi2", None)
    importlib.reload(app_db)

    try:
        if app_db.SQLCIPHER_AVAILABLE:
            pytest.skip("SQLCipher available")
        app_db.add_history("bob", "test", {"data": "value"}, True)
        app_db.get_history("bob")
        data = db_file.read_bytes()
        assert b"bob" in data
        assert b"value" in data
    finally:
        app_db.close_conn()
        if orig_mod is not None:
            sys.modules["pysqlcipher3"] = orig_mod
        if orig_mod_dbapi is not None:
            sys.modules["pysqlcipher3.dbapi2"] = orig_mod_dbapi
        if orig_db_path is not None:
            os.environ["LIBRE_DB_PATH"] = orig_db_path
        else:
            os.environ.pop("LIBRE_DB_PATH", None)
        if orig_db_key is not None:
            os.environ["LIBRE_DB_KEY"] = orig_db_key
        else:
            os.environ.pop("LIBRE_DB_KEY", None)
        importlib.reload(app_db)
