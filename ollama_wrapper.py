#!/usr/bin/env python3
"""
Ollama Wrapper GUI - A simple GUI for managing Ollama server
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import subprocess
import threading
import time
import json
from typing import Optional, Dict, Any


class OllamaWrapper:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Ollama Wrapper")
        self.root.geometry("600x400")
        
        # Ollama server configuration
        self.ollama_host = "http://localhost:11434"
        self.server_status = "Unknown"
        self.auto_refresh = True
        
        self.setup_ui()
        self.start_status_monitor()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Ollama Server Manager", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Server Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Server Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.status_label = ttk.Label(status_frame, text="Checking...", 
                                     font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(status_frame, text="Host:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.host_label = ttk.Label(status_frame, text=self.ollama_host)
        self.host_label.grid(row=1, column=1, sticky=tk.W)
        
        # Refresh button
        self.refresh_button = ttk.Button(status_frame, text="Refresh", 
                                        command=self.check_server_status_async)
        self.refresh_button.grid(row=0, column=2, padx=(10, 0))
        
        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_cb = ttk.Checkbutton(status_frame, text="Auto-refresh", 
                                         variable=self.auto_refresh_var,
                                         command=self.toggle_auto_refresh)
        auto_refresh_cb.grid(row=1, column=2, padx=(10, 0))
        
        # Server Controls Section
        controls_frame = ttk.LabelFrame(main_frame, text="Server Controls", padding="10")
        controls_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Control buttons
        self.start_button = ttk.Button(controls_frame, text="Start Server", 
                                      command=self.start_server_async)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(controls_frame, text="Stop Server", 
                                     command=self.stop_server_async)
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        self.restart_button = ttk.Button(controls_frame, text="Restart Server", 
                                        command=self.restart_server_async)
        self.restart_button.grid(row=0, column=2)
        
        # Server Information Section
        info_frame = ttk.LabelFrame(main_frame, text="Server Information", padding="10")
        info_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        # Text widget for server info with scrollbar
        text_frame = ttk.Frame(info_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.info_text = tk.Text(text_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure main frame grid weights
        main_frame.rowconfigure(3, weight=1)
    
    def check_server_status(self) -> Dict[str, Any]:
        """Check the status of the Ollama server"""
        try:
            # Try to connect to the Ollama API
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
    
    def check_server_status_async(self):
        """Check server status in a separate thread"""
        def check_and_update():
            status_info = self.check_server_status()
            self.root.after(0, lambda: self.update_status_display(status_info))
        
        threading.Thread(target=check_and_update, daemon=True).start()
    
    def update_status_display(self, status_info: Dict[str, Any]):
        """Update the status display with new information"""
        status = status_info.get("status", "Unknown")
        self.server_status = status
        
        # Update status label with color coding
        if status == "Running":
            self.status_label.config(text="🟢 Running", foreground="green")
        elif status == "Stopped":
            self.status_label.config(text="🔴 Stopped", foreground="red")
        elif status == "Timeout":
            self.status_label.config(text="🟡 Timeout", foreground="orange")
        else:
            self.status_label.config(text="❓ Error", foreground="red")
        
        # Update info text
        info_text = f"Status: {status}\n"
        info_text += f"Host: {self.ollama_host}\n"
        info_text += f"Last checked: {time.strftime('%H:%M:%S')}\n"
        
        if "response_time" in status_info:
            info_text += f"Response time: {status_info['response_time']:.3f}s\n"
        
        if "error" in status_info:
            info_text += f"Error: {status_info['error']}\n"
        
        if "model_count" in status_info:
            info_text += f"Available models: {status_info['model_count']}\n"
            
            if status_info.get("models"):
                info_text += "\nModels:\n"
                for model in status_info["models"][:5]:  # Show first 5 models
                    model_name = model.get("name", "Unknown")
                    model_size = model.get("size", 0)
                    size_mb = model_size / (1024 * 1024) if model_size > 0 else 0
                    info_text += f"  • {model_name} ({size_mb:.1f} MB)\n"
                
                if len(status_info["models"]) > 5:
                    info_text += f"  ... and {len(status_info['models']) - 5} more\n"
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info_text)
        
        # Update button states
        self.update_button_states()
    
    def update_button_states(self):
        """Update button states based on server status"""
        if self.server_status == "Running":
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.restart_button.config(state="normal")
        elif self.server_status == "Stopped":
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.restart_button.config(state="disabled")
        else:
            # For timeout/error states, allow all operations
            self.start_button.config(state="normal")
            self.stop_button.config(state="normal")
            self.restart_button.config(state="normal")
    
    def start_server_async(self):
        """Start the Ollama server in a separate thread"""
        def start_server():
            self.root.after(0, lambda: self.set_buttons_loading(True))
            try:
                # Try to start Ollama using common commands
                result = None
                commands = [
                    ["ollama", "serve"],
                    ["systemctl", "start", "ollama"],
                    ["/usr/local/bin/ollama", "serve"]
                ]
                
                for cmd in commands:
                    try:
                        # Start the process in the background
                        process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            start_new_session=True
                        )
                        # Don't wait for completion as 'ollama serve' runs continuously
                        time.sleep(2)  # Give it a moment to start
                        result = {"success": True, "command": " ".join(cmd)}
                        break
                    except FileNotFoundError:
                        continue
                    except Exception as e:
                        result = {"success": False, "error": str(e)}
                
                if result is None:
                    result = {"success": False, "error": "Ollama executable not found"}
                
                self.root.after(0, lambda: self.handle_server_operation_result(
                    "start", result))
            except Exception as e:
                self.root.after(0, lambda: self.handle_server_operation_result(
                    "start", {"success": False, "error": str(e)}))
        
        threading.Thread(target=start_server, daemon=True).start()
    
    def stop_server_async(self):
        """Stop the Ollama server in a separate thread"""
        def stop_server():
            self.root.after(0, lambda: self.set_buttons_loading(True))
            try:
                # Try to stop Ollama using common commands
                result = None
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
                        result = {
                            "success": process.returncode == 0,
                            "command": " ".join(cmd),
                            "output": process.stdout,
                            "error": process.stderr
                        }
                        if result["success"]:
                            break
                    except FileNotFoundError:
                        continue
                    except subprocess.TimeoutExpired:
                        result = {"success": False, "error": "Command timed out"}
                        break
                    except Exception as e:
                        result = {"success": False, "error": str(e)}
                
                if result is None:
                    result = {"success": False, "error": "No stop command succeeded"}
                
                self.root.after(0, lambda: self.handle_server_operation_result(
                    "stop", result))
            except Exception as e:
                self.root.after(0, lambda: self.handle_server_operation_result(
                    "stop", {"success": False, "error": str(e)}))
        
        threading.Thread(target=stop_server, daemon=True).start()
    
    def restart_server_async(self):
        """Restart the Ollama server in a separate thread"""
        def restart_server():
            self.root.after(0, lambda: self.set_buttons_loading(True))
            
            # First stop the server
            self.stop_server_sync()
            time.sleep(3)  # Wait a bit between stop and start
            
            # Then start it again
            try:
                commands = [
                    ["ollama", "serve"],
                    ["systemctl", "restart", "ollama"],
                    ["/usr/local/bin/ollama", "serve"]
                ]
                
                result = None
                for cmd in commands:
                    try:
                        if "systemctl" in cmd:
                            # For systemctl, wait for completion
                            process = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                timeout=10
                            )
                            result = {
                                "success": process.returncode == 0,
                                "command": " ".join(cmd)
                            }
                        else:
                            # For direct ollama serve, start in background
                            process = subprocess.Popen(
                                cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                start_new_session=True
                            )
                            time.sleep(2)
                            result = {"success": True, "command": " ".join(cmd)}
                        
                        if result["success"]:
                            break
                    except FileNotFoundError:
                        continue
                    except Exception as e:
                        result = {"success": False, "error": str(e)}
                
                if result is None:
                    result = {"success": False, "error": "Restart failed"}
                
                self.root.after(0, lambda: self.handle_server_operation_result(
                    "restart", result))
            except Exception as e:
                self.root.after(0, lambda: self.handle_server_operation_result(
                    "restart", {"success": False, "error": str(e)}))
        
        threading.Thread(target=restart_server, daemon=True).start()
    
    def stop_server_sync(self):
        """Stop server synchronously (for restart operation)"""
        commands = [
            ["pkill", "-f", "ollama"],
            ["systemctl", "stop", "ollama"],
            ["killall", "ollama"]
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, capture_output=True, timeout=10)
                return
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
    
    def handle_server_operation_result(self, operation: str, result: Dict[str, Any]):
        """Handle the result of a server operation"""
        self.set_buttons_loading(False)
        
        if result["success"]:
            messagebox.showinfo(
                "Success",
                f"Server {operation} operation completed successfully."
            )
        else:
            error_msg = result.get("error", "Unknown error")
            messagebox.showerror(
                "Error",
                f"Failed to {operation} server: {error_msg}"
            )
        
        # Refresh status after any operation
        self.root.after(1000, self.check_server_status_async)
    
    def set_buttons_loading(self, loading: bool):
        """Set button states to loading or normal"""
        state = "disabled" if loading else "normal"
        self.start_button.config(state=state)
        self.stop_button.config(state=state)
        self.restart_button.config(state=state)
        self.refresh_button.config(state=state)
        
        if loading:
            self.status_label.config(text="⏳ Processing...", foreground="blue")
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh functionality"""
        self.auto_refresh = self.auto_refresh_var.get()
    
    def start_status_monitor(self):
        """Start the automatic status monitoring"""
        def monitor():
            if self.auto_refresh:
                self.check_server_status_async()
            # Schedule next check
            self.root.after(5000, monitor)  # Check every 5 seconds
        
        # Initial check
        self.check_server_status_async()
        # Start monitoring
        self.root.after(5000, monitor)
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    app = OllamaWrapper()
    app.run()


if __name__ == "__main__":
    main()