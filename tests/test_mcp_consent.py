# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

from fastapi.testclient import TestClient


def test_mcp_consent_endpoints(client: TestClient) -> None:
    resp = client.get('/api/v1/mcp/servers')
    data = resp.json()
    names = {s['name'] for s in data['servers']}
    assert 'echo' in names
    off = client.post('/api/v1/mcp/consent/echo', json={'consent': False})
    assert off.status_code == 200
    check = client.get('/api/v1/mcp/consent/echo')
    assert check.json()['consent'] is False
    client.post('/api/v1/mcp/consent/echo', json={'consent': True})


def test_mcp_consent_error_cases(client: TestClient) -> None:
    """Test error cases for MCP consent endpoints."""
    
    # Test POST with missing consent field
    response = client.post('/api/v1/mcp/consent/test_server', json={})
    assert response.status_code == 422  # Validation error
    
    # Test POST with invalid consent type
    response = client.post('/api/v1/mcp/consent/test_server', json={'consent': 'invalid'})
    assert response.status_code == 422  # Validation error
    
    # Test POST with null consent
    response = client.post('/api/v1/mcp/consent/test_server', json={'consent': None})
    assert response.status_code == 422  # Validation error
    
    # Test GET for nonexistent server (should return default False)
    response = client.get('/api/v1/mcp/consent/nonexistent_server')
    assert response.status_code == 200
    assert response.json()['consent'] is False


def test_mcp_consent_workflow(client: TestClient) -> None:
    """Test complete MCP consent workflow."""
    server_name = 'workflow_test_server'
    
    # Initial state should be False
    response = client.get(f'/api/v1/mcp/consent/{server_name}')
    assert response.status_code == 200
    assert response.json()['consent'] is False
    
    # Set to True
    response = client.post(f'/api/v1/mcp/consent/{server_name}', json={'consent': True})
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
    
    # Verify it's True
    response = client.get(f'/api/v1/mcp/consent/{server_name}')
    assert response.status_code == 200
    assert response.json()['consent'] is True
    
    # Set back to False
    response = client.post(f'/api/v1/mcp/consent/{server_name}', json={'consent': False})
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
    
    # Verify it's False
    response = client.get(f'/api/v1/mcp/consent/{server_name}')
    assert response.status_code == 200
    assert response.json()['consent'] is False


def test_mcp_servers_endpoint_comprehensive(client: TestClient) -> None:
    """Test MCP servers endpoint comprehensively."""
    response = client.get('/api/v1/mcp/servers')
    
    assert response.status_code == 200
    data = response.json()
    assert 'servers' in data
    assert isinstance(data['servers'], list)
    
    # Each server should have required fields
    for server in data['servers']:
        assert 'name' in server
        assert 'consent' in server
        assert isinstance(server['consent'], bool)
