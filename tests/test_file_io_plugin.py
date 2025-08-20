from __future__ import annotations

from pathlib import Path
from typing import Any

from libreassistant.plugins import file_io
from libreassistant.plugins.file_io import FileIOPlugin


def test_file_io_plugin_unit(tmp_path: Path) -> None:
    file_io.ALLOWED_BASE_DIR = str(tmp_path)
    plugin = FileIOPlugin()
    path = tmp_path / "example.txt"
    state: dict[str, Any] = {}
    result = plugin.run(state, {"operation": "create", "path": str(path), "content": "hello"})
    assert result == {"status": "created"}
    result = plugin.run(state, {"operation": "read", "path": str(path)})
    assert result == {"content": "hello"}
    result = plugin.run(state, {"operation": "update", "path": str(path), "content": "world"})
    assert "error" in result
    result = plugin.run(state, {"operation": "update", "path": str(path), "content": "world", "confirm": True})
    assert result == {"status": "updated"}
    result = plugin.run(state, {"operation": "delete", "path": str(path)})
    assert "error" in result
    result = plugin.run(state, {"operation": "delete", "path": str(path), "confirm": True})
    assert result == {"status": "deleted"}

    # attempt to access a file outside allowed directory
    outside = tmp_path.parent / "other.txt"
    result = plugin.run(state, {"operation": "create", "path": str(outside), "content": "oops"})
    assert result == {"error": "path outside allowed directory"}


def test_file_io_plugin_path_sanitization(tmp_path: Path) -> None:
    file_io.ALLOWED_BASE_DIR = str(tmp_path)
    plugin = FileIOPlugin()
    state: dict[str, Any] = {}

    # Path that includes traversal but stays within the allowed directory
    inside = tmp_path / "folder" / ".." / "sanitized.txt"
    result = plugin.run(state, {"operation": "create", "path": str(inside), "content": "hi"})
    assert result == {"status": "created"}
    assert state["last_file_path"] == str(tmp_path / "sanitized.txt")

    # Path that escapes the allowed directory is rejected and does not update state
    outside = tmp_path.parent / "other.txt"
    result = plugin.run(state, {"operation": "read", "path": str(outside)})
    assert result == {"error": "path outside allowed directory"}
    assert state["last_file_path"] == str(tmp_path / "sanitized.txt")


def test_file_io_plugin_integration(client, tmp_path: Path) -> None:
    file_io.ALLOWED_BASE_DIR = str(tmp_path)
    file_io.register()
    path = tmp_path / "note.txt"
    response = client.post(
        "/api/v1/invoke",
        json={
            "plugin": "file_io",
            "payload": {"operation": "create", "path": str(path), "content": "hello"},
            "user_id": "alice",
        },
    )
    assert response.status_code == 200
    assert response.json()["result"] == {"status": "created"}

    # disallowed path
    outside = tmp_path.parent / "note.txt"
    response = client.post(
        "/api/v1/invoke",
        json={
            "plugin": "file_io",
            "payload": {"operation": "create", "path": str(outside), "content": "bad"},
            "user_id": "alice",
        },
    )
    assert response.status_code == 200
    assert response.json()["result"] == {"error": "path outside allowed directory"}

    response = client.post(
        "/api/v1/invoke",
        json={
            "plugin": "file_io",
            "payload": {"operation": "read", "path": str(path)},
            "user_id": "alice",
        },
    )
    assert response.status_code == 200
    assert response.json()["result"] == {"content": "hello"}
