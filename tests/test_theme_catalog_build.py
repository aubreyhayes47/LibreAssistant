# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.
"""Tests for building the theme catalog from community themes."""

from __future__ import annotations

import json
from pathlib import Path

import importlib.util


def _load_builder():
    path = Path(__file__).resolve().parents[1] / "scripts" / "build_theme_catalog.py"
    spec = importlib.util.spec_from_file_location("build_theme_catalog", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module.build_catalog


def test_build_catalog_generates_sanitized_css(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    theme_dir = repo / "mytheme"
    theme_dir.mkdir()
    (theme_dir / "metadata.json").write_text(
        json.dumps({
            "id": "mytheme",
            "name": "My Theme",
            "author": "Tester",
            "preview": "#fff",
            "rating": 0,
        })
    )
    (theme_dir / "theme.css").write_text(".x{color:red;position:absolute;}")
    dest = tmp_path / "out"
    catalog = tmp_path / "catalog.json"
    build_catalog = _load_builder()
    build_catalog(repo, dest, catalog)
    css = (dest / "mytheme.css").read_text()
    assert "position" not in css
    data = json.loads(catalog.read_text())
    assert any(t["id"] == "mytheme" for t in data)
