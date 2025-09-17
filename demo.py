#!/usr/bin/env python3
"""
Demo version of Ollama Manager with mock data for testing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ollama_manager import app, create_templates
from unittest.mock import patch

# Mock data for demonstration
MOCK_MODELS = [
    {
        'name': 'llama2:7b',
        'size': 3825200000,  # ~3.8GB
        'modified_at': '2024-01-15T10:30:00Z',
        'details': {'family': 'llama'}
    },
    {
        'name': 'mistral:7b',
        'size': 4109000000,  # ~4.1GB
        'modified_at': '2024-01-14T14:20:00Z',
        'details': {'family': 'mistral'}
    },
    {
        'name': 'codellama:13b',
        'size': 7365000000,  # ~7.4GB
        'modified_at': '2024-01-13T09:15:00Z',
        'details': {'family': 'llama'}
    }
]

def mock_list_models():
    return MOCK_MODELS

def mock_pull_model(model_name):
    return True

def mock_delete_model(model_name):
    return True

def mock_show_model_info(model_name):
    return {
        'modelfile': f'FROM {model_name}\nPARAMETER temperature 0.8',
        'parameters': 'temperature 0.8\ntop_p 0.9\nrepeat_penalty 1.1',
        'template': '{{ .System }}\n\n{{ .Prompt }}',
        'details': {
            'family': 'llama',
            'format': 'gguf',
            'families': ['llama'],
            'parameter_size': '7B',
            'quantization_level': 'Q4_0'
        }
    }

def main():
    """Run the demo version with mocked data"""
    create_templates()
    
    print("Starting Ollama Model Manager Demo...")
    print("This version runs with mock data for demonstration purposes.")
    print("Open your browser and go to: http://localhost:5000")
    print()
    
    # Patch the API methods with mock implementations
    with patch('ollama_manager.api.list_models', side_effect=mock_list_models), \
         patch('ollama_manager.api.pull_model', side_effect=mock_pull_model), \
         patch('ollama_manager.api.delete_model', side_effect=mock_delete_model), \
         patch('ollama_manager.api.show_model_info', side_effect=mock_show_model_info):
        
        app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()