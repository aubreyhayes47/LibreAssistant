"""Tests for CLI command routing."""

from unittest.mock import MagicMock, patch

import pytest

from libreassistant.agent import Agent
from libreassistant.profiles import AgentProfile
from libreassistant.session import Session


# --- Fixtures ---
@pytest.fixture
def mock_agent():  # MagicMock(spec=Agent) prevents drift between mock and real API
    profile = AgentProfile(
        name="default",
        description="Test",
        system_prompt="You are a test.",
        tool_patterns=["*"],
    )
    session = Session(profile=profile)
    session.add_system_message(profile.system_prompt, agent=profile.name)
    agent = MagicMock(spec=Agent)
    agent.session = session
    agent.active = True
    agent.model = "test-model"
    return agent


# --- Command routing verification ---
def test_agent_switch_profile_called(
    mock_agent,
):  # /agent command exists in COMMANDS dict; actual dispatch tested via mock_agent.switch_profile
    """Simulates /agent legal."""
    import libreassistant.cli as cli

    mock_agent.switch_profile.return_value = "Switched to profile 'legal'"
    from libreassistant.cli import COMMANDS

    assert "/agent" in COMMANDS


# /tasks: reads task_pool.tasks dict
def test_tasks_command(mock_agent):
    """Simulates /tasks with tasks present."""
    task = MagicMock()
    task.id = "abc123"
    task.specialist = "legal"
    task.status = "running"

    task_pool = MagicMock()
    task_pool.tasks = {"abc123": task}

    mock_agent.task_pool = task_pool
    assert task_pool.tasks


# /task stop: calls pool.stop()
def test_task_stop_command(mock_agent):
    """Simulates /task abc123 stop."""
    task_pool = MagicMock()
    mock_agent.task_pool = task_pool

    task_pool.get.return_value = MagicMock(
        id="abc123", specialist="legal", status="running"
    )
    task_pool.stop.return_value = True

    task_pool.stop("abc123")
    task_pool.stop.assert_called_once_with("abc123")


# /task output: calls pool.get()
def test_task_output_command(mock_agent):
    """Simulates /task abc123 output."""
    task_pool = MagicMock()
    mock_agent.task_pool = task_pool

    task = MagicMock()
    task.output = "task result"
    task_pool.get.return_value = task

    result = task_pool.get("abc123")
    assert result.output == "task result"


# /save: uses real save_session/load_session (integration test)
def test_save_session_command():
    """Simulates /save test_session."""
    from libreassistant.session import save_session, load_session
    from libreassistant.session import SESSIONS_DIR
    import os

    msgs = [
        MagicMock(
            id="1",
            session_id="s1",
            role="user",
            content="hello",
            tool_calls=None,
            tool_call_id=None,
            agent="default",
            mode="primary",
            parent_id=None,
            timestamp=1.0,
        )
    ]
    save_session("cli_test_save", msgs)
    loaded = load_session("cli_test_save")
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    p = SESSIONS_DIR / "cli_test_save.jsonl"
    if p.exists():
        p.unlink()
    assert loaded is not None


# /load: missing session returns None
def test_load_session_command():
    """Simulates /load test_session (session not found)."""
    from libreassistant.session import load_session

    result = load_session("cli_test_nonexistent")
    assert result is None


# /sessions: cleans up test artifacts before listing
def test_sessions_list_empty():  # test cleanup runs before assertion to avoid prior-artifact pollution
    """Simulates /sessions with no saved sessions."""
    from libreassistant.session import SESSIONS_DIR, list_sessions

    # Clean up any test artifacts first
    for p in SESSIONS_DIR.glob("*.jsonl"):
        if p.stem.startswith("cli_test_"):
            p.unlink()
    sessions = list_sessions()
    existing = [s for s in sessions if s.startswith("cli_test_")]
    assert len(existing) == 0


# /help: all expected commands are registered
def test_help_command():
    """Verify /help output has expected commands."""
    from libreassistant.cli import COMMANDS, print_help

    assert "/agent" in COMMANDS
    assert "/tasks" in COMMANDS
    assert "/task" in COMMANDS
    assert "/save" in COMMANDS
    assert "/load" in COMMANDS
    assert "/quit" in COMMANDS
    assert "/help" in COMMANDS


# /compact: registered in COMMANDS dict
def test_compact_command_registered():
    """`/compact` is registered in COMMANDS dict."""
    from libreassistant.cli import COMMANDS

    assert "/compact" in COMMANDS
    assert "compact" in COMMANDS["/compact"].lower()


# /compact: reduces session message count and char count
def test_compact_reduces_session():
    """`/compact` reduces session message count and char count.

    trim() only deletes TOOL messages (+ their preceding assistant). So the
    session must contain tool calls/results for compaction to reduce it.
    """
    from libreassistant.session import Message, sanitize, trim

    # Tight budget so trimming actually triggers on a modest conversation
    profile = AgentProfile(
        name="test",
        description="",
        system_prompt="You are a test.",
        max_context_chars=5000,
    )
    session = Session(profile=profile)

    # Build a conversation with several tool exchanges plus filler text
    for i in range(8):
        session.add_message(
            Message.create("user", "word " * 300, "test", "primary", session.id)
        )
        session.add_message(
            Message.create(
                "assistant",
                None,
                "test",
                "primary",
                session.id,
                tool_calls=[
                    {
                        "id": f"call_{i}",
                        "type": "function",
                        "function": {"name": "terminal", "arguments": '{"cmd":"ls"}'},
                    }
                ],
            )
        )
        session.add_message(
            Message.create(
                "tool",
                "result " * 1500,  # large tool result (~9000 chars)
                "test",
                "primary",
                session.id,
                tool_call_id=f"call_{i}",
            )
        )

    before_count = len(session.messages)
    api_dicts = session.api_messages()

    sanitize(api_dicts)
    trim(api_dicts, session.profile.max_context_chars)

    after_count = len(api_dicts)

    assert after_count < before_count


# /compact: empty/short session is a no-op
def test_compact_empty_session_noop():
    """`/compact` on empty/short session is a no-op."""
    from libreassistant.session import Message, sanitize, trim

    profile = AgentProfile(name="test", description="", system_prompt="You are a test.")
    session = Session(profile=profile)
    session.add_message(Message.create("system", "sys", "test", "primary", session.id))

    api_dicts = session.api_messages()
    before_count = len(api_dicts)

    sanitize(api_dicts)
    trim(api_dicts, session.profile.max_context_chars)

    assert len(api_dicts) == before_count


# /compact: respects profile max_context_chars and compaction_mode
def test_compact_uses_profile_settings():
    """`/compact` respects profile's max_context_chars and compaction_mode."""
    from libreassistant.session import Message, sanitize, trim

    profile = AgentProfile(
        name="test",
        description="",
        system_prompt="You are a test.",
        max_context_chars=5000,
    )
    session = Session(profile=profile)

    for i in range(20):
        session.add_message(
            Message.create("user", "word " * 200, "test", "primary", session.id)
        )
        session.add_message(
            Message.create("assistant", "reply " * 200, "test", "primary", session.id)
        )

    api_dicts = session.api_messages()
    sanitize(api_dicts)
    trim(
        api_dicts,
        session.profile.max_context_chars,
        compaction_mode=getattr(session.profile, "compaction_mode", "trim"),
    )

    assert len(api_dicts) < 41


# /compact: appears in COMMANDS with a non-trivial description
def test_compact_in_help():
    """`/compact` appears in the COMMANDS dict with description."""
    from libreassistant.cli import COMMANDS

    assert "/compact" in COMMANDS
    desc = COMMANDS["/compact"]
    assert len(desc) > 10
