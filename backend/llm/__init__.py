"""
LLM integration package for LibreAssistant.
"""

from .ollama_client import (
    OllamaClient,
    get_ollama_client,
    close_ollama_client
)
from .prompt_manager import (
    PromptManager,
    PromptTemplate,
    ConversationContext,
    PromptBuilder,
    get_prompt_manager,
    get_conversation_context,
    clear_conversation_context,
    get_prompt_builder
)

__all__ = [
    'OllamaClient',
    'get_ollama_client',
    'close_ollama_client',
    'PromptManager',
    'PromptTemplate',
    'ConversationContext',
    'PromptBuilder',
    'get_prompt_manager',
    'get_conversation_context',
    'clear_conversation_context',
    'get_prompt_builder'
]