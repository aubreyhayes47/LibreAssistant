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


def test_error_tracking(client):
    app = client.app

    @app.get("/fail")
    def fail():  # pragma: no cover - simple stub
        from fastapi import Response

        return Response(status_code=500)

    before = client.get("/api/v1/health").json()["error_count"]
    resp = client.get("/fail")
    assert resp.status_code == 500
    after = client.get("/api/v1/health").json()["error_count"]
    assert after == before + 1
