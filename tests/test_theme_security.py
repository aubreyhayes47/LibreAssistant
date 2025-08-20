# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for secure theme loading architecture."""

from __future__ import annotations

import pytest
import libreassistant.themes as themes


def test_sanitize_css_removes_disallowed_properties():
    css = ".a{color:red;position:absolute;}"
    cleaned, modified = themes.sanitize_css(css)
    assert "position" not in cleaned
    assert "color:red" in cleaned
    assert modified


def test_sanitize_css_removes_imports():
    css = '@import "evil.css"; .a{color:red;}'
    cleaned, modified = themes.sanitize_css(css)
    assert "@import" not in cleaned
    assert "color:red" in cleaned
    assert modified


def test_sanitize_css_removes_urls():
    css = ".a{background:url(http://evil.com);color:red;}"
    cleaned, modified = themes.sanitize_css(css)
    assert "background" not in cleaned
    assert "color:red" in cleaned
    assert modified


def test_theme_endpoint_sanitizes(tmp_path, client, monkeypatch):
    bad = tmp_path / "bad.css"
    bad.write_text(".x{color:blue;position:absolute;}")
    monkeypatch.setattr(themes, "THEME_DIR", tmp_path)
    res = client.get("/api/v1/themes/bad.css")
    assert res.status_code == 200
    assert "position" not in res.text
    assert "color:blue" in res.text
    assert res.headers.get("x-theme-sanitized") == "true"


def test_theme_endpoint_removes_urls_and_reports(tmp_path, client, monkeypatch):
    bad = tmp_path / "bad.css"
    bad.write_text(".x{color:blue;background:url(http://evil.com);}")
    monkeypatch.setattr(themes, "THEME_DIR", tmp_path)
    res = client.get("/api/v1/themes/bad.css")
    assert res.status_code == 200
    assert "background" not in res.text
    assert res.headers.get("x-theme-sanitized") == "true"


def test_theme_endpoint_no_header_for_clean_css(tmp_path, client, monkeypatch):
    good = tmp_path / "good.css"
    good.write_text(".x{color:blue;}")
    monkeypatch.setattr(themes, "THEME_DIR", tmp_path)
    res = client.get("/api/v1/themes/good.css")
    assert res.status_code == 200
    assert "x-theme-sanitized" not in res.headers


def test_csp_header_present(client):
    res = client.get("/")
    csp = res.headers.get("content-security-policy")
    assert csp is not None
    assert "default-src 'self'" in csp


def test_get_theme_css_rejects_path_traversal(tmp_path, monkeypatch):
    good = tmp_path / "good.css"
    good.write_text(".a{color:blue;}")
    monkeypatch.setattr(themes, "THEME_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        themes.get_theme_css("../good")
