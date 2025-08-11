# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Simple provider abstraction and registry for AI backends."""

from __future__ import annotations

from typing import Dict, Protocol


class Provider(Protocol):
    """Protocol defining an AI provider."""

    def generate(self, prompt: str, api_key: str | None = None) -> str:
        """Generate a response for the given prompt."""


class ProviderManager:
    """Registry managing provider implementations and API keys."""

    def __init__(self) -> None:
        self._providers: Dict[str, Provider] = {}
        self._api_keys: Dict[str, str] = {}

    def register(self, name: str, provider: Provider) -> None:
        """Register a provider implementation."""
        self._providers[name] = provider

    def set_api_key(self, name: str, key: str) -> None:
        """Store the API key for a provider."""
        self._api_keys[name] = key

    def generate(self, name: str, prompt: str) -> str:
        """Generate a response using the named provider."""
        provider = self._providers.get(name)
        if provider is None:
            raise KeyError(name)
        key = self._api_keys.get(name)
        return provider.generate(prompt, key)

    def reset(self) -> None:
        """Reset the registry and stored API keys. Intended for tests."""
        self._providers.clear()
        self._api_keys.clear()


providers = ProviderManager()
