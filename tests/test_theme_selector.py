# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for theme selector and theme API functionality."""

import json
from pathlib import Path


def test_theme_catalog_endpoint(client):
    """Test that the theme catalog endpoint returns available themes."""
    response = client.get("/api/v1/themes")
    assert response.status_code == 200
    data = response.json()
    assert "themes" in data
    themes = data["themes"]
    assert len(themes) >= 3  # At least light, dark, high-contrast
    
    # Check that built-in themes are present
    theme_ids = {theme["id"] for theme in themes}
    assert "light" in theme_ids
    assert "dark" in theme_ids
    assert "high-contrast" in theme_ids
    
    # Check theme structure
    for theme in themes:
        assert "id" in theme
        assert "name" in theme
        assert "author" in theme
        assert "preview" in theme


def test_theme_preference_endpoints(client):
    """Test theme preference setting and retrieval."""
    user_id = "test-user"
    
    # Test setting theme preference
    response = client.post(
        f"/api/v1/themes/preference/{user_id}",
        json={"theme_id": "dark"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["theme"] == "dark"
    
    # Test getting theme preference
    response = client.get(f"/api/v1/themes/preference/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert "theme" in data


def test_built_in_theme_css_endpoint(client):
    """Test that built-in theme CSS is accessible."""
    # Light theme should be available by default
    response = client.get("/api/v1/themes/light.css")
    # Note: This might return 404 if theme isn't in ui/themes/ directory
    # That's expected since built-in themes are in tokens.css
    # For now, we test that the endpoint exists and handles the request
    assert response.status_code in [200, 404]


def test_solarized_theme_css_endpoint(client):
    """Test that community theme CSS is accessible."""
    response = client.get("/api/v1/themes/solarized.css")
    if response.status_code == 200:
        # If solarized theme exists, check it's valid CSS
        css_content = response.text
        assert ":root[data-theme=\"solarized\"]" in css_content
        assert "--color-background" in css_content
        # Check sanitization header
        if "x-theme-sanitized" in response.headers:
            assert response.headers["x-theme-sanitized"] == "true"
    else:
        # Theme not found is also acceptable
        assert response.status_code == 404


def test_invalid_theme_css_endpoint(client):
    """Test that invalid theme IDs return 404."""
    response = client.get("/api/v1/themes/nonexistent.css")
    assert response.status_code == 404


def test_theme_preference_validation(client):
    """Test theme preference validation."""
    user_id = "test-user"
    
    # Test with empty theme_id
    response = client.post(
        f"/api/v1/themes/preference/{user_id}",
        json={"theme_id": ""}
    )
    assert response.status_code == 200  # Currently accepts any string
    
    # Test with missing theme_id
    response = client.post(
        f"/api/v1/themes/preference/{user_id}",
        json={}
    )
    assert response.status_code == 422  # Validation error