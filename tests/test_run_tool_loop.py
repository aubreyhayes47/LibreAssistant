"""Tests for run_tool_loop(): the core tool-calling loop."""
from unittest.mock import MagicMock

import pytest

from libreassistant.profiles import AgentProfile
from libreassistant.session import (
    Message,
    Session,
    run_tool_loop,
    sanitize,
    trim,
)
from libreassistant.tool_registry import ToolRegistry


# --- Text-only response (no tool calls) ---
def test_run_tool_loop_text_response():  # simplest path: model returns text, no tools involved
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
    session = Session(profile=profile)

    client = MagicMock()
    choice = MagicMock()
    choice.message.content = "Hello!"
    choice.message.tool_calls = None
    choice.message.role = "assistant"
    resp = MagicMock()
    resp.choices = [choice]
    client.chat.completions.create.return_value = resp

    registry = MagicMock()
    result = run_tool_loop(session, client, registry, "test-model")
    assert result == "Hello!"
    assert len(session.messages) == 1
    assert session.messages[0].role == "assistant"
    assert session.messages[0].content == "Hello!"


# --- Single tool call then response ---
def test_run_tool_loop_single_tool_call():  # side_effect alternates: first call returns tool_call, second returns text
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
    session = Session(profile=profile)

    tc = MagicMock()
    tc.id = "call_1"
    tc.type = "function"
    tc.function.name = "test_tool"
    tc.function.arguments = '{"arg": "val"}'

    client = MagicMock()
    call_count = [0]

    def side_effect(**kwargs):
        call_count[0] += 1
        choice = MagicMock()
        if call_count[0] == 1:
            choice.message.content = None
            choice.message.tool_calls = [tc]
        else:
            choice.message.content = "Done"
            choice.message.tool_calls = None
        choice.message.role = "assistant"
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    client.chat.completions.create.side_effect = side_effect

    registry = MagicMock()
    registry.dispatch.return_value = "tool_result"
    registry.schemas = [{"type": "function", "function": {"name": "test_tool"}}]

    result = run_tool_loop(session, client, registry, "test-model")
    assert result == "Done"
    registry.dispatch.assert_called_once_with("test_tool", {"arg": "val"})
    assert len(session.messages) >= 2
    tool_msgs = [m for m in session.messages if m.role == "tool"]
    assert len(tool_msgs) >= 1
    assert tool_msgs[0].content == "tool_result"


# --- JSON decode error recovery ---
def test_run_tool_loop_json_decode_error():  # malformed tool arguments → dispatched as empty dict {}; loop continues  # malformed tool arguments -> dispatched as empty dict {}; loop continues
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
    session = Session(profile=profile)

    tc = MagicMock()
    tc.id = "call_bad"
    tc.type = "function"
    tc.function.name = "test_tool"
    tc.function.arguments = "not valid json"

    client = MagicMock()
    call_count = [0]

    def side_effect(**kwargs):
        call_count[0] += 1
        choice = MagicMock()
        if call_count[0] == 1:
            choice.message.content = None
            choice.message.tool_calls = [tc]
        else:
            choice.message.content = "Recovered"
            choice.message.tool_calls = None
        choice.message.role = "assistant"
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    client.chat.completions.create.side_effect = side_effect

    registry = MagicMock()
    registry.dispatch.return_value = "handled"
    registry.schemas = [{"type": "function", "function": {"name": "test_tool"}}]

    result = run_tool_loop(session, client, registry, "test-model")
    assert result == "Recovered"
    registry.dispatch.assert_called_once_with("test_tool", {})


# --- Max rounds exhaustion ---
def test_run_tool_loop_max_rounds_exhaustion():  # max_rounds=2 → three API calls: 2 tool + 1 final text  # max_rounds=2 -> three API calls: 2 tool + 1 final text
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
    session = Session(profile=profile)

    tc = MagicMock()
    tc.id = "call_repeat"
    tc.type = "function"
    tc.function.name = "test_tool"
    tc.function.arguments = "{}"

    client = MagicMock()
    call_count = [0]

    def side_effect(**kwargs):
        call_count[0] += 1
        choice = MagicMock()
        if call_count[0] <= 2:
            choice.message.content = None
            choice.message.tool_calls = [tc]
        else:
            choice.message.content = "Final answer after exhaustion"
            choice.message.tool_calls = None
        choice.message.role = "assistant"
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    client.chat.completions.create.side_effect = side_effect

    registry = MagicMock()
    registry.dispatch.return_value = "result"
    registry.schemas = [{"type": "function", "function": {"name": "test_tool"}}]

    result = run_tool_loop(session, client, registry, "test-model", max_rounds=2)
    assert result == "Final answer after exhaustion"
    assert call_count[0] == 3


# --- Callbacks: status and reasoning ---
def test_run_tool_loop_status_callback():  # status_callback receives (message, round_number) for CLI display
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
    session = Session(profile=profile)

    client = MagicMock()
    choice = MagicMock()
    choice.message.content = "Done"
    choice.message.tool_calls = None
    choice.message.role = "assistant"
    resp = MagicMock()
    resp.choices = [choice]
    client.chat.completions.create.return_value = resp

    registry = MagicMock()
    status_log = []

    def status_cb(msg, round_n):
        status_log.append((msg, round_n))

    run_tool_loop(session, client, registry, "test-model", status_callback=status_cb)
    assert len(status_log) >= 1
    assert status_log[0][1] == 1


def test_run_tool_loop_reasoning_callback():  # reasoning_callback receives the raw reasoning_content for streaming display
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
    session = Session(profile=profile)

    client = MagicMock()
    choice = MagicMock()
    choice.message.content = "Thoughtful answer"
    choice.message.tool_calls = None
    choice.message.role = "assistant"
    choice.message.reasoning_content = "I am thinking..."
    resp = MagicMock()
    resp.choices = [choice]
    client.chat.completions.create.return_value = resp

    registry = MagicMock()
    reasoning_log = []

    def reasoning_cb(text):
        reasoning_log.append(text)

    run_tool_loop(session, client, registry, "test-model", reasoning_callback=reasoning_cb)
    assert reasoning_log == ["I am thinking..."]


# --- Edge cases ---
def test_run_tool_loop_empty_choices():  # empty choices → None (API returned nothing usable)  # empty choices -> None (API returned nothing usable)
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
    session = Session(profile=profile)

    client = MagicMock()
    resp = MagicMock()
    resp.choices = []
    client.chat.completions.create.return_value = resp

    registry = MagicMock()
    result = run_tool_loop(session, client, registry, "test-model")
    assert result is None


# --- Tool result truncation ---
def test_run_tool_loop_truncates_result():  # long tool results are truncated with "[truncated at N chars]" suffix
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
    session = Session(profile=profile)

    tc = MagicMock()
    tc.id = "call_long"
    tc.type = "function"
    tc.function.name = "test_tool"
    tc.function.arguments = "{}"

    long_result = "x" * 200

    client = MagicMock()
    call_count = [0]

    def side_effect(**kwargs):
        call_count[0] += 1
        choice = MagicMock()
        if call_count[0] == 1:
            choice.message.content = None
            choice.message.tool_calls = [tc]
        else:
            choice.message.content = "Done"
            choice.message.tool_calls = None
        choice.message.role = "assistant"
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    client.chat.completions.create.side_effect = side_effect

    registry = MagicMock()
    registry.dispatch.return_value = long_result
    registry.schemas = [{"type": "function", "function": {"name": "test_tool"}}]

    run_tool_loop(session, client, registry, "test-model", truncate_result_chars=50)
    tool_msgs = [m for m in session.messages if m.role == "tool"]
    assert len(tool_msgs) == 1
    assert len(tool_msgs[0].content) < 100
    assert "[truncated at 50 chars]" in tool_msgs[0].content


def test_run_tool_loop_no_truncate():  # truncate_result_chars=0 means no truncation
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
    session = Session(profile=profile)

    tc = MagicMock()
    tc.id = "call_long"
    tc.type = "function"
    tc.function.name = "test_tool"
    tc.function.arguments = "{}"

    long_result = "x" * 200

    client = MagicMock()
    call_count = [0]

    def side_effect(**kwargs):
        call_count[0] += 1
        choice = MagicMock()
        if call_count[0] == 1:
            choice.message.content = None
            choice.message.tool_calls = [tc]
        else:
            choice.message.content = "Done"
            choice.message.tool_calls = None
        choice.message.role = "assistant"
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    client.chat.completions.create.side_effect = side_effect

    registry = MagicMock()
    registry.dispatch.return_value = long_result
    registry.schemas = [{"type": "function", "function": {"name": "test_tool"}}]

    run_tool_loop(session, client, registry, "test-model", truncate_result_chars=0)
    tool_msgs = [m for m in session.messages if m.role == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0].content == long_result


# --- tool_call_callback ---
def test_tool_call_callback_invoked():
    """tool_call_callback receives (name, args, result) for each tool call."""
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
    session = Session(profile=profile)

    tc = MagicMock()
    tc.id = "call_1"
    tc.type = "function"
    tc.function.name = "test_tool"
    tc.function.arguments = '{"arg": "val"}'

    client = MagicMock()
    call_count = [0]

    def side_effect(**kwargs):
        call_count[0] += 1
        choice = MagicMock()
        if call_count[0] == 1:
            choice.message.content = None
            choice.message.tool_calls = [tc]
        else:
            choice.message.content = "Done"
            choice.message.tool_calls = None
        choice.message.role = "assistant"
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    client.chat.completions.create.side_effect = side_effect

    registry = MagicMock()
    registry.dispatch.return_value = "tool_result"
    registry.schemas = [{"type": "function", "function": {"name": "test_tool"}}]

    callback_log = []

    def tool_cb(name, args, result):
        callback_log.append((name, args, result))

    run_tool_loop(session, client, registry, "test-model", tool_call_callback=tool_cb)
    assert len(callback_log) == 1
    assert callback_log[0] == ("test_tool", {"arg": "val"}, "tool_result")


def test_tool_call_callback_not_invoked_when_none():
    """No callback = no error, loop still works."""
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
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
        choice = MagicMock()
        if call_count[0] == 1:
            choice.message.content = None
            choice.message.tool_calls = [tc]
        else:
            choice.message.content = "Done"
            choice.message.tool_calls = None
        choice.message.role = "assistant"
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    client.chat.completions.create.side_effect = side_effect

    registry = MagicMock()
    registry.dispatch.return_value = "result"
    registry.schemas = [{"type": "function", "function": {"name": "test_tool"}}]

    result = run_tool_loop(session, client, registry, "test-model")
    assert result == "Done"


def test_tool_call_callback_receives_full_result():
    """Callback receives the full result before truncation."""
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
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
        choice = MagicMock()
        if call_count[0] == 1:
            choice.message.content = None
            choice.message.tool_calls = [tc]
        else:
            choice.message.content = "Done"
            choice.message.tool_calls = None
        choice.message.role = "assistant"
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    client.chat.completions.create.side_effect = side_effect

    long_result = "x" * 500
    registry = MagicMock()
    registry.dispatch.return_value = long_result
    registry.schemas = [{"type": "function", "function": {"name": "test_tool"}}]

    callback_log = []

    def tool_cb(name, args, result):
        callback_log.append(result)

    run_tool_loop(session, client, registry, "test-model", truncate_result_chars=50, tool_call_callback=tool_cb)
    # Callback should see the FULL result, not the truncated one
    assert len(callback_log) == 1
    assert callback_log[0] == long_result
    # But the stored message should be truncated
    tool_msgs = [m for m in session.messages if m.role == "tool"]
    assert "[truncated" in tool_msgs[0].content
