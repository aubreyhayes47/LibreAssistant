# Export PluginLoader, Plugin, PluginManifestError, and loader/validator functions

__all__ = [
    "PluginLoader", "Plugin", "PluginManifestError",
    "load_plugin_manifest", "validate_plugin_manifest"
]

# Load a plugin manifest from a file
def load_plugin_manifest(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Validate a plugin manifest using the schema
def validate_plugin_manifest(manifest: dict) -> bool:
    schema_path = SCHEMA_PATH
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    validate(instance=manifest, schema=schema)
    return True
## (removed duplicate __all__ assignment)
"""
LibreAssistant Plugin Loader
- Discovers plugins in the /plugins directory
- Reads and validates plugin manifests (plugin.json)
- Builds a registry of available plugins
- (Lifecycle: start/stop logic in next step)
"""

import os
import json
import subprocess
import threading
import time
from typing import Dict, List, Optional
from jsonschema import validate, ValidationError


PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "plugins")
MANIFEST_FILENAME = "plugin-manifest.json"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "plugin-manifest.schema.json")


class PluginManifestError(Exception):
    pass

class Plugin:
    def __init__(self, manifest: Dict, path: str):
        self.manifest = manifest
        self.path = path
        self.id = manifest.get("id")
        self.name = manifest.get("name")
        self.version = manifest.get("version")
        self.description = manifest.get("description")
        self.author = manifest.get("author")
        self.entrypoint = manifest.get("entrypoint")
        self.mcp_port = manifest.get("mcp_port")
        self.permissions = manifest.get("permissions", [])
        self.config = manifest.get("config", {})
        self.homepage = manifest.get("homepage")
        self.license = manifest.get("license")
        self.granted_permissions = set()
        self.user_approved = False
        self.log_dir = os.path.join(self.path, "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.stdout_log = os.path.join(self.log_dir, "stdout.log")
        self.stderr_log = os.path.join(self.log_dir, "stderr.log")
        self.process = None
        self.status = "stopped"  # "running", "stopped", "error"
        self.last_error = None
        self.stdout_file = None
        self.stderr_file = None

    def __repr__(self):
        return f"<Plugin {self.id} v{self.version} at {self.path} status={self.status}>"

    def permissions_required(self) -> set:
        return set(self.permissions)

    def permissions_granted(self) -> set:
        return set(self.granted_permissions)

    def needs_user_approval(self) -> bool:
        # Sensitive permissions requiring explicit user consent
        sensitive = {"file_io", "network", "read_config", "write_config"}
        return bool(sensitive & self.permissions_required())

    def approve_permissions(self, granted: set):
        self.granted_permissions = granted
        self.user_approved = True

    def start(self, extra_env: Optional[Dict[str, str]] = None) -> bool:
        # Enforce permissions: only start if all required permissions are granted
        if not self.user_approved and self.needs_user_approval():
            print(f"[Plugin] User approval required for permissions: {self.permissions_required() - self.permissions_granted()}")
            self.status = "blocked"
            self.last_error = "User approval required for permissions."
            return False
        if not self.permissions_required() <= self.permissions_granted():
            print(f"[Plugin] Not all required permissions granted for {self.id}: {self.permissions_required() - self.permissions_granted()}")
            self.status = "blocked"
            self.last_error = "Not all required permissions granted."
            return False
        if self.process and self.process.poll() is None:
            self.status = "running"
            return True  # Already running
        try:
            env = os.environ.copy()
            if extra_env:
                env.update(extra_env)
            # Split entrypoint for subprocess, run in plugin dir
            cmd = self.entrypoint if isinstance(self.entrypoint, list) else self.entrypoint.split()
            self.stdout_file = open(self.stdout_log, "ab")
            self.stderr_file = open(self.stderr_log, "ab")
            self.process = subprocess.Popen(
                cmd,
                cwd=self.path,
                env=env,
                stdout=self.stdout_file,
                stderr=self.stderr_file,
            )
            self.status = "running"
            self.last_error = None
            # Start a thread to monitor process
            threading.Thread(target=self._monitor_process, daemon=True).start()
            return True
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            print(f"[Plugin] Failed to start {self.id}: {e}")
            return False
    # Permissions enforcement and user consent scaffolding
    def get_permissions_status(self, plugin: 'Plugin') -> Dict:
        """Return dict of required, granted, and missing permissions for a plugin."""
        required = plugin.permissions_required()
        granted = plugin.permissions_granted()
        missing = required - granted
        return {
            "required": required,
            "granted": granted,
            "missing": missing,
            "user_approved": plugin.user_approved
        }

    def prompt_user_for_permissions(self, plugin: 'Plugin') -> set:
        """Stub: In production, integrate with UI/backend to prompt user for permissions."""
        # For now, auto-approve all permissions (replace with real UI prompt)
        print(f"[PluginLoader] Prompting user to approve permissions for {plugin.id}: {plugin.permissions_required()}")
        # In a real app, this would be a UI dialog or API call
        return plugin.permissions_required()

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.status = "stopped"
        self.process = None
        
        # Close file handles
        if self.stdout_file:
            self.stdout_file.close()
            self.stdout_file = None
        if self.stderr_file:
            self.stderr_file.close()
            self.stderr_file = None

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None
    
    def is_reachable(self) -> bool:
        """Check if plugin is reachable via HTTP (more reliable than process tracking)"""
        if not self.mcp_port:
            return False
        try:
            import requests
            response = requests.get(f"http://localhost:{self.mcp_port}/api/plugins", timeout=2)
            return response.status_code == 200
        except:
            return False

    def _monitor_process(self):
        if not self.process:
            return
        try:
            self.process.wait()
            if self.process.returncode == 0:
                self.status = "stopped"
            else:
                self.status = "error"
                self.last_error = f"Exited with code {self.process.returncode}"
                print(f"[Plugin] {self.id} crashed or exited with error code {self.process.returncode}")
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            print(f"[Plugin] {self.id} monitor error: {e}")

    def get_logs(self, n_lines: int = 50) -> Dict[str, str]:
        """Return the last n lines of stdout and stderr logs for this plugin."""
        def tail(filepath):
            if not os.path.isfile(filepath):
                return ""
            with open(filepath, "rb") as f:
                try:
                    f.seek(0, os.SEEK_END)
                    size = f.tell()
                    block = 4096
                    data = b""
                    while size > 0 and data.count(b"\n") <= n_lines:
                        read_size = min(block, size)
                        size -= read_size
                        f.seek(size)
                        data = f.read(read_size) + data
                    return b"\n".join(data.splitlines()[-n_lines:]).decode(errors="replace")
                except Exception:
                    return ""
        return {
            "stdout": tail(self.stdout_log),
            "stderr": tail(self.stderr_log)
        }



# PluginLoader class at module level
class PluginLoader:
    def __init__(self, plugin_dir: Optional[str] = None, schema_path: Optional[str] = None):
        self.plugin_dir = plugin_dir or PLUGIN_DIR
        self.plugins: List[Plugin] = []
        self.schema_path = schema_path or SCHEMA_PATH
        self._schema = None

    def _load_schema(self):
        if self._schema is None:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
        return self._schema

    def validate_manifest(self, manifest: Dict, manifest_path: str):
        schema = self._load_schema()
        try:
            validate(instance=manifest, schema=schema)
        except ValidationError as e:
            raise PluginManifestError(f"Manifest validation failed for {manifest_path}: {e.message}")

    def discover_plugins(self) -> List['Plugin']:
        self.plugins = []
        if not os.path.isdir(self.plugin_dir):
            return []
        for entry in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, entry)
            if os.path.isdir(plugin_path):
                manifest_path = os.path.join(plugin_path, MANIFEST_FILENAME)
                if os.path.isfile(manifest_path):
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            manifest = json.load(f)
                        self.validate_manifest(manifest, manifest_path)
                        plugin = Plugin(manifest, plugin_path)
                        self.plugins.append(plugin)
                    except Exception as e:
                        print(f"[PluginLoader] Error loading {manifest_path}: {e}")
        return self.plugins

    def start_plugin(self, plugin_id: str, extra_env: Optional[Dict[str, str]] = None) -> bool:
        plugin = self.get_plugin_by_id(plugin_id)
        if not plugin:
            print(f"[PluginLoader] Plugin {plugin_id} not found.")
            return False
        # Prompt for permissions if needed
        if plugin.needs_user_approval() and not plugin.user_approved:
            granted = self.prompt_user_for_permissions(plugin)
            plugin.approve_permissions(granted)
        return plugin.start(extra_env=extra_env)

    def stop_plugin(self, plugin_id: str) -> bool:
        plugin = self.get_plugin_by_id(plugin_id)
        if not plugin:
            print(f"[PluginLoader] Plugin {plugin_id} not found.")
            return False
        plugin.stop()
        return True

    def stop_all_plugins(self):
        for plugin in self.plugins:
            plugin.stop()

    def get_plugin_by_id(self, plugin_id: str) -> Optional['Plugin']:
        for plugin in self.plugins:
            if plugin.id == plugin_id:
                return plugin
        return None

    def auto_approve_all_plugins(self):
        """Auto-approve all permissions for all plugins (for auto-start mode)"""
        for plugin in self.plugins:
            if plugin.permissions_required():
                plugin.approve_permissions(plugin.permissions_required())
                plugin.user_approved = True
                print(f"[AutoStart] Auto-approved permissions for {plugin.id}: {plugin.permissions_required()}")

    def prompt_user_for_permissions(self, plugin: 'Plugin') -> set:
        """Stub: In production, integrate with UI/backend to prompt user for permissions."""
        # For now, auto-approve all permissions (replace with real UI prompt)
        print(f"[PluginLoader] Auto-approving permissions for {plugin.id}: {plugin.permissions_required()}")
        # In a real app, this would be a UI dialog or API call
        return plugin.permissions_required()

# Example usage (for testing):
# if __name__ == "__main__":
#     loader = PluginLoader()
#     plugins = loader.discover_plugins()
#     print(f"Discovered {len(plugins)} plugins:")
#     for plugin in plugins:
#         print(f"- {plugin.name} ({plugin.id}) v{plugin.version}")
