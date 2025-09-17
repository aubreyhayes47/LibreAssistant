#!/usr/bin/env python3
"""
Command-line version of Ollama Wrapper for testing and headless use
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import subprocess
import time
import json
from typing import Dict, Any

class OllamaWrapperCLI:
    def __init__(self):
        self.ollama_host = "http://localhost:11434"
    
    def check_server_status(self) -> Dict[str, Any]:
        """Check the status of the Ollama server"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "Running",
                    "models": data.get("models", []),
                    "model_count": len(data.get("models", [])),
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "Error",
                    "error": f"HTTP {response.status_code}",
                    "response_time": response.elapsed.total_seconds()
                }
        except requests.exceptions.ConnectionError:
            return {"status": "Stopped", "error": "Connection refused"}
        except requests.exceptions.Timeout:
            return {"status": "Timeout", "error": "Request timed out"}
        except Exception as e:
            return {"status": "Error", "error": str(e)}
    
    def start_server(self) -> Dict[str, Any]:
        """Start the Ollama server"""
        commands = [
            ["ollama", "serve"],
            ["systemctl", "start", "ollama"],
            ["/usr/local/bin/ollama", "serve"]
        ]
        
        for cmd in commands:
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )
                time.sleep(2)
                return {"success": True, "command": " ".join(cmd)}
            except FileNotFoundError:
                continue
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Ollama executable not found"}
    
    def stop_server(self) -> Dict[str, Any]:
        """Stop the Ollama server"""
        commands = [
            ["pkill", "-f", "ollama"],
            ["systemctl", "stop", "ollama"],
            ["killall", "ollama"]
        ]
        
        for cmd in commands:
            try:
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if process.returncode == 0:
                    return {"success": True, "command": " ".join(cmd)}
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "Command timed out"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "No stop command succeeded"}
    
    def print_status(self):
        """Print the current server status"""
        print("Checking Ollama server status...")
        status_info = self.check_server_status()
        
        status = status_info.get("status", "Unknown")
        print(f"Status: {status}")
        print(f"Host: {self.ollama_host}")
        
        if "error" in status_info:
            print(f"Error: {status_info['error']}")
        
        if "response_time" in status_info:
            print(f"Response time: {status_info['response_time']:.3f}s")
        
        if "model_count" in status_info:
            print(f"Available models: {status_info['model_count']}")
            
            if status_info.get("models"):
                print("Models:")
                for model in status_info["models"]:
                    model_name = model.get("name", "Unknown")
                    model_size = model.get("size", 0)
                    size_mb = model_size / (1024 * 1024) if model_size > 0 else 0
                    print(f"  • {model_name} ({size_mb:.1f} MB)")
        
        return status_info
    
    def run_interactive(self):
        """Run interactive CLI mode"""
        print("Ollama Wrapper CLI")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Check server status")
            print("2. Start server")
            print("3. Stop server")
            print("4. Restart server")
            print("5. Exit")
            
            try:
                choice = input("\nSelect option (1-5): ").strip()
                
                if choice == "1":
                    self.print_status()
                
                elif choice == "2":
                    print("Starting Ollama server...")
                    result = self.start_server()
                    if result["success"]:
                        print("✓ Server start command executed successfully")
                        print("Note: The server starts in the background")
                    else:
                        print(f"✗ Failed to start server: {result['error']}")
                
                elif choice == "3":
                    print("Stopping Ollama server...")
                    result = self.stop_server()
                    if result["success"]:
                        print("✓ Server stopped successfully")
                    else:
                        print(f"✗ Failed to stop server: {result['error']}")
                
                elif choice == "4":
                    print("Restarting Ollama server...")
                    stop_result = self.stop_server()
                    if stop_result["success"]:
                        print("✓ Server stopped")
                        time.sleep(3)
                        start_result = self.start_server()
                        if start_result["success"]:
                            print("✓ Server restarted successfully")
                        else:
                            print(f"✗ Failed to start server: {start_result['error']}")
                    else:
                        print(f"✗ Failed to stop server: {stop_result['error']}")
                
                elif choice == "5":
                    print("Goodbye!")
                    break
                
                else:
                    print("Invalid option. Please select 1-5.")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break

def main():
    """Main entry point"""
    cli = OllamaWrapperCLI()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "status":
            cli.print_status()
        elif command == "start":
            result = cli.start_server()
            if result["success"]:
                print("✓ Server start command executed")
            else:
                print(f"✗ Failed: {result['error']}")
        elif command == "stop":
            result = cli.stop_server()
            if result["success"]:
                print("✓ Server stopped")
            else:
                print(f"✗ Failed: {result['error']}")
        elif command == "restart":
            print("Restarting server...")
            stop_result = cli.stop_server()
            if stop_result["success"]:
                time.sleep(3)
                start_result = cli.start_server()
                if start_result["success"]:
                    print("✓ Server restarted")
                else:
                    print(f"✗ Start failed: {start_result['error']}")
            else:
                print(f"✗ Stop failed: {stop_result['error']}")
        else:
            print(f"Unknown command: {command}")
            print("Usage: python cli.py [status|start|stop|restart]")
    else:
        cli.run_interactive()

if __name__ == "__main__":
    main()