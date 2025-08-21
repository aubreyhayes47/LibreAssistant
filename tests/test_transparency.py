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
