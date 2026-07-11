"""Tests for agent.py: Agent turn loop, profile switching, tool dispatch."""
import unittest
from unittest.mock import MagicMock

import pytest

from libreassistant.agent import Agent
from libreassistant.profiles import AgentProfile
from libreassistant.session import Session
from libreassistant.tool_registry import ToolRegistry


def _mock_response(text="response", tool_calls=None, reasoning=None):  # factory helper: builds a mock API response with optional tool_calls and reasoning
    choice = MagicMock()
    choice.message.content = text
    choice.message.tool_calls = tool_calls
    choice.message.role = "assistant"
    choice.message.reasoning_content = reasoning
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.fixture
def profile():
    return AgentProfile(
        name="default",
        description="Test",
        system_prompt="You are a test.",
        tool_patterns=["*"],
    )


@pytest.fixture
def session(profile):
    return Session(profile=profile)


@pytest.fixture
def registry():
    reg = ToolRegistry()
    reg.register(
        "test_tool",
        "A test tool",
        {"type": "object", "properties": {}, "required": []},
        lambda _: "called",
    )
    return reg


# --- Agent construction ---
class TestAgentInit:
    def test_agent_init(self):  # agent constructed with all-mock dependencies for isolated unit testing
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_registry = MagicMock()
        mock_task_pool = MagicMock()
        agent = Agent(
            session=mock_session,
            client=mock_client,
            registry=mock_registry,
            task_pool=mock_task_pool,
            model="test-model",
        )
        assert agent.active is True
        assert agent.session is mock_session
        assert agent.model == "test-model"


# --- Agent turn() pipeline ---
class TestAgentTurn:
    def test_agent_turn_adds_user_message(self, session, registry):  # turn() prepends user message, calls API, appends assistant response
        client = MagicMock()
        client.chat.completions.create.return_value = _mock_response(text="hello back")
        agent = Agent(
            session=session,
            client=client,
            registry=registry,
            task_pool=None,
            model="test-model",
        )
        agent.turn("hello")
        assert session.messages[0].role == "user"
        assert session.messages[0].content == "hello"
        assert len(session.messages) >= 2

# backlog is drained at the start of every turn (absorb_completed_tasks)
    def test_agent_turn_absorbs_backlog(self, session, registry):
        assert session.absorb_completed_tasks() == 0
        client = MagicMock()
        client.chat.completions.create.return_value = _mock_response(text="done")
        agent = Agent(
            session=session,
            client=client,
            registry=registry,
            task_pool=None,
            model="test-model",
        )
        task = MagicMock()
        task._already_injected = False
        task.id = "task_1"
        task.specialist = "legal"
        task.input = "research question"
        task.output = "research result"
        task.error = None
        task.needs_verification = []
        session.backlog.put(task)
        agent.turn("hi")
        system_msgs = [m for m in session.messages if m.role == "system"]
        assert len(system_msgs) >= 1

# text-only response: no tools involved
    def test_agent_loop_text_response(self, session, registry):
        client = MagicMock()
        client.chat.completions.create.return_value = _mock_response(text="hello back")
        agent = Agent(
            session=session,
            client=client,
            registry=registry,
            task_pool=None,
            model="test-model",
        )
        result = agent.turn("hi")
        assert result == "hello back"
        assert session.messages[-1].role == "assistant"
        assert session.messages[-2].role == "user"

# sanitize() runs on messages before they reach the API
    def test_agent_sanitize_before_call(self, session, registry):
        client = MagicMock()
        client.chat.completions.create.return_value = _mock_response(text="clean")
        agent = Agent(
            session=session,
            client=client,
            registry=registry,
            task_pool=None,
            model="test-model",
        )
        agent.turn("hi")
        sent_messages = client.chat.completions.create.call_args[1]["messages"]
        for msg in sent_messages:
            assert "reasoning_content" not in msg

# tool loop runs up to max_tool_rounds; side_effect simulates sequential calls
    def test_agent_loop_max_rounds(self, registry):  # mutable list used as closure workaround for call count
        tc = MagicMock()
        tc.id = "call_1"
        tc.type = "function"
        tc.function.name = "test_tool"
        tc.function.arguments = "{}"
        profile = AgentProfile(
            name="test",
            description="Test",
            system_prompt="You are a test.",
            max_tool_rounds=3,
            tool_patterns=["*"],
        )
        sess = Session(profile=profile)
        client = MagicMock()
        call_count = [0]

        def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] <= 3:
                return _mock_response(text=None, tool_calls=[tc])
            return _mock_response(text="final")

        client.chat.completions.create.side_effect = side_effect
        agent = Agent(
            session=sess,
            client=client,
            registry=registry,
            task_pool=None,
            model="test-model",
        )
        result = agent.turn("hi")
        assert result == "final"

    def test_agent_turn_empty_choices(self, session, registry):  # empty choices → None (no response from API)
        client = MagicMock()
        resp = MagicMock()
        resp.choices = []
        client.chat.completions.create.return_value = resp
        agent = Agent(
            session=session,
            client=client,
            registry=registry,
            task_pool=None,
            model="test-model",
        )
        result = agent.turn("hi")
        assert result is None

# tool dispatch exception → error message sent back to model → model recovers
    def test_agent_turn_dispatch_exception(self, session, registry):
        registry.register("failing_tool", "raises", {}, lambda _: (_ for _ in ()).throw(Exception("boom")))
        tc = MagicMock()
        tc.id = "call_fail"
        tc.type = "function"
        tc.function.name = "failing_tool"
        tc.function.arguments = "{}"

        client = MagicMock()
        call_count = [0]
        def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return _mock_response(text=None, tool_calls=[tc])
            return _mock_response(text="recovered")

        client.chat.completions.create.side_effect = side_effect
        agent = Agent(
            session=session,
            client=client,
            registry=registry,
            task_pool=None,
            model="test-model",
        )
        result = agent.turn("hi")
        assert result is not None


# --- Profile switching ---
class TestAgentSwitchProfile:
    def test_agent_switch_profile(self, session, registry):  # switch_profile() replaces system prompt and filters tool registry
        session.add_system_message(
            session.profile.system_prompt, agent=session.profile.name
        )
        agent = Agent(
            session=session,
            client=MagicMock(),
            registry=registry,
            task_pool=None,
            model="test-model",
        )
        result = agent.switch_profile("legal")
        assert session.profile.name == "legal"
        assert result == "Switched to profile 'legal'"
        system_msgs = [m for m in session.messages if m.role == "system"]
        assert any(
            "Your role is now:" in m.content for m in system_msgs
        )

    def test_agent_switch_profile_deduplicates_role_directives(self, session, registry):
        session.add_system_message(
            session.profile.system_prompt, agent=session.profile.name
        )
        agent = Agent(
            session=session,
            client=MagicMock(),
            registry=registry,
            task_pool=None,
            model="test-model",
        )
        agent.switch_profile("legal")
        agent.switch_profile("legal")
        agent.switch_profile("legal")
        switch_msgs = [
            m for m in session.messages
            if m.role == "system" and m.content.startswith("IMPORTANT: You have switched to the")
        ]
        assert len(switch_msgs) == 1

    def test_agent_switch_profile_same(self, session, registry):
        session.add_system_message(
            session.profile.system_prompt, agent=session.profile.name
        )
        agent = Agent(
            session=session,
            client=MagicMock(),
            registry=registry,
            task_pool=None,
            model="test-model",
        )
        result = agent.switch_profile("default")
        assert result == "Already using profile 'default'"

# profile.model override takes precedence over the agent's default model
    def test_switch_profile_model_override(self, session, registry):
        import libreassistant.agent as agent_module
        profile_with_model = AgentProfile(
            name="custom",
            description="Custom",
            system_prompt="Custom prompt",
            model="gpt-4",
            tool_patterns=["*"],
        )
        with unittest.mock.patch.object(agent_module, "get_profile", return_value=profile_with_model):
            session.add_system_message(
                session.profile.system_prompt, agent=session.profile.name
            )
            agent = Agent(
                session=session,
                client=MagicMock(),
                registry=registry,
                task_pool=None,
                model="test-model",
            )
            agent.switch_profile("custom")
            assert agent.model == "gpt-4"

