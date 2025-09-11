# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Test the test environment setup utilities."""

import json
import pytest
from pathlib import Path

from tests.test_env_setup import TestEnvironmentSetup, mock_external_api_call


def test_mock_think_tank_response():
    """Test that mock Think Tank response has expected structure."""
    response = TestEnvironmentSetup.get_mock_think_tank_response()
    
    assert "summary" in response
    assert "analysis" in response
    
    analysis = response["analysis"]
    assert "goal" in analysis
    assert "executive" in analysis
    assert "research" in analysis
    assert "devils_advocate" in analysis
    assert "argument" in analysis
    assert "communications" in analysis
    assert "visualizer" in analysis
    
    # Verify nested structure
    assert isinstance(analysis["executive"]["tasks"], list)
    assert len(analysis["executive"]["tasks"]) > 0
    assert isinstance(analysis["research"]["sources"], list)
    assert isinstance(analysis["devils_advocate"]["concerns"], list)
    assert isinstance(analysis["argument"]["points"], list)


def test_mock_law_analysis_response():
    """Test that mock Law analysis response has expected structure."""
    response = TestEnvironmentSetup.get_mock_law_analysis_response()
    
    assert "summary" in response
    assert "analysis" in response
    
    analysis = response["analysis"]
    assert "legal_context" in analysis
    assert "relevant_statutes" in analysis
    assert "precedent_cases" in analysis
    assert "risk_assessment" in analysis
    assert "recommendations" in analysis
    
    assert isinstance(analysis["relevant_statutes"], list)
    assert isinstance(analysis["precedent_cases"], list)
    assert isinstance(analysis["recommendations"], list)


def test_environment_variable_setup(monkeypatch, tmp_path):
    """Test that environment variables are set up correctly."""
    env_vars = TestEnvironmentSetup.setup_test_environment_variables(monkeypatch, tmp_path)
    
    # Check that all expected environment variables are set
    expected_vars = [
        "LIBRE_DB_PATH",
        "LIBRE_DB_KEY", 
        "LA_MODELS_DIR",
        "LA_DATASETS_DIR",
        "THINK_TANK_MODEL_RESPONSE",
        "LAW_ANALYSIS_MODEL_RESPONSE",
        "TEST_MODE",
        "LOG_LEVEL",
        "MOCK_EXTERNAL_APIS"
    ]
    
    for var in expected_vars:
        assert var in env_vars
        # Verify the environment variable was actually set (monkeypatch should have set it)
        import os
        assert os.getenv(var) is not None
    
    # Verify JSON responses are valid
    think_tank_response = json.loads(env_vars["THINK_TANK_MODEL_RESPONSE"])
    assert "summary" in think_tank_response
    
    law_response = json.loads(env_vars["LAW_ANALYSIS_MODEL_RESPONSE"])
    assert "summary" in law_response
    
    # Verify directories exist
    assert Path(env_vars["LA_MODELS_DIR"]).exists()
    assert Path(env_vars["LA_DATASETS_DIR"]).exists()


def test_test_data_files_creation(tmp_path):
    """Test that test data files are created correctly."""
    test_files = TestEnvironmentSetup.create_test_data_files(tmp_path)
    
    # Check that all expected files were created
    expected_files = ["sample_txt", "sample_json", "config_ini"]
    for file_key in expected_files:
        assert file_key in test_files
        assert test_files[file_key].exists()
    
    # Verify file contents
    assert "sample text file" in test_files["sample_txt"].read_text()
    
    json_content = json.loads(test_files["sample_json"].read_text())
    assert json_content["test"] == "data"
    assert json_content["numbers"] == [1, 2, 3]
    
    config_content = test_files["config_ini"].read_text()
    assert "[database]" in config_content
    assert "[api]" in config_content


def test_mock_api_responses():
    """Test mock API response structure."""
    responses = TestEnvironmentSetup.create_mock_api_responses()
    
    assert "openai_completion" in responses
    assert "local_llm_response" in responses
    assert "mcp_server_tools" in responses
    
    # Verify OpenAI response structure
    openai_resp = responses["openai_completion"]
    assert "choices" in openai_resp
    assert len(openai_resp["choices"]) > 0
    assert "message" in openai_resp["choices"][0]
    assert "content" in openai_resp["choices"][0]["message"]
    
    # Verify MCP server tools structure
    mcp_resp = responses["mcp_server_tools"]
    assert "tools" in mcp_resp
    assert len(mcp_resp["tools"]) > 0
    tool = mcp_resp["tools"][0]
    assert "name" in tool
    assert "description" in tool
    assert "inputSchema" in tool


def test_mock_external_api_call():
    """Test the mock external API call function."""
    # Test known API names
    openai_response = mock_external_api_call("openai")
    assert "choices" in openai_response
    
    local_response = mock_external_api_call("local_llm")
    assert "response" in local_response
    
    mcp_response = mock_external_api_call("mcp_server")
    assert "tools" in mcp_response
    
    # Test unknown API name
    unknown_response = mock_external_api_call("unknown_api")
    assert "error" in unknown_response
    assert "Unknown API" in unknown_response["error"]


def test_complete_environment_setup_integration(monkeypatch, tmp_path):
    """Test complete environment setup for integration testing."""
    # Set up full test environment
    env_vars = TestEnvironmentSetup.setup_test_environment_variables(monkeypatch, tmp_path)
    test_files = TestEnvironmentSetup.create_test_data_files(tmp_path)
    TestEnvironmentSetup.setup_mock_mcp_server_response(monkeypatch)
    
    # Verify we can access Think Tank mock data
    import os
    think_tank_data = json.loads(os.getenv("THINK_TANK_MODEL_RESPONSE"))
    assert think_tank_data["analysis"]["goal"] == "Improve education"
    
    # Verify we can access test files
    assert test_files["sample_txt"].read_text().startswith("This is a sample")
    
    # Verify MCP mock responses are set
    assert os.getenv("MCP_MOCK_RESPONSES") is not None
    mcp_responses = json.loads(os.getenv("MCP_MOCK_RESPONSES"))
    assert "mcp_server_tools" in mcp_responses