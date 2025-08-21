# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for provider registry and API endpoints."""

from __future__ import annotations

import threading
import sys
from types import SimpleNamespace

import pytest

from libreassistant.providers import providers
from libreassistant.providers.cloud import CloudConfig, CloudProvider
from libreassistant.providers.local import LocalConfig, LocalProvider


def test_local_provider(client, monkeypatch) -> None:
    monkeypatch.setattr(
        LocalProvider,
        "generate",
        lambda self, prompt, api_key=None: f"local:{prompt}",
    )
    response = client.post(
        "/api/v1/generate",
        json={"provider": "local", "prompt": "hi"},
    )
    assert response.status_code == 200
    assert response.json() == {"result": "local:hi"}


def test_cloud_provider_requires_key(client, monkeypatch) -> None:
    monkeypatch.setattr(
        CloudProvider,
        "generate",
        lambda self, prompt, api_key=None: (
            (_ for _ in ()).throw(ValueError("API key required"))
            if api_key is None
            else f"cloud:{prompt}"
        ),
    )
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


# ---------------------------------------------------------------------------
# Provider adapter tests with mocked API responses


def _mock_openai(
    monkeypatch,
    result: str | None = None,
    error: Exception | None = None,
    choices: list | None = None,
):
    """Patch the ``openai`` module with a minimal stub."""

    class _Chat:
        def __init__(self):
            self.completions = SimpleNamespace(
                create=lambda **_: (_ for _ in ()).throw(error)
                if error
                else SimpleNamespace(
                    choices=choices
                    if choices is not None
                    else [SimpleNamespace(message={"content": result or ""})]
                )
            )

    class _Client:
        def __init__(self, api_key=None):
            self.api_key = api_key
            self.chat = _Chat()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=_Client))


def test_cloud_provider_success(monkeypatch):
    _mock_openai(monkeypatch, result="ok")
    provider = CloudProvider(CloudConfig())
    assert provider.generate("hi", api_key="key") == "ok"


def test_cloud_provider_error(monkeypatch):
    _mock_openai(monkeypatch, error=Exception("boom"))
    provider = CloudProvider(CloudConfig())
    with pytest.raises(RuntimeError):
        provider.generate("hi", api_key="key")


def test_cloud_provider_rate_limit(monkeypatch):
    _mock_openai(monkeypatch, result="ok")
    provider = CloudProvider(CloudConfig(rate_limit_per_minute=1))
    provider.generate("hi", api_key="key")
    with pytest.raises(RuntimeError):
        provider.generate("hi", api_key="key")


def test_cloud_provider_empty_choices(monkeypatch):
    _mock_openai(monkeypatch, choices=[])
    provider = CloudProvider(CloudConfig())
    with pytest.raises(RuntimeError):
        provider.generate("hi", api_key="key")


def _mock_http(monkeypatch, response: dict | None = None, error: Exception | None = None):
    class Resp:
        def __init__(self, data, exc):
            self._data = data
            self._exc = exc

        def raise_for_status(self):
            if self._exc:
                raise self._exc

        def json(self):
            return self._data

    def fake_post(*args, **kwargs):
        if error:
            raise error
        return Resp(response or {"response": ""}, None)

    monkeypatch.setitem(sys.modules, "httpx", SimpleNamespace(post=fake_post))


def test_local_provider_success(monkeypatch):
    _mock_http(monkeypatch, {"response": "ok"})
    provider = LocalProvider(LocalConfig())
    assert provider.generate("hi") == "ok"


def test_local_provider_error(monkeypatch):
    _mock_http(monkeypatch, error=RuntimeError("bad"))
    provider = LocalProvider(LocalConfig())
    with pytest.raises(RuntimeError):
        provider.generate("hi")


def test_local_provider_rate_limit(monkeypatch):
    _mock_http(monkeypatch, {"response": "ok"})
    provider = LocalProvider(LocalConfig(rate_limit_per_minute=1))
    provider.generate("hi")
    with pytest.raises(RuntimeError):
        provider.generate("hi")


def _concurrent_throttle(provider, threads: int) -> list[str]:
    """Run ``provider._throttle`` concurrently in multiple threads."""

    barrier = threading.Barrier(threads)
    results: list[str] = [""] * threads

    def worker(idx: int) -> None:
        barrier.wait()
        try:
            provider._throttle()
            results[idx] = "ok"
        except Exception as exc:  # pragma: no cover - unexpected
            results[idx] = str(exc)

    tlist = [threading.Thread(target=worker, args=(i,)) for i in range(threads)]
    for t in tlist:
        t.start()
    for t in tlist:
        t.join()
    return results


def test_cloud_provider_concurrent_throttle() -> None:
    provider = CloudProvider(CloudConfig(rate_limit_per_minute=1))
    results = _concurrent_throttle(provider, 5)
    assert results.count("ok") == 1
    assert results.count("Rate limit exceeded") == 4
    assert len(provider._request_times) == 1


def test_local_provider_concurrent_throttle() -> None:
    provider = LocalProvider(LocalConfig(rate_limit_per_minute=1))
    results = _concurrent_throttle(provider, 5)
    assert results.count("ok") == 1
    assert results.count("Rate limit exceeded") == 4
    assert len(provider._request_times) == 1
