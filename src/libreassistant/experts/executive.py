# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Executive analysis module backed by a language model."""

from __future__ import annotations

import json
from typing import Dict, List

from ..providers import providers


def analyze(goal: str) -> Dict[str, List[str]]:
    """Provide an executive breakdown of ``goal`` using model reasoning."""

    prompt = (
        "Break down the goal '" + goal + "' into three actionable steps. "
        "Respond in JSON with a 'tasks' array of strings ordered sequentially."
    )
    raw = providers.generate("cloud", prompt)
    try:
        data = json.loads(raw)
    except Exception as exc:  # pragma: no cover - invalid model output
        raise ValueError("Model did not return valid JSON") from exc
    if "tasks" not in data or not isinstance(data["tasks"], list):
        raise ValueError("Model response missing 'tasks'")
    return data  # type: ignore[return-value]
