# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""
Comprehensive edge case testing for all UI endpoints.
Ensures all endpoints used by the UI are exercised with various edge cases.
"""

from __future__ import annotations


def test_mcp_servers_endpoint_edge_cases(client) -> None:
    """Test edge cases for /api/v1/mcp/servers endpoint."""
    
    # Basic functionality
    response = client.get("/api/v1/mcp/servers")
    assert response.status_code == 200
    data = response.json()
    assert "servers" in data
    assert isinstance(data["servers"], list)
    
    # Multiple rapid requests should be handled gracefully
    for _ in range(15):
        resp = client.get("/api/v1/mcp/servers")
        assert resp.status_code == 200
        assert "servers" in resp.json()
    
    # Server structure validation
    for server in data["servers"]:
        assert "name" in server
        assert "consent" in server
        assert isinstance(server["name"], str)
        assert isinstance(server["consent"], bool)


def test_mcp_consent_endpoint_special_server_names(client) -> None:
    """Test MCP consent endpoints with various server name formats."""
    
    # Test with various server name formats
    server_names = [
        "simple_server",
        "server-with-dashes",
        "server_with_underscores",
        "ServerWithCaps",
        "server123",
        "server.with.dots",
        "a",  # Single character
        "very_long_server_name_that_exceeds_normal_length_expectations_but_should_still_work"
    ]
    
    for server_name in server_names:
        # Test GET (should always work)
        response = client.get(f"/api/v1/mcp/consent/{server_name}")
        assert response.status_code == 200
        assert "consent" in response.json()
        assert isinstance(response.json()["consent"], bool)
        
        # Test POST with valid consent
        response = client.post(
            f"/api/v1/mcp/consent/{server_name}",
            json={"consent": True}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        
        # Verify the consent was set
        response = client.get(f"/api/v1/mcp/consent/{server_name}")
        assert response.status_code == 200
        assert response.json()["consent"] is True


def test_mcp_consent_json_edge_cases(client) -> None:
    """Test MCP consent POST endpoint with various JSON edge cases."""
    
    server_name = "json_test_server"
    
    # Valid cases
    valid_cases = [
        {"consent": True},
        {"consent": False},
    ]
    
    for case in valid_cases:
        response = client.post(f"/api/v1/mcp/consent/{server_name}", json=case)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    # Invalid cases that should return 422
    invalid_cases = [
        {},  # Missing consent field
        {"consent": None},  # Null consent
        {"consent": "true"},  # String instead of boolean
        {"consent": 1},  # Number instead of boolean
        {"consent": []},  # Array instead of boolean
        {"consent": {}},  # Object instead of boolean
        {"invalid_field": True},  # Wrong field name
        {"consent": True, "extra": "field"},  # Extra fields (may be accepted depending on Pydantic config)
    ]
    
    for case in invalid_cases[:6]:  # Skip the last case as it may be valid depending on config
        response = client.post(f"/api/v1/mcp/consent/{server_name}", json=case)
        assert response.status_code == 422, f"Case {case} should return 422 but got {response.status_code}"


def test_history_endpoint_user_id_edge_cases(client) -> None:
    """Test history endpoints with various user ID formats."""
    
    # Test with various user ID formats
    user_ids = [
        "simple_user",
        "user-with-dashes",
        "user_with_underscores",
        "UserWithCaps",
        "user123",
        "user.with.dots",
        "u",  # Single character
        "very_long_user_id_that_exceeds_normal_expectations_but_should_work",
        "user@email.com",  # Email-like format
        "user%20with%20spaces",  # URL encoded spaces
    ]
    
    for user_id in user_ids:
        # Test GET (should always work)
        response = client.get(f"/api/v1/history/{user_id}")
        assert response.status_code == 200, f"GET failed for user_id: {user_id}"
        data = response.json()
        assert "history" in data
        assert isinstance(data["history"], list)
        
        # Test POST with valid history entry
        response = client.post(
            f"/api/v1/history/{user_id}",
            json={
                "plugin": "test_plugin",
                "payload": {"test": "data"},
                "granted": True
            }
        )
        assert response.status_code == 200, f"POST failed for user_id: {user_id}"
        assert response.json()["status"] == "ok"


def test_history_endpoint_payload_edge_cases(client) -> None:
    """Test history POST endpoint with various payload formats."""
    
    user_id = "payload_test_user"
    
    # Valid payload cases
    valid_payloads = [
        {"simple": "value"},
        {"nested": {"object": {"with": "values"}}},
        {"array": [1, 2, 3]},
        {"mixed": {"string": "value", "number": 42, "boolean": True, "null": None}},
        {"empty": {}},
        {"unicode": "🚀 Test with emojis and ñ special chars"},
        {"large_string": "x" * 1000},  # Large string
    ]
    
    for i, payload in enumerate(valid_payloads):
        response = client.post(
            f"/api/v1/history/{user_id}",
            json={
                "plugin": f"test_plugin_{i}",
                "payload": payload,
                "granted": True
            }
        )
        assert response.status_code == 200, f"Failed for payload: {payload}"
        assert response.json()["status"] == "ok"


def test_health_endpoint_consistency(client) -> None:
    """Test health endpoint consistency under various conditions."""
    
    # Get baseline health
    baseline = client.get("/api/v1/health")
    assert baseline.status_code == 200
    baseline_data = baseline.json()
    
    # Required fields
    required_fields = ["requests", "uptime"]
    for field in required_fields:
        assert field in baseline_data, f"Missing required field: {field}"
    
    # Generate some activity
    activity_requests = []
    for i in range(10):
        # Mix different endpoint calls
        activity_requests.append(client.get("/api/v1/mcp/servers"))
        activity_requests.append(client.get(f"/api/v1/history/activity_user_{i}"))
        activity_requests.append(client.get(f"/api/v1/mcp/consent/activity_server_{i}"))
    
    # All activity requests should succeed
    for req in activity_requests:
        assert req.status_code == 200
    
    # Health should still work and show increased activity
    post_activity = client.get("/api/v1/health")
    assert post_activity.status_code == 200
    post_activity_data = post_activity.json()
    
    # Request count should have increased
    assert post_activity_data["requests"] > baseline_data["requests"]
    
    # Uptime should still be reasonable (not negative, not too large)
    assert post_activity_data["uptime"] >= 0
    assert post_activity_data["uptime"] < 3600  # Less than 1 hour for tests


def test_endpoint_error_recovery(client) -> None:
    """Test that endpoints recover gracefully from error conditions."""
    
    # Cause various errors
    error_requests = [
        # MCP consent errors
        lambda: client.post("/api/v1/mcp/consent/test", json={}),
        lambda: client.post("/api/v1/mcp/consent/test", json={"consent": "invalid"}),
        
        # History errors
        lambda: client.post("/api/v1/history/test", json={}),
        lambda: client.post("/api/v1/history/test", json={"plugin": "test"}),
        
        # Non-existent endpoints
        lambda: client.get("/api/v1/nonexistent"),
        lambda: client.post("/api/v1/nonexistent", json={}),
    ]
    
    # Generate errors
    for error_func in error_requests:
        response = error_func()
        # Should get error responses, not crashes
        assert response.status_code in [404, 422, 500]
    
    # After errors, all main endpoints should still work
    test_endpoints = [
        lambda: client.get("/api/v1/health"),
        lambda: client.get("/api/v1/mcp/servers"), 
        lambda: client.get("/api/v1/history/recovery_test_user"),
        lambda: client.get("/api/v1/mcp/consent/recovery_test_server"),
    ]
    
    for test_func in test_endpoints:
        response = test_func()
        assert response.status_code == 200, f"Endpoint failed after errors: {test_func}"


def test_cross_endpoint_data_consistency(client) -> None:
    """Test data consistency across related endpoints."""
    
    # Test MCP consent consistency
    server_name = "consistency_test_server"
    
    # Set consent to True
    set_response = client.post(
        f"/api/v1/mcp/consent/{server_name}",
        json={"consent": True}
    )
    assert set_response.status_code == 200
    
    # Verify via GET
    get_response = client.get(f"/api/v1/mcp/consent/{server_name}")
    assert get_response.status_code == 200
    assert get_response.json()["consent"] is True
    
    # Set consent to False
    set_response = client.post(
        f"/api/v1/mcp/consent/{server_name}",
        json={"consent": False}
    )
    assert set_response.status_code == 200
    
    # Verify via GET
    get_response = client.get(f"/api/v1/mcp/consent/{server_name}")
    assert get_response.status_code == 200
    assert get_response.json()["consent"] is False
    
    # Test history consistency
    user_id = "consistency_test_user"
    
    # Record multiple history entries
    entries = [
        {"plugin": "plugin_1", "payload": {"test": 1}, "granted": True},
        {"plugin": "plugin_2", "payload": {"test": 2}, "granted": False},
        {"plugin": "plugin_3", "payload": {"test": 3}, "granted": True},
    ]
    
    for entry in entries:
        response = client.post(f"/api/v1/history/{user_id}", json=entry)
        assert response.status_code == 200
    
    # Verify all entries are in history
    history_response = client.get(f"/api/v1/history/{user_id}")
    assert history_response.status_code == 200
    history_data = history_response.json()["history"]
    
    # Should have at least the entries we added
    assert len(history_data) >= len(entries)
    
    # Check that our entries are present (they should be at the end)
    for i, entry in enumerate(entries):
        history_entry = history_data[-(len(entries)-i)]
        assert history_entry["plugin"] == entry["plugin"]
        assert history_entry["payload"] == entry["payload"]
        assert history_entry["granted"] == entry["granted"]


def test_concurrent_endpoint_usage(client) -> None:
    """Test endpoints under concurrent-like usage patterns."""
    
    # Simulate concurrent usage by rapidly alternating between endpoints
    operations = []
    
    # Generate a mix of operations
    for i in range(30):
        operations.extend([
            ("GET", f"/api/v1/health"),
            ("GET", f"/api/v1/mcp/servers"),
            ("GET", f"/api/v1/history/concurrent_user_{i % 5}"),
            ("GET", f"/api/v1/mcp/consent/concurrent_server_{i % 3}"),
            ("POST", f"/api/v1/mcp/consent/concurrent_server_{i % 3}", {"consent": i % 2 == 0}),
            ("POST", f"/api/v1/history/concurrent_user_{i % 5}", {
                "plugin": f"concurrent_plugin_{i}",
                "payload": {"iteration": i},
                "granted": True
            }),
        ])
    
    # Execute all operations
    results = []
    for op_type, url, *args in operations:
        if op_type == "GET":
            response = client.get(url)
        elif op_type == "POST":
            response = client.post(url, json=args[0])
        else:
            continue
        
        results.append((op_type, url, response.status_code))
    
    # All operations should succeed
    for op_type, url, status_code in results:
        assert status_code in [200, 422], f"Operation {op_type} {url} failed with {status_code}"
        
        # Specifically, all GET operations should succeed
        if op_type == "GET":
            assert status_code == 200, f"GET operation {url} failed with {status_code}"