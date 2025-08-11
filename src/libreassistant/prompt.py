# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Expose the initial system prompt used by the application."""

from __future__ import annotations

from importlib import resources

SYSTEM_PROMPT = resources.files("libreassistant").joinpath("system_prompt.txt").read_text()
