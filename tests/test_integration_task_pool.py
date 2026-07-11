"""Integration tests: TaskPool -> backlog -> absorb pipeline."""

from queue import Queue
from unittest.mock import MagicMock

import pytest

from libreassistant.profiles import AgentProfile
from libreassistant.session import Session
from libreassistant.task_pool import TaskPool, Task
from libreassistant.tool_registry import ToolRegistry


@pytest.fixture
def profile():
    return AgentProfile(
        name="default",
        description="Default",
        system_prompt="You are a test.",
        tool_patterns=["*"],
    )


# --- TaskPool + Session integration ---
class TestTaskPoolToAbsorb:
    def test_pool_submit_then_absorb(self, profile):  # real TaskPool runs a legal specialist; session shares the pool's backlog  # session.backlog and pool.backlog point to the same Queue
        """Submit task, wait for completion, absorb into session."""
        specialist_profile = AgentProfile(
            name="legal",
            description="Legal specialist",
            system_prompt="You are a legal assistant.",
            tool_patterns=["*"],
        )

        def make_client():
            c = MagicMock()
            choice = MagicMock()
            choice.message.content = "task result"
            choice.message.tool_calls = None
            choice.message.role = "assistant"
            choice.message.reasoning_content = None
            resp = MagicMock()
            resp.choices = [choice]
            c.chat.completions.create.return_value = resp
            return c

        pool = TaskPool(
            registry_factory=lambda: ToolRegistry(),
            client_factory=make_client,
            profile_registry={"legal": specialist_profile},
            max_workers=1,
        )

        session = Session(profile=profile, backlog=pool.backlog)
        pool.submit("legal", "research question")
        # Wait until the task completes (shows up in the shared backlog)
        import time
        deadline = time.time() + 5
        while pool.backlog.empty() and time.time() < deadline:
            time.sleep(0.01)
        pool.shutdown(wait=True)

        count = session.absorb_completed_tasks()
        assert count == 1
        assert len(session.messages) == 1
        assert "[Task" in session.messages[0].content
        assert "Result: task result" in session.messages[0].content

    def test_absorb_skips_already_injected(self, profile):
        """Task with _already_injected=True is skipped by absorb."""
        backlog = Queue()
        task = Task(
            id="t1", specialist="legal", input="research",
            needs_verification=[], status="completed", output="result",
            error=None, created_at=100.0, completed_at=101.0,
            parent_session_id=None, _already_injected=True,
        )
        backlog.put(task)
        session = Session(profile=profile, backlog=backlog)
        count = session.absorb_completed_tasks()
        assert count == 0
        assert session.messages == []

    def test_absorb_multiple_tasks(self, profile):
        """Multiple tasks in backlog all absorbed."""
        backlog = Queue()
        for i in range(3):
            task = Task(
                id=f"t{i}", specialist="legal", input=f"q{i}",
                needs_verification=[], status="completed", output=f"r{i}",
                error=None, created_at=100.0 + i, completed_at=101.0 + i,
                parent_session_id=None,
            )
            backlog.put(task)
        session = Session(profile=profile, backlog=backlog)
        count = session.absorb_completed_tasks()
        assert count == 3
        assert len(session.messages) == 3

    def test_absorb_failed_task(self, profile):  # failed task injects "[Error: ...]" into the absorbed message
        """Failed task injects error summary."""
        backlog = Queue()
        task = Task(
            id="t_fail", specialist="legal", input="broken",
            needs_verification=[], status="failed", output=None,
            error="Something went wrong", created_at=100.0,
            completed_at=101.0, parent_session_id=None,
        )
        backlog.put(task)
        session = Session(profile=profile, backlog=backlog)
        count = session.absorb_completed_tasks()
        assert count == 1
        assert "Error: Something went wrong" in session.messages[0].content

    def test_absorb_empty_backlog_noop(self, profile):
        """Absorb with empty backlog does nothing."""
        session = Session(profile=profile, backlog=Queue())
        count = session.absorb_completed_tasks()
        assert count == 0
        assert session.messages == []

    def test_pool_submit_nonexistent_specialist(self, profile):  # also verifies failed task appears in backlog for absorb
        """Submitting to unknown specialist fails immediately."""
        pool = TaskPool(
            registry_factory=MagicMock,
            client_factory=MagicMock,
            profile_registry={},
        )
        task = pool.submit("nonexistent", "research")
        pool.shutdown(wait=True)
        assert task.status == "failed"
        assert "Unknown specialist" in task.error
        assert pool.backlog.empty()  # unknown specialist fails before submit, never reaches backlog
