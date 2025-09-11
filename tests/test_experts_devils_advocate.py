# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

import pytest

from libreassistant.experts import devils_advocate


def test_devils_advocate_valid_json(monkeypatch):
    monkeypatch.setattr(
        devils_advocate.providers,
        "generate",
        lambda provider, prompt: '{"concerns": ["risk", "cost"]}',
    )
    result = devils_advocate.analyze("launch project")
    assert result == {"concerns": ["risk", "cost"]}


def test_devils_advocate_malformed_json(monkeypatch):
    monkeypatch.setattr(
        devils_advocate.providers,
        "generate",
        lambda provider, prompt: "not json",
    )
    with pytest.raises(ValueError):
        devils_advocate.analyze("goal")
