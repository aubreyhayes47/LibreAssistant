# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Placeholder implementation of a local AI provider."""

from __future__ import annotations


class LocalProvider:
    """Local provider that does not require an API key."""

    def generate(self, prompt: str, api_key: str | None = None) -> str:
        return f"local:{prompt}"
