# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Adapters for cloud hosted LLM providers.

This module provides a thin wrapper around the `openai` Python client.  The
previous implementation returned a canned string and existed purely for test
purposes.  The real implementation interacts with OpenAI's Chat Completions
API and adds basic rate limiting and model configuration options.

The provider is intentionally lightweight – imports for third‑party
dependencies are performed lazily so that the package can be installed without
requiring the dependencies at runtime.  Tests patch the ``openai`` module to
avoid network access.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from collections.abc import Sequence
from threading import Lock
from time import monotonic
from types import SimpleNamespace


@dataclass
class CloudConfig:
    """Configuration for :class:`CloudProvider`.

    Attributes:
        model: OpenAI model name.
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature.
        rate_limit_per_minute: Number of requests allowed per minute.  A value
            of ``0`` disables rate limiting.
    """

    model: str = "gpt-3.5-turbo"
    max_tokens: int = 256
    temperature: float = 0.7
    rate_limit_per_minute: int = 60


class CloudProvider:
    """Cloud-based provider that requires an API key."""

    def __init__(self, config: CloudConfig | None = None) -> None:
        self.config = config or CloudConfig()
        self._client: SimpleNamespace | None = None
        self._request_times: deque[float] = deque()
        self._lock = Lock()

    # ------------------------------------------------------------------
    def _throttle(self) -> None:
        """Enforce a simple requests-per-minute rate limit."""
        limit = self.config.rate_limit_per_minute
        if limit <= 0:
            return
        with self._lock:
            now = monotonic()
            while self._request_times and now - self._request_times[0] > 60:
                self._request_times.popleft()
            if len(self._request_times) >= limit:
                raise RuntimeError("Rate limit exceeded")
            self._request_times.append(now)

    # ------------------------------------------------------------------
    def _get_client(self, api_key: str):
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:  # pragma: no cover - import error path
            raise RuntimeError("openai package is required for CloudProvider") from exc

        if self._client is None or getattr(self._client, "api_key", None) != api_key:
            self._client = OpenAI(api_key=api_key)
        return self._client

    # ------------------------------------------------------------------
    def generate(self, prompt: str, api_key: str | None = None) -> str:
        if not api_key:
            raise ValueError("API key required")

        self._throttle()
        client = self._get_client(api_key)

        try:
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
        except Exception as exc:  # pragma: no cover - network error path
            raise RuntimeError(str(exc)) from exc

        # Validate response structure before returning the content
        choices = getattr(response, "choices", None)
        if not isinstance(choices, Sequence) or not choices:
            raise RuntimeError("invalid response structure")

        message = getattr(choices[0], "message", None)
        if not isinstance(message, dict) or "content" not in message:
            raise RuntimeError("invalid response structure")

        return message["content"]
