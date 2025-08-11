# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Placeholder implementation of a cloud AI provider."""

from __future__ import annotations


class CloudProvider:
    """Cloud-based provider that requires an API key."""

    def generate(self, prompt: str, api_key: str | None = None) -> str:
        if not api_key:
            raise ValueError("API key required")
        return f"cloud:{prompt}"
