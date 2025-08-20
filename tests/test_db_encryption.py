# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

import importlib
import importlib.util

import pytest

from libreassistant import db as app_db


try:
    import pysqlcipher3.dbapi2 as _sqlcipher  # type: ignore
    # The conftest stub proxies to the standard ``sqlite3`` module whose
    # ``__name__`` is simply ``"sqlite3"``. Real pysqlcipher3 exposes its full
    # module name, so we can detect the stub this way.
    _HAS_PYSQLCIPHER = _sqlcipher.__name__ != "sqlite3"
except Exception:  # pragma: no cover - module missing or misconfigured
    _HAS_PYSQLCIPHER = False


@pytest.mark.skipif(not _HAS_PYSQLCIPHER, reason="pysqlcipher3 not installed")
def test_database_file_is_encrypted(tmp_path, monkeypatch):
    db_file = tmp_path / "enc.db"
    monkeypatch.setenv("LIBRE_DB_PATH", str(db_file))
    monkeypatch.setenv("LIBRE_DB_KEY", "secret-key")
    importlib.reload(app_db)

    app_db.add_history("bob", "test", {"data": "value"}, True)
    app_db.get_history("bob")

    data = db_file.read_bytes()
    assert b"bob" not in data
    assert b"value" not in data
