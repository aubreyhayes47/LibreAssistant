#!/usr/bin/env python3
"""
Test script for the Ollama Manager to verify core functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ollama_manager import OllamaAPI, format_size, format_datetime, app
import requests
from unittest.mock import Mock, patch

def test_ollama_api():
    """Test the OllamaAPI class functionality"""
    print("Testing OllamaAPI class...")
    
    api = OllamaAPI()
    
    # Test that the API object is created correctly
    assert api.base_url == "http://localhost:11434"
    print("✓ API object created successfully")
    
    # Test with custom URL
    custom_api = OllamaAPI("http://example.com:8080/")
    assert custom_api.base_url == "http://example.com:8080"
    print("✓ Custom URL handled correctly")
    
    print("OllamaAPI tests passed!")

def test_utility_functions():
    """Test utility functions"""
    print("\nTesting utility functions...")
    
    # Test format_size
    assert format_size(0) == "0 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1024 * 1024) == "1.0 MB"
    assert format_size(1024 * 1024 * 1024) == "1.0 GB"
    print("✓ format_size function works correctly")
    
    # Test format_datetime
    test_date = "2024-01-15T10:30:00Z"
    formatted = format_datetime(test_date)
    assert "2024-01-15" in formatted
    print("✓ format_datetime function works correctly")
    
    print("Utility function tests passed!")

def test_flask_app():
    """Test Flask app creation and basic functionality"""
    print("\nTesting Flask app...")
    
    # Test app creation
    assert app is not None
    print("✓ Flask app created successfully")
    
    # Test that we can create a test client
    with app.test_client() as client:
        # Test that the app routes are registered
        assert '/api/models' in [rule.rule for rule in app.url_map.iter_rules()]
        assert '/api/download' in [rule.rule for rule in app.url_map.iter_rules()]
        assert '/api/delete' in [rule.rule for rule in app.url_map.iter_rules()]
        print("✓ API routes registered correctly")
        
        # Test that templates directory gets created
        from ollama_manager import create_templates
        create_templates()
        assert os.path.exists('templates')
        assert os.path.exists('templates/index.html')
        print("✓ Templates created successfully")
    
    print("Flask app tests passed!")

def test_api_endpoints():
    """Test API endpoints with mock data"""
    print("\nTesting API endpoints...")
    
    with app.test_client() as client:
        # Mock the OllamaAPI to avoid needing actual Ollama running
        with patch('ollama_manager.api') as mock_api:
            # Test successful models list
            mock_api.list_models.return_value = [
                {
                    'name': 'test-model',
                    'size': 1024,
                    'modified_at': '2024-01-15T10:30:00Z',
                    'details': {'family': 'test-family'}
                }
            ]
            
            response = client.get('/api/models')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] == True
            assert len(data['models']) == 1
            assert data['models'][0]['name'] == 'test-model'
            print("✓ /api/models endpoint works correctly")
            
            # Test download endpoint
            mock_api.pull_model.return_value = True
            response = client.post('/api/download', 
                                 json={'model_name': 'test-model'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] == True
            print("✓ /api/download endpoint works correctly")
            
            # Test delete endpoint
            mock_api.delete_model.return_value = True
            response = client.post('/api/delete', 
                                 json={'model_name': 'test-model'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] == True
            print("✓ /api/delete endpoint works correctly")
            
            # Test info endpoint
            mock_api.show_model_info.return_value = {
                'modelfile': 'test modelfile',
                'parameters': 'test parameters'
            }
            response = client.get('/api/info/test-model')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] == True
            assert 'info' in data
            print("✓ /api/info endpoint works correctly")
    
    print("API endpoints tests passed!")

def main():
    """Run all tests"""
    print("Running Ollama Manager tests...\n")
    
    try:
        test_ollama_api()
        test_utility_functions()
        test_flask_app()
        test_api_endpoints()
        
        print("\n🎉 All tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())