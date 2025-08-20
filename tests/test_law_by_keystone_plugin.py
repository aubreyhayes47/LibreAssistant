import json
import shutil
from pathlib import Path

from typing import Any

import pytest

from libreassistant.plugins import file_io, law_by_keystone
from libreassistant.plugins.law_by_keystone import LawByKeystonePlugin


if shutil.which("node") is None:
    class _DummyClient:
        def __init__(self, module, env=None, timeout=None):
            pass

        def request(self, method, params=None, timeout=None):
            return {"tools": []}

        def invoke(self, tool, params):
            output = Path(params["output_path"]) / "summary.json"
            output.write_text(json.dumps({"query": params["query"]}))
            return {"status": "exported"}

        def close(self):
            pass

    @pytest.fixture(autouse=True)
    def _mock_mcp_client(monkeypatch):
        monkeypatch.setattr("libreassistant.mcp_adapter.MCPClient", _DummyClient)


def test_export_creates_file(tmp_path: Path) -> None:
    file_io.ALLOWED_BASE_DIR = str(tmp_path)
    plugin = LawByKeystonePlugin()
    payload = {
        "query": "test query",
        "output_format": "json",
        "output_path": str(tmp_path),
    }
    state: dict[str, Any] = {}
    result = plugin.run(state, payload)
    assert result["status"] == "exported"
    created = tmp_path / "summary.json"
    assert created.exists()
    data = json.loads(created.read_text())
    assert data["query"] == "test query"


def test_law_by_keystone_integration(client, tmp_path: Path) -> None:
    file_io.ALLOWED_BASE_DIR = str(tmp_path)
    law_by_keystone.register()
    payload = {
        "query": "integration test",
        "output_format": "json",
        "output_path": str(tmp_path),
    }
    response = client.post(
        "/api/v1/invoke",
        json={
            "plugin": "law_by_keystone",
            "payload": payload,
            "user_id": "alice",
        },
    )
    assert response.status_code == 200
    assert response.json()["result"]["status"] == "exported"
    created = tmp_path / "summary.json"
    assert created.exists()


def test_rejects_outside_directory(tmp_path: Path) -> None:
    file_io.ALLOWED_BASE_DIR = str(tmp_path)
    plugin = LawByKeystonePlugin()
    outside = tmp_path.parent / "outside" / "dir"
    payload = {
        "query": "test",
        "output_format": "json",
        "output_path": str(outside),
    }
    state: dict[str, Any] = {}
    result = plugin.run(state, payload)
    assert result == {"error": "path outside allowed directory"}
    assert not outside.exists()
