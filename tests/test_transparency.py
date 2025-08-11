# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for transparency dashboards."""

from __future__ import annotations


def test_bom_lists_dependencies(client):
    resp = client.get("/api/v1/bom")
    assert resp.status_code == 200
    data = resp.json()
    assert "dependencies" in data
    assert any(dep.startswith("fastapi") for dep in data["dependencies"])


def test_health_reports_metrics(client):
    first = client.get("/api/v1/health").json()["requests"]
    client.get("/")
    second = client.get("/api/v1/health").json()["requests"]
    assert second >= first + 2
