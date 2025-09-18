# LibreAssistant LLM Protocol Documentation

## Overview

LibreAssistant now supports a structured JSON schema protocol for LLM communication that enables deterministic plugin/MCP invocation and response handling.

## Features

### 1. JSON Schema Validation
- All LLM responses are validated against a strict JSON schema
- Supports two response types: `message` and `plugin_invoke`
- Provides graceful fallback for non-JSON responses

### 2. System Instructions with Plugin Discovery
- Auto-generates system instructions that expose available plugins to the LLM
- Updates dynamically based on running plugin servers
- Includes plugin capabilities and usage guidelines

### 3. Plugin Integration Flow
1. LLM decides to invoke a plugin using structured response
2. System automatically invokes the plugin with provided input
3. Plugin result is fed back to LLM for user-friendly response
4. Final response is delivered to user with plugin usage indication

### 4. Dual Mode Support
- **Schema Mode** (default): Uses structured JSON protocol with plugin support
- **Legacy Mode**: Backward compatible with original chat functionality

## API Endpoints

### Chat Generation
```
POST /api/generate
{
  "model": "model_name",
  "prompt": "user_prompt", 
  "history": [...],
  "use_schema": true,
  "stream": false
}
```

### Schema Access
```
GET /api/llm/schema
```
Returns the JSON schema for LLM responses.

### Response Validation
```
POST /api/llm/validate
{
  "response": {...}
}
```

### System Instructions
```
GET /api/llm/system_instructions
```
Returns current system instructions with available plugins.

## JSON Schema Format

### Message Response
```json
{
  "action": "message",
  "content": {
    "text": "Response text",
    "markdown": false
  }
}
```

### Plugin Invocation
```json
{
  "action": "plugin_invoke",
  "content": {
    "plugin": "plugin_id",
    "input": {"key": "value"},
    "reason": "Why calling this plugin"
  }
}
```

## UI Features

- **Plugin Support Toggle**: Enable/disable structured protocol in chat UI
- **Plugin Usage Indicators**: Visual feedback when plugins are used
- **Enhanced Message Styling**: Distinguished styling for plugin-enhanced responses

## Implementation Notes

### Streaming vs Non-Streaming
- Plugin invocations use non-streaming mode for deterministic parsing
- User messages can use either streaming or non-streaming
- Schema validation works with both modes

### Error Handling
- Invalid JSON responses fall back to plain text message format
- Schema validation errors are logged but don't break functionality
- Plugin invocation failures are gracefully handled with error messages

### Plugin Discovery
- Plugins are automatically discovered from running MCP servers
- System instructions are updated when plugins start/stop
- Plugin capabilities can be enhanced with better manifest data

## Testing

Run the comprehensive test suite:
```bash
python test_llm_protocol.py
python test_ollama_manager.py
```

## Migration

Existing chat functionality continues to work unchanged. The new protocol is enabled by default but can be disabled via the UI toggle or API parameter.