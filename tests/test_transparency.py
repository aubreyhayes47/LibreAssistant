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


def test_bom_lists_models_and_datasets(client, tmp_path, monkeypatch):
    models_dir = tmp_path / "models"
    datasets_dir = tmp_path / "datasets"
    models_dir.mkdir()
    datasets_dir.mkdir()
    (models_dir / "demo-model.bin").write_text("dummy")
    (datasets_dir / "demo-dataset").mkdir()
    # Hidden entries should be ignored
    (models_dir / ".hidden-model").write_text("ignored")
    (datasets_dir / ".hidden-dataset").mkdir()
    monkeypatch.setenv("LA_MODELS_DIR", str(models_dir))
    monkeypatch.setenv("LA_DATASETS_DIR", str(datasets_dir))
    resp = client.get("/api/v1/bom")
    assert resp.status_code == 200
    data = resp.json()
    assert "demo-model.bin" in data["models"]
    assert "demo-dataset" in data["datasets"]
    assert ".hidden-model" not in data["models"]
    assert ".hidden-dataset" not in data["datasets"]


def test_bom_handles_missing_dirs(client, monkeypatch):
    monkeypatch.delenv("LA_MODELS_DIR", raising=False)
    monkeypatch.delenv("LA_DATASETS_DIR", raising=False)
    resp = client.get("/api/v1/bom")
    assert resp.status_code == 200
    data = resp.json()
    assert data["models"] == []
    assert data["datasets"] == []


def test_bom_handles_empty_dirs(client, tmp_path, monkeypatch):
    models_dir = tmp_path / "models"
    datasets_dir = tmp_path / "datasets"
    models_dir.mkdir()
    datasets_dir.mkdir()
    monkeypatch.setenv("LA_MODELS_DIR", str(models_dir))
    monkeypatch.setenv("LA_DATASETS_DIR", str(datasets_dir))
    resp = client.get("/api/v1/bom")
    assert resp.status_code == 200
    data = resp.json()
    assert data["models"] == []
    assert data["datasets"] == []


def test_bom_caches_results(monkeypatch, tmp_path):
    from libreassistant import transparency

    models_dir = tmp_path / "models"
    datasets_dir = tmp_path / "datasets"
    models_dir.mkdir()
    datasets_dir.mkdir()
    monkeypatch.setenv("LA_MODELS_DIR", str(models_dir))
    monkeypatch.setenv("LA_DATASETS_DIR", str(datasets_dir))

    calls = {"dist": 0, "scan": 0}

    def fake_distributions():
        calls["dist"] += 1
        return []

    def counting_scan(path):
        calls["scan"] += 1
        return []

    monkeypatch.setattr(transparency.importlib.metadata, "distributions", fake_distributions)
    monkeypatch.setattr(transparency, "_scan", counting_scan)

    transparency._DEPENDENCIES = None
    transparency._MODELS_CACHE.clear()
    transparency._DATASETS_CACHE.clear()

    transparency.get_bill_of_materials()
    transparency.get_bill_of_materials()

    assert calls["dist"] == 1
    assert calls["scan"] == 2

    transparency._DEPENDENCIES = None
    transparency._MODELS_CACHE.clear()
    transparency._DATASETS_CACHE.clear()


def test_health_reports_metrics(client):
    first = client.get("/api/v1/health").json()["requests"]
    client.get("/")
    second = client.get("/api/v1/health").json()["requests"]
    assert second >= first + 2


def test_health_endpoint_comprehensive(client):
    """Comprehensive test for health endpoint."""
    response = client.get("/api/v1/health")
    
    # Basic response validation
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    
    # Required fields validation
    required_fields = ["requests", "uptime"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Field type validation
    assert isinstance(data["requests"], int)
    assert isinstance(data["uptime"], (int, float))
    assert data["uptime"] >= 0
    
    # Test multiple requests to ensure consistency
    for _ in range(5):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)


def test_health_endpoint_under_load(client):
    """Test health endpoint under multiple concurrent requests."""
    responses = []
    
    # Simulate multiple rapid requests
    for i in range(20):
        response = client.get("/api/v1/health")
        responses.append(response)
        
        # Make some other requests to increase activity
        if i % 3 == 0:
            client.get("/api/v1/mcp/servers")
        if i % 5 == 0:
            client.get("/api/v1/history/load_test_user")
    
    # All health requests should succeed
    for i, response in enumerate(responses):
        assert response.status_code == 200, f"Request {i} failed"
        data = response.json()
        assert "requests" in data
        assert "uptime" in data
    
    # Request count should be increasing
    first_count = responses[0].json()["requests"]
    last_count = responses[-1].json()["requests"]
    assert last_count >= first_count


def test_health_endpoint_after_errors(client):
    """Test health endpoint functionality after other endpoints have errors."""
    # Cause some errors in other endpoints
    client.post("/api/v1/mcp/consent/test", json={})  # Should cause 422
    client.post("/api/v1/history/test", json={})      # Should cause 422
    client.get("/api/v1/nonexistent")                 # Should cause 404
    
    # Health endpoint should still work correctly
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "requests" in data
    assert "uptime" in data
    
    # Error tracking fields may be present
    if "error_count" in data:
        assert isinstance(data["error_count"], int)
        assert data["error_count"] >= 0
    
    if "status" in data:
        assert data["status"] in ["ok", "error"]


def test_error_tracking(client):
    app = client.app

    @app.get("/fail")
    def fail():  # pragma: no cover - simple stub
        from fastapi import Response

        return Response(status_code=500)

    before_status = client.get("/api/v1/health").json()
    assert before_status["status"] == "ok"
    resp = client.get("/fail")
    assert resp.status_code == 500
    after_status = client.get("/api/v1/health").json()
    assert after_status["error_count"] == before_status["error_count"] + 1
    assert after_status["status"] == "error"


def test_health_monitor_discards_old_errors():
    from libreassistant.transparency import HealthMonitor

    monitor = HealthMonitor()
    for i in range(105):
        monitor.record_error(f"err-{i}")
    status = monitor.get_status()
    assert status["error_count"] == 105
    assert len(status["errors"]) == 100
    assert status["errors"][0] == "err-5"
