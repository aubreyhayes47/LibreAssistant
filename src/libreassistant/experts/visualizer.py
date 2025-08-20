"""Visualization analysis module powered by a model."""

from __future__ import annotations

import json
from typing import Any, Dict

from ..providers import providers


def analyze(goal: str) -> Dict[str, Any]:
    """Return visualization metadata and data for ``goal`` via model output."""

    prompt = (
        "For the goal '"
        + goal
        + "', propose a simple bar chart with phases and values. Respond as JSON "
        + "{\"description\": str, \"data\": {\"type\": \"bar\", \"labels\": [str], \"values\": [number]}}."
    )
    raw = providers.generate("cloud", prompt)
    try:
        data = json.loads(raw)
    except Exception as exc:  # pragma: no cover - invalid model output
        raise ValueError("Model did not return valid JSON") from exc
    if "description" not in data or "data" not in data:
        raise ValueError("Model response missing fields")
    return data
