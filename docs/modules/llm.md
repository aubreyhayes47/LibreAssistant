# LibreAssistant LLM Module

⚠️ **Implementation Status**: This module describes current Ollama integration and planned advanced features.

🟢 **Currently Working**: Basic Ollama client, simple chat functionality  
🟡 **Partially Working**: Conversation context, prompt management  
🔴 **Planned**: Advanced prompt templates, model management, performance optimization

This module handles Large Language Model integration with Ollama for local AI processing.

## Current vs Planned Features

**Current Implementation:**
- Basic Ollama client for chat
- Simple conversation context
- Manual model management
- Basic prompt handling

**Planned Enhancements:**
- **Phase 1.2**: Advanced prompt template system
- **Phase 1.3**: Persistent conversation context with database integration
- **Phase 1.4**: Model management UI and automatic model switching
- **Phase 2**: RAG (Retrieval-Augmented Generation) with knowledge base

See the [Implementation Roadmap](../IMPLEMENTATION_ROADMAP.md) for detailed development timeline.

## Overview

LibreAssistant integrates with Ollama to provide local AI capabilities while maintaining privacy. All AI processing happens on-device with no external API calls.

## Components

### Ollama Client (`ollama_client.py`)

Handles communication with local Ollama instance:

```python
from backend.llm.ollama_client import OllamaClient

client = OllamaClient()
response = await client.generate("What is AI?", model="llama2")
```

### Prompt Manager (`prompt_manager.py`)

Manages conversation context and prompt templates:

```python
from backend.llm.prompt_manager import PromptManager

pm = PromptManager()
pm.add_user_message("Hello!")
pm.add_assistant_message("Hi there!")
context = pm.get_conversation_context()
```

## Configuration

### Ollama Setup

Ensure Ollama is installed and running:

```bash
# Install Ollama (follow official instructions)
# Pull a model
ollama pull llama2

# Verify installation
ollama list
```

### Model Management

```python
# List available models
models = await client.list_models()

# Pull new model
await client.pull_model("mistral")

# Set default model
await settings.save_setting("default_model", "mistral")
```

## Usage Patterns

### Basic Chat

```python
from backend.llm.chat_handler import ChatHandler

chat = ChatHandler()
response = await chat.process_message(
    message="Explain quantum computing",
    session_id="session_123"
)
```

### Content Summarization

```python
# Summarize web content
summary = await summarize_content(
    content=extracted_text,
    prompt_template="summarize_article",
    max_tokens=150
)
```

### Context Management

```python
# Maintain conversation context
pm = PromptManager(session_id="session_123")
pm.load_context()  # Load from database

# Add new interaction
pm.add_interaction(user_msg, assistant_response)
pm.save_context()  # Save to database
```

## Prompt Templates

### Built-in Templates

Located in `prompts/templates/`:

- `system_prompt.txt` - Base system prompt
- `summarize_article.txt` - Article summarization
- `answer_question.txt` - Q&A responses
- `web_search_summary.txt` - Search result summaries

### Custom Templates

```python
# Register custom template
pm.register_template(
    name="custom_summary",
    template="Summarize this content in {style} style: {content}"
)

# Use template
response = await pm.apply_template(
    "custom_summary",
    style="technical",
    content=article_text
)
```

## Performance Optimization

### Model Selection

```python
# Choose model based on task
def select_model(task_type):
    if task_type == "summarization":
        return "llama2"  # Fast, good for summaries
    elif task_type == "analysis":
        return "mistral"  # Better reasoning
    else:
        return settings.get("default_model")
```

### Response Caching

```python
# Cache similar prompts
cache_key = hash(prompt + model + parameters)
cached_response = await get_cached_response(cache_key)

if not cached_response:
    response = await client.generate(prompt)
    await cache_response(cache_key, response)
```

### Context Window Management

```python
# Manage context length
def trim_context(context, max_tokens=2048):
    # Keep system prompt + recent messages
    # Summarize older conversation if needed
    return trimmed_context
```

## Privacy Features

### Local Processing
- All AI processing happens locally
- No data sent to external services
- User prompts never leave device

### Data Retention
- Configurable conversation retention
- Automatic context cleanup
- User-controlled data deletion

### Security
- No API keys or external authentication
- Local model storage
- Encrypted conversation storage

## API Reference

### OllamaClient Class

#### Core Methods

**generate(prompt: str, model: str = None, **kwargs) -> dict**
- Generates text response
- Supports model override
- Returns structured response

**chat(messages: list, model: str = None) -> dict**
- Multi-turn conversation
- Maintains context automatically
- Supports system messages

**list_models() -> list**
- Returns available models
- Includes model metadata
- Cached for performance

#### Configuration Methods

**set_default_model(model: str) -> None**
- Sets default model for generation
- Validates model availability
- Updates user settings

**get_model_info(model: str) -> dict**
- Returns model details
- Includes size and capabilities
- Cached response

### PromptManager Class

#### Context Management

**add_user_message(message: str) -> None**
- Adds user message to context
- Timestamps automatically
- Maintains conversation flow

**add_assistant_message(message: str) -> None**
- Adds assistant response
- Links to previous user message
- Updates context state

**get_conversation_context(max_messages: int = 20) -> list**
- Returns recent conversation
- Formatted for LLM input
- Includes system prompt

#### Template Management

**load_template(name: str) -> str**
- Loads prompt template
- Supports variables
- Cached for performance

**apply_template(name: str, **variables) -> str**
- Applies variables to template
- Validates required variables
- Returns formatted prompt

## Development

### Adding New Features

1. **New Prompt Template:**
   ```python
   # Add to prompts/templates/
   # Register in prompt_manager.py
   # Add tests for template
   ```

2. **Model Integration:**
   ```python
   # Extend ollama_client.py
   # Add model-specific configurations
   # Update model selection logic
   ```

3. **Processing Pipeline:**
   ```python
   # Create new processor in processors/
   # Integrate with main pipeline
   # Add appropriate tests
   ```

### Testing

```bash
# Run LLM tests (requires Ollama)
cd backend
python -m pytest llm/tests/

# Run without Ollama (mocked)
python -m pytest llm/tests/ --mock-ollama
```

## Error Handling

### Common Issues

1. **Ollama Not Running:**
   ```python
   try:
       response = await client.generate(prompt)
   except ConnectionError:
       return {"error": "Ollama not available"}
   ```

2. **Model Not Found:**
   ```python
   if model not in available_models:
       # Fallback to default model
       model = settings.get("default_model")
   ```

3. **Context Too Long:**
   ```python
   if token_count > max_context:
       context = trim_context(context, max_context)
   ```

## Configuration

### LLM Settings

```python
LLM_CONFIG = {
    "ollama": {
        "base_url": "http://localhost:11434",
        "timeout": 60,
        "default_model": "llama2",
        "max_context": 2048,
        "temperature": 0.7
    },
    "caching": {
        "enabled": True,
        "ttl": 3600,
        "max_size": 1000
    },
    "templates": {
        "path": "backend/llm/templates",
        "auto_reload": True
    }
}
```

### Model Presets

```python
MODEL_PRESETS = {
    "fast": {
        "model": "llama2",
        "temperature": 0.5,
        "max_tokens": 256
    },
    "accurate": {
        "model": "mistral",
        "temperature": 0.3,
        "max_tokens": 512
    },
    "creative": {
        "model": "llama2",
        "temperature": 0.9,
        "max_tokens": 1024
    }
}
```

## Integration Points

### With Database Module
- Conversation persistence
- Settings management
- Response caching

### With Web Agents
- Content summarization
- Search result processing
- Question answering

### With Frontend
- Real-time chat interface
- Progress indicators
- Model selection UI

## Examples

### Simple Generation

```python
from backend.llm.ollama_client import OllamaClient

client = OllamaClient()
response = await client.generate(
    "Explain the concept of machine learning in simple terms."
)

print(response['text'])
```

### Conversation with Context

```python
from backend.llm.prompt_manager import PromptManager
from backend.llm.ollama_client import OllamaClient

pm = PromptManager(session_id="demo")
client = OllamaClient()

# First exchange
pm.add_user_message("What is Python?")
context = pm.get_conversation_context()
response = await client.chat(context)
pm.add_assistant_message(response['message']['content'])

# Follow-up question
pm.add_user_message("Can you show me an example?")
context = pm.get_conversation_context()
response = await client.chat(context)
pm.add_assistant_message(response['message']['content'])
```

### Content Summarization

```python
async def summarize_article(url: str) -> str:
    # Extract content
    from backend.agents.content_extractor import extract_content
    content = await extract_content(url)
    
    if not content['success']:
        return "Failed to extract content"
    
    # Create summarization prompt
    pm = PromptManager()
    prompt = pm.apply_template(
        "summarize_article",
        content=content['data']['text'],
        max_length=200
    )
    
    # Generate summary
    client = OllamaClient()
    response = await client.generate(prompt)
    
    return response['text']
```

This LLM module enables LibreAssistant to provide intelligent, privacy-preserving AI capabilities through local processing while maintaining excellent performance and user control.
