# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

import pytest

from libreassistant.experts import argumentation


def test_argumentation_valid_json(monkeypatch):
    monkeypatch.setattr(
        argumentation.providers,
        "generate",
        lambda provider, prompt: '{"points": ["A", "B", "C"]}',
    )
    result = argumentation.analyze("reach the moon")
    assert result == {"points": ["A", "B", "C"]}


def test_argumentation_malformed_json(monkeypatch):
    monkeypatch.setattr(
        argumentation.providers,
        "generate",
        lambda provider, prompt: "not json",
    )
    with pytest.raises(ValueError):
        argumentation.analyze("goal")


def test_argumentation_missing_points(monkeypatch):
    monkeypatch.setattr(
        argumentation.providers,
        "generate",
        lambda provider, prompt: '{"point": []}',
    )
    with pytest.raises(ValueError):
        argumentation.analyze("goal")
