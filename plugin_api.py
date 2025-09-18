"""
PluginAPI: Communication layer for LibreAssistant MCP plugins
- Sends JSON-RPC requests to plugin MCP servers (over HTTP)
- Handles registration, action invocation, and error handling
- Aligns with MCP (Model Context Protocol) standards
"""
import requests
import uuid
import time
from typing import Any, Dict, Optional

class PluginAPIError(Exception):
    pass

class PluginAPI:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def _json_rpc(self, method: str, params: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}/rpc"
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            if 'error' in data:
                raise PluginAPIError(data['error'])
            return data.get('result')
        except Exception as e:
            raise PluginAPIError(f"Plugin API call failed: {e}")

    def get_manifest(self) -> Dict:
        """Fetch plugin manifest/capabilities from the MCP server."""
        return self._json_rpc("get_manifest")

    def list_actions(self) -> Dict:
        """List available actions/capabilities provided by the plugin."""
        return self._json_rpc("list_actions")

    def invoke_action(self, action: str, params: Optional[Dict] = None) -> Any:
        """Invoke a specific action/capability on the plugin."""
        return self._json_rpc(action, params)

    def health_check(self) -> bool:
        """Check if the plugin MCP server is alive and responsive."""
        try:
            result = self._json_rpc("health_check")
            return result is True
        except PluginAPIError:
            return False

# Example usage:
if __name__ == "__main__":
    # Example: plugin running at http://localhost:5101
    api = PluginAPI("http://localhost:5101")
    try:
        print("Manifest:", api.get_manifest())
        print("Actions:", api.list_actions())
        print("Health check:", api.health_check())
        # Example action invocation:
        # print(api.invoke_action("search", {"query": "LibreAssistant"}))
    except PluginAPIError as e:
        print("Plugin API error:", e)
