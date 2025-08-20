# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Adapter for local LLM deployments.

The placeholder implementation simply echoed the prompt.  The new
implementation communicates with a locally hosted model over HTTP.  It follows
the same interface as :class:`CloudProvider` and supports basic rate limiting
and model configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from time import monotonic


@dataclass
class LocalConfig:
    """Configuration for :class:`LocalProvider`.

    Attributes:
        url: Endpoint of the local model API.
        model: Model identifier used by the API server.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        rate_limit_per_minute: Number of requests allowed per minute.  ``0``
            disables rate limiting.
    """

    url: str = "http://localhost:11434/api/generate"
    model: str = "llama2"
    max_tokens: int = 256
    temperature: float = 0.7
    rate_limit_per_minute: int = 60


class LocalProvider:
    """Provider for local HTTP-based LLMs (e.g. Ollama)."""

    def __init__(self, config: LocalConfig | None = None) -> None:
        self.config = config or LocalConfig()
        self._request_times: deque[float] = deque()

    # ------------------------------------------------------------------
    def _throttle(self) -> None:
        limit = self.config.rate_limit_per_minute
        if limit <= 0:
            return
        now = monotonic()
        while self._request_times and now - self._request_times[0] > 60:
            self._request_times.popleft()
        if len(self._request_times) >= limit:
            raise RuntimeError("Rate limit exceeded")
        self._request_times.append(now)

    # ------------------------------------------------------------------
    def generate(self, prompt: str, api_key: str | None = None) -> str:
        self._throttle()

        try:
            import httpx  # type: ignore
        except Exception as exc:  # pragma: no cover - import error path
            raise RuntimeError("httpx package is required for LocalProvider") from exc

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        try:
            response = httpx.post(self.config.url, json=payload, timeout=30.0)
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - network error path
            raise RuntimeError(str(exc)) from exc

        data = response.json()
        return data.get("response", "")
