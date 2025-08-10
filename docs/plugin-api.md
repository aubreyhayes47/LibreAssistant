<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Plugin API

Plugins extend LibreAssistant by implementing custom behavior that can be invoked through the microkernel.

## Plugin Interface

A plugin is any object that provides a `run` method with the following signature:

```python
from typing import Any, Dict

def run(self, user_state: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the plugin logic."""
    ...
```

- `user_state` is a mutable dictionary persisted for each user. Plugins may read or modify this dictionary to maintain state between invocations.
- `payload` contains the arguments supplied by the caller.
- The return value is a dictionary that becomes the plugin's response.

## Registration

Plugins must be registered with the microkernel before they can be invoked. Registration associates a plugin instance with a unique name:

```python
from libreassistant.kernel import kernel

class MyPlugin:
    def run(self, user_state, payload):
        ...

kernel.register_plugin("my-plugin", MyPlugin())
```

Built-in plugins may expose a helper function to encapsulate registration.

## Example

The built-in `echo` plugin returns the provided message and stores it in the user's state:

```python
from typing import Any, Dict
from libreassistant.kernel import kernel

class EchoPlugin:
    def run(self, user_state: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        message = payload.get("message", "")
        user_state["last_message"] = message
        return {"echo": message}

def register() -> None:
    kernel.register_plugin("echo", EchoPlugin())
```

The plugin can then be invoked through the `/api/v1/invoke` endpoint by specifying its name and a payload.
