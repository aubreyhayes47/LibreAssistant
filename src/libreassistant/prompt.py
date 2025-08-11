# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Expose the initial system prompt used by the application."""

from __future__ import annotations

from importlib import resources

raw_prompt = resources.files("libreassistant").joinpath("system_prompt.txt").read_text().splitlines()
SYSTEM_PROMPT = "\n".join(line for line in raw_prompt if not line.startswith("#"))
