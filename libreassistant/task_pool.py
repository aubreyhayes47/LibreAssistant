"""Background task delegation pool — runs specialist agents in separate threads and collects results for injection into the main conversation."""

from __future__ import annotations

import queue
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable

from .profiles import AgentProfile
from .session import Message, Session, run_tool_loop


class TaskStopped(Exception):
    """Raised when a delegated task is cancelled before completion."""


@dataclass
class VerificationItem:
    """A single blind-rubric criterion. The delegator (not the specialist) evaluates this after the task completes."""
    description: str
    passed: bool | None = None


# Task uses dataclass (not __slots__) because it's mutated freely across threads
# (status, output, error, _already_injected) and __slots__ prevents dynamic attribute
# addition.  _already_injected lives on the instance rather than in a separate set
# so the guard travels with the Task object through the backlog queue — no external
# bookkeeping needed.  See also: Session.absorb_completed_tasks().
@dataclass
class Task:
    """Structured work order for a delegated specialist. Runs in a background thread with its own session, profile, and budget."""
    id: str
    specialist: str
    input: str
    needs_verification: list[VerificationItem]
    status: str
    output: str | None
    error: str | None
    created_at: float  # epoch seconds — used by status() for "how long ago" display and by /task command for age
    completed_at: float | None  # set in finally block so it's always recorded, even on failure/stop
    parent_session_id: str | None
    _already_injected: bool = False  # guard against double-injection by absorb_completed_tasks()
    _stop_event: threading.Event = field(default_factory=threading.Event)  # allows stop() to abort a running task mid-execution


class TaskPool:
    """Thread-safe pool of delegated task workers. Each task runs in its own session with filtered tools. Completed tasks are placed on backlog for the main session to consume."""
    def __init__(
        self,
        # Why callables instead of a shared registry/client?  Each background thread
        # gets its own fresh instances to avoid sharing OpenAI clients or registry
        # state across threads.  OpenAI clients hold connection pools that aren't
        # safe to share; a per-thread client prevents socket corruption.
        registry_factory: Callable[[], Any],
        client_factory: Callable[[], Any],
        profile_registry: dict[str, AgentProfile],
        max_workers: int = 3,
    ):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)  # max_workers=3 as per architecture decision (PLAN.md "Parallel tasks")
        self.tasks: dict[str, Task] = {}
        self.backlog: queue.Queue[Task] = queue.Queue()  # consumed by Session.absorb_completed_tasks()
        self.registry_factory = registry_factory
        self.client_factory = client_factory
        self.profile_registry = profile_registry
        self._lock = threading.Lock()

    def submit(
        self,
        specialist: str,
        input: str,
        needs_verification: list[str] | None = None,
        parent_session_id: str | None = None,
    ) -> Task:
        """Create a Task, register it, and submit it to the background thread pool. Returns immediately (non-blocking).
        Ordering rationale: 1) build Task offline (no lock), 2) fail-fast on unknown
        specialist (avoids wasting a thread slot), 3) lock → insert (so status() can
        see the task before it starts running), 4) executor.submit (dispatch to pool).
        """
        task_id = uuid.uuid4().hex[:12]  # 12 hex chars — short enough for CLI display, unique enough for lookup
        items: list[VerificationItem] = []
        if needs_verification:
            items = [VerificationItem(description=d) for d in needs_verification]

        task = Task(
            id=task_id,
            specialist=specialist,
            input=input,
            needs_verification=items,
            status="queued",
            output=None,
            error=None,
            created_at=time.time(),
            completed_at=None,
            parent_session_id=parent_session_id,
        )

        if specialist not in self.profile_registry:
            task.status = "failed"
            task.error = f"Unknown specialist: {specialist}"
            return task

        with self._lock:  # lock must cover insertion to prevent race on concurrent submits
            self.tasks[task.id] = task

        self.executor.submit(self._run_task, task)
        return task

    def _run_task(self, task: Task) -> None:
        """Background execution: build isolated task profile, create private session, run tool loop, optionally verify output, then enqueue completion."""
        if task.status == "failed":
            self.backlog.put(task)
            return

        with self._lock:
            task.status = "running"
            self.tasks[task.id] = task

        if task._stop_event.is_set():
            raise TaskStopped

        try:
            profile = self.profile_registry[task.specialist]
            task_profile = _create_task_profile(profile)  # clone with tighter budgets (30K ctx / 5 rounds / 5K result) to prevent 400 errors and runaway costs

            sess = Session(profile=task_profile)
            registry = self.registry_factory().filter(task_profile.tool_patterns or ["*"])
            client = self.client_factory()

            msg = Message.create(
                role="user",
                content=task.input,
                agent=task.specialist,
                mode="task",
                session_id=sess.id,
            )
            sess.add_message(msg)

            result = run_tool_loop(
                sess,
                client,
                registry,
                profile.model or "big-pickle",
                max_rounds=task_profile.max_tool_rounds,
                truncate_result_chars=task_profile.max_tool_result_chars,
                stop_event=task._stop_event,
            )

            # ── Blind verification: invoke a separate LLM call to check each rubric criterion ──
            # Why "blind"?  The verifier's system prompt says only "Determine if the given
            # output satisfies the criterion" — it does NOT see the rubric description as
            # part of its role instructions.  The criterion is injected into the user message.
            # This prevents the model from pattern-matching its own instructions rather than
            # genuinely evaluating the output, giving a more honest pass/fail signal.
            task.output = result
            if task.needs_verification and result:
                for v in task.needs_verification:
                    if task._stop_event.is_set():
                        raise TaskStopped
                    try:
                        resp = client.chat.completions.create(  # using the delegator's model (profile.model), NOT the task profile model
                            model=profile.model or "big-pickle",
                            messages=[
                                {"role": "system", "content": "You are a verifier. Determine if the given output satisfies the criterion. Answer only YES or NO."},  # verifier sees the output but NOT the rubric description in its system prompt — only in the user message
                                {"role": "user", "content": f"Output:\n{result}\n\nCriterion: {v.description}\n\nDoes the output satisfy this criterion?"},
                            ],
                            max_tokens=10,
                        )
                        answer = resp.choices[0].message.content.strip().upper()
                        v.passed = answer == "YES"
                    except Exception:
                        v.passed = False
            task.status = "completed"  # status set BEFORE finally block so completed_at is always recorded
        except TaskStopped:
            pass
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
        finally:
            task.completed_at = time.time()
            self.backlog.put(task)  # Always enqueue — even on failure/stop — so the main session can report status. The queue decouples the background thread from the REPL thread.
            with self._lock:
                self.tasks[task.id] = task

    def stop(self, task_id: str) -> bool:
        """Request cancellation of a running task via its threading.Event flag."""
        with self._lock:
            task = self.tasks.get(task_id)
            if task is None:
                return False
            if task.status == "running":
                task._stop_event.set()
            if task.status in ("queued", "running"):
                task.status = "stopped"
            return True

    def stop_all(self) -> int:
        """Request cancellation of every running/queued task. Returns the number of tasks stopped."""
        stopped = 0
        with self._lock:
            for task in self.tasks.values():
                if task.status in ("queued", "running"):
                    task._stop_event.set()
                    task.status = "stopped"
                    stopped += 1
        return stopped

    def status(self, task_id: str) -> dict | None:
        """Return a JSON-safe dict summary of a task (or None if not found)."""
        with self._lock:
            task = self.tasks.get(task_id)
            if task is None:
                return None
            return task_dict(task)

    def get(self, task_id: str) -> Task | None:
        """Return the raw Task object for the caller that holds the lock (e.g. absorb_completed_tasks)."""
        with self._lock:
            return self.tasks.get(task_id)

    def shutdown(self, wait: bool = True) -> None:
        """Shut down the thread pool. Blocks until all running tasks finish unless wait=False."""
        self.executor.shutdown(wait=wait)


def _create_task_profile(profile: AgentProfile) -> AgentProfile:
    """Build an AgentProfile for task sessions with tighter budgets than the delegator profile.
    Why these specific numbers?  30K context chars fits ~7K tokens — enough for a focused
    subtask but small enough to prevent 400 errors from oversized payloads.  5 tool rounds
    limits runaway agentic loops (the delegator gets 10).  5K result truncation keeps
    individual tool outputs from bloating the task context.
    """
    return AgentProfile(
        name=profile.name,
        description=profile.description,
        system_prompt=profile.system_prompt,
        tool_patterns=profile.tool_patterns,
        model=profile.model,
        max_context_chars=30_000,
        max_tool_rounds=20,
        max_tool_result_chars=5_000,
    )


def task_dict(task: Task) -> dict:
    """Serialize a Task to a plain dict for JSON-safe status API responses.
    Why exclude needs_verification and parent_session_id?  Verification items
    contain pass/fail state that's already merged into the injected summary
    (see Session._summarize_task), and parent_session_id is internal routing
    metadata that shouldn't leak to status consumers.  Keeping the API surface
    minimal avoids accidental coupling to internal bookkeeping fields.
    """
    return {
        "id": task.id,
        "specialist": task.specialist,
        "status": task.status,
        "output": task.output,
        "error": task.error,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
    }
