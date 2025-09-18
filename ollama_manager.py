

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
from llm_protocol import llm_protocol, LLMProtocolError
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
    """API endpoint to generate a chat response using conversation history with plugin support"""
    try:
        data = request.get_json(force=True)
        model = data.get('model')
        prompt = data.get('prompt')
        stream = data.get('stream', False)
        history = data.get('history', [])
        use_schema = data.get('use_schema', True)  # Enable schema by default
        
        if not model or not prompt:
            return jsonify({'success': False, 'error': 'Model and prompt are required'}), 400

        # Get available plugins for system instructions
        available_plugins = []
        try:
            plugins = plugin_api.list_plugins()
            for plugin in plugins:
                # Get plugin capabilities from manifest or default info
                plugin_info = {
                    'id': plugin.get('name', 'unknown').lower().replace(' ', '_'),
                    'name': plugin.get('name', 'Unknown'),
                    'description': plugin.get('description', 'No description available'),
                    'capabilities': []  # This could be enhanced with actual capability discovery
                }
                available_plugins.append(plugin_info)
        except Exception as e:
            print(f"Warning: Could not fetch plugins for system instructions: {e}")

        # Build the full prompt from history
        if use_schema:
            # Use structured system instructions
            system_instructions = llm_protocol.generate_system_instructions(available_plugins)
            full_prompt = f"{system_instructions}\n\nConversation History:\n"
        else:
            # Use legacy format for backward compatibility
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

        # Track request for plugin access monitoring
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
            ollama_data = response.json()
            llm_response = ollama_data.get('response', '')
            
            if not use_schema:
                # Legacy mode - return response as-is
                return jsonify({
                    'success': True,
                    'response': llm_response,
                    'request_id': req_id
                })
            
            # Parse and route the structured response
            try:
                parsed_response = llm_protocol.parse_response(llm_response)
                
                if llm_protocol.is_plugin_invocation(parsed_response):
                    # Handle plugin invocation
                    plugin_id, plugin_input, reason = llm_protocol.extract_plugin_call(parsed_response)
                    
                    # Track plugin access
                    if plugin_id not in CURRENT_REQUEST['plugins']:
                        CURRENT_REQUEST['plugins'].append(plugin_id)
                    
                    # Invoke the plugin
                    try:
                        plugin_result = plugin_api.invoke_plugin(plugin_id, plugin_input)
                        
                        # Generate follow-up prompt for LLM to process plugin result
                        follow_up_prompt = llm_protocol.create_plugin_result_prompt(
                            plugin_id, plugin_result, prompt
                        )
                        
                        # Call LLM again to process plugin result
                        follow_up_response = requests.post(
                            f"{api.base_url}/api/generate",
                            json={
                                "model": model,
                                "prompt": follow_up_prompt,
                                "stream": False  # Use non-streaming for plugin result processing
                            },
                            timeout=60
                        )
                        follow_up_response.raise_for_status()
                        follow_up_data = follow_up_response.json()
                        final_response = follow_up_data.get('response', '')
                        
                        # Parse the final response
                        final_parsed = llm_protocol.parse_response(final_response)
                        if llm_protocol.is_user_message(final_parsed):
                            text, markdown = llm_protocol.extract_user_message(final_parsed)
                            return jsonify({
                                'success': True,
                                'response': text,
                                'plugin_used': plugin_id,
                                'plugin_reason': reason,
                                'markdown': markdown,
                                'request_id': req_id
                            })
                        else:
                            # Fallback if LLM doesn't return a proper message
                            return jsonify({
                                'success': True,
                                'response': f"Plugin {plugin_id} executed successfully. Result: {plugin_result.get('response', plugin_result)}",
                                'plugin_used': plugin_id,
                                'plugin_reason': reason,
                                'request_id': req_id
                            })
                    
                    except Exception as plugin_error:
                        return jsonify({
                            'success': False,
                            'error': f'Plugin {plugin_id} execution failed: {str(plugin_error)}',
                            'request_id': req_id
                        })
                
                elif llm_protocol.is_user_message(parsed_response):
                    # Handle user-facing message
                    text, markdown = llm_protocol.extract_user_message(parsed_response)
                    return jsonify({
                        'success': True,
                        'response': text,
                        'markdown': markdown,
                        'request_id': req_id
                    })
                
                else:
                    # Fallback for unexpected response format
                    return jsonify({
                        'success': True,
                        'response': llm_response,
                        'schema_error': 'Unexpected response format',
                        'request_id': req_id
                    })
                    
            except LLMProtocolError as e:
                # Schema validation failed, return raw response with warning
                return jsonify({
                    'success': True,
                    'response': llm_response,
                    'schema_error': str(e),
                    'request_id': req_id
                })
                
        except requests.RequestException as e:
            return jsonify({'success': False, 'error': f'Failed to generate response: {e}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/llm/schema', methods=['GET'])
def api_llm_schema():
    """API endpoint to get the LLM response schema"""
    try:
        schema = llm_protocol._load_schema()
        return jsonify({'success': True, 'schema': schema})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/llm/validate', methods=['POST'])
def api_llm_validate():
    """API endpoint to validate an LLM response against the schema"""
    try:
        data = request.get_json(force=True)
        response_data = data.get('response')
        if response_data is None:
            return jsonify({'success': False, 'error': 'Response data is required'})
        
        llm_protocol.validate_response(response_data)
        return jsonify({'success': True, 'valid': True})
    except LLMProtocolError as e:
        return jsonify({'success': True, 'valid': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/llm/system_instructions', methods=['GET'])
def api_llm_system_instructions():
    """API endpoint to get current system instructions with available plugins"""
    try:
        available_plugins = []
        try:
            plugins = plugin_api.list_plugins()
            for plugin in plugins:
                plugin_info = {
                    'id': plugin.get('name', 'unknown').lower().replace(' ', '_'),
                    'name': plugin.get('name', 'Unknown'),
                    'description': plugin.get('description', 'No description available'),
                    'capabilities': []
                }
                available_plugins.append(plugin_info)
        except Exception as e:
            print(f"Warning: Could not fetch plugins for system instructions: {e}")
        
        instructions = llm_protocol.generate_system_instructions(available_plugins)
        return jsonify({
            'success': True, 
            'instructions': instructions,
            'plugins': available_plugins
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


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

@app.route('/chat')
def chat():
    """Chat interface"""
    return render_template('chat.html')

@app.route('/demo')
def demo():
    """Demo interface"""
    return render_template('demo.html')

@app.route('/plugin_catalogue')
def plugin_catalogue():
    """Plugin catalogue interface"""
    return render_template('plugin_catalogue.html')

@app.route('/requests_screen')
def requests_screen():
    """Requests screen interface"""
    return render_template('requests_screen.html')

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
    """Create the HTML templates directory"""
    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)


## (Removed main() and app.run() to avoid duplicate app context in tests)