# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for pagination performance optimizations."""

from __future__ import annotations


def test_pagination_endpoint(client) -> None:
    """Test the new pagination functionality in the history endpoint."""
    # Create test data
    for i in range(50):
        payload = {"message": f"test message {i}", "index": i}
        client.post(
            "/api/v1/history/test_user",
            json={"plugin": "test_plugin", "payload": payload, "granted": True},
        )
    
    # Test paginated retrieval
    response = client.get("/api/v1/history/test_user?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    
    # Check pagination metadata
    assert "pagination" in data
    pagination = data["pagination"]
    assert pagination["total"] == 50
    assert pagination["limit"] == 10
    assert pagination["offset"] == 0
    assert pagination["has_more"] == True
    
    # Check history data
    assert len(data["history"]) == 10
    
    # Test different page
    response = client.get("/api/v1/history/test_user?limit=10&offset=40")
    assert response.status_code == 200
    data = response.json()
    
    assert data["pagination"]["offset"] == 40
    assert data["pagination"]["has_more"] == False
    assert len(data["history"]) == 10  # Last 10 entries


def test_backward_compatibility_no_pagination(client) -> None:
    """Test that the API still works without pagination parameters."""
    # Create small dataset
    for i in range(5):
        payload = {"message": f"compat test {i}"}
        client.post(
            "/api/v1/history/compat_user",
            json={"plugin": "compat_plugin", "payload": payload, "granted": True},
        )
    
    # Test without pagination parameters (should return all)
    response = client.get("/api/v1/history/compat_user")
    assert response.status_code == 200
    data = response.json()
    
    # Should include pagination metadata even without params
    assert "pagination" in data
    assert data["pagination"]["total"] == 5
    assert data["pagination"]["limit"] is None
    assert data["pagination"]["offset"] == 0
    assert data["pagination"]["has_more"] == False
    
    # Should return all history
    assert len(data["history"]) == 5


def test_large_dataset_performance(client) -> None:
    """Test performance with larger datasets."""
    # Create larger dataset
    user_id = "perf_user"
    for i in range(200):
        payload = {"message": f"performance test {i}", "data": "x" * 100}
        client.post(
            f"/api/v1/history/{user_id}",
            json={"plugin": f"perf_plugin_{i % 10}", "payload": payload, "granted": i % 2 == 0},
        )
    
    # Test small page retrieval
    response = client.get(f"/api/v1/history/{user_id}?limit=25&offset=50")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["history"]) == 25
    assert data["pagination"]["total"] == 200
    assert data["pagination"]["offset"] == 50
    assert data["pagination"]["has_more"] == True
    
    # Verify data integrity
    for entry in data["history"]:
        assert "plugin" in entry
        assert "payload" in entry
        assert entry["plugin"].startswith("perf_plugin_")