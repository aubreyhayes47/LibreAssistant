"""File read/write operations with home-directory sandboxing."""
import os
import subprocess
from pathlib import Path

from ..config import kms_mode as _kms_mode
from ..prompt import user_prompt

_SANDBOX_ROOT: str | None = None  # Set via set_sandbox_root(); None = Path.home()
# Why module-level state with a setter?  The sandbox root is configured once at
# startup (from --sandbox-root) and read on every file operation.  A module-level
# variable avoids threading the root through every function signature, while the
# setter keeps it overridable for tests.
def set_sandbox_root(path: str | None) -> None:
    global _SANDBOX_ROOT
    _SANDBOX_ROOT = path

MAX_READ_SIZE = 10 * 1024 * 1024  # 10 MB

SENSITIVE_PATHS = [
    # Why a separate deny list in addition to the sandbox?  The sandbox restricts
    # access to the home directory, but ~/.ssh, ~/.gnupg, etc. are INSIDE the home
    # directory.  This deny list provides defense-in-depth: even in --kms mode (which
    # bypasses the sandbox), sensitive credential directories remain blocked.
    Path.home() / ".ssh",
    Path.home() / ".gnupg",
    Path.home() / ".config" / "chromium",
    Path.home() / ".config" / "google-chrome",
    Path.home() / ".password-store",
    Path.home() / ".aws",
    Path.home() / ".kube",
    Path.home() / ".docker",
]


# Resolve a user-supplied path and enforce the sandbox.
# Why this specific ordering: resolve → sensitive → sandbox?
# 1. resolve() first (expanduser + resolve): canonicalizes symlinks and "../" so that
#    subsequent checks operate on the real path, not a tricksy relative form.
# 2. Sensitive path check second: even if --kms bypasses the sandbox, ~/.ssh, ~/.gnupg,
#    etc. remain blocked.  This is defense-in-depth — the deny list is independent of
#    the sandbox boundary.
# 3. Sandbox check last: only applies when --kms is NOT active.  By this point the path
#    is fully resolved, so relative_to() correctly catches symlink escapes that
#    startswith() would miss.
def _resolve_path(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    for sensitive in SENSITIVE_PATHS:
        try:
            p.relative_to(sensitive)
            raise PermissionError(f"Error: access to {sensitive} is restricted")
        except ValueError:
            pass
    if p.name == ".env":
        raise PermissionError("Error: access to .env files is restricted")
    base = Path(_SANDBOX_ROOT).expanduser().resolve() if _SANDBOX_ROOT else Path.home()
    if not _kms_mode():  # bypass sandbox when --kms is active
        try:
            p.relative_to(base)
        except ValueError:
            raise PermissionError(
                f"Path must be under {base} for safety. "
                f"Use --kms flag to allow any path."
            )
    return p


def read_file(args: dict) -> str:
    """Read a file's contents as text. Supports PDF extraction via pdftotext. Returns error string on failure."""
    path = args.get("path", "")
    if not path:
        return "Error: path is required"
    try:
        p = _resolve_path(path)
        if not p.exists():
            return f"Error: file not found: {p}"

        # Reject files over 10 MB to avoid memory pressure
        file_size = p.stat().st_size
        if file_size > MAX_READ_SIZE:
            return (
                f"Error: file too large ({file_size} bytes). "
                f"Maximum read size is {MAX_READ_SIZE} bytes (10 MB). "
                "Use terminal tool with tools like 'head' or 'split' for large files."
            )

        data = p.read_bytes()

        # PDF detection by magic bytes
        # Check magic bytes — handles mislabelled Content-Type from web-downloaded files
        if data[:5] == b"%PDF-":
            try:
                result = subprocess.run(
                    ["pdftotext", "-", "-"],
                    input=data,
                    capture_output=True,
                    timeout=30,
                )
                text = result.stdout
                if not text.strip():
                    text = "(PDF appears to have no extractable text)"
                return text
            except FileNotFoundError:
                return (
                    f"File is a PDF ({len(data)} bytes). "
                    "Install pdftotext (part of poppler-utils) to extract text, "
                    "or use the terminal tool with another method."
                )

        # Try UTF-8 first; fall back to latin-1 (which never fails on arbitrary bytes) thereby guaranteeing no data loss
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1")

        return text
    except PermissionError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading file: {e}"


def save_file(args: dict) -> str:
    """Write content to a file, creating parent directories as needed. Returns a status message."""
    path = args.get("path", "")
    content = args.get("content", "")
    if not path:
        return "Error: path is required"
    try:
        p = _resolve_path(path)
        # Auto-create parent directories: save_file is "create or overwrite", so
        # mkdir(parents=True) lets the LLM write to new paths without a prior mkdir call.
        # append_file intentionally does NOT create parents — it's "append to existing",
        # and creating a file under a nonexistent directory is likely a path error.
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        size = len(content.encode("utf-8"))
        return f"File saved: {p} ({size} bytes)"
    except PermissionError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error saving file: {e}"


def append_file(args: dict) -> str:
    """Append content to an existing file."""
    path = args.get("path", "")
    content = args.get("content", "")
    if not path:
        return "Error: path is required"
    try:
        p = _resolve_path(path)
        if not p.exists():  # fail early if target does not exist (append-only semantics)
            return f"Error: file not found: {p}"
        with p.open("a") as f:
            f.write(content)
        return f"Appended to {p} ({len(content)} chars)"
    except PermissionError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error appending to file: {e}"


def delete_file(args: dict) -> str:
    """Delete a file with interactive confirmation (unless --kms is active)."""
    path = args.get("path", "")
    if not path:
        return "Error: path is required"
    try:
        p = _resolve_path(path)
        if not p.exists():
            return f"Error: file not found: {p}"
        if not p.is_file():
            return f"Error: not a file: {p}"

        # Interactive confirmation — skipped in --kms mode
        if not _kms_mode():
            print(f"\n[!] Delete this file?")
            print(f"    {p}")
            answer = user_prompt("Delete? [y/N]: ")
            if answer != "y":
                return "Delete cancelled."

        p.unlink()
        return f"Deleted: {p}"
    except PermissionError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error deleting file: {e}"
