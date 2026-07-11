"""Tests for profiles.py (agent profiles)."""
import json
from unittest.mock import MagicMock, patch

import pytest

from libreassistant.profiles import (
    AGENTS_DIR,
    UnknownProfileError,
    delegatee_profiles,
    get_profile,
    list_profiles,
    load_profiles,
)


# --- Built-in profiles ---
@patch("libreassistant.profiles.AGENTS_DIR")
def test_profiles_builtin_default(mock_agents_dir):  # default profile has wildcard tool access
    mock_agents_dir.glob.return_value = []
    profiles = load_profiles()
    default = profiles["default"]
    assert default.name == "default"
    assert default.description
    assert default.tool_patterns == ["*"]


@patch("libreassistant.profiles.AGENTS_DIR")
def test_profiles_builtin_legal(mock_agents_dir):  # legal profile restricts tools to courtlistener + web search/fetch
    mock_agents_dir.glob.return_value = []
    profiles = load_profiles()
    legal = profiles["legal"]
    assert "mcp/courtlistener/*" in legal.tool_patterns
    assert "web_search" in legal.tool_patterns


@patch("libreassistant.profiles.AGENTS_DIR")
def test_profiles_builtin_code(mock_agents_dir):  # code profile excludes courtlistener; includes file + terminal tools
    mock_agents_dir.glob.return_value = []
    profiles = load_profiles()
    code = profiles["code"]
    assert "mcp/courtlistener/*" not in code.tool_patterns
    assert "read_file" in code.tool_patterns
    assert "terminal" in code.tool_patterns


# --- Profile registry API ---
@patch("libreassistant.profiles.AGENTS_DIR")
def test_profiles_list(mock_agents_dir):
    mock_agents_dir.glob.return_value = []
    result = list_profiles()
    assert "default" in result
    assert "legal" in result
    assert "code" in result
    assert result == sorted(result)


@patch("libreassistant.profiles.AGENTS_DIR")
def test_profiles_unknown(mock_agents_dir):  # get_profile for unknown name raises, not returns None
    mock_agents_dir.glob.return_value = []
    with pytest.raises(UnknownProfileError):
        get_profile("nonexistent")


# --- User override behaviour ---
@patch("libreassistant.profiles.AGENTS_DIR")
def test_profiles_user_override(mock_agents_dir):  # user JSON in AGENTS_DIR overrides built-in of the same name
    fake_path = MagicMock()
    fake_path.read_text.return_value = json.dumps({
        "name": "default",
        "description": "User description",
        "system_prompt": "User prompt",
    })
    mock_agents_dir.glob.return_value = [fake_path]
    profiles = load_profiles()
    assert profiles["default"].description == "User description"


@patch("libreassistant.profiles.AGENTS_DIR")
def test_profiles_delegatee(mock_agents_dir):  # delegatee_profiles excludes the current profile from routing options
    mock_agents_dir.glob.return_value = []
    result = delegatee_profiles("default")
    assert isinstance(result, list)
    for item in result:
        assert "name" in item
        assert "description" in item
        assert item["name"] != "default"


# --- Edge cases: malformed/incomplete user profiles ---
@patch("libreassistant.profiles.AGENTS_DIR")
def test_profiles_malformed_json(mock_agents_dir):  # malformed JSON is silently skipped; built-in still loads
    fake_path = MagicMock()
    fake_path.read_text.return_value = "not json"
    mock_agents_dir.glob.return_value = [fake_path]
    profiles = load_profiles()
    assert "default" in profiles


@patch("libreassistant.profiles.AGENTS_DIR")
def test_profiles_model_override(mock_agents_dir):  # model=None means "use CLI default" (no override)
    mock_agents_dir.glob.return_value = []
    result = get_profile("legal")
    assert result.model is None


@patch("libreassistant.profiles.AGENTS_DIR")
# empty tool_patterns means no tools available for this profile
def test_profiles_empty_tool_patterns(mock_agents_dir):
    fake_path = MagicMock()
    fake_path.read_text.return_value = json.dumps({
        "name": "restricted",
        "description": "No tools allowed",
        "system_prompt": "You have no tools.",
        "tool_patterns": [],
    })
    mock_agents_dir.glob.return_value = [fake_path]
    profiles = load_profiles()
    assert profiles["restricted"].tool_patterns == []


@patch("libreassistant.profiles.AGENTS_DIR")
# missing required fields -> profile silently dropped
def test_profiles_missing_required_fields(mock_agents_dir):
    fake_path = MagicMock()
    fake_path.read_text.return_value = json.dumps({
        "name": "incomplete",
    })
    mock_agents_dir.glob.return_value = [fake_path]
    profiles = load_profiles()
    assert "incomplete" not in profiles


@patch("libreassistant.profiles.AGENTS_DIR")
# partial override: user supplies only description+prompt, built-in defaults for rest
def test_profiles_partial_override(mock_agents_dir):  # tool_patterns default to [] when not specified (not inherited from built-in)
    fake_path = MagicMock()
    fake_path.read_text.return_value = json.dumps({
        "name": "default",
        "description": "Overridden description",
        "system_prompt": "Overridden prompt",
    })
    mock_agents_dir.glob.return_value = [fake_path]
    profiles = load_profiles()
    default = profiles["default"]
    assert default.description == "Overridden description"
    assert default.system_prompt == "Overridden prompt"
    assert default.name == "default"
    assert default.tool_patterns is None
    assert default.model is None
