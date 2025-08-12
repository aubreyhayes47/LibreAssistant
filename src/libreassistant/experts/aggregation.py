"""Aggregate expert analyses into a final summary."""
from typing import Dict


def summarize(analysis: Dict[str, str]) -> str:
    """Combine expert outputs into a concise summary."""
    parts = [
        analysis["communications"],
        f"Argument: {analysis['argument']}",
        f"Caveats: {analysis['devils_advocate']}",
    ]
    return "\n".join(parts)
