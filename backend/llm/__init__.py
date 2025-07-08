"""
LLM integration package for LibreAssistant.
"""

from .ollama_client import OllamaClient, close_ollama_client, get_ollama_client
from .prompt_manager import (
    ConversationContext,
    PromptBuilder,
    PromptManager,
    PromptTemplate,
    clear_conversation_context,
    get_conversation_context,
    get_prompt_builder,
    get_prompt_manager,
)

__all__ = [
    "OllamaClient",
    "get_ollama_client",
    "close_ollama_client",
    "PromptManager",
    "PromptTemplate",
    "ConversationContext",
    "PromptBuilder",
    "get_prompt_manager",
    "get_conversation_context",
    "clear_conversation_context",
    "get_prompt_builder",
]
