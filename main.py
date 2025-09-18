#!/usr/bin/env python3
"""
Entry point for the LibreAssistant GUI application.
Supports both Ollama model management (legacy) and plugin/MCP integration.
"""

from ollama_manager import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)