# LibreAssistant API Documentation

This document describes all available backend commands accessible through the Tauri frontend.

## Command Structure

All commands follow this pattern:

**Frontend (JavaScript/Svelte):**
```javascript
import { invoke } from '@tauri-apps/api/core';

const result = await invoke('command_name', { param1: 'value1', param2: 'value2' });
```

**Response Format:**
```json
{
  "success": true|false,
  "error": "error message if success is false",
  "data": "command-specific response data"
}
```

## Available Commands

### Core Commands

#### `hello_backend`
Test connectivity to the Python backend.

**Parameters:**
- `name` (string): Name to greet

**Example:**
```javascript
const result = await invoke('hello_backend', { name: 'World' });
```

#### `init_database`
Initialize the SQLite database with required tables.

**Parameters:** None

**Example:**
```javascript
const result = await invoke('init_database');
```

### Content Processing

#### `process_url`
Extract content from a web page.

**Parameters:**
- `url` (string): URL to process

**Example:**
```javascript
const result = await invoke('process_url', { url: 'https://example.com' });
```

#### `summarize_page`
Extract and summarize content from a web page using AI.

**Parameters:**
- `url` (string): URL to summarize

**Returns:**
- `summary` (string): AI-generated summary
- `title` (string): Page title
- `url` (string): Original URL

**Example:**
```javascript
const result = await invoke('summarize_page', { url: 'https://example.com' });
```

#### `analyze_content`
Analyze text content with AI.

**Parameters:**
- `content` (string): Text content to analyze

**Example:**
```javascript
const result = await invoke('analyze_content', { content: 'Some text to analyze' });
```

### Search Commands

#### `search_web`
Search the web using DuckDuckGo.

**Parameters:**
- `query` (string): Search query
- `provider` (string, optional): Search provider (default: "duckduckgo")
- `limit` (number, optional): Maximum number of results

**Returns:**
- `results` (array): Search results with title, url, snippet

**Example:**
```javascript
const result = await invoke('search_web', { 
  query: 'artificial intelligence', 
  limit: 10 
});
```

### Chat Commands

#### `chat_with_llm`
Chat with the local Ollama LLM.

**Parameters:**
- `message` (string): User message
- `session_id` (string, optional): Chat session ID (generated if not provided)

**Returns:**
- `response` (string): AI response
- `session_id` (string): Session ID for context
- `model` (string): Model used

**Example:**
```javascript
const result = await invoke('chat_with_llm', { 
  message: 'Hello, how are you?',
  session_id: 'my-session'
});
```

#### `get_chat_history`
Retrieve chat conversation history.

**Parameters:**
- `session_id` (string, optional): Session to retrieve
- `limit` (number, optional): Maximum number of messages

**Returns:**
- `messages` (array): Chat messages with role, content, timestamp

**Example:**
```javascript
const result = await invoke('get_chat_history', { session_id: 'my-session', limit: 50 });
```

#### `clear_chat_history`
Clear chat history for a session or all sessions.

**Parameters:**
- `session_id` (string, optional): Session to clear (all sessions if not provided)

**Example:**
```javascript
const result = await invoke('clear_chat_history', { session_id: 'my-session' });
```

#### `clear_conversation_context`
Clear the in-memory conversation context for LLM.

**Parameters:**
- `session_id` (string, optional): Session context to clear

**Example:**
```javascript
const result = await invoke('clear_conversation_context', { session_id: 'my-session' });
```

### Bookmark Commands

#### `save_bookmark`
Save a bookmark to the database.

**Parameters:**
- `url` (string): Bookmark URL
- `title` (string): Bookmark title
- `content` (string, optional): Page content

**Example:**
```javascript
const result = await invoke('save_bookmark', { 
  url: 'https://example.com',
  title: 'Example Site'
});
```

#### `get_bookmarks`
Retrieve saved bookmarks.

**Parameters:**
- `search_query` (string, optional): Filter bookmarks by query

**Returns:**
- `bookmarks` (array): Bookmark objects with url, title, created_at

**Example:**
```javascript
const result = await invoke('get_bookmarks');
```

#### `search_bookmarks`
Search through saved bookmarks.

**Parameters:**
- `query` (string): Search query
- `limit` (number, optional): Maximum number of results

**Example:**
```javascript
const result = await invoke('search_bookmarks', { query: 'example', limit: 20 });
```

### History Commands

#### `get_browser_history`
Retrieve browsing history.

**Parameters:**
- `limit` (number, optional): Maximum number of entries
- `search_query` (string, optional): Filter by query

**Returns:**
- `history` (array): History entries with url, title, visit_time

**Example:**
```javascript
const result = await invoke('get_browser_history', { limit: 100 });
```

#### `add_history_entry`
Add an entry to browsing history.

**Parameters:**
- `url` (string): Page URL
- `title` (string): Page title
- `visit_time` (string, optional): Timestamp (current time if not provided)

**Example:**
```javascript
const result = await invoke('add_history_entry', { 
  url: 'https://example.com',
  title: 'Example Page'
});
```

#### `clear_browser_history`
Clear all browsing history.

**Parameters:** None

**Example:**
```javascript
const result = await invoke('clear_browser_history');
```

### Settings Commands

#### `set_user_setting`
Save a user preference.

**Parameters:**
- `key` (string): Setting key
- `value` (string): Setting value

**Example:**
```javascript
const result = await invoke('set_user_setting', { 
  key: 'theme',
  value: 'dark'
});
```

#### `get_user_setting`
Retrieve a user preference.

**Parameters:**
- `key` (string): Setting key

**Returns:**
- `value` (string): Setting value

**Example:**
```javascript
const result = await invoke('get_user_setting', { key: 'theme' });
```

### Legacy Commands

#### `get_browser_data`
Legacy command for accessing browser data.

**Parameters:**
- `data_type` (string): Type of data to retrieve

**Example:**
```javascript
const result = await invoke('get_browser_data', { data_type: 'history' });
```

## Error Handling

All commands return a response with a `success` field. Check this field before accessing the data:

```javascript
const result = await invoke('some_command', { param: 'value' });

if (result.success) {
  // Use result.data or other response fields
  console.log('Success:', result.data);
} else {
  // Handle error
  console.error('Error:', result.error);
}
```

## Adding New Commands

To add a new command:

1. **Add to Python backend** (`backend/main.py`):
```python
async def my_new_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    # Implementation
    return {"success": True, "data": "result"}
```

2. **Register in commands dictionary**:
```python
self.commands = {
    # ...existing commands...
    "my_new_command": self.my_new_command,
}
```

3. **Add Tauri wrapper** (`frontend/src-tauri/src/lib.rs`):
```rust
#[tauri::command]
async fn my_new_command(param: String) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    payload_data.insert("param".to_string(), serde_json::Value::String(param));
    call_python_backend("my_new_command".to_string(), CommandPayload { data: payload_data }).await
}
```

4. **Add to invoke handler**:
```rust
.invoke_handler(tauri::generate_handler![
    // ...existing commands...
    my_new_command
])
```

5. **Use in frontend**:
```javascript
const result = await invoke('my_new_command', { param: 'value' });
```
