# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Built-in plugins for LibreAssistant."""

# Re-export registration functions for built-in plugins
from .echo import register as register_echo
from .file_io import register as register_file_io
from .law_by_keystone import register as register_law_by_keystone
from .think_tank import register as register_think_tank

__all__ = [
    "register_echo",
    "register_file_io",
    "register_law_by_keystone",
    "register_think_tank",
]
