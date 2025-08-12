# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Transparency utilities for Bill of Materials and system health."""

from __future__ import annotations

import time
from typing import Any, Dict, List

import importlib.metadata


class HealthMonitor:
    """Simple in-memory tracker for system health metrics."""

    def __init__(self) -> None:
        self.start_time = time.time()
        self.requests = 0
        self.error_count = 0
        self.errors: List[str] = []

    def record_request(self) -> None:
        """Increment the total request count."""
        self.requests += 1

    def record_error(self, message: str) -> None:
        """Record an error event with a message."""
        self.error_count += 1
        self.errors.append(message)

    def get_status(self) -> Dict[str, Any]:
        """Return a snapshot of current system health metrics."""
        return {
            "status": "ok",
            "uptime": time.time() - self.start_time,
            "requests": self.requests,
            "error_count": self.error_count,
            "errors": self.errors,
        }


def get_bill_of_materials() -> Dict[str, List[str]]:
    """Gather a list of installed dependencies, models, and datasets."""
    dependencies = sorted(
        f"{dist.metadata['Name']}=={dist.version}" for dist in importlib.metadata.distributions()
    )
    return {"dependencies": dependencies, "models": [], "datasets": []}
