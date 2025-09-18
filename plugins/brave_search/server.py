import sys
import os
# Ensure project root is in sys.path for plugin_config import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import os
import json
from flask import Flask, request, jsonify
from plugin_config import get_plugin_config
import requests

app = Flask(__name__)

PLUGIN_ID = "brave_search"
BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"

@app.route('/api/plugins', methods=['GET'])
def get_plugins():
    """Return plugin metadata for discovery"""
    return jsonify({
        'plugins': [{
            'name': 'Brave Search',
            'id': 'brave-search',
            'version': '1.0.0',
            'description': 'Search the web using Brave Search API. Returns relevant web results for a given query.',
            'type': 'MCP Plugin',
            'status': 'running'
        }]
    })

# Helper to get API key from config
def get_api_key():
    config = get_plugin_config(PLUGIN_ID)
    key = config.get("api_key")
    if not key:
        raise Exception("Brave Search API key not configured.")
    return key

@app.route("/search", methods=["POST"])
def search_web():
    data = request.get_json(force=True)
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "error": "Missing search query."}), 400
    try:
        api_key = get_api_key()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 401
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key
    }
    params = {"q": query, "count": 10}
    try:
        resp = requests.get(BRAVE_API_URL, headers=headers, params=params, timeout=10)
        if resp.status_code == 401:
            return jsonify({"success": False, "error": "Invalid or missing Brave Search API key."}), 401
        resp.raise_for_status()
        results = resp.json().get("web", {}).get("results", [])
        return jsonify({"success": True, "results": results})
    except requests.RequestException as e:
        return jsonify({"success": False, "error": f"Network error: {e}"}), 502
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Optionally, add get_result_details endpoint if Brave API supports it

if __name__ == "__main__":
    app.run(port=5103)
