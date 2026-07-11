"""MCP server configuration — built-in servers, Google template, and user-defined server loading with validation."""
import json, os
from pathlib import Path

from ..config import CONFIG_DIR

# Built-in server: CourtListener MCP (uses DCR for dynamic client registration)
# Why a BUILTIN_SERVERS pattern?  Built-in servers ship with the app and require
# no user configuration — they're always available.  User-defined servers from
# mcp_servers.json are appended after, so built-ins can't be accidentally overridden
# or removed by a malformed user config.
BUILTIN_SERVERS = [
    {
        "name": "courtlistener",
        "transport": "http",
        "url": "https://mcp.courtlistener.com/",
        "oauth": {
            "dcr": True,
            "scopes": ["openid", "api"],
            "registration_url": "https://www.courtlistener.com/o/register/",
            "auth_meta_url": "https://mcp.courtlistener.com/.well-known/oauth-protected-resource",
        },
    },
]

# Google API servers template (Gmail, Drive, Calendar). Activated only when LIBREASSISTANT_GOOGLE_CLIENT_* env vars are set.
# Why env-gated?  Google OAuth requires a registered client_id/client_secret.
# Shipping hardcoded credentials would be a security risk and would break for users
# who haven't set up their own Google Cloud project.  The env-var gate lets users
# opt in without polluting the UI for those who don't use Google services.
GOOGLE_SERVERS_TEMPLATE = [
    {
        "name": "google-gmail",
        "transport": "http",
        "url": "https://gmailmcp.googleapis.com/mcp/v1",
        "oauth": {
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "auth_meta_url": None,
        },
    },
    {
        "name": "google-drive",
        "transport": "http",
        "url": "https://drivemcp.googleapis.com/mcp/v1",
        "oauth": {
            "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "auth_meta_url": None,
        },
    },
    {
        "name": "google-calendar",
        "transport": "http",
        "url": "https://calendarmcp.googleapis.com/mcp/v1",
        "oauth": {
            "scopes": ["https://www.googleapis.com/auth/calendar.events.readonly"],
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "auth_meta_url": None,
        },
    },
]

MCP_SERVERS_PATH = CONFIG_DIR / "mcp_servers.json"  # Path to user-defined server configs (JSON list or {"servers": [...]})

def _validate_server_entry(entry: dict, index: int) -> str | None:
    """Validate a user-supplied MCP server entry. Returns error message or None.

    What makes a server config valid:
    - Must be a dict with a non-empty string `name` (used as tool prefix and key).
    - `transport` must be "http" or "stdio" (no other transports supported).
    - HTTP servers require a `url` starting with http:// or https://.
    - stdio servers require a `command` string (the executable to launch).
    - If `oauth` is present, it must be a dict (contents not validated here —
      errors surface at runtime when the OAuth flow is attempted).

    Validation is intentionally strict on required fields but lenient on optional
    ones (like oauth), so that partially-configured servers fail gracefully at
    auth time rather than blocking startup entirely.
    """
    if not isinstance(entry, dict):
        return f"Entry {index} is not a dictionary"
    if not isinstance(entry.get("name"), str) or not entry["name"].strip():
        return f"Entry {index}: missing or invalid 'name' (must be non-empty string)"
    if not isinstance(entry.get("transport"), str):
        return f"Entry {index} ('{entry.get('name', '?')}'): missing or invalid 'transport' (must be string)"
    if entry["transport"] not in ("http", "stdio"):
        return f"Entry {index} ('{entry['name']}'): 'transport' must be 'http' or 'stdio', got '{entry['transport']}'"
    if entry["transport"] == "http":
        url = entry.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            return f"Entry {index} ('{entry['name']}'): missing or invalid 'url' for http transport"
    if entry["transport"] == "stdio":
        if not isinstance(entry.get("command"), str):
            return f"Entry {index} ('{entry['name']}'): missing 'command' for stdio transport"
    if "oauth" in entry and not isinstance(entry["oauth"], dict):
        return f"Entry {index} ('{entry['name']}'): 'oauth' must be a dictionary if present"
    return None


def get_servers() -> list[dict]:
    """Assemble the full server list: built-in + Google (if env-configured) + user-defined (validated).

    The merged list is ordered deliberately:
    1. Built-in servers always come first — they ship with the app and can't be
       accidentally removed or overridden by a malformed user config.
    2. Google servers (env-gated) come second — they require user-provided credentials.
    3. User-defined servers from mcp_servers.json come last — they're validated but
       cannot shadow built-in names (MCPManager deduplicates by name on connect).

    This order ensures the most reliable servers are attempted first, giving the
    best startup experience even if user config is broken.
    """
    servers = list(BUILTIN_SERVERS)

    client_id = os.environ.get("LIBREASSISTANT_GOOGLE_CLIENT_ID")  # Google servers are enabled only when both client_id and client_secret are set in the environment
    client_secret = os.environ.get("LIBREASSISTANT_GOOGLE_CLIENT_SECRET")
    if client_id and client_secret:
        for g in GOOGLE_SERVERS_TEMPLATE:
            servers.append({
                "name": g["name"],
                "transport": "http",
                "url": g["url"],
                "oauth": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scopes": g["oauth"]["scopes"],
                    "auth_url": g["oauth"]["auth_url"],
                    "token_url": g["oauth"]["token_url"],
                    "auth_meta_url": g["oauth"]["auth_meta_url"],
                },
            })
    else:
        pass  # Google not configured — skip silently; CLI may still warn at startup

    # Load and validate user-defined servers from mcp_servers.json
    if MCP_SERVERS_PATH.exists():
        try:
            user_data = json.loads(MCP_SERVERS_PATH.read_text())
            user_servers = user_data if isinstance(user_data, list) else user_data.get("servers", [])  # Accept either a top-level list or {"servers": [...]} for backward compatibility
            if not isinstance(user_servers, list):
                print(f"Warning: {MCP_SERVERS_PATH}: expected a list of server configs, got {type(user_servers).__name__}")
            else:
                for i, entry in enumerate(user_servers):
                    err = _validate_server_entry(entry, i)
                    if err:
                        print(f"Warning: {MCP_SERVERS_PATH}: {err}")
                    else:
                        servers.append(entry)
        except (json.JSONDecodeError, Exception) as e:  # Corrupt file is skipped entirely rather than aborting startup
            print(f"Warning: {MCP_SERVERS_PATH} is invalid ({e}), ignoring.")

    return servers
