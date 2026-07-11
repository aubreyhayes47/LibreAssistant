"""Integration tests for profile switching: tool visibility, model override, round-trip restore."""
"""Integration tests: Profile switching pipeline."""

from unittest.mock import MagicMock, patch

import pytest

from libreassistant.agent import Agent
from libreassistant.profiles import AgentProfile, get_profile
from libreassistant.session import Session
from libreassistant.tool_registry import ToolRegistry


# --- Fixtures ---
@pytest.fixture
def profile():
    return AgentProfile(
        name="default",
        description="General purpose",
        system_prompt="You are a helpful assistant.",
        tool_patterns=["*"],
    )


@pytest.fixture
def session(profile):  # session pre-seeded with a system message for the default profile
    s = Session(profile=profile)
    s.add_system_message(profile.system_prompt, agent=profile.name)
    return s


@pytest.fixture
def registry():  # registry pre-loaded with tools from all profiles for before/after comparison
    reg = ToolRegistry()
    for name in ["web_search", "web_fetch", "read_file", "terminal",
                  "mcp/courtlistener/search", "save_file"]:
        reg.register(name, "", {}, lambda x, n=name: n)
    return reg


# --- Profile switch effects ---
class TestProfileSwitchIntegration:
    def test_switch_profile_replaces_system_prompt(self, session, registry):  # legal profile filters to courtlistener + web tools; excludes terminal/save_file
        agent = Agent(
            session=session, client=MagicMock(), registry=registry,
            task_pool=None, model="test-model",
        )
        agent.switch_profile("legal")
        assert session.messages[0].content == get_profile("legal").system_prompt
        assert session.profile.name == "legal"

    def test_switch_profile_filters_registry(self, session, registry):
        agent = Agent(
            session=session, client=MagicMock(), registry=registry,
            task_pool=None, model="test-model",
        )
        agent.switch_profile("legal")
        after_tools = set(agent.registry.tool_names)
        assert "mcp/courtlistener/search" in after_tools
        assert "web_search" in after_tools
        assert "web_fetch" in after_tools
        assert "read_file" in after_tools
        assert "terminal" not in after_tools
        assert "save_file" not in after_tools

    def test_switch_to_code_profile(self, session, registry):  # code profile includes file+terminal; excludes courtlistener
        agent = Agent(
            session=session, client=MagicMock(), registry=registry,
            task_pool=None, model="test-model",
        )
        agent.switch_profile("code")
        code_tools = set(agent.registry.tool_names)
        assert "read_file" in code_tools
        assert "save_file" in code_tools
        assert "terminal" in code_tools
        assert "web_search" in code_tools
        assert "mcp/courtlistener/search" not in code_tools

    def test_switch_back_to_default_restores_tools(self, session, registry):  # switching back to default restores all tools
        agent = Agent(
            session=session, client=MagicMock(), registry=registry,
            task_pool=None, model="test-model",
        )
        agent.switch_profile("legal")
        agent.switch_profile("default")
        final_tools = set(agent.registry.tool_names)
        assert "mcp/courtlistener/search" in final_tools
        assert "web_search" in final_tools
        assert "web_fetch" in final_tools
        assert "read_file" in final_tools

    def test_switch_profile_model_override(self, session):  # uses patch.object to inject a custom profile into get_profile()
        """Profile with model override updates agent.model."""
        from libreassistant import agent as agent_module

        profile_with_model = AgentProfile(
            name="custom", description="Custom", system_prompt="Custom prompt",
            model="gpt-4", tool_patterns=["*"],
        )
        reg = ToolRegistry()
        reg.register("test_tool", "", {}, lambda x: x)

        with patch.object(agent_module, "get_profile", return_value=profile_with_model):
            agent = Agent(
                session=session, client=MagicMock(), registry=reg,
                task_pool=None, model="test-model",
            )
            agent.switch_profile("custom")
            assert agent.model == "gpt-4"

    def test_switch_profile_same_profile(self, session, registry):  # switching to the same profile returns a no-op message
        agent = Agent(
            session=session, client=MagicMock(), registry=registry,
            task_pool=None, model="test-model",
        )
        result = agent.switch_profile("default")
        assert result == "Already using profile 'default'"

    def test_switch_adds_confirmation_message(self, session, registry):  # a confirmation message like "have switched to the legal profile" is added to the conversation
        agent = Agent(
            session=session, client=MagicMock(), registry=registry,
            task_pool=None, model="test-model",
        )
        agent.switch_profile("legal")
        switch_msgs = [m for m in session.messages if "have switched to the" in m.content]
        assert len(switch_msgs) >= 1
