# LibreAssistant Plugin API & MCP Server Development Guide

This document describes how to create plugins (MCP servers) for LibreAssistant, including the manifest format, server protocol, example code, and best practices.

---

## Plugin Manifest Format

Each plugin must include a `plugin-manifest.json` file in its root directory. This manifest describes the plugin’s metadata, entrypoint, permissions, config, and more.

**Required fields:**
- `name` (string): Human-readable plugin name
- `id` (string): Unique identifier (lowercase, hyphens only, e.g. `my-plugin`)
- `version` (string): Plugin version (semver)
- `description` (string): Short description
- `author` (string): Plugin author or maintainer
- `entrypoint` (string): Command to launch the MCP server (e.g. `python3 server.py`)
- `mcp_port` (integer): Port the plugin server listens on (1024-65535)
- `permissions` (array): List of permissions required (e.g. `["file:read"]`)

**Optional fields:**
- `config` (object): User-configurable fields (see below)
- `homepage` (string): URL for documentation
- `license` (string): License identifier (e.g. `MIT`)

**Example:**
```json
{
  "name": "Local File I/O",
  "id": "local-fileio",
  "version": "1.0.0",
  "description": "Securely read, write, list, and delete files on your device within a sandboxed directory.",
  "author": "LibreAssistant Team",
  "entrypoint": "python3 server.py",
  "mcp_port": 5101,
  "permissions": ["file:read", "file:write"],
  "config": {
    "base_directory": {
      "type": "string",
      "description": "The root directory for all file operations.",
      "required": true,
      "default": "~/LibreAssistantFiles"
    }
  },
  "homepage": "https://github.com/aubreyhayes47/LibreAssistant",
  "license": "MIT"
}
```

---

## MCP Server Protocol

A plugin MCP server is a web server (usually Flask or FastAPI) that exposes HTTP endpoints for LibreAssistant to call. The server must:
- Listen on the port specified in `mcp_port`
- Implement endpoints as described in its manifest/config
- Accept and return JSON
- Enforce permissions and config as needed

**Example endpoints for a file I/O plugin:**
- `POST /list` — List files in a directory
- `POST /read` — Read a file
- `POST /write` — Write to a file
- `POST /delete` — Delete a file or directory

**Request/Response Example:**
```json
# Request to /read
{
  "path": "notes/todo.txt"
}

# Response
{
  "success": true,
  "content": "Buy milk\nCall Alice"
}
```

**Permissions:**
- Plugins must check and enforce permissions as declared in their manifest.
- LibreAssistant will prompt the user for approval if a plugin requests sensitive permissions.

**Config:**
- Plugins can define user-configurable fields in the manifest (`config`).
- These are passed as environment variables or via stdin at startup.

**Lifecycle:**
- Plugins are started/stopped by LibreAssistant as needed.
- Plugins should handle SIGTERM/SIGINT for graceful shutdown.

---

## Minimal Example Plugin

**plugin-manifest.json**
```json
{
  "name": "Test Plugin",
  "id": "test-plugin",
  "version": "1.0.0",
  "description": "A minimal plugin for development and testing.",
  "author": "LibreAssistant Test Suite",
  "entrypoint": "python3 server.py",
  "mcp_port": 5199,
  "permissions": [],
  "config": {},
  "homepage": "https://example.com/",
  "license": "MIT"
}
```

**server.py**
```python
import time
if __name__ == "__main__":
    while True:
        time.sleep(1)
```

---

## Best Practices & Security

- **Sandboxing:** Always restrict file/network access to only what is needed. Use config to sandbox file operations.
- **Validate Input:** Never trust input from LibreAssistant or users—validate all paths, data, and parameters.
- **Graceful Shutdown:** Handle SIGTERM/SIGINT to clean up resources.
- **Minimal Permissions:** Request only the permissions your plugin needs.
- **Documentation:** Clearly document your endpoints, config, and permissions in the manifest and README.
- **Versioning:** Use semantic versioning for your plugin.
- **Testing:** Provide a test script or instructions for validating your plugin independently.

---

For more advanced examples, see the `plugins/` directory in this repository.
