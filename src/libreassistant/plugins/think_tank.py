# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""ThinkTank plugin coordinating multiple internal experts."""

from __future__ import annotations

from typing import Any, Dict

from ..kernel import kernel
from ..experts import (
    argumentation,
    communications,
    devils_advocate,
    executive,
    research,
    visualizer,
    aggregation,
)


class ThinkTankPlugin:
    """Orchestrate specialist agents to deliver a polished answer."""

    def run(self, user_state: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        goal = payload.get("goal") or payload.get("question")
        if not goal:
            return {"error": "goal required"}

        analysis = {
            "goal": goal,
            "executive": executive.analyze(goal),
            "research": research.analyze(goal),
            "devils_advocate": devils_advocate.analyze(goal),
            "argument": argumentation.analyze(goal),
            "communications": communications.analyze(goal),
            "visualizer": visualizer.analyze(goal),
        }
        dossier = user_state.setdefault("thinktank_dossier", [])
        dossier.append(analysis)
        summary = aggregation.summarize(analysis)

        return {"summary": summary, "analysis": analysis}


def register() -> None:
    """Register the ThinkTank plugin with the microkernel."""
    kernel.register_plugin("think_tank", ThinkTankPlugin())
