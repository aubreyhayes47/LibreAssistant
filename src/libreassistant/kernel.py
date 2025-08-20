# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Minimal microkernel managing plugins and user state."""

from __future__ import annotations

from typing import Any, Dict, Protocol

from pydantic import BaseModel, ValidationError


class Plugin(Protocol):
    """Protocol that all plugins must implement."""

    def run(
        self, user_state: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the plugin with the given user state and payload."""


class Microkernel:
    """Core microkernel responsible for plugin coordination."""

    def __init__(self) -> None:
        self._plugins: Dict[str, Plugin] = {}
        self._states: Dict[str, Dict[str, Any]] = {}

    def register_plugin(self, name: str, plugin: Plugin) -> None:
        """Register a plugin implementation under a specific name."""
        self._plugins[name] = plugin

    def get_state(self, user_id: str) -> Dict[str, Any]:
        """Retrieve mutable state for a user, creating it if necessary."""
        state = self._states.setdefault(user_id, {})
        state.setdefault("user_id", user_id)
        return state

    def invoke(
        self, name: str, user_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke a registered plugin for the given user."""
        plugin = self._plugins.get(name)
        if plugin is None:
            raise KeyError(name)
        state = self.get_state(user_id)
        model = getattr(plugin, "InputModel", None)
        if isinstance(model, type) and issubclass(model, BaseModel):
            try:
                payload = model.model_validate(payload).model_dump()
            except ValidationError as exc:
                return {"error": exc.errors()}
        return plugin.run(state, payload)

    def reset(self) -> None:
        """Reset the registry and user state store. Intended for tests."""
        self._plugins.clear()
        self._states.clear()

    def shutdown(self) -> None:
        """Call any cleanup hooks exposed by registered plugins."""
        for plugin in self._plugins.values():
            close = getattr(plugin, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:  # pragma: no cover - best effort cleanup
                    pass


kernel = Microkernel()
