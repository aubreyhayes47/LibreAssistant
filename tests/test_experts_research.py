import pytest

from libreassistant.experts import research


def test_research_valid_json(monkeypatch):
    monkeypatch.setattr(
        research.providers,
        "generate",
        lambda provider, prompt: '{"summary": "info", "sources": ["http://example.com"]}',
    )
    result = research.analyze("goal")
    assert result == {"summary": "info", "sources": ["http://example.com"]}


def test_research_malformed_json(monkeypatch):
    monkeypatch.setattr(
        research.providers,
        "generate",
        lambda provider, prompt: "not json",
    )
    with pytest.raises(ValueError):
        research.analyze("goal")
