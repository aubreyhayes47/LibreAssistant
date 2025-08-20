"""Argumentation analysis module driven by a language model."""

from __future__ import annotations

import json
from typing import Dict, List

from ..providers import providers


def analyze(goal: str) -> Dict[str, List[str]]:
    """Return a list of supporting arguments for ``goal`` using a model call."""

    prompt = (
        "Provide three persuasive arguments supporting the goal '" + goal + "'. "
        "Respond in JSON with a 'points' array of strings."
    )
    raw = providers.generate("cloud", prompt)
    try:
        data = json.loads(raw)
    except Exception as exc:  # pragma: no cover - invalid model output
        raise ValueError("Model did not return valid JSON") from exc
    if "points" not in data or not isinstance(data["points"], list):
        raise ValueError("Model response missing 'points'")
    return data  # type: ignore[return-value]
