"""Research analysis module powered by a language model."""

from __future__ import annotations

import json
from typing import Dict, List

from ..providers import providers


def analyze(goal: str) -> Dict[str, List[str]]:
    """Return lightweight research findings for the goal via model query."""

    prompt = (
        "Provide a brief research summary and a single citation for the goal '"
        + goal
        + "'. Respond in JSON with keys 'summary' and 'sources' (array of URLs)."
    )
    raw = providers.generate("cloud", prompt)
    try:
        data = json.loads(raw)
    except Exception as exc:  # pragma: no cover - invalid model output
        raise ValueError("Model did not return valid JSON") from exc
    if not {"summary", "sources"} <= data.keys():
        raise ValueError("Model response missing fields")
    return data  # type: ignore[return-value]
