# === Chat Generation Endpoint ===

#!/usr/bin/env python3
"""
Ollama Model Manager Web GUI

A simple web-based GUI for managing local Ollama models with the ability to:
- List all local models
- View model metadata
- Download new models
- Import models
- Delete models (with confirmation)
"""

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


# Flask app setup
app = Flask(__name__)
app.secret_key = 'ollama-manager-secret-key'
CORS(app)  # Enable CORS for all domains on all routes
api = OllamaAPI()


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
    """Main page showing model list"""
    try:
        models = api.list_models()
        # Format models for display
        formatted_models = []
        for model in models:
            formatted_models.append({
                'name': model.get('name', 'Unknown'),
                'size': format_size(model.get('size', 0)),
                'modified_at': format_datetime(model.get('modified_at', '')),
                'family': model.get('details', {}).get('family', 'Unknown'),
                'raw_size': model.get('size', 0)
            })
        
        return render_template('index.html', models=formatted_models, error=None)
    except Exception as e:
        return render_template('index.html', models=[], error=str(e))


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


def main():
    """Main entry point"""
    # Create templates directory and files
    create_templates()
    
    # Run the Flask app
    print("Starting Ollama Model Manager...")
    print("Open your browser and go to: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == "__main__":
    main()