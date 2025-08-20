# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for provider registry and API endpoints."""

from __future__ import annotations

from libreassistant.providers import providers


def test_local_provider(client) -> None:
    response = client.post(
        "/api/v1/generate",
        json={"provider": "local", "prompt": "hi"},
    )
    assert response.status_code == 200
    assert response.json() == {"result": "local:hi"}


def test_cloud_provider_requires_key(client) -> None:
    bad = client.post(
        "/api/v1/generate",
        json={"provider": "cloud", "prompt": "hi"},
    )
    assert bad.status_code == 400
    set_key = client.post("/api/v1/providers/cloud/key", json={"key": "abc"})
    assert set_key.status_code == 200
    token = providers._api_keys["cloud"]
    assert isinstance(token, bytes)
    assert token != b"abc"
    good = client.post(
        "/api/v1/generate",
        json={"provider": "cloud", "prompt": "hi"},
    )
    assert good.json() == {"result": "cloud:hi"}


def test_api_key_encrypted_storage() -> None:
    class CaptureProvider:
        def __init__(self) -> None:
            self.received: str | None = None

        def generate(self, prompt: str, api_key: str | None = None) -> str:
            self.received = api_key
            return "ok"

    provider = CaptureProvider()
    providers.register("capture", provider)
    providers.set_api_key("capture", "secret")

    token = providers._api_keys["capture"]
    assert isinstance(token, bytes)
    assert token != b"secret"
    assert providers._fernet.decrypt(token).decode() == "secret"

    providers.generate("capture", "hi")
    assert provider.received == "secret"
