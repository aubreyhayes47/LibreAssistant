import pytest

from libreassistant.experts import visualizer


def test_visualizer_valid_json(monkeypatch):
    monkeypatch.setattr(
        visualizer.providers,
        "generate",
        lambda provider, prompt: '{"description": "chart", "data": {"type": "bar", "labels": ["a"], "values": [1]}}',
    )
    result = visualizer.analyze("goal")
    assert result == {
        "description": "chart",
        "data": {"type": "bar", "labels": ["a"], "values": [1]},
    }


def test_visualizer_malformed_json(monkeypatch):
    monkeypatch.setattr(
        visualizer.providers,
        "generate",
        lambda provider, prompt: "<xml>",
    )
    with pytest.raises(ValueError):
        visualizer.analyze("goal")
