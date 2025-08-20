# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Communications analysis module using a language model."""

from __future__ import annotations

import json
from typing import Dict

from ..providers import providers


def analyze(goal: str) -> Dict[str, str]:
    """Return a structured communication plan for ``goal`` via a model call."""

    prompt = (
        "Rewrite the goal '" + goal + "' into a concise public message and "
        "identify the target audience. Respond as JSON with keys 'message' and "
        "'audience'."
    )
    raw = providers.generate("cloud", prompt)
    try:
        data = json.loads(raw)
    except Exception as exc:  # pragma: no cover - invalid model output
        raise ValueError("Model did not return valid JSON") from exc
    if not {"message", "audience"} <= data.keys():
        raise ValueError("Model response missing fields")
    return data  # type: ignore[return-value]
