# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Built-in plugins for LibreAssistant."""

# Re-export registration functions for built-in plugins
from .echo import register as register_echo

__all__ = ["register_echo"]
