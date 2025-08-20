import importlib

from libreassistant import db as app_db


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
