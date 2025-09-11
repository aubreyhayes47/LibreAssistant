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

    def test_mcp_servers_error_resilience(self):
        """Test MCP servers endpoint error resilience."""
        # Multiple rapid requests should all succeed
        for _ in range(10):
            response = self.client.get('/api/v1/mcp/servers')
            self.assertEqual(response.status_code, 200)
            self.assertIn('servers', response.json())

    def test_mcp_consent_comprehensive_error_cases(self):
        """Test comprehensive error cases for MCP consent endpoints."""
        
        # Test GET with various server names
        response = self.client.get('/api/v1/mcp/consent/nonexistent_server')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['consent'], False)
        
        # Test POST with missing consent field
        response = self.client.post('/api/v1/mcp/consent/test_server', json={})
        self.assertEqual(response.status_code, 422)
        
        # Test POST with invalid consent type
        response = self.client.post('/api/v1/mcp/consent/test_server', json={'consent': 'invalid'})
        self.assertEqual(response.status_code, 422)
        
        # Test POST with malformed JSON
        response = self.client.post('/api/v1/mcp/consent/test_server', 
                                  data='invalid json',
                                  headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 422)

    def test_history_endpoint_comprehensive_error_cases(self):
        """Test comprehensive error cases for history endpoints."""
        
        # Test GET for various user IDs
        test_user_ids = ['test_user', 'user_with_underscores', 'user-with-dashes', 'user123']
        for user_id in test_user_ids:
            response = self.client.get(f'/api/v1/history/{user_id}')
            self.assertEqual(response.status_code, 200)
            self.assertIn('history', response.json())
        
        # Test POST with missing fields
        response = self.client.post('/api/v1/history/test_user', json={})
        self.assertEqual(response.status_code, 422)
        
        # Test POST with invalid field types
        response = self.client.post('/api/v1/history/test_user', json={
            'plugin': 'test',
            'payload': 'invalid',  # Should be dict
            'granted': True
        })
        self.assertEqual(response.status_code, 422)

    def test_endpoint_integration_workflow(self):
        """Test integration workflow across multiple endpoints."""
        
        # 1. Check health
        health_response = self.client.get('/api/v1/health')
        self.assertEqual(health_response.status_code, 200)
        initial_requests = health_response.json()['requests']
        
        # 2. List MCP servers
        servers_response = self.client.get('/api/v1/mcp/servers')
        self.assertEqual(servers_response.status_code, 200)
        
        # 3. Set MCP consent
        consent_response = self.client.post('/api/v1/mcp/consent/workflow_test', 
                                          json={'consent': True})
        self.assertEqual(consent_response.status_code, 200)
        
        # 4. Check history
        history_response = self.client.get('/api/v1/history/workflow_user')
        self.assertEqual(history_response.status_code, 200)
        
        # 5. Record history entry
        record_response = self.client.post('/api/v1/history/workflow_user', json={
            'plugin': 'workflow_test',
            'payload': {'test': 'data'},
            'granted': True
        })
        self.assertEqual(record_response.status_code, 200)
        
        # 6. Verify health shows increased activity
        final_health = self.client.get('/api/v1/health')
        self.assertEqual(final_health.status_code, 200)
        final_requests = final_health.json()['requests']
        self.assertGreater(final_requests, initial_requests)

    def test_error_isolation_between_endpoints(self):
        """Test that errors in one endpoint don't affect others."""
        
        # Cause errors in various endpoints
        self.client.post('/api/v1/mcp/consent/test', json={})  # 422 error
        self.client.post('/api/v1/history/test', json={})     # 422 error
        
        # All endpoints should still work correctly
        self.assertEqual(self.client.get('/api/v1/health').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/mcp/servers').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/history/test_user').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/mcp/consent/test_server').status_code, 200)


if __name__ == '__main__':
    unittest.main()