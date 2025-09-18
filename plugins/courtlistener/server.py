import sys
import os
# Ensure project root is in sys.path for plugin_config import (if needed in future)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Default API key (LibreAssistant CourtListener Key)
DEFAULT_API_KEY = "6348098dc6c452a31ec930d5211eba732e1235d5"

@app.route('/api/plugins', methods=['GET'])
def get_plugins():
    """Return plugin metadata for discovery"""
    return jsonify({
        'plugins': [{
            'name': 'CourtListener',
            'id': 'courtlistener',
            'version': '1.0.0',
            'description': 'Legal research plugin for US court opinions, dockets, and case search via the CourtListener API.',
            'type': 'MCP Plugin',
            'status': 'running'
        }]
    })

# Load config (in real use, this would be loaded from plugin config)
def get_api_key():
    # Try env var, then config file, then default
    key = os.environ.get("COURTLISTENER_API_KEY")
    if key:
        return key
    # Try config file
    config_path = os.path.join(os.path.dirname(__file__), "plugin-config.json")
    if os.path.exists(config_path):
        import json
        with open(config_path) as f:
            cfg = json.load(f)
            if "api_key" in cfg:
                return cfg["api_key"]
    return DEFAULT_API_KEY

API_BASE = "https://www.courtlistener.com/api/rest/v3"

# --- API Endpoints ---
@app.route("/search", methods=["POST"])
def search_cases():
    data = request.get_json(force=True)
    query = data.get("query", "")
    params = data.get("params", {})
    api_key = get_api_key()
    headers = {"Authorization": f"Token {api_key}"}
    try:
        resp = requests.get(f"{API_BASE}/search/", params={"q": query, **params}, headers=headers, timeout=15)
        resp.raise_for_status()
        return jsonify({"success": True, "results": resp.json()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/opinion", methods=["POST"])
def fetch_opinion():
    data = request.get_json(force=True)
    opinion_id = data.get("opinion_id")
    api_key = get_api_key()
    headers = {"Authorization": f"Token {api_key}"}
    try:
        resp = requests.get(f"{API_BASE}/opinions/{opinion_id}/", headers=headers, timeout=15)
        resp.raise_for_status()
        return jsonify({"success": True, "opinion": resp.json()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/docket", methods=["POST"])
def get_docket():
    data = request.get_json(force=True)
    docket_id = data.get("docket_id")
    api_key = get_api_key()
    headers = {"Authorization": f"Token {api_key}"}
    try:
        resp = requests.get(f"{API_BASE}/dockets/{docket_id}/", headers=headers, timeout=15)
        resp.raise_for_status()
        return jsonify({"success": True, "docket": resp.json()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5102)
