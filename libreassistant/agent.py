"""Agent class — orchestrates a single turn, manages profile switching, and delegates to session for tool execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .profiles import get_profile
from .session import Message, Session, run_tool_loop
from .skills import get_skill_names_descriptions

if TYPE_CHECKING:
    from .task_pool import TaskPool
    from .tool_registry import ToolRegistry


# ---- Agent: binds a Session+Registry+Client together for one conversation ----
# Agent is deliberately thin (facade pattern): it delegates all heavy lifting
# to Session.absorb_completed_tasks() and session.run_tool_loop().  This keeps
# the session/testable without needing an OpenAI client, and lets Agent focus
# only on cross-cutting concerns (profile switching, task absorption timing).
#
# There is no close/cleanup method here because resource teardown
# (MCP shutdown, task pool drain) lives in cli.py's finally block.
# This keeps Agent lifecycle-independent — it can be created and used
# without owning any OS-level resources.
class Agent:
    def __init__(
        self,
        session: Session,
        client,
        registry: ToolRegistry,
        task_pool: TaskPool | None,
        model: str,
    ):
        self.session = session
        self.client = client
        self.registry = registry
        self.task_pool = task_pool
        self.model = model
        self.active = True
        self.registry.current_profile = session.profile.name
        # Wire registry → session so delegated tasks can track their parent.
        # When a background task calls the delegate_task tool, the task's
        # Session gets parent_session_id from registry.session_id.  Later,
        # absorb_completed_tasks() uses parent_session_id to route task
        # results back to the correct session (preventing cross-session
        # contamination if multiple sessions share the same registry).
        self.registry.session_id = session.id

    # ---- Turn: absorb tasks, add user message, run tool loop ----
    # The three-step ordering matters:
    #  1. absorb_completed_tasks() — inject background task results FIRST so the
    #     model sees them before the user's message (earlier in context = more
    #     influence on the response).  This also prevents a race where a task
    #     completes between the user typing and the API call.
    #  2. add_message(user) — the user's input must follow absorbed tasks so the
    #     model treats task results as prior context, not as something to respond to.
    #  3. run_tool_loop() — processes the full updated context including tasks + user.
    def turn(self, user_input: str, reasoning_callback=None, status_callback=None, tool_call_callback=None,
             abort_event=None, steer_queue=None) -> str | None:
        self.session.absorb_completed_tasks()
        msg = Message.create(
            role="user",
            content=user_input,
            agent=self.session.profile.name,
            mode="primary",
            session_id=self.session.id,
        )
        self.session.add_message(msg)
        return run_tool_loop(
            self.session,
            self.client,
            self.registry,
            self.model,
            max_rounds=self.session.profile.max_tool_rounds,
            truncate_result_chars=self.session.profile.max_tool_result_chars,
            reasoning_callback=reasoning_callback,
            status_callback=status_callback,
            tool_call_callback=tool_call_callback,
            abort_event=abort_event,
            steer_queue=steer_queue,
        )

    # ---- Profile switch: replace system prompt, swap registry filter, log the change ----
    def switch_profile(self, name: str) -> str:
        new_profile = get_profile(name)
        if new_profile.name == self.session.profile.name:
            return f"Already using profile '{name}'"
        for msg in self.session.messages:
            if msg.role == "system":
                msg.content = new_profile.system_prompt  # Replace in-place so the API never sees two system messages at index 0
                break
        else:
            self.session.messages.insert(
                0,
                Message.create(
                    role="system",
                    content=new_profile.system_prompt,
                    agent=self.session.profile.name,
                    mode="primary",
                    session_id=self.session.id,
                ),
            )
        self.session.profile = new_profile
        self.registry = self.registry.filter(new_profile.tool_patterns)  # Re-filter the registry for the new profile's tool patterns
        if self.registry.mcp_manager:
            self.registry.mcp_manager.update_registry(self.registry)
        self.registry.current_profile = new_profile.name

        # Update the skill listing for the new profile (skills may differ by profile).
        # Find and replace the existing skill listing system message, or append if missing.
        skill_listing = get_skill_names_descriptions(new_profile.tool_patterns, new_profile.name)
        if skill_listing:
            # Look for existing skill listing (second system message, after the main prompt)
            replaced = False
            for i, msg in enumerate(self.session.messages):
                if msg.role == "system" and i > 0 and msg.content.startswith("## Available Skills"):
                    msg.content = skill_listing
                    replaced = True
                    break
            if not replaced:
                self.session.add_system_message(skill_listing, agent=new_profile.name)

        # Inject an explicit role-switch directive after the system prompt.
        # This is a separate system message (not the [0] system prompt) that
        # tells the model to fully adopt the new persona.  We add it as its own
        # message rather than appending to the system prompt because the API treats
        # messages[0] specially — it is re-read on every call and influences
        # generation differently from mid-conversation system messages.
        # Remove old role-switch directives to avoid cluttering context
        self.session.messages = [
            msg for msg in self.session.messages
            if not (msg.role == "system" and msg.content and msg.content.startswith("IMPORTANT: You have switched to the"))
        ]
        self.session.add_system_message(
            f"IMPORTANT: You have switched to the '{name}' profile. "
            f"Your role is now: {new_profile.description}. "
            f"Disregard any prior role instructions. Adopt this new role fully.",
            agent=self.session.profile.name,
        )
        if new_profile.model:  # If the new profile specifies a model override, apply it
            self.model = new_profile.model
        return f"Switched to profile '{name}'"


