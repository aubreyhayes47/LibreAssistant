"""Tests for session.py: Message, Session, sanitize, trim, absorb, and persistence."""

import json
import os
import tempfile
from queue import Queue
from unittest.mock import MagicMock

import pytest

from libreassistant.profiles import AgentProfile
from libreassistant.session import (
    Message,
    Session,
    auto_load,
    auto_save,
    delete_session,
    is_valid_session_name,
    list_sessions,
    load_session,
    sanitize,
    save_session,
    trim,
)


# --- Fixtures ---
@pytest.fixture
def profile() -> AgentProfile:
    return AgentProfile(
        name="test",
        description="Test profile",
        system_prompt="You are a test.",
    )


@pytest.fixture
def session(
    profile: AgentProfile,
) -> Session:  # session created with profile but no messages yet
    return Session(profile=profile)


# --- Message construction and API conversion ---
class TestMessage:
    def test_message_create(self) -> None:
        msg = Message.create(
            role="user",
            content="hello",
            agent="default",
            mode="primary",
            session_id="s1",
        )
        assert msg.id
        assert isinstance(msg.id, str)
        assert msg.timestamp > 0
        assert msg.role == "user"
        assert msg.content == "hello"
        assert msg.agent == "default"
        assert msg.mode == "primary"
        assert msg.session_id == "s1"
        assert msg.tool_calls is None
        assert msg.tool_call_id is None
        assert msg.parent_id is None

    def test_message_from_api_no_tools(
        self,
    ) -> None:  # simulates API response object wrapping
        mock_msg = MagicMock()
        mock_msg.role = "assistant"
        mock_msg.content = "hello"
        mock_msg.tool_calls = None

        msg = Message.from_api_msg(
            mock_msg, agent="default", mode="primary", session_id="s1"
        )
        assert msg.content == "hello"
        assert msg.tool_calls is None
        assert msg.role == "assistant"

    def test_message_from_api_with_tools(
        self,
    ) -> None:  # simulates API response object wrapping
        tc_mock = MagicMock()
        tc_mock.id = "call_123"
        tc_mock.type = "function"
        tc_mock.function.name = "get_weather"
        tc_mock.function.arguments = '{"city": "London"}'

        mock_msg = MagicMock()
        mock_msg.role = "assistant"
        mock_msg.content = None
        mock_msg.tool_calls = [tc_mock]

        msg = Message.from_api_msg(
            mock_msg, agent="default", mode="primary", session_id="s1"
        )
        assert isinstance(msg.tool_calls, list)
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0]["id"] == "call_123"
        assert msg.tool_calls[0]["type"] == "function"
        assert msg.tool_calls[0]["function"]["name"] == "get_weather"
        assert msg.tool_calls[0]["function"]["arguments"] == '{"city": "London"}'

    # reasoning_content and refusal must be discarded to prevent 400 errors
    def test_message_from_api_reasoning_discarded(self) -> None:
        mock_msg = MagicMock()
        mock_msg.role = "assistant"
        mock_msg.content = "final answer"
        mock_msg.tool_calls = None
        mock_msg.reasoning_content = "thinking..."
        mock_msg.refusal = "refused"

        msg = Message.from_api_msg(
            mock_msg, agent="default", mode="primary", session_id="s1"
        )
        assert hasattr(msg, "reasoning_content") is False
        assert hasattr(msg, "refusal") is False

    # only role+content survive; internal routing fields stripped
    def test_message_to_api_dict_strips_internals(self) -> None:
        msg = Message(
            id="abc123",
            session_id="s1",
            role="user",
            content="hi",
            tool_calls=None,
            tool_call_id=None,
            agent="default",
            mode="primary",
            parent_id="p1",
            timestamp=12345.0,
        )
        d = msg.to_api_dict()
        expected = {"role": "user", "content": "hi"}
        assert d == expected
        assert "agent" not in d
        assert "mode" not in d
        assert "id" not in d
        assert "session_id" not in d
        assert "parent_id" not in d
        assert "timestamp" not in d

    # None content is normalized to empty string for API safety
    def test_message_to_api_dict_none_content(self) -> None:
        msg = Message(
            id="x",
            session_id="s1",
            role="assistant",
            content=None,
            tool_calls=None,
            tool_call_id=None,
            agent="default",
            mode="primary",
            parent_id=None,
            timestamp=0.0,
        )
        d = msg.to_api_dict()
        assert d["content"] == ""


# --- Session lifecycle ---
class TestSession:
    def test_session_init(
        self, profile: AgentProfile
    ) -> None:  # uuid4 hex[:12] gives a short, unique session id
        s = Session(profile=profile)
        assert s.messages == []
        assert isinstance(s.backlog, Queue)
        assert s.id
        assert isinstance(s.id, str)
        assert len(s.id) == 12  # uuid4 hex[:12]
        assert s.parent_session_id is None
        assert s.auto_save_enabled is True
        assert s.created_at > 0
        assert s.updated_at > 0
        assert s.history_file is None

    def test_session_add_message(
        self, session: Session
    ) -> None:  # messages list grows; no dedup or ordering sort applied
        msg = Message.create(
            role="user",
            content="hello",
            agent="test",
            mode="primary",
            session_id=session.id,
        )
        session.add_message(msg)
        assert len(session.messages) == 1
        assert session.messages[0] is msg

    def test_session_add_system_message(self, session: Session) -> None:
        msg = session.add_system_message("hello", "system")
        assert msg.role == "system"
        assert msg.content == "hello"
        assert len(session.messages) == 1

    def test_session_api_messages(
        self, session: Session
    ) -> None:  # api_messages() strips internals via to_api_dict()
        msg = Message.create(
            role="user",
            content="hi",
            agent="test",
            mode="primary",
            session_id=session.id,
        )
        session.add_message(msg)
        result = session.api_messages()
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "hi"


# --- sanitize() --- strip reasoning_content/refusal/usage before API call ---
class TestSanitize:
    def test_sanitize_removes_reasoning(self) -> None:
        d = {
            "role": "assistant",
            "content": "hi",
            "reasoning_content": "thinking",
            "refusal": "no",
            "usage": {},
        }
        sanitize([d])
        assert "reasoning_content" not in d
        assert "refusal" not in d
        assert "usage" not in d
        assert d["role"] == "assistant"
        assert d["content"] == "hi"

    def test_sanitize_handles_none_content(
        self,
    ) -> None:  # None -> "" prevents API rejection of null content
        d = {"role": "assistant", "content": None}
        sanitize([d])
        assert d["content"] == ""

    # no-op for user messages (no reasoning fields to strip)
    def test_sanitize_noop(self) -> None:
        d = {"role": "user", "content": "hi"}
        sanitize([d])
        assert d == {"role": "user", "content": "hi"}

    # structured content arrays (text parts with reasoning) must be cleaned recursively
    def test_sanitize_content_list_strips_reasoning(self) -> None:
        d = {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "hello"},
                {"type": "text", "text": "world", "reasoning_content": "thinking"},
            ],
        }
        sanitize([d])
        for part in d["content"]:
            assert "reasoning_content" not in part

    # tool_calls can carry reasoning_content at the call level
    def test_sanitize_tool_calls_strips_reasoning(self) -> None:
        d = {
            "role": "assistant",
            "content": "hi",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "test", "arguments": "{}"},
                    "reasoning_content": "thinking about calling test",
                }
            ],
        }
        sanitize([d])
        for tc in d["tool_calls"]:
            assert "reasoning_content" not in tc


# --- trim() --- budget enforcement to prevent 400 errors ---
class TestTrim:
    def test_trim_under_budget(
        self,
    ) -> None:  # short messages stay untouched; budget is generous
        d = [{"role": "user", "content": "short"}]
        orig = list(d)
        trim(d, max_chars=100000)
        assert d == orig

    def test_trim_preserves_system(
        self,
    ) -> None:  # system prompt at index 0 is always preserved (mandatory for routing)
        d = [
            {"role": "system", "content": "You are a bot."},
            {"role": "user", "content": "x" * 5000},
            {"role": "tool", "content": "y" * 5000},
            {"role": "tool", "content": "z" * 5000},
            {"role": "tool", "content": "w" * 5000},
        ]
        trim(d, max_chars=1000)
        assert len(d) >= 1
        assert d[0]["role"] == "system"

    def test_trim_prunes_tool_results_phase2(self) -> None:
        """Oversized unprotected tool results (>5000 chars) are pruned to a stub."""
        d = [
            {"role": "system", "content": "You are a bot."},
            {"role": "user", "content": "hello"},
            {
                "role": "assistant",
                "content": "let me check",
                "tool_calls": [
                    {
                        "id": "c1",
                        "type": "function",
                        "function": {"name": "f", "arguments": "{}"},
                    }
                ],
            },
            {
                "role": "tool",
                "content": "x" * 6000,
                "tool_call_id": "c1",
            },  # index 3, unprotected, >5000
            {"role": "user", "content": "a"},
            {"role": "user", "content": "b"},
            {"role": "user", "content": "c"},
            {"role": "user", "content": "d"},
            {"role": "user", "content": "e"},
            {"role": "user", "content": "f"},
            {"role": "user", "content": "g"},
            {"role": "user", "content": "h"},
            {"role": "user", "content": "i"},
            {"role": "tool", "content": "y" * 30000},  # index 13, fills protected tail
        ]
        # n=14, recency_zone=6 → last 6 (indices 8-13) protected; index 3 is not.
        # Total ≈ 36042. With max_chars=37000 → effective_budget = 37000 - max(2000, 1850) = 35000.
        # 36042 > 35000 → trimming triggers; index 3 (6000 chars) gets pruned.
        trim(d, max_chars=37000)
        tool_content = d[3]["content"]
        assert tool_content.startswith("[pruned")

    def test_trim_drops_tool_messages_phase3(self) -> None:
        d = [
            {"role": "system", "content": "You are a bot."},
            {"role": "user", "content": "hello"},
            {"role": "tool", "content": "x" * 200},
        ]
        trim(d, max_chars=50)
        assert len(d) >= 1
        assert d[0]["role"] == "system"

    def test_trim_never_drops_system_prompt(self) -> None:
        d = [
            {"role": "system", "content": "x" * 5000},
            {"role": "tool", "content": "y" * 5000},
            {"role": "user", "content": "a"},
            {"role": "user", "content": "b"},
            {"role": "user", "content": "c"},
            {"role": "tool", "content": "z" * 30000},
        ]
        trim(d, max_chars=100)
        assert d[0]["role"] == "system"


# --- absorb_completed_tasks() --- drain TaskPool backlog into messages ---
class TestAbsorb:
    def test_absorb_completed_tasks_empty(
        self, session: Session
    ) -> None:  # no backlog -> no-op, returns 0
        result = session.absorb_completed_tasks()
        assert result == 0
        assert session.messages == []

    def test_absorb_completed_tasks_with_task(
        self, session: Session
    ) -> None:  # each completed task becomes a system-style message with result summary
        from libreassistant.task_pool import Task, VerificationItem

        task = Task(
            id="task_1",
            specialist="legal",
            input="research",
            needs_verification=[],
            status="completed",
            output="result data",
            error=None,
            created_at=100.0,
            completed_at=101.0,
            parent_session_id=None,
        )
        session.backlog.put(task)
        result = session.absorb_completed_tasks()
        assert result == 1
        assert len(session.messages) == 1
        assert "[Task task_1" in session.messages[0].content
        assert "Result: result data" in session.messages[0].content

    # _already_injected flag prevents duplicate absorption on retry
    def test_absorb_completed_tasks_skips_already_injected(
        self, session: Session
    ) -> None:
        from libreassistant.task_pool import Task

        task = Task(
            id="task_1",
            specialist="legal",
            input="research",
            needs_verification=[],
            status="completed",
            output="result data",
            error=None,
            created_at=100.0,
            completed_at=101.0,
            parent_session_id=None,
            _already_injected=True,
        )
        session.backlog.put(task)
        result = session.absorb_completed_tasks()
        assert result == 0
        assert session.messages == []

    def test_absorb_completed_tasks_multiple(
        self, session: Session
    ) -> None:  # backlog drained in FIFO order; each task becomes one message
        from libreassistant.task_pool import Task

        for i in range(3):
            task = Task(
                id=f"task_{i}",
                specialist="legal",
                input=f"research {i}",
                needs_verification=[],
                status="completed",
                output=f"result {i}",
                error=None,
                created_at=100.0 + i,
                completed_at=101.0 + i,
                parent_session_id=None,
            )
            session.backlog.put(task)
        result = session.absorb_completed_tasks()
        assert result == 3
        assert len(session.messages) == 3


# --- Persistence: save/load/auto-save ---
class TestSessionPersistence:
    def test_save_load_roundtrip(
        self, profile: AgentProfile
    ) -> None:  # round-trip: save to temp file, load back, compare
        import tempfile, os

        s = Session(profile=profile)
        s.add_system_message("hello", "test")
        msg = Message.create(
            role="user", content="hi", agent="test", mode="primary", session_id=s.id
        )
        s.add_message(msg)
        tmp = os.path.join(
            tempfile.gettempdir(), "test_session_" + str(id(s)) + ".jsonl"
        )
        try:
            s.save(tmp)
            loaded = Session.load(tmp, profile)
            assert len(loaded.messages) == 2
            assert loaded.messages[0].content == "hello"
            assert loaded.messages[0].role == "system"
            assert loaded.messages[1].content == "hi"
            assert loaded.messages[1].role == "user"
        finally:
            os.unlink(tmp)

    def test_save_load_empty(
        self, profile: AgentProfile
    ) -> None:  # empty session save/load returns empty messages list
        import tempfile, os

        s = Session(profile=profile)
        tmp = os.path.join(
            tempfile.gettempdir(), "test_session_empty_" + str(id(s)) + ".jsonl"
        )
        try:
            s.save(tmp)
            loaded = Session.load(tmp, profile)
            assert len(loaded.messages) == 0
        finally:
            os.unlink(tmp)

    def test_load_nonexistent(
        self, profile: AgentProfile
    ) -> None:  # missing file returns empty session (not an error)
        loaded = Session.load("/tmp/nonexistent_file_xyz.jsonl", profile)
        assert len(loaded.messages) == 0
        assert loaded.profile.name == "test"

    # backward compat: old format (plain JSON dict, no Message fields) still loads
    def test_load_backward_compat(self, profile: AgentProfile) -> None:
        import tempfile, os, json

        old_format_data = json.dumps(
            {
                "role": "user",
                "content": "hello",
            }
        )
        tmp = os.path.join(
            tempfile.gettempdir(), "test_backward_" + str(id(profile)) + ".jsonl"
        )
        try:
            with open(tmp, "w") as f:
                f.write(old_format_data + "\n")
            loaded = Session.load(tmp, profile)
            assert len(loaded.messages) == 1
            msg = loaded.messages[0]
            assert msg.role == "user"
            assert msg.content == "hello"
            assert msg.agent == "default"
            assert msg.mode == "primary"
            assert msg.parent_id is None
            assert msg.tool_call_id is None
            assert msg.tool_calls is None
        finally:
            os.unlink(tmp)

    # auto_save_enabled=False prevents writes to the shared auto-save path
    def test_auto_save_disabled(self, profile: AgentProfile) -> None:
        import tempfile, os
        from libreassistant.session import AUTO_SESSION_PATH

        old_content = None
        if AUTO_SESSION_PATH.exists():
            old_content = AUTO_SESSION_PATH.read_bytes()
            AUTO_SESSION_PATH.unlink()
        try:
            s = Session(profile=profile)
            s.auto_save_enabled = False
            s.add_system_message("hello", "test")
            s.auto_save()
            assert not AUTO_SESSION_PATH.exists()
        finally:
            if old_content is not None:
                AUTO_SESSION_PATH.write_bytes(old_content)

    # auto_save skips when only 0-1 messages (too early to persist)
    def test_auto_save_skips_few_messages(self, profile: AgentProfile) -> None:
        import tempfile, os
        from libreassistant.session import AUTO_SESSION_PATH

        old_content = None
        if AUTO_SESSION_PATH.exists():
            old_content = AUTO_SESSION_PATH.read_bytes()
            AUTO_SESSION_PATH.unlink()
        try:
            s = Session(profile=profile)
            s.auto_save()
            assert not AUTO_SESSION_PATH.exists()
        finally:
            if old_content is not None:
                AUTO_SESSION_PATH.write_bytes(old_content)

    # is_valid_session_name: security gate against path traversal
    def test_is_valid_session_name(self) -> None:
        assert is_valid_session_name("hello") is True
        assert is_valid_session_name("my_session_123") is True
        assert is_valid_session_name("") is False
        assert is_valid_session_name("../foo") is False
        assert is_valid_session_name("path/with/slashes") is False
        assert is_valid_session_name("no spaces") is False

    # list_sessions: scans SESSIONS_DIR for .jsonl files
    def test_list_sessions(self) -> None:
        from libreassistant.session import SESSIONS_DIR
        import tempfile, os

        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        for name in ["test_a", "test_b"]:
            (SESSIONS_DIR / f"{name}.jsonl").write_text(
                '{"role":"user","content":"hi"}\n'
            )
        try:
            sessions = list_sessions()
            assert "test_a" in sessions
            assert "test_b" in sessions
        finally:
            for name in ["test_a", "test_b"]:
                p = SESSIONS_DIR / f"{name}.jsonl"
                if p.exists():
                    p.unlink()

    # delete_session: removes session file, returns success bool
    def test_delete_session(self) -> None:
        from libreassistant.session import SESSIONS_DIR

        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        p = SESSIONS_DIR / "test_delete.jsonl"
        p.write_text('{"role":"user","content":"hi"}\n')
        assert delete_session("test_delete") is True
        assert not p.exists()
        assert delete_session("nonexistent") is False

    # save_session/load_session: module-level convenience wrappers
    def test_save_load_session_functions(self, profile: AgentProfile) -> None:
        from libreassistant.session import SESSIONS_DIR
        import os

        name = "test_func_" + str(id(profile))
        msgs = [
            Message.create(
                role="user",
                content="hello",
                agent="test",
                mode="primary",
                session_id="s1",
            ),
            Message.create(
                role="assistant",
                content="world",
                agent="test",
                mode="primary",
                session_id="s1",
            ),
        ]
        try:
            save_session(name, msgs)
            loaded = load_session(name)
            assert loaded is not None
            assert len(loaded) == 2
            assert loaded[0].content == "hello"
            assert loaded[1].content == "world"
        finally:
            p = SESSIONS_DIR / (name + ".jsonl")
            if p.exists():
                p.unlink()

    def test_load_session_nonexistent(
        self,
    ) -> None:  # missing session -> None (no exception)
        result = load_session("definitely_does_not_exist_xyz")
        assert result is None

    # auto_save/auto_load: module-level wrappers for the shared session file
    def test_auto_save_load_module_functions(self) -> None:
        from libreassistant.session import AUTO_SESSION_PATH, auto_save, auto_load
        import os, json

        old_content = None
        if AUTO_SESSION_PATH.exists():
            old_content = AUTO_SESSION_PATH.read_bytes()
            AUTO_SESSION_PATH.unlink()
        try:
            msgs = [
                Message.create(
                    role="user",
                    content="auto test",
                    agent="test",
                    mode="primary",
                    session_id="s_auto",
                ),
            ]
            auto_save(msgs)
            assert not AUTO_SESSION_PATH.exists()
            msgs.append(
                Message.create(
                    role="assistant",
                    content="response",
                    agent="test",
                    mode="primary",
                    session_id="s_auto",
                )
            )
            auto_save(msgs)
            loaded = auto_load()
            assert loaded is not None
            assert len(loaded) == 2
            assert loaded[0]["content"] == "auto test"
            assert loaded[1]["content"] == "response"
        finally:
            if old_content is not None:
                AUTO_SESSION_PATH.write_bytes(old_content)
            elif AUTO_SESSION_PATH.exists():
                AUTO_SESSION_PATH.unlink()


# --- Security edge cases ---
class TestSecurity:
    # recursive reasoning_content stripping in content array parts
    def test_sanitize_strips_reasoning_from_content_array_parts(self):
        d = {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "part1", "reasoning_content": "hidden1"},
                {"type": "text", "text": "part2"},
                {"type": "tool_use", "reasoning_content": "hidden2"},
            ],
        }
        sanitize([d])
        for part in d["content"]:
            assert "reasoning_content" not in part

    # recursive reasoning_content stripping in tool_call items
    def test_sanitize_strips_reasoning_from_tool_call_items(self):
        d = {
            "role": "assistant",
            "content": "response",
            "tool_calls": [
                {
                    "id": "c1",
                    "type": "function",
                    "function": {"name": "a", "arguments": "{}"},
                    "reasoning_content": "think1",
                },
                {
                    "id": "c2",
                    "type": "function",
                    "function": {"name": "b", "arguments": "{}"},
                    "reasoning_content": "think2",
                },
            ],
        }
        sanitize([d])
        for tc in d["tool_calls"]:
            assert "reasoning_content" not in tc

    # trim survives extreme conditions: massive system prompt + tiny budget
    def test_trim_never_drops_system_under_extreme_budget(self):
        d = [
            {"role": "system", "content": "You are a helpful assistant. " * 100},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
            {"role": "user", "content": "do something"},
            {"role": "tool", "content": "x" * 5000},
            {"role": "tool", "content": "y" * 5000},
        ]
        trim(d, max_chars=100)
        assert d[0]["role"] == "system"

    # system-only messages are never dropped, even when they exceed budget
    def test_trim_system_preserved_when_only_message(self):
        d = [{"role": "system", "content": "You are a bot. " * 200}]
        trim(d, max_chars=100)
        assert len(d) == 1
        assert d[0]["role"] == "system"

    # sanitize removes only reasoning_content/refusal/usage; all other fields survive
    def test_sanitize_preserves_other_fields(self):
        d = {
            "role": "user",
            "content": "hello",
            "reasoning_content": "thinking",
            "custom_field": "should_stay",
        }
        sanitize([d])
        assert "reasoning_content" not in d
        assert d["custom_field"] == "should_stay"
        assert d["role"] == "user"
        assert d["content"] == "hello"
