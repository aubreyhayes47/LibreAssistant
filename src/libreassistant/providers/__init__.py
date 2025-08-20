# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Simple provider abstraction and registry for AI backends."""

from __future__ import annotations

from typing import Dict, Protocol

from cryptography.fernet import Fernet


class Provider(Protocol):
    """Protocol defining an AI provider."""

    def generate(self, prompt: str, api_key: str | None = None) -> str:
        """Generate a response for the given prompt."""


class ProviderManager:
    """Registry managing provider implementations and API keys."""

    def __init__(self) -> None:
        self._providers: Dict[str, Provider] = {}
        self._api_keys: Dict[str, bytes] = {}
        self._fernet = Fernet(Fernet.generate_key())

    def register(self, name: str, provider: Provider) -> None:
        """Register a provider implementation."""
        self._providers[name] = provider

    def set_api_key(self, name: str, key: str) -> None:
        """Store the API key for a provider encrypted with Fernet."""
        token = self._fernet.encrypt(key.encode())
        self._api_keys[name] = token

    def generate(self, name: str, prompt: str) -> str:
        """Generate a response using the named provider."""
        provider = self._providers.get(name)
        if provider is None:
            raise KeyError(name)
        token = self._api_keys.get(name)
        key = self._fernet.decrypt(token).decode() if token else None
        return provider.generate(prompt, key)

    def reset(self) -> None:
        """Reset the registry and stored API keys. Intended for tests."""
        self._providers.clear()
        self._api_keys.clear()


providers = ProviderManager()
