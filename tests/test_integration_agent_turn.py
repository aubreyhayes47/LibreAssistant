"""Integration tests for Agent.turn() with real Session, ToolRegistry, and tool execution."""

from unittest.mock import MagicMock, patch

import pytest

from libreassistant.agent import Agent
from libreassistant.profiles import AgentProfile
from libreassistant.session import Session, Message
from libreassistant.tool_registry import ToolRegistry


def _mock_response(text="response", tool_calls=None):
    choice = MagicMock()
    choice.message.content = text
    choice.message.tool_calls = tool_calls
    choice.message.role = "assistant"
    choice.message.reasoning_content = None
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# --- Fixtures (real Session, ToolRegistry) ---
@pytest.fixture
def profile():
    return AgentProfile(
        name="default",
        description="Default test profile",
        system_prompt="You are a test assistant.",
        tool_patterns=["*"],
    )


@pytest.fixture
def registry():  # real ToolRegistry with one registered tool for tool-call tests
    reg = ToolRegistry()
    reg.register("test_tool", "A test tool",
                 {"type": "object", "properties": {}, "required": []},
                 lambda _: "tool_result")
    return reg


# --- Full turn pipeline ---
class TestAgentTurnIntegration:
    def test_turn_adds_user_and_assistant_messages(self, profile, registry):
        """Full turn: absorb -> add user -> call API -> add assistant message."""
        session = Session(profile=profile, backlog=MagicMock())

        client = MagicMock()
        client.chat.completions.create.return_value = _mock_response(text="Hello!")

        agent = Agent(
            session=session,
            client=client,
            registry=registry,
            task_pool=None,
            model="test-model",
        )

        result = agent.turn("hi")
        assert result == "Hello!"
        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[0].content == "hi"
        assert session.messages[1].role == "assistant"
        assert session.messages[1].content == "Hello!"

    def test_turn_with_tool_call_chain(self, profile, registry):
        """Tool call in first response -> dispatch -> second response."""
        session = Session(profile=profile)

        tc = MagicMock()
        tc.id = "call_1"
        tc.type = "function"
        tc.function.name = "test_tool"
        tc.function.arguments = "{}"

        client = MagicMock()
        call_count = [0]

        def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return _mock_response(text=None, tool_calls=[tc])
            return _mock_response(text="final answer")

        client.chat.completions.create.side_effect = side_effect

        agent = Agent(
            session=session,
            client=client,
            registry=registry,
            task_pool=None,
            model="test-model",
        )

        result = agent.turn("do something")
        assert result == "final answer"
        assert len(session.messages) >= 3
        tool_msgs = [m for m in session.messages if m.role == "tool"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0].content == "tool_result"

    def test_turn_truncates_tool_result(self, profile):
        """Tool result truncated at max_tool_result_chars."""
        long_result = "x" * 500
        profile.max_tool_result_chars = 100

        reg = ToolRegistry()
        reg.register("long_tool", "Returns long data",
                     {"type": "object", "properties": {}, "required": []},
                     lambda _: long_result)

        session = Session(profile=profile)

        tc = MagicMock()
        tc.id = "call_long"
        tc.type = "function"
        tc.function.name = "long_tool"
        tc.function.arguments = "{}"

        client = MagicMock()
        call_count = [0]

        def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return _mock_response(text=None, tool_calls=[tc])
            return _mock_response(text="done")

        client.chat.completions.create.side_effect = side_effect

        agent = Agent(
            session=session,
            client=client,
            registry=reg,
            task_pool=None,
            model="test-model",
        )

        agent.turn("get long data")
        tool_msgs = [m for m in session.messages if m.role == "tool"]
        assert len(tool_msgs) == 1
        assert "[truncated" in tool_msgs[0].content
        assert len(tool_msgs[0].content) < 200

    def test_turn_max_rounds_exhausted(self, profile):
        """After max_tool_rounds tool calls, final tool-less call returns result."""
        tc = MagicMock()
        tc.id = "call_repeat"
        tc.type = "function"
        tc.function.name = "test_tool"
        tc.function.arguments = "{}"

        profile.max_tool_rounds = 2

        reg = ToolRegistry()
        reg.register("test_tool", "test",
                     {"type": "object", "properties": {}, "required": []},
                     lambda _: "result")

        session = Session(profile=profile)

        client = MagicMock()
        call_count = [0]

        def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                return _mock_response(text=None, tool_calls=[tc])
            return _mock_response(text="exhausted final")

        client.chat.completions.create.side_effect = side_effect

        agent = Agent(
            session=session,
            client=client,
            registry=reg,
            task_pool=None,
            model="test-model",
        )

        result = agent.turn("do it")
        assert result == "exhausted final"
        assert call_count[0] == 3

    def test_turn_sanitizes_before_api_call(self, profile, registry):  # pre-seeds a message with reasoning to verify sanitize strips it before API call
        """Messages sent to API should not contain reasoning_content."""
        session = Session(profile=profile)

        client = MagicMock()
        client.chat.completions.create.return_value = _mock_response(text="clean")

        session.add_message(Message(
            id="m1", session_id=session.id, role="assistant",
            content="has reasoning", tool_calls=None, tool_call_id=None,
            agent="default", mode="primary", parent_id=None, timestamp=1.0,
        ))

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
            assert "refusal" not in msg
            assert "usage" not in msg
