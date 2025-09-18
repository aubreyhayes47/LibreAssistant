from typing import Dict
def validate_plugin_config(schema: Dict, config: Dict) -> bool:
    for key, meta in schema.items():
        if meta.get('required') and key not in config:
            raise Exception(f"Missing required config field: {key}")
        if key in config:
            if meta.get('type') == 'string' and not isinstance(config[key], str):
                raise Exception(f"Config field {key} must be a string")
            # Add more type checks as needed
    return True
"""
plugin_config.py: Plugin configuration management for LibreAssistant
- Stores and retrieves plugin config (API keys, settings) securely
- Provides backend methods for UI to get/set config
- Passes config to plugin MCP servers at startup (via env or stdin)
"""
import os
import json
from typing import Dict, Optional

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "plugin_config.json")

class PluginConfigManager:
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or CONFIG_FILE
        self._config = self._load_config()

    def _load_config(self) -> Dict:
        if os.path.isfile(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_config(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2)

    def get_plugin_config(self, plugin_id: str) -> Dict:
        return self._config.get(plugin_id, {})

    def set_plugin_config(self, plugin_id: str, config: Dict):
        self._config[plugin_id] = config
        self._save_config()

    def update_plugin_config(self, plugin_id: str, updates: Dict):
        cfg = self._config.get(plugin_id, {})
        cfg.update(updates)
        self._config[plugin_id] = cfg
        self._save_config()

    def delete_plugin_config(self, plugin_id: str):
        if plugin_id in self._config:
            del self._config[plugin_id]
            self._save_config()


# Top-level helpers for test compatibility (must be after class definition)
_default_manager = PluginConfigManager()
def get_plugin_config(plugin_id: str):
    return _default_manager.get_plugin_config(plugin_id)
def set_plugin_config(plugin_id: str, config: dict):
    return _default_manager.set_plugin_config(plugin_id, config)

# Top-level helpers for test compatibility (must be after class definition)
_default_manager = PluginConfigManager()
def get_plugin_config(plugin_id: str):
    return _default_manager.get_plugin_config(plugin_id)
def set_plugin_config(plugin_id: str, config: dict):
    return _default_manager.set_plugin_config(plugin_id, config)

# Example usage (backend):
if __name__ == "__main__":
    mgr = PluginConfigManager()
    mgr.set_plugin_config("brave-search", {"api_key": "sk-123"})
    print(mgr.get_plugin_config("brave-search"))
    mgr.update_plugin_config("brave-search", {"region": "us"})
    print(mgr.get_plugin_config("brave-search"))
    mgr.delete_plugin_config("brave-search")
    print(mgr.get_plugin_config("brave-search"))
