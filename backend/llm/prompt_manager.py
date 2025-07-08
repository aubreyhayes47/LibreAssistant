"""
Prompt management and context handling for LibreAssistant.
"""

# ruff: noqa: E501

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# Use absolute imports when running as main module
try:
    from ..utils.config import get_config
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from utils.config import get_config
    from utils.logger import get_logger

logger = get_logger("llm")


@dataclass
class PromptTemplate:
    """Template for system prompts."""

    name: str
    content: str
    variables: List[str]
    description: str

    def format(self, **kwargs) -> str:
        """Format the template with provided variables."""
        try:
            return self.content.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing variable for prompt template '{self.name}': {e}")
            return self.content


class PromptManager:
    """Manages system prompts and conversation context."""

    def __init__(self):
        """Initialize prompt manager with default templates."""
        self.templates = self._initialize_templates()
        self.config = get_config()

    def _initialize_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize default prompt templates."""
        templates = {}

        # General chat assistant
        templates["chat_assistant"] = PromptTemplate(
            name="chat_assistant",
            content="""You are LibreAssistant, a privacy-focused AI assistant that helps users with web browsing, content analysis, and general assistance. You have access to the user's browsing history and bookmarks, and can help analyze web content.

Key capabilities:
- Analyze and summarize web pages
- Search through browsing history and bookmarks
- Provide general assistance and answer questions
- Help organize and understand web content

Current date and time: {current_time}
User preferences: {user_preferences}

Be helpful, accurate, and respect user privacy. Always explain your reasoning and provide sources when possible.""",
            variables=["current_time", "user_preferences"],
            description="General chat assistant for LibreAssistant",
        )

        # Web content summarization
        templates["content_summarizer"] = PromptTemplate(
            name="content_summarizer",
            content="""You are a web content analyzer for LibreAssistant. Summarize the following page briefly and list key points.

Instructions:
1. Write a concise summary of no more than 3 sentences (under 150 words)
2. Provide 3–5 bullet points of the most important information
3. Identify the content type (article, blog post, documentation, etc.)
4. Mention any actionable items or important dates
5. Maintain objectivity and accuracy

URL: {url}
Title: {title}
Content length: {content_length} characters

Focus on the most relevant information for the user.""",
            variables=["url", "title", "content_length"],
            description="Summarizes web page content",
        )

        # Search query enhancement
        templates["search_enhancer"] = PromptTemplate(
            name="search_enhancer",
            content="""You are a search query optimizer for LibreAssistant. Help improve search queries to get better results.

User's original query: "{original_query}"
Context: {context}

Provide:
1. An enhanced version of the query with better keywords
2. Alternative search terms or phrases
3. Specific search strategies that might be helpful
4. Any clarifying questions if the query is ambiguous

Focus on making the search more effective and comprehensive.""",
            variables=["original_query", "context"],
            description="Enhances search queries for better results",
        )

        # Content analysis for bookmarking
        templates["bookmark_analyzer"] = PromptTemplate(
            name="bookmark_analyzer",
            content="""You are analyzing web content to help organize bookmarks in LibreAssistant.

Analyze this content and provide:
1. Suggested tags (3-5 relevant keywords)
2. Recommended folder/category
3. Content type (article, tutorial, reference, news, etc.)
4. Why this content might be valuable to bookmark
5. Related topics or themes

URL: {url}
Title: {title}
Content preview: {content_preview}

Focus on making the content easily discoverable and well-organized.""",
            variables=["url", "title", "content_preview"],
            description="Analyzes content for bookmark organization",
        )

        # Error explanation
        templates["error_explainer"] = PromptTemplate(
            name="error_explainer",
            content="""You are helping a user understand an error in LibreAssistant.

Error details:
- Error type: {error_type}
- Error message: {error_message}
- Context: {context}

Provide:
1. A clear explanation of what went wrong
2. Possible causes of the error
3. Step-by-step troubleshooting suggestions
4. How to prevent this error in the future

Be helpful and non-technical in your explanation.""",
            variables=["error_type", "error_message", "context"],
            description="Explains errors in user-friendly terms",
        )

        return templates

    def get_prompt(self, template_name: str, **kwargs) -> str:
        """Get a formatted prompt from a template."""
        if template_name not in self.templates:
            logger.warning(f"Unknown prompt template: {template_name}")
            return self.templates["chat_assistant"].format(
                current_time=datetime.now().isoformat(), user_preferences="default"
            )

        template = self.templates[template_name]

        # Add default values for common variables
        defaults = {
            "current_time": datetime.now().isoformat(),
            "user_preferences": "default",
            "context": "general assistance",
        }

        # Merge provided kwargs with defaults
        format_kwargs = {**defaults, **kwargs}

        return template.format(**format_kwargs)

    def add_template(self, template: PromptTemplate):
        """Add a custom prompt template."""
        self.templates[template.name] = template
        logger.info(f"Added prompt template: {template.name}")

    def list_templates(self) -> List[Dict[str, str]]:
        """List all available prompt templates."""
        return [
            {
                "name": template.name,
                "description": template.description,
                "variables": template.variables,
            }
            for template in self.templates.values()
        ]


class ConversationContext:
    """Manages conversation context and history."""

    def __init__(self, session_id: str):
        """Initialize conversation context for a session."""
        self.session_id = session_id
        self.messages: List[Dict[str, str]] = []
        self.config = get_config()
        self.max_context_length = self.config.llm.max_context_length

    def add_message(self, role: str, content: str):
        """Add a message to the conversation context."""
        self.messages.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )

        # Trim context if it gets too long
        self._trim_context()

    def get_context_messages(self) -> List[Dict[str, str]]:
        """Get messages formatted for LLM consumption."""
        # Return only role and content for LLM
        return [
            {"role": msg["role"], "content": msg["content"]} for msg in self.messages
        ]

    def _trim_context(self):
        """Trim conversation context to stay within limits."""
        if len(self.messages) <= 2:  # Keep at least one exchange
            return

        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        total_chars = sum(len(msg["content"]) for msg in self.messages)
        estimated_tokens = total_chars // 4

        # If we're over the limit, remove older messages (but keep the first system message)
        while estimated_tokens > self.max_context_length and len(self.messages) > 2:
            # Remove the second message (keep system message if present)
            if self.messages[0]["role"] == "system":
                self.messages.pop(1)
            else:
                self.messages.pop(0)

            total_chars = sum(len(msg["content"]) for msg in self.messages)
            estimated_tokens = total_chars // 4

        if len(self.messages) != len(self.messages):  # If we trimmed anything
            logger.info(f"Trimmed conversation context for session {self.session_id}")

    def clear_context(self):
        """Clear all conversation context."""
        self.messages = []
        logger.info(f"Cleared conversation context for session {self.session_id}")

    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context."""
        if not self.messages:
            return {
                "message_count": 0,
                "total_chars": 0,
                "estimated_tokens": 0,
                "last_message_time": None,
            }

        total_chars = sum(len(msg["content"]) for msg in self.messages)
        return {
            "message_count": len(self.messages),
            "total_chars": total_chars,
            "estimated_tokens": total_chars // 4,
            "last_message_time": self.messages[-1]["timestamp"],
        }


class PromptBuilder:
    """Helper class for building complex prompts."""

    def __init__(self, prompt_manager: PromptManager):
        """Initialize prompt builder."""
        self.prompt_manager = prompt_manager

    def build_chat_prompt(
        self, user_message: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build a chat prompt with context."""
        context = context or {}

        # Get user preferences (could be loaded from database)
        user_preferences = context.get("user_preferences", "default")

        return self.prompt_manager.get_prompt(
            "chat_assistant",
            current_time=datetime.now().isoformat(),
            user_preferences=user_preferences,
        )

    def build_summarization_prompt(self, url: str, title: str, content: str) -> str:
        """Build a prompt for content summarization."""
        return self.prompt_manager.get_prompt(
            "content_summarizer",
            url=url,
            title=title or "Unknown Title",
            content_length=len(content),
        )

    def build_bookmark_analysis_prompt(self, url: str, title: str, content: str) -> str:
        """Build a prompt for bookmark analysis."""
        # Use first 500 characters as preview
        content_preview = content[:500] + "..." if len(content) > 500 else content

        return self.prompt_manager.get_prompt(
            "bookmark_analyzer",
            url=url,
            title=title or "Unknown Title",
            content_preview=content_preview,
        )

    def build_search_enhancement_prompt(self, query: str, context: str = "") -> str:
        """Build a prompt for search query enhancement."""
        return self.prompt_manager.get_prompt(
            "search_enhancer", original_query=query, context=context
        )


# Global instances
_prompt_manager: Optional[PromptManager] = None
_contexts: Dict[str, ConversationContext] = {}


def get_prompt_manager() -> PromptManager:
    """Get global prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


def get_conversation_context(session_id: str) -> ConversationContext:
    """Get conversation context for a session."""
    global _contexts
    if session_id not in _contexts:
        _contexts[session_id] = ConversationContext(session_id)
    return _contexts[session_id]


def clear_conversation_context(session_id: str):
    """Clear conversation context for a session."""
    global _contexts
    if session_id in _contexts:
        del _contexts[session_id]
        logger.info(f"Cleared conversation context for session {session_id}")


def get_prompt_builder() -> PromptBuilder:
    """Get prompt builder instance."""
    return PromptBuilder(get_prompt_manager())
