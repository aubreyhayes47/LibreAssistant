# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

import importlib

from libreassistant import db as app_db


def test_database_key_with_quotes(tmp_path, monkeypatch):
    db_file = tmp_path / "enc.db"
    key = "quo'te\"key"  # includes single and double quotes
    monkeypatch.setenv("LIBRE_DB_PATH", str(db_file))
    monkeypatch.setenv("LIBRE_DB_KEY", key)
    importlib.reload(app_db)

    app_db.add_history("bob", "test", {"data": "value"}, True)
    history = app_db.get_history("bob")
    assert history[0]["plugin"] == "test"
