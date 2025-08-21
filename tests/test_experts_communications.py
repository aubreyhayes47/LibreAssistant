import pytest

from libreassistant.experts import communications


def test_communications_valid_json(monkeypatch):
    monkeypatch.setattr(
        communications.providers,
        "generate",
        lambda provider, prompt: '{"message": "Stay curious", "audience": "everyone"}',
    )
    result = communications.analyze("learn")
    assert result == {"message": "Stay curious", "audience": "everyone"}


def test_communications_malformed_json(monkeypatch):
    monkeypatch.setattr(
        communications.providers,
        "generate",
        lambda provider, prompt: "<xml>",
    )
    with pytest.raises(ValueError):
        communications.analyze("goal")


def test_communications_missing_fields(monkeypatch):
    monkeypatch.setattr(
        communications.providers,
        "generate",
        lambda provider, prompt: '{"message": "hi"}',
    )
    with pytest.raises(ValueError):
        communications.analyze("goal")
