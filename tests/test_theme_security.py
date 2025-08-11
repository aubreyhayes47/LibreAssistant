# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for secure theme loading architecture."""

from __future__ import annotations

import libreassistant.themes as themes


def test_sanitize_css_removes_disallowed_properties():
    css = ".a{color:red;position:absolute;}"
    cleaned = themes.sanitize_css(css)
    assert "position" not in cleaned
    assert "color:red" in cleaned


def test_theme_endpoint_sanitizes(tmp_path, client, monkeypatch):
    bad = tmp_path / "bad.css"
    bad.write_text(".x{color:blue;position:absolute;}")
    monkeypatch.setattr(themes, "THEME_DIR", tmp_path)
    res = client.get("/api/v1/themes/bad.css")
    assert res.status_code == 200
    assert "position" not in res.text
    assert "color:blue" in res.text


def test_csp_header_present(client):
    res = client.get("/")
    csp = res.headers.get("content-security-policy")
    assert csp is not None
    assert "default-src 'self'" in csp
