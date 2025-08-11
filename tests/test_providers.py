# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for provider registry and API endpoints."""

from __future__ import annotations


def test_local_provider(client) -> None:
    response = client.post("/api/v1/generate", json={"provider": "local", "prompt": "hi"})
    assert response.status_code == 200
    assert response.json() == {"result": "local:hi"}


def test_cloud_provider_requires_key(client) -> None:
    bad = client.post("/api/v1/generate", json={"provider": "cloud", "prompt": "hi"})
    assert bad.status_code == 400
    set_key = client.post("/api/v1/providers/cloud/key", json={"key": "abc"})
    assert set_key.status_code == 200
    good = client.post("/api/v1/generate", json={"provider": "cloud", "prompt": "hi"})
    assert good.json() == {"result": "cloud:hi"}
