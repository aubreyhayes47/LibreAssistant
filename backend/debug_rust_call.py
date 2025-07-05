"""
Debug utility for testing Tauri-Python communication.
"""
import json
import subprocess
import sys
import os

def test_command_via_rust():
    """Test command as it would be called from Rust."""
    backend_path = os.path.dirname(os.path.abspath(__file__))
    
    # Test hello command
    payload = {"name": "Rust Test", "timestamp": "123456789"}
    payload_json = json.dumps(payload)
    
    print(f"Testing command: hello")
    print(f"Payload: {payload_json}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            [sys.executable, "main.py", "hello", payload_json],
            cwd=backend_path,
            capture_output=True,
            text=True
        )
        
        print(f"Exit code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                print(f"Parsed response: {json.dumps(response, indent=2)}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
        
    except Exception as e:
        print(f"Error running command: {e}")

if __name__ == "__main__":
    test_command_via_rust()
