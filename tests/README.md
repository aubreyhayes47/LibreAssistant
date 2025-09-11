<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Tests

This directory contains the test suite for LibreAssistant.

## Layout

* Python tests live at the root of this folder (e.g., `test_cli.py`, `test_kernel.py`).
* Expert analysis modules have dedicated tests such as `test_experts_argumentation.py`,
  `test_experts_communications.py`, `test_experts_devils_advocate.py`,
  `test_experts_executive.py`, `test_experts_research.py`, and
  `test_experts_visualizer.py`.
* TypeScript tests for the Model Context Protocol (MCP) adapters live in `mcp/*.test.ts`.

## Running Python tests

Python tests use `pytest`. From the repository root:

```bash
pytest
```

## Running TypeScript tests

The TypeScript tests use Node's built-in test runner with `ts-node`. Install dependencies and run:

```bash
npm install
npm test
```

This executes all `*.test.ts` files under `tests/mcp`.

### npm proxy warnings

If running `npm` commands produces a warning like `npm warn Unknown env config "http-proxy"`, clear any old proxy settings by running:

```bash
npm_config_http_proxy="" npm_config_https_proxy="" npm test
```

Setting the variables to empty strings removes the deprecated `http-proxy` configuration.

## Environment variables and mocks

Tests use environment variables to inject mock data and configure test environments. The `TestEnvironmentSetup` utility class in `tests/test_env_setup.py` provides standardized mock data and environment configuration.

### Core Environment Variables

* `THINK_TANK_MODEL_RESPONSE` – provides a mocked Think Tank analysis used by `tests/test_think_tank_plugin.py` and `tests/mcp/think_tank.test.ts`.
* `LAW_ANALYSIS_MODEL_RESPONSE` – provides mock legal analysis data for law-related plugins.
* `LIBRE_DB_PATH` and `LIBRE_DB_KEY` – temporary database path and encryption key for `tests/test_db_encryption.py`.
* `LA_MODELS_DIR` and `LA_DATASETS_DIR` – temporary directories for transparency tests in `tests/test_transparency.py`.

### Test Control Variables

* `TEST_MODE` – set to "true" to enable test mode behavior across the application.
* `LOG_LEVEL` – controls logging verbosity during tests (default: "DEBUG").
* `MOCK_EXTERNAL_APIS` – set to "true" to use mock responses instead of real API calls.
* `MCP_MOCK_RESPONSES` – JSON-encoded mock responses for MCP server interactions.

### Using the Test Environment Setup

```python
from tests.test_env_setup import TestEnvironmentSetup

def test_example(monkeypatch, tmp_path):
    # Set up all standard test environment variables
    env_vars = TestEnvironmentSetup.setup_test_environment_variables(monkeypatch, tmp_path)
    
    # Create test data files
    test_files = TestEnvironmentSetup.create_test_data_files(tmp_path)
    
    # Your test code here
```

### Quick Start for Developers

For rapid development setup with all mock data and environment variables:

```bash
# Generate and source test environment
python scripts/setup-test-env.py --output-script test-env.sh
source test-env.sh

# Run all tests
pytest tests/
npm test

# Run specific test categories
pytest tests/test_think_tank_plugin.py -v
pytest tests/test_mock_integration.py -v
```

### Test Categories

* **Unit tests** - Individual plugin and component tests with mocks
* **Integration tests** - Cross-component tests using mock environment
* **MCP tests** - TypeScript tests for Model Context Protocol adapters
* **Environment tests** - Tests for mock data setup and environment configuration

All tests use comprehensive mock data to avoid external dependencies and ensure reproducible results.
