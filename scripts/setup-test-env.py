#!/usr/bin/env python3
# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Script to set up test environment variables and mock data for development."""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
# Also add the tests directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

try:
    from test_env_setup import TestEnvironmentSetup
except ImportError:
    print("Error: Could not import test environment setup. Run from project root.")
    sys.exit(1)


def setup_test_environment(output_file: str = None, temp_dir: str = None) -> None:
    """Set up test environment and optionally save to a shell script."""
    
    if temp_dir:
        temp_dir = Path(temp_dir)
    else:
        temp_dir = Path(tempfile.mkdtemp(prefix="libreassistant_test_"))
    
    print(f"Setting up test environment in: {temp_dir}")
    
    # Create directories
    models_dir = temp_dir / "models"
    datasets_dir = temp_dir / "datasets"
    models_dir.mkdir(parents=True, exist_ok=True)
    datasets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock model and dataset files
    (models_dir / "mock-model.bin").write_text("mock model data for testing")
    (models_dir / "sentiment-analyzer.pkl").write_text("mock sentiment model")
    (datasets_dir / "training-data").mkdir(exist_ok=True)
    (datasets_dir / "validation-set").mkdir(exist_ok=True)
    
    # Get mock data
    think_tank_data = TestEnvironmentSetup.get_mock_think_tank_response()
    law_data = TestEnvironmentSetup.get_mock_law_analysis_response()
    api_responses = TestEnvironmentSetup.create_mock_api_responses()
    
    # Prepare environment variables
    env_vars = {
        "TEST_MODE": "true",
        "LOG_LEVEL": "DEBUG",
        "MOCK_EXTERNAL_APIS": "true",
        "LIBRE_DB_PATH": str(temp_dir / "test.db"),
        "LIBRE_DB_KEY": "test-encryption-key-for-development",
        "LA_MODELS_DIR": str(models_dir),
        "LA_DATASETS_DIR": str(datasets_dir),
        "THINK_TANK_MODEL_RESPONSE": json.dumps(think_tank_data),
        "LAW_ANALYSIS_MODEL_RESPONSE": json.dumps(law_data),
        "MCP_MOCK_RESPONSES": json.dumps(api_responses),
    }
    
    # Create test data files
    test_data_files = TestEnvironmentSetup.create_test_data_files(temp_dir)
    
    print("\nTest environment setup complete!")
    print(f"Temporary directory: {temp_dir}")
    print(f"Mock models directory: {models_dir}")
    print(f"Mock datasets directory: {datasets_dir}")
    print(f"Test data files: {list(test_data_files.keys())}")
    
    # Output environment variables
    if output_file:
        write_env_script(env_vars, output_file)
    else:
        print("\nEnvironment variables to set:")
        for key, value in env_vars.items():
            print(f"export {key}='{value}'")
    
    return env_vars, temp_dir


def write_env_script(env_vars: dict, output_file: str) -> None:
    """Write environment variables to a shell script."""
    script_path = Path(output_file)
    
    with open(script_path, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# Generated test environment setup script\n")
        f.write("# Source this file to set up test environment variables\n\n")
        
        for key, value in env_vars.items():
            # Escape single quotes in values
            escaped_value = value.replace("'", "'\"'\"'")
            f.write(f"export {key}='{escaped_value}'\n")
        
        f.write("\necho 'Test environment variables set up!'\n")
        f.write("echo 'Run tests with: pytest tests/'\n")
        f.write("echo 'Run TypeScript tests with: npm test'\n")
    
    script_path.chmod(0o755)
    print(f"\nEnvironment script written to: {script_path}")
    print(f"Source it with: source {script_path}")


def print_usage():
    """Print usage information."""
    print("Usage: python scripts/setup-test-env.py [OPTIONS]")
    print("\nOptions:")
    print("  --output-script FILE    Write environment variables to shell script")
    print("  --temp-dir DIR         Use specific temporary directory")
    print("  --help                 Show this help message")
    print("\nExamples:")
    print("  python scripts/setup-test-env.py")
    print("  python scripts/setup-test-env.py --output-script test-env.sh")
    print("  python scripts/setup-test-env.py --temp-dir /tmp/my-test-env --output-script setup.sh")


def main():
    """Main entry point."""
    args = sys.argv[1:]
    output_file = None
    temp_dir = None
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--help":
            print_usage()
            return
        elif arg == "--output-script":
            if i + 1 < len(args):
                output_file = args[i + 1]
                i += 2
            else:
                print("Error: --output-script requires a filename")
                sys.exit(1)
        elif arg == "--temp-dir":
            if i + 1 < len(args):
                temp_dir = args[i + 1]
                i += 2
            else:
                print("Error: --temp-dir requires a directory path")
                sys.exit(1)
        else:
            print(f"Error: Unknown argument: {arg}")
            print_usage()
            sys.exit(1)
    
    try:
        setup_test_environment(output_file, temp_dir)
    except Exception as e:
        print(f"Error setting up test environment: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()