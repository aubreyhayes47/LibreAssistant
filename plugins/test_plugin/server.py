import sys
import os
# Ensure project root is in sys.path for plugin_config import (if needed in future)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import json
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/plugins', methods=['GET'])
def get_plugins():
    """Return plugin metadata for discovery"""
    return jsonify({
        'plugins': [{
            'name': 'Test Plugin',
            'id': 'test-plugin',
            'version': '1.0.0',
            'description': 'A dummy plugin for testing enable/disable/config endpoints.',
            'type': 'MCP Plugin',
            'status': 'running'
        }]
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5199, debug=False)
