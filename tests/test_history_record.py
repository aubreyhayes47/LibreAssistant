# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for recording history entries explicitly."""


def test_record_history_endpoint(client) -> None:
    response = client.post(
        "/api/v1/history/alice",
        json={
            "plugin": "echo",
            "payload": {"message": "hi"},
            "granted": True,
        },
    )
    assert response.status_code == 200
    hist = client.get("/api/v1/history/alice").json()["history"]
    assert hist[-1] == {
        "plugin": "echo",
        "payload": {"message": "hi"},
        "granted": True,
    }


def test_history_endpoint_error_cases(client) -> None:
    """Test error cases for history endpoints."""
    
    # Test POST with missing required fields
    response = client.post(
        "/api/v1/history/test_user",
        json={"plugin": "test_plugin"}  # Missing payload and granted
    )
    assert response.status_code == 422  # Validation error
    
    # Test POST with missing plugin field
    response = client.post(
        "/api/v1/history/test_user",
        json={
            "payload": {"key": "value"},
            "granted": True
        }
    )
    assert response.status_code == 422  # Validation error
    
    # Test POST with missing payload field
    response = client.post(
        "/api/v1/history/test_user",
        json={
            "plugin": "test_plugin",
            "granted": True
        }
    )
    assert response.status_code == 422  # Validation error
    
    # Test POST with missing granted field
    response = client.post(
        "/api/v1/history/test_user",
        json={
            "plugin": "test_plugin",
            "payload": {"key": "value"}
        }
    )
    assert response.status_code == 422  # Validation error
    
    # Test POST with invalid granted type
    response = client.post(
        "/api/v1/history/test_user",
        json={
            "plugin": "test_plugin",
            "payload": {"key": "value"},
            "granted": "invalid"
        }
    )
    assert response.status_code == 422  # Validation error
    
    # Test POST with invalid payload type
    response = client.post(
        "/api/v1/history/test_user",
        json={
            "plugin": "test_plugin",
            "payload": "invalid",  # Should be dict
            "granted": True
        }
    )
    assert response.status_code == 422  # Validation error


def test_history_get_endpoint_edge_cases(client) -> None:
    """Test GET history endpoint edge cases."""
    
    # Test GET for nonexistent user (should return empty history)
    response = client.get("/api/v1/history/nonexistent_user")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert data["history"] == []
    
    # Test GET with various user ID formats
    edge_case_user_ids = [
        "user_with_underscores",
        "user-with-dashes", 
        "user123",
        "UserWithCaps"
    ]
    
    for user_id in edge_case_user_ids:
        response = client.get(f"/api/v1/history/{user_id}")
        assert response.status_code == 200
        assert "history" in response.json()


def test_history_workflow_integration(client) -> None:
    """Test complete history workflow."""
    user_id = "workflow_test_user"
    
    # Check initial empty history
    response = client.get(f"/api/v1/history/{user_id}")
    assert response.status_code == 200
    initial_history = response.json()["history"]
    initial_count = len(initial_history)
    
    # Record a history entry
    response = client.post(
        f"/api/v1/history/{user_id}",
        json={
            "plugin": "workflow_test",
            "payload": {"test": "data"},
            "granted": True
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    
    # Verify history was updated
    response = client.get(f"/api/v1/history/{user_id}")
    assert response.status_code == 200
    updated_history = response.json()["history"]
    assert len(updated_history) == initial_count + 1
    
    # Verify the entry content
    assert updated_history[-1]["plugin"] == "workflow_test"
    assert updated_history[-1]["payload"] == {"test": "data"}
    assert updated_history[-1]["granted"] is True
