#!/usr/bin/env python3
"""
Entry point for the LibreAssistant GUI application.
Supports both Ollama model management (legacy) and plugin/MCP integration.
"""

import os
import signal
import sys
import time
from ollama_manager import app, create_templates, set_plugin_loader
from plugin_loader import PluginLoader
from app_config import get_config

# Global plugin loader instance for cleanup
plugin_loader = None

def auto_start_plugins():
    """
    Automatically discover and start all available MCP plugin servers.
    Can be disabled by setting DISABLE_PLUGIN_AUTOSTART environment variable.
    """
    config = get_config()
    if config.disable_plugin_autostart:
        print("[AutoStart] Plugin auto-start disabled via DISABLE_PLUGIN_AUTOSTART environment variable")
        return None
    
    global plugin_loader
    plugin_loader = PluginLoader()
    plugins = plugin_loader.discover_plugins()
    
    if not plugins:
        print("[AutoStart] No plugins found to start")
        return plugin_loader
    
    print(f"[AutoStart] Found {len(plugins)} plugins, auto-approving permissions and starting them...")
    
    # Auto-approve all permissions for auto-start mode
    plugin_loader.auto_approve_all_plugins()
    
    started_count = 0
    failed_count = 0
    
    for plugin in plugins:
        try:
            print(f"[AutoStart] Starting plugin: {plugin.name} ({plugin.id})")
            
            # Start the plugin
            success = plugin.start()
            if success:
                print(f"[AutoStart] ✓ Successfully started {plugin.name} on port {plugin.mcp_port}")
                started_count += 1
                # Small delay to avoid port conflicts
                time.sleep(0.5)
            else:
                print(f"[AutoStart] ✗ Failed to start {plugin.name}: {plugin.last_error}")
                failed_count += 1
                
        except Exception as e:
            print(f"[AutoStart] ✗ Error starting {plugin.name}: {e}")
            failed_count += 1
    
    print(f"[AutoStart] Plugin startup complete: {started_count} started, {failed_count} failed")
    
    # Share the plugin_loader instance with ollama_manager
    set_plugin_loader(plugin_loader)
    
    return plugin_loader

def signal_handler(signum, frame):
    """Handle shutdown signals to gracefully stop all plugin servers"""
    print(f"\n[Shutdown] Received signal {signum}, shutting down...")
    if plugin_loader:
        print("[Shutdown] Stopping all plugin servers...")
        plugin_loader.stop_all_plugins()
        print("[Shutdown] All plugins stopped")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # Create templates
    create_templates()
    
    # Only start plugins if we're not in the Flask reloader subprocess
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Auto-start plugin servers only in main process
        plugin_loader = auto_start_plugins()
    else:
        # In the reloaded process, we need to set up the plugin_loader too
        plugin_loader = PluginLoader()
        plugin_loader.discover_plugins()
        set_plugin_loader(plugin_loader)
    
    print("[Main] Starting Flask application...")
    config = get_config()
    flask_config = config.get_flask_config()
    try:
        app.run(host=flask_config['host'], port=flask_config['port'], debug=flask_config['debug'])
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)