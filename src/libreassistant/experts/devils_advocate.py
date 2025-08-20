"""Devil's advocate analysis module using a model call."""

from __future__ import annotations

import json
from typing import Dict, List

from ..providers import providers


def analyze(goal: str) -> Dict[str, List[str]]:
    """Highlight potential issues with the goal via a language model."""

    prompt = (
        "List two potential risks or unintended consequences of the goal '"
        + goal
        + "'. Respond in JSON with a 'concerns' array of strings."
    )
    raw = providers.generate("cloud", prompt)
    try:
        data = json.loads(raw)
    except Exception as exc:  # pragma: no cover - invalid model output
        raise ValueError("Model did not return valid JSON") from exc
    if "concerns" not in data or not isinstance(data["concerns"], list):
        raise ValueError("Model response missing 'concerns'")
    return data  # type: ignore[return-value]
