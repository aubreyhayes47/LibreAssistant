# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

import json
from pathlib import Path

from typing import Any

import pytest

from libreassistant.plugins import file_io, law_by_keystone
from libreassistant.plugins.law_by_keystone import LawByKeystonePlugin


class _DummyClient:
    def __init__(self, module, env=None, timeout=None):
        pass

    def request(self, method, params=None, timeout=None):
        return {"tools": []}

    def invoke(self, tool, params):
        fmt = params.get("output_format", "md")
        ext = fmt if fmt != "md" else "md"
        output = Path(params["output_path"]) / f"summary.{ext}"
        output.write_text(
            json.dumps(
                {
                    "query": params["query"],
                    "source": params.get("source"),
                    "format": fmt,
                }
            )
        )
        return {"status": "exported"}

    def close(self):
        pass


@pytest.fixture(autouse=True)
def _mock_mcp_client(monkeypatch):
    monkeypatch.setattr("libreassistant.mcp_adapter.MCPClient", _DummyClient)


@pytest.mark.parametrize(
    "source,fmt",
    [
        ("govinfo", "json"),
        ("ecfr", "txt"),
        ("openstates", "xml"),
    ],
)
def test_export_creates_file(tmp_path: Path, source: str, fmt: str) -> None:
    file_io.ALLOWED_BASE_DIR = str(tmp_path)
    plugin = LawByKeystonePlugin()
    payload = {
        "query": "test query",
        "source": source,
        "output_format": fmt,
        "output_path": str(tmp_path),
    }
    state: dict[str, Any] = {}
    result = plugin.run(state, payload)
    assert result["status"] == "exported"
    ext = fmt if fmt != "md" else "md"
    created = tmp_path / f"summary.{ext}"
    assert created.exists()

    if created.suffix == ".json":
        data = json.loads(created.read_text())
        assert data["query"] == "test query"
        assert data["source"] == source


def test_law_by_keystone_integration(client, tmp_path: Path) -> None:
    file_io.ALLOWED_BASE_DIR = str(tmp_path)
    law_by_keystone.register()
    payload = {
        "query": "integration test",
        "source": "govinfo",
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
        "source": "govinfo",
        "output_format": "json",
        "output_path": str(outside),
    }
    state: dict[str, Any] = {}
    result = plugin.run(state, payload)
    assert result == {"error": "path outside allowed directory"}
    assert not outside.exists()
