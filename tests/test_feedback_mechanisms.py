# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for user feedback mechanisms in LibreAssistant."""

import unittest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestFeedbackMechanisms(unittest.TestCase):
    """Test that all actions provide clear feedback."""

    def setUp(self):
        # Import here to avoid module not found issues
        try:
            from libreassistant.main import create_app
            self.app = create_app()
            self.client = TestClient(self.app)
        except ImportError:
            self.skipTest("FastAPI dependencies not available")

    def test_request_generation_success_feedback(self):
        """Test that successful request generation returns appropriate response."""
        # Mock the provider to return a successful response
        with patch('libreassistant.providers.providers.generate') as mock_generate:
            mock_generate.return_value = "Test response"
            
            response = self.client.post('/api/v1/generate', json={
                'provider': 'cloud',
                'prompt': 'test prompt'
            })
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('result', response.json())
            self.assertEqual(response.json()['result'], 'Test response')

    def test_request_generation_error_feedback(self):
        """Test that failed request generation returns error details."""
        with patch('libreassistant.providers.providers.generate') as mock_generate:
            mock_generate.side_effect = ValueError("API key missing")
            
            response = self.client.post('/api/v1/generate', json={
                'provider': 'cloud',
                'prompt': 'test prompt'
            })
            
            self.assertEqual(response.status_code, 400)
            self.assertIn('detail', response.json())
            self.assertEqual(response.json()['detail'], 'API key missing')

    def test_plugin_consent_success_feedback(self):
        """Test that plugin consent changes return success status."""
        response = self.client.post('/api/v1/mcp/consent/test_plugin', json={
            'consent': True
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

    def test_plugin_consent_retrieval(self):
        """Test that plugin consent status can be retrieved."""
        # Set consent first
        self.client.post('/api/v1/mcp/consent/test_plugin', json={
            'consent': True
        })
        
        response = self.client.get('/api/v1/mcp/consent/test_plugin')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('consent', response.json())
        self.assertTrue(response.json()['consent'])

    def test_theme_preference_success_feedback(self):
        """Test that theme preference changes return success status."""
        response = self.client.post('/api/v1/themes/preference/test_user', json={
            'theme_id': 'dark'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        self.assertEqual(response.json()['theme'], 'dark')

    def test_theme_preference_retrieval(self):
        """Test that theme preferences can be retrieved."""
        response = self.client.get('/api/v1/themes/preference/test_user')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('theme', response.json())

    def test_theme_css_success_feedback(self):
        """Test that theme CSS loading returns appropriate headers."""
        # Test with a built-in theme
        response = self.client.get('/api/v1/themes/light.css')
        
        # Should return 200 or 404 if theme doesn't exist
        self.assertIn(response.status_code, [200, 404])
        
        if response.status_code == 200:
            self.assertEqual(response.headers['content-type'], 'text/css; charset=utf-8')

    def test_mcp_servers_listing(self):
        """Test that MCP servers can be listed with consent status."""
        response = self.client.get('/api/v1/mcp/servers')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('servers', response.json())
        # Should be a list (can be empty)
        self.assertIsInstance(response.json()['servers'], list)

    def test_plugin_invoke_error_feedback(self):
        """Test that plugin invocation errors return appropriate feedback."""
        response = self.client.post('/api/v1/invoke', json={
            'plugin': 'nonexistent_plugin',
            'user_id': 'test_user',
            'payload': {'message': 'test'}
        })
        
        self.assertEqual(response.status_code, 404)
        self.assertIn('detail', response.json())
        self.assertEqual(response.json()['detail'], 'Plugin not found')

    def test_provider_key_setting_feedback(self):
        """Test that provider key setting returns success feedback."""
        response = self.client.post('/api/v1/providers/cloud/key', json={
            'key': 'test_api_key'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

    def test_health_endpoint_feedback(self):
        """Test that health endpoint provides system status."""
        response = self.client.get('/api/v1/health')
        
        self.assertEqual(response.status_code, 200)
        # Should contain metrics about system health
        data = response.json()
        self.assertIsInstance(data, dict)


if __name__ == '__main__':
    unittest.main()