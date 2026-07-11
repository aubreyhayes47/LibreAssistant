"""Session and message model, persistence, context trimming, and the core tool-calling loop."""

from __future__ import annotations

import json
import queue
import re
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import CONFIG_DIR
from .profiles import AgentProfile
from .tool_registry import ToolRegistry
# TaskStopped is imported lazily inside run_tool_loop to break a
# circular import (task_pool.py imports from this module)


SESSIONS_DIR = (
    CONFIG_DIR / "sessions"
)  # Directory for named saved sessions; auto-save lives at the config root
# JSONL (one JSON object per line) is used instead of a single JSON array
# for three reasons: (1) crash resilience — each line is self-contained so a
# mid-write crash only loses the current line, not the entire file; (2) append
# friendly — new messages can be written without reading or rewriting the whole
# file; (3) streaming — the file can be read line-by-line without loading the
# entire session into memory.
AUTO_SESSION_PATH = CONFIG_DIR / "last_session.jsonl"

SESSION_NAME_RE = re.compile(
    r"^[a-zA-Z0-9_-]+$"
)  # Only allow safe filename characters for session names


def is_valid_session_name(name: str) -> bool:
    return bool(SESSION_NAME_RE.match(name))


# ---- Message value object ----
@dataclass
class Message:
    """A single message in a conversation. Tagged with agent name and mode for multi-profile / multi-session routing."""

    id: str
    session_id: str
    role: str
    content: str | None
    tool_calls: list | None
    tool_call_id: str | None
    agent: str
    mode: str
    parent_id: str | None
    timestamp: float

    # Factory: create a new message with auto-generated id and current timestamp
    @staticmethod
    def create(
        role: str,
        content: str | None,
        agent: str,
        mode: str,
        session_id: str,
        tool_calls: list | None = None,
        tool_call_id: str | None = None,
        parent_id: str | None = None,
    ) -> Message:
        return Message(
            id=uuid.uuid4().hex[:12],
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            agent=agent,
            mode=mode,
            parent_id=parent_id,
            timestamp=time.time(),
        )

    # Factory: convert an OpenAI API response Message into our internal format
    @staticmethod
    def from_api_msg(msg, agent: str, mode: str, session_id: str) -> Message:
        tc = None
        if (
            msg.tool_calls
        ):  # Convert OpenAI tool_calls (object list) to plain dicts for serialization
            tc = [
                {
                    "id": call.id,
                    "type": call.type,
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                for call in msg.tool_calls
            ]
        return Message(
            id=uuid.uuid4().hex[:12],
            session_id=session_id,
            role=msg.role,
            content=msg.content,
            tool_calls=tc,
            tool_call_id=None,
            agent=agent,
            mode=mode,
            parent_id=None,
            timestamp=time.time(),
        )

    # Serialize to the dict format expected by the OpenAI chat completions API
    def to_api_dict(self) -> dict:
        d: dict[str, Any] = {"role": self.role}
        d["content"] = self.content if self.content is not None else ""
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if (
            self.tool_call_id
        ):  # Only include tool_call_id when this is a tool-role response
            d["tool_call_id"] = self.tool_call_id
        return d


# _msg_to_dict: explicit field-by-field serialization rather than dataclasses.asdict()
# to avoid accidentally exposing new internal fields (like _already_injected) to the
# API or disk format.  Deduplication matters: both Session.save() and the standalone
# auto_save() call this, so a single canonical serialization path prevents drift.
def _msg_to_dict(msg: Message) -> dict:
    return {
        "id": msg.id,
        "session_id": msg.session_id,
        "role": msg.role,
        "content": msg.content,
        "tool_calls": msg.tool_calls,
        "tool_call_id": msg.tool_call_id,
        "agent": msg.agent,
        "mode": msg.mode,
        "parent_id": msg.parent_id,
        "timestamp": msg.timestamp,
    }


# ---- Session: conversation container with message history and backlog absorption ----
class Session:
    def __init__(
        self,
        profile: AgentProfile,
        backlog: queue.Queue | None = None,
        session_id: str | None = None,
        parent_session_id: str | None = None,
        history_file: str | None = None,
    ):
        self.id = (
            session_id or uuid.uuid4().hex[:12]
        )  # Generate a short random id if none provided
        self.profile = profile
        self.messages: list[Message] = []
        # The backlog queue is the bridge between TaskPool (running in worker
        # threads) and this Session (running in the main thread).  TaskPool
        # puts completed Task objects here; absorb_completed_tasks() drains it
        # on every Agent.turn() call.  This is a thread-safe queue.Queue, not
        # a list — worker threads push, the main thread pops, no lock needed.
        self.backlog: queue.Queue = backlog or queue.Queue()
        self.history_file: str | None = history_file
        self.parent_session_id: str | None = parent_session_id
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.auto_save_enabled: bool = True

    def add_message(self, msg: Message) -> None:
        self.messages.append(msg)
        self.updated_at = time.time()

    def add_system_message(self, content: str, agent: str) -> Message:
        msg = Message.create(
            role="system",
            content=content,
            agent=agent,
            mode="primary",
            session_id=self.id,
        )
        self.add_message(msg)
        return msg

    def api_messages(self) -> list[dict]:
        return [m.to_api_dict() for m in self.messages]

    # Drain completed background tasks from the backlog and inject them as system messages.
    # Why drain before every turn (not on a timer)?  This guarantees the model always
    # sees task results before the user's next message — no race condition between
    # the background thread finishing and the REPL reading input.  The _already_injected
    # guard prevents double-injection if absorb is called multiple times.
    def absorb_completed_tasks(self) -> int:
        injected = 0
        while not self.backlog.empty():
            try:
                task = self.backlog.get_nowait()
            except queue.Empty:  # Gracefully handle empty queue (nothing to absorb)
                break
            if getattr(
                task, "_already_injected", False
            ):  # Skip tasks already injected in a previous absorb cycle
                continue
            parent_session_id = getattr(task, "parent_session_id", None)
            if isinstance(parent_session_id, str) and parent_session_id != self.id:
                continue
            summary = self._summarize_task(task)
            self.add_system_message(summary, agent=task.specialist)
            task._already_injected = True
            injected += 1
        return injected

    # Format a completed task's summary for injection into context
    def _summarize_task(self, task) -> str:
        parts = [
            f"[Task {task.id} — {task.specialist}]",
            f"Request: {getattr(task, 'input', '')[:300]}",
        ]
        output = getattr(task, "output", None)
        error = getattr(task, "error", None)
        if output:
            parts.append(f"Result: {output[:1000]}")
        elif error:
            parts.append(f"Error: {error}")
        else:
            parts.append("(no result)")
        needs_verification = getattr(
            task, "needs_verification", None
        )  # Include verification pass/fail results in the summary
        if needs_verification:
            passed = [v for v in needs_verification if v.passed]
            failed = [v for v in needs_verification if v.passed is False]
            if passed:
                parts.append(f"Verified: {'; '.join(v.description for v in passed)}")
            if failed:
                parts.append(f"FAILED: {'; '.join(v.description for v in failed)}")
        return "\n".join(parts)

    # Persist all messages as newline-delimited JSON to a file
    def save(self, path: str) -> None:
        # Ensure parent directory exists — auto_save targets AUTO_SESSION_PATH
        # which lives at the config root, but named sessions target
        # SESSIONS_DIR/{name}.jsonl and the directory might not exist yet.
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            for msg in self.messages:
                f.write(json.dumps(_msg_to_dict(msg), ensure_ascii=False) + "\n")

    # Auto-save: write to last_session.jsonl unless disabled or only system message exists
    def auto_save(self) -> None:
        if not self.auto_save_enabled:
            return
        if len(self.messages) <= 1:
            return
        self.save(str(AUTO_SESSION_PATH))

    # Classmethod: reconstruct a Session from a JSONL file
    @classmethod
    def load(
        cls,
        path: str,
        profile: AgentProfile,
        backlog: queue.Queue | None = None,
    ) -> Session:
        session = cls(profile=profile, backlog=backlog)
        p = Path(path)
        if not p.exists():
            return session
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                data.setdefault("agent", "default")
                data.setdefault("mode", "primary")
                data.setdefault("parent_id", None)
                data.setdefault("tool_call_id", None)
                data.setdefault("tool_calls", None)
                data.setdefault(
                    "content", None
                )  # Ensure backward-compat: supply defaults for fields that older saves may lack
                session.messages.append(
                    Message(
                        id=data.get("id", ""),
                        session_id=data.get("session_id", session.id),
                        role=data["role"],
                        content=data["content"],
                        tool_calls=data["tool_calls"],
                        tool_call_id=data["tool_call_id"],
                        agent=data["agent"],
                        mode=data["mode"],
                        parent_id=data["parent_id"],
                        timestamp=data.get("timestamp", 0.0),
                    )
                )
        session.id = (
            session.messages[0].session_id if session.messages else session.id
        )  # Restore the original session_id from the first message (not the one we generated at construction)
        return session


# ---- Context sanitization: strip API-injected fields that trigger 400 errors ----
# Why a separate sanitize() + trim() pattern?  Sanitize handles schema
# compliance (removing fields the API rejects on the next call), while trim
# handles context-window budget.  They are independent concerns that run
# together before every API call in run_tool_loop().
def sanitize(api_dicts: list[dict]) -> None:
    for d in api_dicts:
        d.pop("reasoning_content", None)
        d.pop("refusal", None)
        d.pop(
            "usage", None
        )  # Strip refusal, usage, and reasoning_content that the model may leak back
        if d.get("content") is None:
            d["content"] = ""
        content = d.get(
            "content"
        )  # Normalize None content to empty string for API compliance
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    part.pop("reasoning_content", None)
        tc = d.get(
            "tool_calls"
        )  # Also strip reasoning_content nested inside tool_call dicts
        if tc:
            for tc_item in tc:
                if isinstance(tc_item, dict):
                    tc_item.pop("reasoning_content", None)


def _estimate_chars(api_dicts: list[dict]) -> int:
    # Estimate total character count from content + tool call arguments
    total = 0
    for d in api_dicts:
        total += len(d.get("content", "") or "")
        tc = d.get("tool_calls")
        if tc:
            for tc_item in tc:
                fn = tc_item.get("function", {})
                total += len(fn.get("arguments", "") or "")
                total += len(fn.get("name", "") or "")
    return total


def summarize(
    api_dicts: list[dict], client, model: str, budget_chars: int = 2000
) -> None:
    if len(api_dicts) <= 5:
        return

    protected = set()
    protected.add(0)
    for i in range(max(1, len(api_dicts) - 4), len(api_dicts)):
        protected.add(i)

    old_indices = []
    for i in range(len(api_dicts)):
        if i in protected:
            continue
        msg = api_dicts[i]
        if msg.get("role") in ("user", "assistant", "tool") and msg.get("content"):
            old_indices.append(i)

    if len(old_indices) < 3:
        return

    existing_summary_text = ""
    for i in old_indices:
        content = api_dicts[i].get("content", "") or ""
        if "[Conversation Summary]" in content:
            existing_summary_text = content
            break

    old_text_parts = []
    for i in old_indices:
        msg = api_dicts[i]
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if content:
            limit = 500 if role == "tool" else 2000
            old_text_parts.append(f"[{role}]: {content[:limit]}")

    old_text = "\n".join(old_text_parts)
    if len(old_text) < 500:
        return

    system_prompt = (
        "You are a conversation summarizer. Compress the following conversation into a "
        "structured summary with these sections:\n"
        "- **Goal**: What the user is trying to accomplish\n"
        "- **Key Decisions**: Important choices made\n"
        "- **Progress**: What has been completed\n"
        "- **Open Items**: Pending questions or tasks\n"
        "- **Critical Context**: Any technical details, names, numbers to remember\n"
        "Output only the summary, no preamble."
    )
    user_content = f"Summarize this conversation segment:\n\n{old_text[:8000]}"
    if existing_summary_text:
        user_content = (
            f"Previous summary context: {existing_summary_text}\n\n{user_content}"
        )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=512,
        )
        summary_text = resp.choices[0].message.content
        if not summary_text:
            return

        summary_msg = {
            "role": "assistant",
            "content": f"[Conversation Summary]\n{summary_text}",
        }

        for i in reversed(old_indices):
            del api_dicts[i]

        insert_pos = min(old_indices) if old_indices else len(api_dicts)
        api_dicts.insert(insert_pos, summary_msg)

    except Exception:
        pass


# ---- Context window trim: drop/prune messages when budget is exceeded ----
def _tool_name_for_result(api_dicts: list[dict], result_index: int) -> str:
    """Find the tool name for a tool result by matching its tool_call_id to the
    preceding assistant message's tool_calls. Falls back to 'tool' if not found."""
    result_id = api_dicts[result_index].get("tool_call_id")
    if not result_id:
        return "tool"
    for j in range(result_index - 1, -1, -1):
        tc = api_dicts[j].get("tool_calls")
        if tc:
            for call in tc:
                fn = call.get("function", {})
                if call.get("id") == result_id and fn.get("name"):
                    return fn["name"]
    return "tool"


def trim(
    api_dicts: list[dict],
    max_chars: int,
    compaction_mode: str = "trim",
    client=None,
    model: str | None = None,
) -> None:
    if compaction_mode == "summarize" and client and model:
        summarize(api_dicts, client, model)

    effective_budget = max_chars - max(2000, max_chars // 20)
    if _estimate_chars(api_dicts) <= effective_budget:
        return
    if not api_dicts:
        return

    n = len(api_dicts)
    recency_zone = max(6, n // 10)

    protected: set[int] = {0}
    for i in range(max(0, n - recency_zone), n):
        protected.add(i)

    tool_chars = 0
    for i in range(n - 1, -1, -1):
        if api_dicts[i].get("role") == "tool":
            protected.add(i)
            tool_chars += len(api_dicts[i].get("content", "") or "")
            if tool_chars >= 30000:
                break

    if _estimate_chars(api_dicts) <= effective_budget:
        return

    for i in range(n):
        if i in protected:
            continue
        if api_dicts[i].get("role") != "tool":
            continue
        c = api_dicts[i].get("content", "") or ""
        clen = len(c)
        if clen > 5000:
            tool_name = _tool_name_for_result(api_dicts, i)
            api_dicts[i]["content"] = f"[pruned {tool_name}: was {clen} chars]"
        elif clen > 1000:
            api_dicts[i]["content"] = f"[tool result: {clen} chars]"

    if _estimate_chars(api_dicts) <= effective_budget:
        return

    delete_indices = set()
    for i in range(1, n):
        if i in protected:
            continue
        if api_dicts[i].get("role") == "tool":
            for j in range(i - 1, -1, -1):
                if api_dicts[j].get("role") == "assistant" and api_dicts[j].get(
                    "tool_calls"
                ):
                    if j not in protected:
                        delete_indices.add(j)
                    break
            delete_indices.add(i)

    if delete_indices:
        for i in reversed(sorted(delete_indices)):
            del api_dicts[i]
            if _estimate_chars(api_dicts) <= effective_budget:
                break


# ---- Core tool-calling loop: iterate up to max_rounds, dispatch tools, stop on text-only response ----
# Call chain: cli.py → agent.turn() → session.run_tool_loop() → registry.dispatch()
# This function is the innermost loop of the system — it owns the conversation
# with the LLM.  It is a free function (not a Session method) so that TaskPool
# can also call it with its own Session + registry for background tasks,
# keeping the main-thread and worker-thread code paths identical.
def run_tool_loop(
    session: Session,
    client,
    registry: ToolRegistry,
    model: str,
    max_rounds: int = 10,
    truncate_result_chars: int = 10_000,
    status_callback=None,
    reasoning_callback=None,
    tool_call_callback=None,
    stop_event: threading.Event | None = None,
    abort_event: threading.Event | None = None,
    steer_queue: queue.Queue | None = None,
) -> str | None:
    from libreassistant.task_pool import TaskStopped

    for round_n in range(1, max_rounds + 1):
        if stop_event and stop_event.is_set():
            raise TaskStopped
        if abort_event and abort_event.is_set():
            return None
        # Sanitize and trim context before every API call (the 400-error fix)
        api_dicts = session.api_messages()
        sanitize(api_dicts)
        trim(
            api_dicts,
            session.profile.max_context_chars,
            compaction_mode=getattr(session.profile, "compaction_mode", "trim"),
            client=client,
            model=model,
        )
        if len(api_dicts) < len(session.messages) * 0.7 and len(session.messages) > 10:
            recovery = Message.create(
                role="system",
                content=(
                    "[Context compacted — older messages were summarized to fit the context window. "
                    "The summary above preserves key facts and decisions. "
                    "Continue the conversation from where it left off.]"
                ),
                agent=session.profile.name,
                mode="primary",
                session_id=session.id,
            )
            session.add_message(recovery)

        if status_callback:
            status_callback("Thinking...", round_n)

        response = client.chat.completions.create(
            model=model,
            messages=api_dicts,
            tools=registry.schemas if registry.schemas else None,
            max_tokens=4096,
        )  # Chat completion with optional tool schemas; no tools sent when registry is empty

        if abort_event and abort_event.is_set():
            return None

        if not response.choices:
            return None

        msg = response.choices[0].message

        refusal = getattr(msg, "refusal", None)
        if isinstance(refusal, str) and refusal:
            return refusal

        reasoning = getattr(msg, "reasoning_content", None)
        if (
            isinstance(reasoning, str) and reasoning and reasoning_callback
        ):  # If the model emitted reasoning, forward it to the UI callback
            reasoning_callback(reasoning)

        api_msg = Message.from_api_msg(
            msg,
            agent=session.profile.name,
            mode="primary",
            session_id=session.id,
        )
        session.add_message(api_msg)

        if not msg.tool_calls:
            return (
                msg.content
            )  # No tool_calls means the model produced a final text answer — return it

        # Dispatch each tool call in sequence, collecting results
        for tc in msg.tool_calls:
            if abort_event and abort_event.is_set():
                # Mark the remaining tool calls as aborted
                tool_msg = Message.create(
                    role="tool",
                    content="Tool execution aborted by user.",
                    agent=session.profile.name,
                    mode="primary",
                    session_id=session.id,
                    tool_call_id=tc.id,
                )
                session.add_message(tool_msg)
                return None

            fn_name = tc.function.name
            args_raw = tc.function.arguments
            args = {}
            if args_raw:
                try:
                    args = json.loads(args_raw)
                except json.JSONDecodeError:
                    args = {}  # Gracefully handle malformed JSON arguments from the model by treating them as empty

            if status_callback:
                status_callback(f"Calling {fn_name}(...)...", round_n)

            try:
                result = registry.dispatch(fn_name, args)
            except Exception as exc:
                result = f"Tool error: {exc}"

            if tool_call_callback:
                tool_call_callback(fn_name, args, result)

            if (
                truncate_result_chars > 0 and len(result) > truncate_result_chars
            ):  # Truncate tool results to keep context budget in check
                result = (
                    result[:truncate_result_chars]
                    + f"\n\n[truncated at {truncate_result_chars} chars]"
                )

            tool_msg = Message.create(
                role="tool",
                content=result,
                agent=session.profile.name,
                mode="primary",
                session_id=session.id,
                tool_call_id=tc.id,
            )
            session.add_message(tool_msg)

        # Poll steer queue between tool rounds — inject user messages before next LLM call
        if steer_queue:
            while True:
                try:
                    steer_text = steer_queue.get_nowait()
                except queue.Empty:
                    break
                steer_msg = Message.create(
                    role="user",
                    content=steer_text,
                    agent=session.profile.name,
                    mode="primary",
                    session_id=session.id,
                )
                session.add_message(steer_msg)

    # Fallback: after exhausting max_tool_rounds, force one final completion
    # WITHOUT tools to get a closing text response.  Without this, the model
    # might end the loop with an unfinished tool-calling chain — the user would
    # see "(no response)".  By re-sending the context without tool schemas,
    # we compel the model to produce a natural-language summary of its progress.
    api_dicts = session.api_messages()
    sanitize(api_dicts)
    trim(
        api_dicts,
        session.profile.max_context_chars,
        compaction_mode=getattr(session.profile, "compaction_mode", "trim"),
        client=client,
        model=model,
    )
    if len(api_dicts) < len(session.messages) * 0.7 and len(session.messages) > 10:
        recovery = Message.create(
            role="system",
            content=(
                "[Context compacted — older messages were summarized to fit the context window. "
                "The summary above preserves key facts and decisions. "
                "Continue the conversation from where it left off.]"
            ),
            agent=session.profile.name,
            mode="primary",
            session_id=session.id,
        )
        session.add_message(recovery)

    response = client.chat.completions.create(
        model=model,
        messages=api_dicts,
        max_tokens=4096,
    )
    if response.choices:
        msg = response.choices[0].message
        api_msg = Message.from_api_msg(
            msg,
            agent=session.profile.name,
            mode="primary",
            session_id=session.id,
        )
        session.add_message(api_msg)
        return msg.content
    return None


# ---- Standalone session persistence helpers ----
def save_session(name: str, messages: list[Message]) -> None:
    path = SESSIONS_DIR / f"{name}.jsonl"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for msg in messages:
            f.write(json.dumps(_msg_to_dict(msg), ensure_ascii=False) + "\n")


def load_session(name: str) -> list[Message] | None:
    # Load a named session from disk; returns None if not found
    path = SESSIONS_DIR / f"{name}.jsonl"
    if not path.exists():
        return None
    messages: list[Message] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            data.setdefault("id", "")
            data.setdefault("session_id", "")
            data.setdefault("agent", "default")
            data.setdefault("mode", "primary")
            data.setdefault("parent_id", None)
            data.setdefault("tool_call_id", None)
            data.setdefault("tool_calls", None)
            data.setdefault("content", None)
            data.setdefault("timestamp", 0.0)
            messages.append(
                Message(**data)
            )  # Unpack serialized dict directly into Message constructor (keys match dataclass fields)
    return messages if messages else None


def list_sessions() -> list[str]:
    # List all saved sessions by their .jsonl filenames (sorted)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(p.stem for p in SESSIONS_DIR.glob("*.jsonl"))


def delete_session(name: str) -> bool:
    # Delete a named session file; returns True if it existed
    path = SESSIONS_DIR / f"{name}.jsonl"
    if path.exists():
        path.unlink()
        return True
    return False


def auto_save(messages: list[Message]) -> None:
    # Auto-save current messages to the volatile last_session.jsonl (used for resume on restart)
    if len(messages) <= 1:
        return
    AUTO_SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTO_SESSION_PATH, "w") as f:
        for msg in messages:
            f.write(json.dumps(_msg_to_dict(msg), ensure_ascii=False) + "\n")


def auto_load() -> list[dict] | None:
    # Load the auto-save file for resume prompt; returns list of raw dicts or None
    if not AUTO_SESSION_PATH.exists():
        return None
    messages: list[dict] = []
    with open(AUTO_SESSION_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            messages.append(data)
    return messages if messages else None
