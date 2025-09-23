import sys
import os
# Ensure project root is in sys.path for plugin_config import (if needed in future)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load config (in real use, this would be loaded from plugin config)
BASE_DIR = os.path.expanduser(os.environ.get('LOCAL_FILEIO_BASEDIR', '~/LibreAssistantFiles'))

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR, exist_ok=True)

@app.route('/api/plugins', methods=['GET'])
def get_plugins():
    """Return plugin metadata for discovery"""
    return jsonify({
        'plugins': [{
            'name': 'Local File I/O',
            'id': 'local-fileio',
            'version': '1.0.0',
            'description': 'Securely read, write, list, and delete files on your device within a sandboxed directory.',
            'type': 'MCP Plugin',
            'status': 'running'
        }]
    })

def safe_path(path):
    """Ensure path is within BASE_DIR."""
    full = os.path.abspath(os.path.join(BASE_DIR, path))
    if not full.startswith(os.path.abspath(BASE_DIR)):
        raise ValueError('Access denied: outside sandbox')
    return full

@app.route('/list', methods=['POST'])
def list_files():
    data = request.get_json(force=True)
    rel_path = data.get('path', '')
    try:
        dir_path = safe_path(rel_path)
        if not os.path.isdir(dir_path):
            return jsonify({'success': False, 'error': 'Not a directory'})
        files = []
        for entry in os.scandir(dir_path):
            files.append({
                'name': entry.name,
                'is_dir': entry.is_dir(),
                'size': entry.stat().st_size if entry.is_file() else None
            })
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/read', methods=['POST'])
def read_file():
    data = request.get_json(force=True)
    rel_path = data.get('path')
    try:
        file_path = safe_path(rel_path)
        if not os.path.isfile(file_path):
            return jsonify({'success': False, 'error': 'Not a file'})
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/write', methods=['POST'])
def write_file():
    data = request.get_json(force=True)
    rel_path = data.get('path')
    content = data.get('content', '')
    try:
        file_path = safe_path(rel_path)
        dir_name = os.path.dirname(file_path)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete', methods=['POST'])
def delete_file():
    data = request.get_json(force=True)
    rel_path = data.get('path')
    try:
        file_path = safe_path(rel_path)
        if os.path.isdir(file_path):
            os.rmdir(file_path)
        else:
            os.remove(file_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    import os
    host = os.environ.get('PLUGIN_HOST', '0.0.0.0')
    port = int(os.environ.get('LOCAL_FILEIO_PORT', '5101'))
    app.run(host=host, port=port)
