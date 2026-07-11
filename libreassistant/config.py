"""Configuration file management: API key storage, config load/save, and text sanitization."""

import json, os, re, sys
from getpass import getpass
from pathlib import Path

def kms_mode() -> bool:
    """Check if --kms flag was passed on the command line. Read-only — never set this programmatically.
    Why read sys.argv instead of a module-level variable?  This function is imported and
    called by file_ops.py and terminal.py which run in background threads.  A module-level
    variable would need to be set before import time or risk races; sys.argv is immutable
    after startup and safe to read from any thread.
    """
    return "--kms" in sys.argv

CONFIG_DIR = Path.home() / ".libreassistant"  # All persistent state lives under ~/.libreassistant/
# Why a hidden directory?  `~/.libreassistant/` follows the XDG Base Directory convention
# for application state (analogous to ~/.config/).  The leading dot hides it from casual
# directory listings, reducing the chance that a user accidentally modifies or deletes
# config/session/token files.
CONFIG_PATH = CONFIG_DIR / "config.json"

_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")  # Regex matches ASCII control characters (0x00-0x1F except tab/linefeed/carriage return, plus 0x7F DEL)

def strip_control_chars(text: str | None) -> str:
    # Strip ASCII control characters from text.
    # Why needed?  LLM output may contain terminal escape sequences (e.g. CSI codes,
    # bell characters) that a terminal emulator could interpret.  Stripping them prevents
    # terminal injection attacks where otherwise-innocuous output could hide malicious
    # escape sequences that alter terminal behavior or leak info.
    if text is None:
        return ""
    return _CTRL_RE.sub("", text)

def get_api_key() -> str:
    # Retrieve API key from config file, or prompt the user to enter and persist one
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
            if cfg.get("api_key"):
                return cfg["api_key"]
        except json.JSONDecodeError:
            print(f"Warning: {CONFIG_PATH} is corrupted, ignoring.")
    print("No API key found.")  # No key on disk — prompt interactively
    # Why prompt interactively instead of erroring out?  First-run UX:
    # the user shouldn't have to hunt for a config file on initial launch.
    # getpass() hides the key on screen (no shoulder-surfing) and stdin
    # pipelining still works for scripting.
    key = getpass("Enter your Zen API key (oc-...): ")
    # Atomically write key to disk with restrictive permissions (atomic replace via temp file)
    # Why atomic?  If the process crashes mid-write, the original file remains intact.
    # The .tmp → replace sequence is an atomic rename on POSIX; chmod 600 ensures only
    # the owner can read the API key.  Same pattern used in save_config() and oauth.save_tokens().
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump({"api_key": key}, f, indent=2)
    os.chmod(tmp, 0o600)
    tmp.replace(CONFIG_PATH)
    print(f"Saved to {CONFIG_PATH}")
    return key

def load_config() -> dict:
    # Load the full config dict with sensible defaults
    cfg = {"api_key": None, "search_provider": "duckduckgo", "search_api_key": None}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                cfg.update(json.load(f))
        except json.JSONDecodeError:
            pass
    return cfg

def save_config(updates: dict) -> None:
    # Save config updates atomically: write to .tmp, chmod, then replace
    cfg = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
        except json.JSONDecodeError:
            pass
    cfg.update(updates)
    # Atomic write: temp file + chmod 600 + replace ensures no partial writes or leaked secrets
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(tmp, 0o600)
    tmp.replace(CONFIG_PATH)
