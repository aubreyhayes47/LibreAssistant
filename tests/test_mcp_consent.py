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
