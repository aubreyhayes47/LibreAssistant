

from collections import deque

from typing import List, Dict

# Rolling log of recent requests and their accessed plugins
RECENT_REQUESTS = deque(maxlen=20)  # Each entry: {'timestamp': ..., 'request_id': ..., 'plugins': [plugin_id, ...]}
CURRENT_REQUEST = {'request_id': None, 'plugins': []}

import uuid
import time


from flask import Flask, request, jsonify
from flask_cors import CORS
from plugin_config import PluginConfigManager
from plugin_loader import PluginLoader
plugin_loader = PluginLoader()
plugin_loader.discover_plugins()
config_manager = PluginConfigManager()




# Flask app setup
app = Flask(__name__)
CORS(app)

# Diagnostic health check route for test visibility
@app.route('/api/healthz')
def api_healthz():
    return jsonify({'status': 'ok'})

# Get plugin config
@app.route('/api/plugin/config/<plugin_id>', methods=['GET'])
def api_plugin_config_get(plugin_id):
    cfg = config_manager.get_plugin_config(plugin_id)
    return jsonify({'success': True, 'config': cfg})

# Set plugin config
@app.route('/api/plugin/config/<plugin_id>', methods=['POST'])
def api_plugin_config_set(plugin_id):
    data = request.get_json(force=True)
    config_manager.set_plugin_config(plugin_id, data.get('config', {}))
    return jsonify({'success': True})

# --- Plugin Activity Visualization Endpoint ---
@app.route('/api/plugins/activity')
def api_plugins_activity():
    """API endpoint to get real-time plugin activity for UI visualization"""
    try:
        # For each plugin, return id, name, icon, description, active (bool), lastAction
        plugins = []
        for plugin in plugin_loader.plugins:
            plugins.append({
                'id': plugin.id,
                'name': getattr(plugin, 'name', plugin.id),
                'icon': getattr(plugin, 'icon', None),
                'description': getattr(plugin, 'description', ''),
                'active': getattr(plugin, 'is_active', lambda: False)() or getattr(plugin, 'is_running', lambda: False)(),
                'lastAction': getattr(plugin, 'last_action', None)
            })
        return jsonify(plugins)
    except Exception as e:
        return jsonify([])


# Register plugin config endpoints after app is created


# Register all plugin endpoints after app and plugin_loader are initialized
@app.route('/api/plugin/status', methods=['GET'])
def api_plugin_status_all():
    plugin_loader.discover_plugins()  # Refresh status
    statuses = {}
    for plugin in plugin_loader.plugins:
        statuses[plugin.id] = {
            'status': plugin.status,
            'last_error': plugin.last_error,
            'running': plugin.is_running(),
        }
    return jsonify({'success': True, 'statuses': statuses})

@app.route('/api/plugin/status/<plugin_id>', methods=['GET'])
def api_plugin_status_one(plugin_id):
    plugin = plugin_loader.get_plugin_by_id(plugin_id)
    if not plugin:
        return jsonify({'success': False, 'error': 'Plugin not found'}), 404
    return jsonify({'success': True, 'status': plugin.status, 'last_error': plugin.last_error, 'running': plugin.is_running()})



@app.route('/api/plugin/permissions/<plugin_id>', methods=['GET'])
def api_plugin_permissions_get(plugin_id):
    plugin = plugin_loader.get_plugin_by_id(plugin_id)
    if not plugin:
        return jsonify({'success': False, 'error': 'Plugin not found'}), 404
    perms = plugin_loader.get_permissions_status(plugin)
    return jsonify({'success': True, **perms})

@app.route('/api/plugin/permissions/<plugin_id>', methods=['POST'])
def api_plugin_permissions_post(plugin_id):
    plugin = plugin_loader.get_plugin_by_id(plugin_id)
    if not plugin:
        return jsonify({'success': False, 'error': 'Plugin not found'}), 404
    data = request.get_json(force=True)
    grant = set(data.get('grant', []))
    plugin.approve_permissions(grant)
    return jsonify({'success': True})

@app.route('/api/plugin/enable', methods=['POST'])
def api_plugin_enable():
    plugin_id = request.json.get('plugin_id')
    if not plugin_id:
        return jsonify({'success': False, 'error': 'plugin_id required'})
    ok = plugin_loader.start_plugin(plugin_id)
    if ok:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to start plugin'})

@app.route('/api/plugin/disable', methods=['POST'])
def api_plugin_disable():
    plugin_id = request.json.get('plugin_id')
    if not plugin_id:
        return jsonify({'success': False, 'error': 'plugin_id required'})
    ok = plugin_loader.stop_plugin(plugin_id)
    if ok:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to stop plugin'})
# === Chat Generation Endpoint ===

#!/usr/bin/env python3
"""
LibreAssistant Manager Web GUI

A web-based GUI for managing both:
- Local Ollama models (list, view, download, import, delete)
- LibreAssistant plugins (MCP servers: list, view, install, import, delete, invoke)
"""
# ...existing code...

# --- Plugin API Client ---
class PluginAPI:
    """Client for interacting with LibreAssistant plugins (MCP servers)"""
    def __init__(self, plugin_loader=None):
        self.plugin_loader = plugin_loader or plugin_loader
        
    def _get_plugin_urls(self) -> List[str]:
        """Get all plugin server URLs from discovered plugins"""
        urls = []
        if self.plugin_loader:
            for plugin in self.plugin_loader.plugins:
                if hasattr(plugin, 'mcp_port') and plugin.mcp_port:
                    urls.append(f"http://localhost:{plugin.mcp_port}")
        return urls
    
    def list_plugins(self) -> List[Dict]:
        """Aggregate plugins from all plugin servers"""
        all_plugins = []
        plugin_urls = self._get_plugin_urls()
        
        # If no discovered plugins, return empty list
        if not plugin_urls:
            return []
            
        for base_url in plugin_urls:
            try:
                response = requests.get(f"{base_url}/api/plugins", timeout=10)
                response.raise_for_status()
                data = response.json()
                plugins = data.get('plugins', [])
                # Add server info to each plugin for identification
                for plugin in plugins:
                    plugin['server_url'] = base_url
                all_plugins.extend(plugins)
            except requests.RequestException as e:
                # Log error but continue with other servers
                print(f"Warning: Failed to connect to plugin server {base_url}: {e}")
                continue
        
        # If all servers failed, try the discovered plugins directly
        if not all_plugins and self.plugin_loader:
            for plugin in self.plugin_loader.plugins:
                all_plugins.append({
                    'name': getattr(plugin, 'name', plugin.id),
                    'id': getattr(plugin, 'id', 'unknown'),
                    'version': getattr(plugin, 'version', '1.0.0'),
                    'type': 'MCP Plugin',
                    'size': 0,
                    'modified_at': '',
                    'server_url': f"http://localhost:{getattr(plugin, 'mcp_port', 5001)}"
                })
                
        return all_plugins
    def install_plugin(self, plugin_name: str) -> bool:
        """Install plugin on the appropriate server"""
        plugin_urls = self._get_plugin_urls()
        
        for base_url in plugin_urls:
            try:
                response = requests.post(
                    f"{base_url}/api/install",
                    json={"name": plugin_name},
                    timeout=300
                )
                response.raise_for_status()
                return True
            except requests.RequestException:
                continue
        
        raise Exception(f"Failed to install plugin {plugin_name} on any available server")
    def delete_plugin(self, plugin_name: str) -> bool:
        """Delete plugin from the appropriate server"""
        plugin_urls = self._get_plugin_urls()
        
        for base_url in plugin_urls:
            try:
                response = requests.delete(
                    f"{base_url}/api/delete",
                    json={"name": plugin_name},
                    timeout=30
                )
                response.raise_for_status()
                return True
            except requests.RequestException:
                continue
        
        raise Exception(f"Failed to delete plugin {plugin_name} from any available server")
    def show_plugin_info(self, plugin_name: str) -> Dict:
        """Get plugin info from the appropriate server"""
        plugin_urls = self._get_plugin_urls()
        
        for base_url in plugin_urls:
            try:
                response = requests.post(
                    f"{base_url}/api/show",
                    json={"name": plugin_name},
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException:
                continue
        
        raise Exception(f"Failed to get info for plugin {plugin_name} from any available server")

    def invoke_plugin(self, plugin: str, input_data) -> Dict:
        """Invoke plugin on the appropriate server"""
        plugin_urls = self._get_plugin_urls()
        
        for base_url in plugin_urls:
            try:
                response = requests.post(
                    f"{base_url}/api/invoke",
                    json={"plugin": plugin, "input": input_data},
                    timeout=60
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException:
                continue
        
        raise Exception(f"Failed to invoke plugin {plugin} on any available server")

plugin_api = PluginAPI(plugin_loader)

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import requests
import json
import threading
from datetime import datetime
from typing import List, Dict, Optional
import os


class OllamaAPI:
    """Client for interacting with the Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
    
    def list_models(self) -> List[Dict]:
        """List all local models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('models', [])
        except requests.RequestException as e:
            raise Exception(f"Failed to connect to Ollama: {e}")
    
    def pull_model(self, model_name: str) -> bool:
        """Download/pull a model"""
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=300  # 5 minutes timeout for downloads
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            raise Exception(f"Failed to pull model: {e}")
    
    def delete_model(self, model_name: str) -> bool:
        """Delete a model"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/delete",
                json={"name": model_name},
                timeout=30
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            raise Exception(f"Failed to delete model: {e}")
    
    def show_model_info(self, model_name: str) -> Dict:
        """Get detailed information about a model"""
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model_name},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to get model info: {e}")

api = OllamaAPI()

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def format_datetime(dt_str: str) -> str:
    """Format datetime string to readable format"""
    try:
        # Parse ISO format datetime
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return dt_str




# === Chat Generation Endpoint ===
@app.route('/api/generate', methods=['POST'])
def api_generate():
    """API endpoint to generate a chat response using conversation history"""
    try:
        data = request.get_json(force=True)
        model = data.get('model')
        prompt = data.get('prompt')
        stream = data.get('stream', False)
        history = data.get('history', [])
        if not model or not prompt:
            return jsonify({'success': False, 'error': 'Model and prompt are required'}), 400

        # Build the full prompt from history
        full_prompt = ''
        for turn in history:
            role = turn.get('role', 'user')
            content = turn.get('content', '')
            if role == 'user':
                full_prompt += f"User: {content}\n"
            elif role == 'assistant':
                full_prompt += f"Assistant: {content}\n"
            else:
                full_prompt += f"{role.capitalize()}: {content}\n"
        full_prompt += f"User: {prompt}\nAssistant: "

        # Call Ollama API to generate a response
        try:
            response = requests.post(
                f"{api.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": stream
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return jsonify({
                'success': True,
                'response': data.get('response', '')
            })
        except requests.RequestException as e:
            return jsonify({'success': False, 'error': f'Failed to generate response: {e}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/')
def index():
    """Main page showing models and plugins"""
    try:
        models = api.list_models()
        plugins = plugin_api.list_plugins()
        formatted_models = []
        for model in models:
            formatted_models.append({
                'name': model.get('name', 'Unknown'),
                'size': format_size(model.get('size', 0)),
                'modified_at': format_datetime(model.get('modified_at', '')),
                'family': model.get('details', {}).get('family', 'Unknown'),
                'raw_size': model.get('size', 0)
            })
        formatted_plugins = []
        for plugin in plugins:
            formatted_plugins.append({
                'name': plugin.get('name', 'Unknown'),
                'size': format_size(plugin.get('size', 0)),
                'modified_at': format_datetime(plugin.get('modified_at', '')),
                'type': plugin.get('type', 'Unknown'),
                'raw_size': plugin.get('size', 0)
            })
        return render_template('index.html', models=formatted_models, plugins=formatted_plugins, error=None)
    except Exception as e:
        return render_template('index.html', models=[], plugins=[], error=str(e))

# --- Plugin endpoints ---
@app.route('/api/plugins')
def api_plugins():
    try:
        plugins = plugin_api.list_plugins()
        formatted_plugins = []
        for plugin in plugins:
            formatted_plugins.append({
                'name': plugin.get('name', 'Unknown'),
                'size': format_size(plugin.get('size', 0)),
                'modified_at': format_datetime(plugin.get('modified_at', '')),
                'type': plugin.get('type', 'Unknown'),
                'raw_size': plugin.get('size', 0)
            })
        return jsonify({'success': True, 'plugins': formatted_plugins})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/plugin/install', methods=['POST'])
def api_plugin_install():
    try:
        plugin_name = request.json.get('plugin_name')
        if not plugin_name:
            return jsonify({'success': False, 'error': 'Plugin name is required'})
        def install_plugin():
            try:
                plugin_api.install_plugin(plugin_name)
            except Exception as e:
                print(f"Install error: {e}")
        thread = threading.Thread(target=install_plugin)
        thread.daemon = True
        thread.start()
        return jsonify({'success': True, 'message': f'Install started for {plugin_name}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/plugin/delete', methods=['POST'])
def api_plugin_delete():
    try:
        plugin_name = request.json.get('plugin_name')
        if not plugin_name:
            return jsonify({'success': False, 'error': 'Plugin name is required'})
        plugin_api.delete_plugin(plugin_name)
        return jsonify({'success': True, 'message': f'Plugin {plugin_name} deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/plugin/info/<plugin_name>')
def api_plugin_info(plugin_name):
    try:
        info = plugin_api.show_plugin_info(plugin_name)
        return jsonify({'success': True, 'info': info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/plugin/invoke', methods=['POST'])
def api_plugin_invoke():
    try:
        data = request.get_json(force=True)
        plugin = data.get('plugin')
        input_data = data.get('input')
        if not plugin or input_data is None:
            return jsonify({'success': False, 'error': 'Plugin and input data are required'}), 400

        # Track plugin access for this request
        req_id = data.get('request_id') or str(uuid.uuid4())
        if CURRENT_REQUEST.get('request_id') != req_id:
            # New request, archive previous
            if CURRENT_REQUEST.get('request_id') is not None:
                RECENT_REQUESTS.append({
                    'timestamp': time.time(),
                    'request_id': CURRENT_REQUEST['request_id'],
                    'plugins': CURRENT_REQUEST['plugins'][:]
                })
            CURRENT_REQUEST['request_id'] = req_id
            CURRENT_REQUEST['plugins'] = []
        if plugin not in CURRENT_REQUEST['plugins']:
            CURRENT_REQUEST['plugins'].append(plugin)

        result = plugin_api.invoke_plugin(plugin, input_data)
        return jsonify({'success': True, 'response': result.get('response', ''), 'request_id': req_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
# Endpoint to get plugins accessed for the most recent request
@app.route('/api/plugins/accessed', methods=['GET'])
def api_plugins_accessed():
    """Return the list of plugin IDs accessed for the current or most recent request."""
    try:
        # Return current request if active, else last from RECENT_REQUESTS
        if CURRENT_REQUEST.get('request_id') and CURRENT_REQUEST['plugins']:
            return jsonify({'request_id': CURRENT_REQUEST['request_id'], 'plugins': CURRENT_REQUEST['plugins']})
        elif RECENT_REQUESTS:
            last = RECENT_REQUESTS[-1]
            return jsonify({'request_id': last['request_id'], 'plugins': last['plugins']})
        else:
            return jsonify({'request_id': None, 'plugins': []})
    except Exception as e:
        return jsonify({'request_id': None, 'plugins': [], 'error': str(e)})


@app.route('/api/models')
def api_models():
    """API endpoint to get models as JSON"""
    try:
        models = api.list_models()
        formatted_models = []
        for model in models:
            formatted_models.append({
                'name': model.get('name', 'Unknown'),
                'size': format_size(model.get('size', 0)),
                'modified_at': format_datetime(model.get('modified_at', '')),
                'family': model.get('details', {}).get('family', 'Unknown'),
                'raw_size': model.get('size', 0)
            })
        return jsonify({'success': True, 'models': formatted_models})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/download', methods=['POST'])
def api_download():
    """API endpoint to download a model"""
    try:
        model_name = request.json.get('model_name')
        if not model_name:
            return jsonify({'success': False, 'error': 'Model name is required'})
        
        # Start download in background thread
        def download_model():
            try:
                api.pull_model(model_name)
            except Exception as e:
                print(f"Download error: {e}")
        
        thread = threading.Thread(target=download_model)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': f'Download started for {model_name}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/delete', methods=['POST'])
def api_delete():
    """API endpoint to delete a model"""
    try:
        model_name = request.json.get('model_name')
        if not model_name:
            return jsonify({'success': False, 'error': 'Model name is required'})
        
        api.delete_model(model_name)
        return jsonify({'success': True, 'message': f'Model {model_name} deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/info/<model_name>')
def api_info(model_name):
    """API endpoint to get model information"""
    try:
        info = api.show_model_info(model_name)
        return jsonify({'success': True, 'info': info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/server/status')
def api_server_status():
    """API endpoint to get Ollama server status"""
    try:
        response = requests.get(f"{api.base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'status': 'running',
                'models_count': len(data.get('models', [])),
                'response_time': response.elapsed.total_seconds()
            })
        else:
            return jsonify({
                'success': True,
                'status': 'error',
                'error': f'HTTP {response.status_code}'
            })
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': True,
            'status': 'stopped',
            'error': 'Connection refused'
        })
    except requests.exceptions.Timeout:
        return jsonify({
            'success': True,
            'status': 'timeout',
            'error': 'Request timed out'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/server/logs')
def api_server_logs():
    """API endpoint to get recent server logs"""
    try:
        # Get server status first
        status_response = api_server_status()
        status_data = status_response.get_json()
        
        logs = []
        current_time = datetime.now().isoformat()
        
        if status_data.get('status') == 'running':
            # Server is running - generate realistic logs based on current state
            try:
                models_response = requests.get(f"{api.base_url}/api/tags", timeout=5)
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    models = models_data.get('models', [])
                    
                    logs.extend([
                        {
                            'timestamp': current_time,
                            'level': 'INFO',
                            'message': f'Ollama server is running on {api.base_url}'
                        },
                        {
                            'timestamp': current_time,
                            'level': 'INFO',
                            'message': f'Loaded {len(models)} models'
                        }
                    ])
                    
                    # Add logs for each model
                    for model in models[:3]:  # Limit to 3 most recent
                        logs.append({
                            'timestamp': current_time,
                            'level': 'SUCCESS',
                            'message': f'Model {model.get("name", "unknown")} is available'
                        })
                        
                    # Add API endpoint status
                    logs.append({
                        'timestamp': current_time,
                        'level': 'INFO',
                        'message': 'API endpoints responding normally'
                    })
                        
            except Exception as e:
                logs.append({
                    'timestamp': current_time,
                    'level': 'WARNING',
                    'message': f'Error checking models: {str(e)}'
                })
        else:
            # Server is not running
            logs.append({
                'timestamp': current_time,
                'level': 'ERROR',
                'message': f'Ollama server is not responding: {status_data.get("error", "Unknown error")}'
            })
            
        return jsonify({
            'success': True,
            'logs': logs
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/server/errors')
def api_server_errors():
    """API endpoint to get recent server errors"""
    try:
        # Get server status first
        status_response = api_server_status()
        status_data = status_response.get_json()
        
        errors = []
        current_time = datetime.now().isoformat()
        
        # Check for various error conditions
        if status_data.get('status') == 'stopped':
            errors.append({
                'timestamp': current_time,
                'level': 'critical',
                'title': 'Server Not Running',
                'error': 'Ollama server is not responding',
                'stack': 'Connection refused to ' + api.base_url,
                'suggestion': 'Start the Ollama server using "ollama serve" command'
            })
        elif status_data.get('status') == 'timeout':
            errors.append({
                'timestamp': current_time,
                'level': 'error',
                'title': 'Server Timeout',
                'error': 'Server request timed out',
                'stack': 'Request to ' + api.base_url + '/api/tags timed out',
                'suggestion': 'Check server load and network connectivity'
            })
        elif status_data.get('status') == 'error':
            errors.append({
                'timestamp': current_time,
                'level': 'error', 
                'title': 'Server Error',
                'error': status_data.get('error', 'Unknown server error'),
                'stack': 'HTTP response from ' + api.base_url,
                'suggestion': 'Check Ollama server logs for more details'
            })
        else:
            # Server is running, check for other potential issues
            response_time = status_data.get('response_time', 0)
            if response_time > 2.0:
                errors.append({
                    'timestamp': current_time,
                    'level': 'warning',
                    'title': 'Slow Response Time',
                    'error': f'API response time: {response_time:.2f}s (threshold: 2.0s)',
                    'stack': 'API response measurement',
                    'suggestion': 'Consider checking server load or using a smaller model'
                })
                
        return jsonify({
            'success': True,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# Test endpoint to simulate a running server (for demonstration)
@app.route('/api/server/test-running')
def api_server_test_running():
    """Test endpoint to demonstrate monitoring when server is running"""
    current_time = datetime.now().isoformat()
    
    # Simulate running server logs
    logs = [
        {
            'timestamp': current_time,
            'level': 'INFO',
            'message': 'Ollama server is running on http://localhost:11434'
        },
        {
            'timestamp': current_time,
            'level': 'INFO',
            'message': 'Loaded 3 models'
        },
        {
            'timestamp': current_time,
            'level': 'SUCCESS',
            'message': 'Model llama2:7b is available'
        },
        {
            'timestamp': current_time,
            'level': 'SUCCESS',
            'message': 'Model mistral:7b is available'
        },
        {
            'timestamp': current_time,
            'level': 'INFO',
            'message': 'API endpoints responding normally'
        }
    ]
    
    # When server is running, minimal errors (if any)
    errors = [
        {
            'timestamp': current_time,
            'level': 'warning',
            'title': 'Model Memory Usage',
            'error': 'Model llama2:7b using 4.2GB of memory',
            'stack': 'Memory monitor check',
            'suggestion': 'Monitor memory usage if running multiple models'
        }
    ]
    
    return jsonify({
        'success': True,
        'logs': logs,
        'errors': errors,
        'server_status': 'running'
    })


def create_templates():
    """Create the HTML templates directory and files"""
    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Main template
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ollama Model Manager</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
        }
        .actions {
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }
        .btn-primary {
            background-color: #007bff;
            color: white;
        }
        .btn-primary:hover {
            background-color: #0056b3;
        }
        .btn-success {
            background-color: #28a745;
            color: white;
        }
        .btn-success:hover {
            background-color: #1e7e34;
        }
        .btn-danger {
            background-color: #dc3545;
            color: white;
        }
        .btn-danger:hover {
            background-color: #c82333;
        }
        .btn-info {
            background-color: #17a2b8;
            color: white;
        }
        .btn-info:hover {
            background-color: #138496;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .error {
            color: #dc3545;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 4px;
            color: white;
            display: none;
            z-index: 1000;
        }
        .status.success {
            background-color: #28a745;
        }
        .status.error {
            background-color: #dc3545;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        .modal-content {
            background-color: white;
            margin: 15% auto;
            padding: 20px;
            border-radius: 8px;
            width: 80%;
            max-width: 600px;
            max-height: 70vh;
            overflow-y: auto;
        }
        .modal-header {
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }
        .close {
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close:hover {
            color: #dc3545;
        }
        pre {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Ollama Model Manager</h1>
            <p>Manage your local Ollama models</p>
        </div>

        {% if error %}
        <div class="error">
            <strong>Error:</strong> {{ error }}
        </div>
        {% endif %}

        <div class="actions">
            <button class="btn btn-primary" onclick="refreshModels()">Refresh</button>
            <button class="btn btn-success" onclick="downloadModel()">Download Model</button>
            <button class="btn btn-info" onclick="importModel()">Import Model</button>
            <button class="btn btn-danger" onclick="deleteSelectedModel()">Delete Selected</button>
            <button class="btn btn-info" onclick="showSelectedModelInfo()">Model Info</button>
        </div>

        <table id="modelsTable">
            <thead>
                <tr>
                    <th>Select</th>
                    <th>Model Name</th>
                    <th>Size</th>
                    <th>Modified</th>
                    <th>Family</th>
                </tr>
            </thead>
            <tbody>
                {% for model in models %}
                <tr>
                    <td><input type="radio" name="selectedModel" value="{{ model.name }}"></td>
                    <td>{{ model.name }}</td>
                    <td>{{ model.size }}</td>
                    <td>{{ model.modified_at }}</td>
                    <td>{{ model.family }}</td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="5" style="text-align: center; color: #666;">No models found</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Status notification -->
    <div id="status" class="status"></div>

    <!-- Modal for model info -->
    <div id="infoModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <span class="close" onclick="closeModal()">&times;</span>
                <h2 id="modalTitle">Model Information</h2>
            </div>
            <div id="modalBody">
                <!-- Model info will be inserted here -->
            </div>
        </div>
    </div>

    <script>
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + type;
            status.style.display = 'block';
            setTimeout(() => {
                status.style.display = 'none';
            }, 3000);
        }

        function getSelectedModel() {
            const selected = document.querySelector('input[name="selectedModel"]:checked');
            return selected ? selected.value : null;
        }

        function refreshModels() {
            showStatus('Refreshing models...', 'success');
            location.reload();
        }

        function downloadModel() {
            const modelName = prompt('Enter model name to download (e.g., llama2, mistral):');
            if (!modelName) return;

            showStatus('Starting download...', 'success');
            
            fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ model_name: modelName })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus(data.message, 'success');
                    setTimeout(refreshModels, 2000);
                } else {
                    showStatus('Error: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showStatus('Error: ' + error.message, 'error');
            });
        }

        function importModel() {
            alert('Model import functionality would be implemented here.\\nThis could involve importing from a file or another source.');
        }

        function deleteSelectedModel() {
            const modelName = getSelectedModel();
            if (!modelName) {
                alert('Please select a model first.');
                return;
            }

            if (!confirm(`Are you sure you want to delete the model '${modelName}'?\\n\\nThis action cannot be undone.`)) {
                return;
            }

            showStatus('Deleting model...', 'success');

            fetch('/api/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ model_name: modelName })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus(data.message, 'success');
                    setTimeout(refreshModels, 1000);
                } else {
                    showStatus('Error: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showStatus('Error: ' + error.message, 'error');
            });
        }

        function showSelectedModelInfo() {
            const modelName = getSelectedModel();
            if (!modelName) {
                alert('Please select a model first.');
                return;
            }

            showStatus('Fetching model info...', 'success');

            fetch(`/api/info/${encodeURIComponent(modelName)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayModelInfo(modelName, data.info);
                    showStatus('Model info loaded', 'success');
                } else {
                    showStatus('Error: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showStatus('Error: ' + error.message, 'error');
            });
        }

        function displayModelInfo(modelName, info) {
            const modal = document.getElementById('infoModal');
            const title = document.getElementById('modalTitle');
            const body = document.getElementById('modalBody');

            title.textContent = `Model Info: ${modelName}`;

            let content = `<h3>Model: ${modelName}</h3>`;
            
            if (info.modelfile) {
                content += `<h4>Modelfile:</h4><pre>${info.modelfile}</pre>`;
            }
            
            if (info.parameters) {
                content += `<h4>Parameters:</h4><pre>${info.parameters}</pre>`;
            }
            
            if (info.template) {
                content += `<h4>Template:</h4><pre>${info.template}</pre>`;
            }
            
            if (info.details) {
                content += '<h4>Details:</h4><ul>';
                for (const [key, value] of Object.entries(info.details)) {
                    content += `<li><strong>${key}:</strong> ${value}</li>`;
                }
                content += '</ul>';
            }

            body.innerHTML = content;
            modal.style.display = 'block';
        }

        function closeModal() {
            document.getElementById('infoModal').style.display = 'none';
        }

        // Close modal when clicking outside of it
        window.onclick = function(event) {
            const modal = document.getElementById('infoModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
    </script>
</body>
</html>'''
    
    with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
        f.write(index_html)


## (Removed main() and app.run() to avoid duplicate app context in tests)