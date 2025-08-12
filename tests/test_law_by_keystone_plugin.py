import json
from pathlib import Path

from libreassistant.plugins import file_io, law_by_keystone
from libreassistant.plugins.law_by_keystone import LawByKeystonePlugin


def test_export_creates_file(tmp_path: Path) -> None:
    file_io.ALLOWED_BASE_DIR = str(tmp_path)
    plugin = LawByKeystonePlugin()
    payload = {
        "query": "test query",
        "output_format": "json",
        "output_path": str(tmp_path),
    }
    state = {}
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
        json={"plugin": "law_by_keystone", "payload": payload, "user_id": "alice"},
    )
    assert response.status_code == 200
    assert response.json()["result"]["status"] == "exported"
    created = tmp_path / "summary.json"
    assert created.exists()
