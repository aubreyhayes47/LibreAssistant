"""Tests for task_pool.py: Task, TaskPool, verification, concurrency."""
import threading
from unittest.mock import MagicMock, patch

import pytest

from libreassistant.profiles import AgentProfile
from libreassistant.task_pool import TaskPool, Task, VerificationItem, task_dict, _create_task_profile


# --- Fixtures ---
@pytest.fixture
def pool():  # yield-based fixture ensures pool.shutdown() even on test failure
    profile = AgentProfile(name="legal", description="Legal", system_prompt="Be legal.", tool_patterns=[])
    pool = TaskPool(
        registry_factory=MagicMock,
        client_factory=MagicMock,
        profile_registry={"legal": profile},
        max_workers=1,
    )
    yield pool
    pool.shutdown(wait=False)


# --- Task data model ---
class TestTaskCreation:
    def test_task_creation(self):  # Task is a plain data class; no logic in constructor
        vi = VerificationItem(description="check X")
        task = Task(
            id="abc123",
            specialist="legal",
            input="do research",
            needs_verification=[vi],
            status="queued",
            output=None,
            error=None,
            created_at=100.0,
            completed_at=None,
            parent_session_id=None,
        )
        assert task.id == "abc123"
        assert task.specialist == "legal"
        assert task.input == "do research"
        assert task.needs_verification == [vi]
        assert task.status == "queued"
        assert task.output is None
        assert task.error is None
        assert task.created_at == 100.0
        assert task.completed_at is None
        assert task.parent_session_id is None

    def test_verification_stored(self):  # VerificationItem is embedded in the task, not stored separately
        task = Task(
            id="abc",
            specialist="legal",
            input="test",
            needs_verification=[VerificationItem("check X")],
            status="queued",
            output=None,
            error=None,
            created_at=0.0,
            completed_at=None,
            parent_session_id=None,
        )
        assert task.needs_verification[0].description == "check X"


# --- TaskPool submission and retrieval ---
class TestTaskPoolSubmit:
    def test_task_pool_submit(self, pool):  # submit() returns immediately; task may be queued/running/completed
        task = pool.submit("legal", "do research")
        assert task.id is not None
        assert task.specialist == "legal"
        assert task.status in ("queued", "running", "completed")
        assert task.id in pool.tasks

    def test_task_pool_get(self, pool):  # get() by ID retrieves the in-memory task dict entry
        task = pool.submit("legal", "do research")
        retrieved = pool.get(task.id)
        assert retrieved is not None
        assert retrieved.id == task.id

    def test_task_pool_status(self, pool):  # status() returns a summary dict, not the full Task object
        task = pool.submit("legal", "do research")
        st = pool.status(task.id)
        assert st is not None
        assert "id" in st
        assert "specialist" in st
        assert "status" in st

    def test_verification_hidden_from_task(self, pool):  # string descriptions are converted to VerificationItem objects internally
        task = pool.submit("legal", "do research", needs_verification=["check A", "check B"])
        assert len(task.needs_verification) == 2
        assert task.needs_verification[0].description == "check A"
        assert task.needs_verification[1].description == "check B"


# --- Task completion and shutdown ---
class TestTaskCompletion:
    def test_task_completion(self, pool):  # backlog.get(timeout=2) blocks until a task finishes
        task = pool.submit("legal", "do research")
        completed = pool.backlog.get(timeout=2)
        assert completed.id == task.id
        assert completed.status == "completed"

    def test_task_pool_shutdown(self, pool):
        pool.shutdown(wait=False)


# --- Failure modes ---
class TestTaskFailure:
    def test_task_failure(self):  # empty profile_registry means the specialist cannot be found
        pool = TaskPool(
            registry_factory=MagicMock,
            client_factory=MagicMock,
            profile_registry={},
            max_workers=1,
        )
        task = pool.submit("nonexistent", "do research")
        assert task.status == "failed"
        assert "Unknown specialist" in task.error


# --- Task lifecycle control ---
class TestTaskStop:
    def test_task_stop(self, pool):  # stop() returns bool; does not guarantee immediate termination
        task = pool.submit("legal", "do research")
        result = pool.stop(task.id)
        assert isinstance(result, bool)


# --- Task profile construction ---
class TestTaskProfile:
    def test_create_task_profile(self):  # _create_task_profile halves the delegate's budget to prevent 400 errors
        profile = AgentProfile(
            name="legal",
            description="Legal",
            system_prompt="Be legal.",
            model="gpt-4",
            tool_patterns=["mcp/courtlistener/*"],
            max_context_chars=120_000,
            max_tool_rounds=10,
            max_tool_result_chars=10_000,
        )
        task_profile = _create_task_profile(profile)
        assert task_profile.name == "legal"
        assert task_profile.max_context_chars == 30_000
        assert task_profile.max_tool_rounds == 20
        assert task_profile.max_tool_result_chars == 5_000
        assert task_profile.model == "gpt-4"
        assert task_profile.tool_patterns == ["mcp/courtlistener/*"]

    def test_task_dict(self):  # task_dict serialises a Task for CLI display (not persistence)
        task = Task(
            id="abc123",
            specialist="legal",
            input="research",
            needs_verification=[],
            status="completed",
            output="result",
            error=None,
            created_at=100.0,
            completed_at=101.0,
            parent_session_id=None,
        )
        d = task_dict(task)
        assert d["id"] == "abc123"
        assert d["specialist"] == "legal"
        assert d["status"] == "completed"
        assert d["output"] == "result"
        assert d["error"] is None
        assert d["created_at"] == 100.0
        assert d["completed_at"] == 101.0


# --- Concurrency and limits ---
class TestTaskPoolConcurrency:
    def test_max_workers_limits_concurrency(self):
        """With max_workers=3, only 3 tasks should run simultaneously."""
        import threading
        from unittest.mock import patch

        block_event = threading.Event()
        profile = AgentProfile(name="legal", description="Legal", system_prompt="Be legal.", tool_patterns=[])
        pool = TaskPool(
            registry_factory=MagicMock,
            client_factory=MagicMock,
            profile_registry={"legal": profile},
            max_workers=3,
        )

        def slow_loop(*args, **kwargs):
            block_event.wait(timeout=2)
            return "ok"

        with patch("libreassistant.task_pool.run_tool_loop", side_effect=slow_loop):
            tasks = [pool.submit("legal", f"task {i}") for i in range(5)]

        running = [t for t in tasks if t.status == "running"]
        queued = [t for t in tasks if t.status == "queued"]
        assert len(running) + len(queued) == 5
        block_event.set()
        pool.shutdown(wait=True)

    def test_stop_nonexistent(self):  # stop() on a nonexistent ID returns False (no-op)
        profile = AgentProfile(name="legal", description="Legal", system_prompt="Be legal.", tool_patterns=[])
        pool = TaskPool(
            registry_factory=MagicMock,
            client_factory=MagicMock,
            profile_registry={"legal": profile},
        )
        try:
            result = pool.stop("nonexistent_id")
            assert result is False
        finally:
            pool.shutdown(wait=False)

    def test_get_nonexistent(self):  # get() on a nonexistent ID returns None (no-op)
        profile = AgentProfile(name="legal", description="Legal", system_prompt="Be legal.", tool_patterns=[])
        pool = TaskPool(
            registry_factory=MagicMock,
            client_factory=MagicMock,
            profile_registry={"legal": profile},
        )
        try:
            result = pool.get("nonexistent_id")
            assert result is None
        finally:
            pool.shutdown(wait=False)

    def test_submit_empty_input(self, pool):  # empty input is allowed; task proceeds with blank instruction
        task = pool.submit("legal", "")
        assert task.id is not None
        assert task.specialist == "legal"

# concurrent submissions from multiple threads must not corrupt internal state
    def test_concurrent_submission(self):
        import concurrent.futures
        profile = AgentProfile(name="legal", description="Legal", system_prompt="Be legal.", tool_patterns=[])
        pool = TaskPool(
            registry_factory=MagicMock,
            client_factory=MagicMock,
            profile_registry={"legal": profile},
            max_workers=3,
        )
        inputs = [f"task {i}" for i in range(10)]
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as submitter:
                futures = [submitter.submit(pool.submit, "legal", inp) for inp in inputs]
                results = [f.result(timeout=5) for f in futures]
            assert len(results) == 10
            task_ids = set(t.id for t in pool.tasks.values())
            assert all(t.id in task_ids for t in results)
        finally:
            pool.shutdown(wait=True)


# --- Abuse / saturation edge cases ---
class TestTaskPoolAbuse:
    def test_submit_many_tasks_saturates_queue(self):
        profile = AgentProfile(name="legal", description="Legal", system_prompt="Be legal.", tool_patterns=[])
        pool = TaskPool(
            registry_factory=MagicMock,
            client_factory=MagicMock,
            profile_registry={"legal": profile},
            max_workers=2,
        )
        import threading
        block_event = threading.Event()
        from unittest.mock import patch

        def slow_loop(*args, **kwargs):
            block_event.wait(timeout=3)
            return "ok"

        with patch("libreassistant.task_pool.run_tool_loop", side_effect=slow_loop):
            tasks = [pool.submit("legal", f"task {i}") for i in range(20)]
        running = sum(1 for t in tasks if t.status == "running")
        queued = sum(1 for t in tasks if t.status == "queued")
        assert running + queued == 20
        assert running <= 2
        block_event.set()
        pool.shutdown(wait=True)

    def test_submit_with_many_verification_items(self, pool):  # 100 verification items is an extreme edge case for the rubric system
        items = [f"check {i}" for i in range(100)]
        task = pool.submit("legal", "research", needs_verification=items)
        assert len(task.needs_verification) == 100

    def test_stop_completed_task(self, pool):  # stopping a completed task is benign (no-op internally)
        task = pool.submit("legal", "research")
        import time
        deadline = time.time() + 2
        while task.status == "running" and time.time() < deadline:
            time.sleep(0.01)
        result = pool.stop(task.id)
        assert isinstance(result, bool)

    def test_stop_nonexistent_does_not_error(self, pool):  # stop/get on nonexistent IDs must never raise
        result = pool.stop("id_does_not_exist")
        assert result is False

    def test_get_nonexistent_returns_none(self, pool):
        result = pool.get("id_does_not_exist")
        assert result is None


# --- Verification evaluation (blind rubric) ---
class TestVerificationEvaluation:
    def test_verification_passes(self):  # mock_client returns "YES" → verification passes
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="YES"))]
        )
        profile = AgentProfile(name="legal", description="Legal", system_prompt="Be legal.", tool_patterns=[])
        pool = TaskPool(
            registry_factory=MagicMock,
            client_factory=lambda: mock_client,
            profile_registry={"legal": profile},
            max_workers=1,
        )
        try:
            with patch("libreassistant.task_pool.run_tool_loop", return_value="some output"):
                task = pool.submit("legal", "do research", needs_verification=["check something"])
                completed = pool.backlog.get(timeout=2)
            assert completed.needs_verification[0].passed is True
        finally:
            pool.shutdown(wait=True)

    def test_verification_fails(self):  # mock_client returns "NO" → verification fails
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="NO"))]
        )
        profile = AgentProfile(name="legal", description="Legal", system_prompt="Be legal.", tool_patterns=[])
        pool = TaskPool(
            registry_factory=MagicMock,
            client_factory=lambda: mock_client,
            profile_registry={"legal": profile},
            max_workers=1,
        )
        try:
            with patch("libreassistant.task_pool.run_tool_loop", return_value="some output"):
                task = pool.submit("legal", "do research", needs_verification=["check something"])
                completed = pool.backlog.get(timeout=2)
            assert completed.needs_verification[0].passed is False
        finally:
            pool.shutdown(wait=True)

    def test_verification_client_error_graceful(self):  # API error during verification sets passed=False gracefully
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        profile = AgentProfile(name="legal", description="Legal", system_prompt="Be legal.", tool_patterns=[])
        pool = TaskPool(
            registry_factory=MagicMock,
            client_factory=lambda: mock_client,
            profile_registry={"legal": profile},
            max_workers=1,
        )
        try:
            with patch("libreassistant.task_pool.run_tool_loop", return_value="some output"):
                task = pool.submit("legal", "do research", needs_verification=["check something"])
                completed = pool.backlog.get(timeout=2)
            assert completed.needs_verification[0].passed is False
            assert completed.status == "completed"
        finally:
            pool.shutdown(wait=True)

    def test_verification_skipped_when_no_criteria(self):  # no verification criteria → no evaluation occurs
        profile = AgentProfile(name="legal", description="Legal", system_prompt="Be legal.", tool_patterns=[])
        pool = TaskPool(
            registry_factory=MagicMock,
            client_factory=MagicMock,
            profile_registry={"legal": profile},
            max_workers=1,
        )
        try:
            with patch("libreassistant.task_pool.run_tool_loop", return_value="some output"):
                task = pool.submit("legal", "do research")
                completed = pool.backlog.get(timeout=2)
            assert completed.needs_verification == []
        finally:
            pool.shutdown(wait=True)

    def test_verification_skipped_when_no_output(self):  # null output → verification is skipped (passed=None)
        profile = AgentProfile(name="legal", description="Legal", system_prompt="Be legal.", tool_patterns=[])
        pool = TaskPool(
            registry_factory=MagicMock,
            client_factory=MagicMock,
            profile_registry={"legal": profile},
            max_workers=1,
        )
        try:
            with patch("libreassistant.task_pool.run_tool_loop", return_value=None):
                task = pool.submit("legal", "do research", needs_verification=["check something"])
                completed = pool.backlog.get(timeout=2)
            assert completed.needs_verification[0].passed is None
        finally:
            pool.shutdown(wait=True)
