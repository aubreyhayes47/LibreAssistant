#!/usr/bin/env python3

# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Manual test runner for UI endpoints without pytest dependency."""

import sys
import os
import pathlib
import types
import sqlite3

# Add the src directory to the Python path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

# Mock pysqlcipher3 for testing
pysqlcipher3_stub = types.ModuleType("pysqlcipher3")
setattr(pysqlcipher3_stub, "dbapi2", sqlite3)
sys.modules.setdefault("pysqlcipher3", pysqlcipher3_stub)
sys.modules.setdefault("pysqlcipher3.dbapi2", sqlite3)

# Set test environment
os.environ["LIBRE_DB_PATH"] = ":memory:"
os.environ["LIBRE_DB_KEY"] = "test-db-key"

# Mock out Node.js plugins if not available
try:
    import shutil
    if shutil.which("node") is None:
        from libreassistant.plugins import law_by_keystone as _law_by_keystone
        from libreassistant.plugins import think_tank as _think_tank
        _law_by_keystone.register = lambda: None
        _think_tank.register = lambda: None
except:
    pass

# Now import the app and test client
try:
    from fastapi.testclient import TestClient
    from libreassistant.main import app
    from libreassistant.kernel import kernel
    from libreassistant.plugins.echo import register as register_echo
    from libreassistant.providers import providers
    from libreassistant.providers.cloud import CloudProvider
    from libreassistant.providers.local import LocalProvider
    from libreassistant import db as app_db
    
    print("✓ Successfully imported all dependencies")
except ImportError as e:
    print(f"✗ Failed to import dependencies: {e}")
    sys.exit(1)

def setup_test_environment():
    """Set up the test environment."""
    kernel.reset()
    register_echo()
    providers.reset()
    providers.register("cloud", CloudProvider())
    providers.register("local", LocalProvider())
    app_db.clear()

def run_endpoint_tests():
    """Run comprehensive endpoint tests."""
    setup_test_environment()
    
    print("\n" + "="*60)
    print("COMPREHENSIVE UI ENDPOINT TESTING")
    print("="*60)
    
    client = TestClient(app)
    total_tests = 0
    passed_tests = 0
    failed_tests = []

    def test_case(name, test_func):
        nonlocal total_tests, passed_tests
        total_tests += 1
        try:
            test_func(client)
            print(f"✓ {name}")
            passed_tests += 1
        except Exception as e:
            print(f"✗ {name}: {e}")
            failed_tests.append((name, str(e)))

    # Test /api/v1/health endpoint
    print("\n--- Testing /api/v1/health endpoint ---")
    
    def test_health_basic():
        response = client.get("/api/v1/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Response should be a dict"
        assert "requests" in data, "Should contain requests field"
        assert "uptime" in data, "Should contain uptime field"
    
    test_case("Health endpoint basic functionality", test_health_basic)

    def test_health_request_counting():
        initial_resp = client.get("/api/v1/health")
        initial_count = initial_resp.json()["requests"]
        
        # Make some requests
        client.get("/")
        client.get("/")
        
        final_resp = client.get("/api/v1/health")
        final_count = final_resp.json()["requests"]
        assert final_count >= initial_count + 2, "Request count should increase"
    
    test_case("Health endpoint request counting", test_health_request_counting)

    # Test /api/v1/mcp/servers endpoint
    print("\n--- Testing /api/v1/mcp/servers endpoint ---")
    
    def test_mcp_servers_basic():
        response = client.get("/api/v1/mcp/servers")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "servers" in data, "Response should contain 'servers' field"
        assert isinstance(data["servers"], list), "Servers should be a list"
        
        # Verify server structure
        for server in data["servers"]:
            assert "name" in server, "Each server should have a name"
            assert "consent" in server, "Each server should have consent status"
            assert isinstance(server["consent"], bool), "Consent should be boolean"
    
    test_case("MCP servers endpoint basic functionality", test_mcp_servers_basic)

    # Test /api/v1/mcp/consent/{name} endpoints
    print("\n--- Testing /api/v1/mcp/consent/{name} endpoints ---")
    
    def test_mcp_consent_get():
        response = client.get("/api/v1/mcp/consent/test_server")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "consent" in data, "Response should contain consent field"
        assert isinstance(data["consent"], bool), "Consent should be boolean"
    
    test_case("MCP consent GET endpoint", test_mcp_consent_get)

    def test_mcp_consent_post_valid():
        response = client.post(
            "/api/v1/mcp/consent/test_server",
            json={"consent": True}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "ok", "Should return ok status"
        
        # Verify the consent was set
        get_response = client.get("/api/v1/mcp/consent/test_server")
        assert get_response.json()["consent"] is True, "Consent should be set to True"
    
    test_case("MCP consent POST valid request", test_mcp_consent_post_valid)

    def test_mcp_consent_post_invalid():
        # Missing consent field
        response = client.post(
            "/api/v1/mcp/consent/test_server",
            json={}
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        
        # Invalid consent type
        response = client.post(
            "/api/v1/mcp/consent/test_server",
            json={"consent": "invalid"}
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    
    test_case("MCP consent POST error cases", test_mcp_consent_post_invalid)

    # Test /api/v1/history/{user_id} endpoints
    print("\n--- Testing /api/v1/history/{user_id} endpoints ---")
    
    def test_history_get():
        response = client.get("/api/v1/history/test_user")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "history" in data, "Response should contain history field"
        assert isinstance(data["history"], list), "History should be a list"
    
    test_case("History GET endpoint", test_history_get)

    def test_history_post_valid():
        response = client.post(
            "/api/v1/history/test_user",
            json={
                "plugin": "test_plugin",
                "payload": {"key": "value"},
                "granted": True
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json()["status"] == "ok", "Should return ok status"
    
    test_case("History POST valid request", test_history_post_valid)

    def test_history_post_invalid():
        # Missing required fields
        response = client.post(
            "/api/v1/history/test_user",
            json={"plugin": "test_plugin"}  # Missing payload and granted
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    
    test_case("History POST error cases", test_history_post_invalid)

    # Test error resilience
    print("\n--- Testing error resilience ---")
    
    def test_error_resilience():
        # Cause an error in one endpoint
        client.post("/api/v1/mcp/consent/test", json={})  # Should fail
        
        # Other endpoints should still work
        assert client.get("/api/v1/mcp/servers").status_code == 200
        assert client.get("/api/v1/history/test_user").status_code == 200
        assert client.get("/api/v1/health").status_code == 200
    
    test_case("Error resilience across endpoints", test_error_resilience)

    # Test integration workflows
    print("\n--- Testing integration workflows ---")
    
    def test_mcp_workflow():
        # Complete MCP workflow
        servers_resp = client.get("/api/v1/mcp/servers")
        assert servers_resp.status_code == 200
        
        consent_resp = client.post(
            "/api/v1/mcp/consent/workflow_test",
            json={"consent": True}
        )
        assert consent_resp.status_code == 200
        
        verify_resp = client.get("/api/v1/mcp/consent/workflow_test")
        assert verify_resp.status_code == 200
        assert verify_resp.json()["consent"] is True
    
    test_case("MCP workflow integration", test_mcp_workflow)

    def test_history_workflow():
        user_id = "workflow_test_user"
        
        # Check initial history
        initial_resp = client.get(f"/api/v1/history/{user_id}")
        assert initial_resp.status_code == 200
        initial_count = len(initial_resp.json()["history"])
        
        # Add history entry
        post_resp = client.post(
            f"/api/v1/history/{user_id}",
            json={
                "plugin": "workflow_test",
                "payload": {"test": "data"},
                "granted": True
            }
        )
        assert post_resp.status_code == 200
        
        # Verify history updated
        final_resp = client.get(f"/api/v1/history/{user_id}")
        assert final_resp.status_code == 200
        final_count = len(final_resp.json()["history"])
        assert final_count == initial_count + 1
    
    test_case("History workflow integration", test_history_workflow)

    # Print results
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print("\nFailed tests:")
        for name, error in failed_tests:
            print(f"  ✗ {name}: {error}")
    
    print(f"\nSuccess rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests:
        print("\n⚠️  Some tests failed - endpoint error handling may need improvement")
    else:
        print("\n✅ All tests passed - endpoints are properly exercised!")

    # Cleanup
    app_db.close_conn()
    
    return len(failed_tests) == 0

if __name__ == "__main__":
    success = run_endpoint_tests()
    sys.exit(0 if success else 1)