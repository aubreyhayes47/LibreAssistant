#!/usr/bin/env python3
"""
Entry point for the LibreAssistant GUI application.
Supports both Ollama model management (legacy) and plugin/MCP integration.
"""


from ollama_manager import main



if __name__ == "__main__":
    main()