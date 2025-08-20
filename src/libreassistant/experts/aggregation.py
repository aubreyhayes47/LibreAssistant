# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Aggregate expert analyses into a final summary via a language model."""

from __future__ import annotations

import json
from typing import Any, Dict

from ..providers import providers


def summarize(analysis: Dict[str, Any]) -> str:
    """Combine expert outputs into a concise, human-readable summary."""

    prompt = (
        "Summarize the following analysis in a few sentences highlighting "
        "communications, arguments and caveats. Return plain text.\n" + json.dumps(analysis)
    )
    return providers.generate("cloud", prompt)
