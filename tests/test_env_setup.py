# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Test environment setup utilities for mock data and environment variables."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict


class TestEnvironmentSetup:
    """Utility class for setting up test environments with mock data and environment variables."""

    @staticmethod
    def get_mock_think_tank_response() -> Dict[str, Any]:
        """Get comprehensive mock data for Think Tank analysis."""
        return {
            "summary": (
                "The objective is to improve education. Stakeholders should collaborate on this initiative.\n"
                "Argument: Improve education addresses an important societal need.; "
                "Investing in improve education can produce long-term benefits.; "
                "Improve education aligns with widely shared community values.\n"
                "Caveats: Limited resources could hamper efforts to improve education.; "
                "There may be unintended consequences when attempting to improve education."
            ),
            "analysis": {
                "goal": "Improve education",
                "executive": {
                    "tasks": [
                        "Assess the current state related to improve education.",
                        "Develop a concrete plan to improve education.",
                        "Implement the plan and monitor progress.",
                    ]
                },
                "research": {
                    "summary": "Preliminary surveys on improve education indicate that multiple approaches have been proposed in academic and policy literature.",
                    "sources": ["https://example.org/research/improve_education"],
                },
                "devils_advocate": {
                    "concerns": [
                        "Limited resources could hamper efforts to improve education.",
                        "There may be unintended consequences when attempting to improve education.",
                    ]
                },
                "argument": {
                    "points": [
                        "Improve education addresses an important societal need.",
                        "Investing in improve education can produce long-term benefits.",
                        "Improve education aligns with widely shared community values.",
                    ]
                },
                "communications": {
                    "message": "The objective is to improve education. Stakeholders should collaborate on this initiative.",
                    "audience": "general public",
                },
                "visualizer": {
                    "description": "A bar chart visualizing stages to improve education.",
                    "data": {
                        "type": "bar",
                        "labels": ["Plan", "Execute", "Review"],
                        "values": [1, 2, 1],
                    },
                },
            },
        }

    @staticmethod
    def get_mock_law_analysis_response() -> Dict[str, Any]:
        """Get mock data for Law by Keystone analysis."""
        return {
            "summary": "Legal analysis of constitutional law provisions related to education policy.",
            "analysis": {
                "legal_context": "Constitutional protections for education access",
                "relevant_statutes": [
                    "Education Act Section 504",
                    "Civil Rights Act Title IX"
                ],
                "precedent_cases": [
                    "Brown v. Board of Education (1954)",
                    "San Antonio v. Rodriguez (1973)"
                ],
                "risk_assessment": "Low legal risk with proper implementation",
                "recommendations": [
                    "Ensure compliance with federal accessibility requirements",
                    "Review state-specific education mandates"
                ]
            }
        }

    @staticmethod
    def setup_test_environment_variables(monkeypatch, temp_dir: Path = None) -> Dict[str, str]:
        """Set up all necessary environment variables for testing."""
        if temp_dir is None:
            temp_dir = Path(tempfile.mkdtemp())
        
        # Database configuration
        db_path = temp_dir / "test.db"
        db_key = "test-encryption-key-for-testing-only"
        
        # Model and dataset directories
        models_dir = temp_dir / "models"
        datasets_dir = temp_dir / "datasets"
        models_dir.mkdir(exist_ok=True)
        datasets_dir.mkdir(exist_ok=True)
        
        # Create some mock model and dataset files
        (models_dir / "mock-model.bin").write_text("mock model data")
        (models_dir / "sentiment-analyzer.pkl").write_text("mock sentiment model")
        (datasets_dir / "training-data").mkdir(exist_ok=True)
        (datasets_dir / "validation-set").mkdir(exist_ok=True)
        
        env_vars = {
            "LIBRE_DB_PATH": str(db_path),
            "LIBRE_DB_KEY": db_key,
            "LA_MODELS_DIR": str(models_dir),
            "LA_DATASETS_DIR": str(datasets_dir),
            "THINK_TANK_MODEL_RESPONSE": json.dumps(TestEnvironmentSetup.get_mock_think_tank_response()),
            "LAW_ANALYSIS_MODEL_RESPONSE": json.dumps(TestEnvironmentSetup.get_mock_law_analysis_response()),
            "TEST_MODE": "true",
            "LOG_LEVEL": "DEBUG",
            "MOCK_EXTERNAL_APIS": "true"
        }
        
        # Set environment variables using monkeypatch
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        
        return env_vars

    @staticmethod
    def create_mock_api_responses() -> Dict[str, Any]:
        """Create mock responses for external API calls."""
        return {
            "openai_completion": {
                "choices": [
                    {
                        "message": {
                            "content": "This is a mock response from OpenAI API for testing purposes."
                        }
                    }
                ]
            },
            "local_llm_response": {
                "response": "Mock response from local LLM server for testing."
            },
            "mcp_server_tools": {
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "A test tool for mocking purposes",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "input": {"type": "string"}
                            }
                        }
                    }
                ]
            }
        }

    @staticmethod
    def setup_mock_mcp_server_response(monkeypatch):
        """Set up mock MCP server responses."""
        mock_responses = TestEnvironmentSetup.create_mock_api_responses()
        monkeypatch.setenv("MCP_MOCK_RESPONSES", json.dumps(mock_responses))

    @staticmethod
    def create_test_data_files(base_dir: Path) -> Dict[str, Path]:
        """Create test data files for file I/O operations."""
        test_files = {}
        
        # Create sample text files
        (base_dir / "sample.txt").write_text("This is a sample text file for testing.")
        test_files["sample_txt"] = base_dir / "sample.txt"
        
        # Create sample JSON file
        sample_json = {"test": "data", "numbers": [1, 2, 3], "nested": {"key": "value"}}
        (base_dir / "sample.json").write_text(json.dumps(sample_json, indent=2))
        test_files["sample_json"] = base_dir / "sample.json"
        
        # Create sample configuration file
        config_content = """
[database]
host = localhost
port = 5432
name = test_db

[api]
rate_limit = 100
timeout = 30
"""
        (base_dir / "config.ini").write_text(config_content)
        test_files["config_ini"] = base_dir / "config.ini"
        
        return test_files


def pytest_configure():
    """Global pytest configuration for test environment setup."""
    # Set default test environment variables
    os.environ.setdefault("TEST_MODE", "true")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    os.environ.setdefault("MOCK_EXTERNAL_APIS", "true")


def mock_external_api_call(api_name: str, *args, **kwargs):
    """Mock external API calls to avoid network dependencies in tests."""
    mock_responses = TestEnvironmentSetup.create_mock_api_responses()
    
    if api_name == "openai":
        return mock_responses["openai_completion"]
    elif api_name == "local_llm":
        return mock_responses["local_llm_response"]
    elif api_name == "mcp_server":
        return mock_responses["mcp_server_tools"]
    else:
        return {"error": f"Unknown API: {api_name}"}