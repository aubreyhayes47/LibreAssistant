<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Plugin API

Plugins extend LibreAssistant by implementing custom behavior that can be invoked through the microkernel.

Documentation for built-in plugins:

- [Echo](echo_plugin.md)
- [File I/O](file_io_plugin.md)
- [Think Tank](think_tank_plugin.md)

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

## History

Each invocation is appended to a per-user log that can be retrieved via `GET /api/v1/history/{user_id}`. This history powers the Past Requests tab in the web UI and can aid debugging during plugin development.

## MCP Server Integration

Many plugins delegate work to external Model Context Protocol (MCP) servers.
`MCPPluginAdapter` wraps a server tool and exposes it through the standard
`run` interface:

```python
from libreassistant.mcp_adapter import MCPPluginAdapter

class EchoPlugin(MCPPluginAdapter):
    def __init__(self) -> None:
        super().__init__("servers/echo/index.ts", "echo_message")
```

The adapter handles JSON‑RPC communication with the TypeScript server and
returns the tool's JSON response to the microkernel.

Both :class:`MCPPluginAdapter` and the underlying :class:`MCPClient` implement
the context manager protocol.  When used with ``with`` they ensure that the
spawned MCP subprocess is terminated automatically:

```python
from libreassistant.mcp_adapter import MCPClient

with MCPClient("servers/echo/index.ts") as client:
    client.request("listTools")

with EchoPlugin() as plugin:
    plugin.run({}, {"message": "hi"})
```

## File I/O Plugin Security

The built-in `file_io` plugin exposes basic filesystem operations. It sets
`ALLOWED_BASE_DIR` to the user's `~/desktop` directory and passes this value to
the MCP file server through `MCP_FS_BASE_DIR`.

Before any operation, the plugin normalizes user supplied paths with
`os.path.realpath` and verifies that the result remains within
`ALLOWED_BASE_DIR`. Requests that resolve outside this directory are rejected,
preventing path traversal and confining access to an explicitly approved
workspace.
