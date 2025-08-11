# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for the initial system prompt."""

from __future__ import annotations

from libreassistant.prompt import SYSTEM_PROMPT


def test_system_prompt_mentions_privacy() -> None:
    assert "privacy" in SYSTEM_PROMPT.lower()
