import pytest

from libreassistant.experts import executive


def test_executive_valid_json(monkeypatch):
    monkeypatch.setattr(
        executive.providers,
        "generate",
        lambda provider, prompt: '{"tasks": ["a", "b", "c"]}',
    )
    result = executive.analyze("goal")
    assert result == {"tasks": ["a", "b", "c"]}


def test_executive_malformed_json(monkeypatch):
    monkeypatch.setattr(
        executive.providers,
        "generate",
        lambda provider, prompt: "not json",
    )
    with pytest.raises(ValueError):
        executive.analyze("goal")
