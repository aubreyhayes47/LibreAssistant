# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Integration tests demonstrating enhanced mock data and environment variable usage."""

import json
import os
import pytest
from pathlib import Path

from tests.test_env_setup import TestEnvironmentSetup


def test_complete_mock_environment_integration(monkeypatch, tmp_path):
    """Comprehensive integration test showing all mock data and environment variables working together."""
    
    # Set up the complete test environment
    env_vars = TestEnvironmentSetup.setup_test_environment_variables(monkeypatch, tmp_path)
    test_files = TestEnvironmentSetup.create_test_data_files(tmp_path)
    TestEnvironmentSetup.setup_mock_mcp_server_response(monkeypatch)
    
    # Verify all environment variables are set
    for key in ["TEST_MODE", "MOCK_EXTERNAL_APIS", "THINK_TANK_MODEL_RESPONSE", 
                "LAW_ANALYSIS_MODEL_RESPONSE", "LIBRE_DB_PATH", "LIBRE_DB_KEY",
                "LA_MODELS_DIR", "LA_DATASETS_DIR", "MCP_MOCK_RESPONSES"]:
        assert os.getenv(key) is not None, f"Environment variable {key} not set"
    
    # Verify mock data structure and quality
    think_tank_data = json.loads(os.getenv("THINK_TANK_MODEL_RESPONSE"))
    assert think_tank_data["analysis"]["goal"] == "Improve education"
    assert len(think_tank_data["analysis"]["executive"]["tasks"]) == 3
    
    law_data = json.loads(os.getenv("LAW_ANALYSIS_MODEL_RESPONSE"))
    assert "Constitutional" in law_data["analysis"]["legal_context"]
    assert len(law_data["analysis"]["relevant_statutes"]) >= 2
    
    # Verify test files exist and have content
    assert test_files["sample_txt"].read_text().startswith("This is a sample")
    json_data = json.loads(test_files["sample_json"].read_text())
    assert json_data["test"] == "data"
    
    # Verify directories exist with mock files
    models_dir = Path(os.getenv("LA_MODELS_DIR"))
    datasets_dir = Path(os.getenv("LA_DATASETS_DIR"))
    
    assert models_dir.exists()
    assert datasets_dir.exists()
    assert (models_dir / "mock-model.bin").exists()
    assert (datasets_dir / "training-data").exists()


def test_mock_api_responses_comprehensive(monkeypatch, tmp_path):
    """Test that mock API responses work correctly for external service calls."""
    
    # Set up environment
    TestEnvironmentSetup.setup_test_environment_variables(monkeypatch, tmp_path)
    TestEnvironmentSetup.setup_mock_mcp_server_response(monkeypatch)
    
    # Verify MCP mock responses
    mcp_responses = json.loads(os.getenv("MCP_MOCK_RESPONSES"))
    
    # Test OpenAI mock structure
    openai_mock = mcp_responses["openai_completion"]
    assert "choices" in openai_mock
    assert "message" in openai_mock["choices"][0]
    assert "content" in openai_mock["choices"][0]["message"]
    
    # Test local LLM mock structure  
    local_mock = mcp_responses["local_llm_response"]
    assert "response" in local_mock
    assert isinstance(local_mock["response"], str)
    
    # Test MCP server tools mock structure
    mcp_tools = mcp_responses["mcp_server_tools"]
    assert "tools" in mcp_tools
    assert len(mcp_tools["tools"]) > 0
    tool = mcp_tools["tools"][0]
    assert all(key in tool for key in ["name", "description", "inputSchema"])


def test_environment_isolation_between_tests(monkeypatch, tmp_path):
    """Test that environment setup properly isolates tests from each other."""
    
    # First test setup
    env_vars_1 = TestEnvironmentSetup.setup_test_environment_variables(monkeypatch, tmp_path)
    db_path_1 = os.getenv("LIBRE_DB_PATH")
    
    # Modify an environment variable
    monkeypatch.setenv("LIBRE_DB_PATH", "/custom/path")
    assert os.getenv("LIBRE_DB_PATH") == "/custom/path"
    
    # Set up again with a different temp path
    tmp_path_2 = tmp_path / "second_test"
    tmp_path_2.mkdir()
    env_vars_2 = TestEnvironmentSetup.setup_test_environment_variables(monkeypatch, tmp_path_2)
    
    # Verify the new setup overrode the custom path
    db_path_2 = os.getenv("LIBRE_DB_PATH")
    assert db_path_2 != "/custom/path"
    assert db_path_2 != db_path_1
    assert str(tmp_path_2) in db_path_2


def test_mock_data_consistency_across_invocations():
    """Test that mock data is consistent across multiple invocations."""
    
    # Get mock data multiple times
    think_tank_1 = TestEnvironmentSetup.get_mock_think_tank_response()
    think_tank_2 = TestEnvironmentSetup.get_mock_think_tank_response()
    
    law_1 = TestEnvironmentSetup.get_mock_law_analysis_response()
    law_2 = TestEnvironmentSetup.get_mock_law_analysis_response()
    
    api_1 = TestEnvironmentSetup.create_mock_api_responses()
    api_2 = TestEnvironmentSetup.create_mock_api_responses()
    
    # Verify consistency
    assert think_tank_1 == think_tank_2
    assert law_1 == law_2
    assert api_1 == api_2
    
    # Verify the data is not just empty/None
    assert len(json.dumps(think_tank_1)) > 100
    assert len(json.dumps(law_1)) > 100
    assert len(json.dumps(api_1)) > 100