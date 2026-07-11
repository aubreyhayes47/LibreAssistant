"""Tests for run_tool_loop interrupt (abort_event) and steer queue functionality."""
import threading
from unittest.mock import MagicMock

import pytest

from libreassistant.profiles import AgentProfile
from libreassistant.session import Message, Session, run_tool_loop


def _make_session():
    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
    return Session(profile=profile)


def _text_response(text="Done."):
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = text
    choice.message.tool_calls = None
    choice.message.role = "assistant"
    resp = MagicMock()
    resp.choices = [choice]
    client.chat.completions.create.return_value = resp
    return client


def _tool_then_text(tool_name="test_tool", tool_args="{}", tool_result="ok", text="Done."):
    """Return a client that first emits a tool call, then a text response."""
    client = MagicMock()

    tc = MagicMock()
    tc.id = "call_1"
    tc.type = "function"
    tc.function.name = tool_name
    tc.function.arguments = tool_args

    choice1 = MagicMock()
    choice1.message.content = None
    choice1.message.tool_calls = [tc]
    choice1.message.role = "assistant"

    choice2 = MagicMock()
    choice2.message.content = text
    choice2.message.tool_calls = None
    choice2.message.role = "assistant"

    resp1 = MagicMock()
    resp1.choices = [choice1]
    resp2 = MagicMock()
    resp2.choices = [choice2]
    client.chat.completions.create.side_effect = [resp1, resp2]
    return client


# --- abort_event tests ---
class TestAbortEvent:
    def test_abort_before_turn_returns_none(self):
        """abort_event set before loop starts should return None immediately."""
        session = _make_session()
        client = _text_response("Should not reach here")
        abort = threading.Event()
        abort.set()

        result = run_tool_loop(session, client, MagicMock(), "m", abort_event=abort)
        assert result is None
        # No assistant message should be added
        assert all(m.role != "assistant" for m in session.messages)

    def test_abort_returns_none_no_tool_call_dispatched(self):
        """abort_event set before loop starts should prevent any tool dispatch."""
        session = _make_session()
        registry = MagicMock()
        registry.schemas = [{"type": "function", "function": {"name": "test_tool"}}]
        abort = threading.Event()
        abort.set()

        result = run_tool_loop(session, MagicMock(), registry, "m", abort_event=abort)
        assert result is None
        registry.dispatch.assert_not_called()

    def test_abort_mid_turn_returns_none(self):
        """abort_event set after first API call but before second should cut short."""
        session = _make_session()

        tc = MagicMock()
        tc.id = "call_1"
        tc.type = "function"
        tc.function.name = "test_tool"
        tc.function.arguments = "{}"

        choice1 = MagicMock()
        choice1.message.content = None
        choice1.message.tool_calls = [tc]
        choice1.message.role = "assistant"

        resp1 = MagicMock()
        resp1.choices = [choice1]

        client = MagicMock()
        client.chat.completions.create.return_value = resp1

        registry = MagicMock()
        registry.schemas = [{"type": "function", "function": {"name": "test_tool"}}]
        registry.dispatch.return_value = "result"

        abort = threading.Event()

        def set_abort_after_dispatch(name, args):
            abort.set()
            return "dispatched"

        registry.dispatch.side_effect = set_abort_after_dispatch

        result = run_tool_loop(session, client, registry, "m", abort_event=abort)
        assert result is None

    def test_abort_marks_remaining_tool_calls(self):
        """When abort fires mid-turn, remaining tool calls get 'aborted' messages."""
        session = _make_session()

        tc1 = MagicMock()
        tc1.id = "call_1"
        tc1.type = "function"
        tc1.function.name = "tool_a"
        tc1.function.arguments = "{}"

        tc2 = MagicMock()
        tc2.id = "call_2"
        tc2.type = "function"
        tc2.function.name = "tool_b"
        tc2.function.arguments = "{}"

        choice = MagicMock()
        choice.message.content = None
        choice.message.tool_calls = [tc1, tc2]
        choice.message.role = "assistant"

        resp = MagicMock()
        resp.choices = [choice]

        client = MagicMock()
        client.chat.completions.create.return_value = resp

        registry = MagicMock()
        registry.schemas = [{"type": "function", "function": {"name": "tool_a"}}]
        registry.dispatch.return_value = "ok"

        abort = threading.Event()

        def abort_after_first(name, args):
            abort.set()
            return "ok"

        registry.dispatch.side_effect = abort_after_first

        result = run_tool_loop(session, client, registry, "m", abort_event=abort)
        assert result is None

        # First tool call succeeds, second is aborted
        tool_msgs = [m for m in session.messages if m.role == "tool"]
        assert len(tool_msgs) == 2
        assert tool_msgs[0].content == "ok"  # First tool ran successfully
        assert "aborted" in tool_msgs[1].content.lower()  # Second was aborted


# --- steer_queue tests ---
class TestSteerQueue:
    def test_empty_steer_queue_noop(self):
        """Empty steer queue should not inject anything."""
        session = _make_session()
        client = _text_response("Done.")
        registry = MagicMock()
        registry.schemas = []

        steer = __import__("queue").Queue()
        result = run_tool_loop(session, client, registry, "m", steer_queue=steer)
        assert result == "Done."
        user_msgs = [m for m in session.messages if m.role == "user"]
        assert len(user_msgs) == 0  # No user messages injected by run_tool_loop

    def test_steer_injects_between_rounds(self):
        """Messages in steer_queue should be injected as user messages between tool rounds."""
        session = _make_session()

        tc = MagicMock()
        tc.id = "call_1"
        tc.type = "function"
        tc.function.name = "test_tool"
        tc.function.arguments = "{}"

        choice1 = MagicMock()
        choice1.message.content = None
        choice1.message.tool_calls = [tc]
        choice1.message.role = "assistant"

        choice2 = MagicMock()
        choice2.message.content = "Done."
        choice2.message.tool_calls = None
        choice2.message.role = "assistant"

        resp1 = MagicMock()
        resp1.choices = [choice1]
        resp2 = MagicMock()
        resp2.choices = [choice2]

        client = MagicMock()
        client.chat.completions.create.side_effect = [resp1, resp2]

        registry = MagicMock()
        registry.schemas = [{"type": "function", "function": {"name": "test_tool"}}]
        registry.dispatch.return_value = "ok"

        steer = __import__("queue").Queue()
        steer.put("Please stop using tools and just answer.")

        result = run_tool_loop(session, client, registry, "m", steer_queue=steer)
        assert result == "Done."

        # Verify steer message was injected
        user_msgs = [m for m in session.messages if m.role == "user"]
        steer_msgs = [m for m in user_msgs if m.content == "Please stop using tools and just answer."]
        assert len(steer_msgs) == 1

    def test_multiple_steer_messages(self):
        """Multiple messages in steer_queue should all be injected."""
        session = _make_session()

        tc = MagicMock()
        tc.id = "call_1"
        tc.type = "function"
        tc.function.name = "test_tool"
        tc.function.arguments = "{}"

        choice1 = MagicMock()
        choice1.message.content = None
        choice1.message.tool_calls = [tc]
        choice1.message.role = "assistant"

        choice2 = MagicMock()
        choice2.message.content = "Done."
        choice2.message.tool_calls = None
        choice2.message.role = "assistant"

        resp1 = MagicMock()
        resp1.choices = [choice1]
        resp2 = MagicMock()
        resp2.choices = [choice2]

        client = MagicMock()
        client.chat.completions.create.side_effect = [resp1, resp2]

        registry = MagicMock()
        registry.schemas = [{"type": "function", "function": {"name": "test_tool"}}]
        registry.dispatch.return_value = "ok"

        steer = __import__("queue").Queue()
        steer.put("First steer")
        steer.put("Second steer")

        result = run_tool_loop(session, client, registry, "m", steer_queue=steer)
        assert result == "Done."

        user_msgs = [m for m in session.messages if m.role == "user"]
        steer_msgs = [m for m in user_msgs if m.content in ("First steer", "Second steer")]
        assert len(steer_msgs) == 2


# --- TaskPool.stop_all tests ---
class TestTaskPoolStopAll:
    def test_stop_all_empty_pool(self):
        """stop_all on empty pool returns 0."""
        from libreassistant.task_pool import TaskPool
        pool = TaskPool(MagicMock(), MagicMock(), "m")
        assert pool.stop_all() == 0

    def test_stop_all_sets_stop_event(self):
        """stop_all should set _stop_event on each running task."""
        from libreassistant.task_pool import TaskPool
        pool = TaskPool(MagicMock(), MagicMock(), "m")
        task = MagicMock()
        task.id = "test-1"
        task.status = "running"
        task.future.done.return_value = False
        task._stop_event = threading.Event()
        task._stop_event.clear()
        pool.tasks["test-1"] = task
        pool.stop_all()
        assert task._stop_event.is_set()

    def test_stop_all_returns_count(self):
        """stop_all should return the number of running tasks stopped."""
        from libreassistant.task_pool import TaskPool
        pool = TaskPool(MagicMock(), MagicMock(), "m")
        # Simulate tasks by adding a mock entry
        task = MagicMock()
        task.id = "test-1"
        task.status = "running"
        task.future.done.return_value = False
        pool.tasks["test-1"] = task
        count = pool.stop_all()
        assert count == 1
        assert task.status == "stopped"

    def test_stop_all_marks_completed_tasks_as_not_stopped(self):
        """Completed tasks should not count as stopped."""
        from libreassistant.task_pool import TaskPool
        pool = TaskPool(MagicMock(), MagicMock(), "m")
        task = MagicMock()
        task.id = "test-1"
        task.status = "completed"
        task.future.done.return_value = True
        pool.tasks["test-1"] = task
        count = pool.stop_all()
        assert count == 0
        assert task.status == "completed"
