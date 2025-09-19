# Fix JSON Response Parsing for Proper Plugin Invocations

## Issue Description

The LibreAssistant LLM responses were not being properly parsed to handle plugin invocations deterministically. The first response from the LLM was getting passed directly to the user as a message, without properly:

1. Parsing out plugin invocations 
2. Actually performing the operations deterministically (e.g., calling CourtListener API, calling Brave Search API, performing file operations on local files, etc.)
3. Feeding plugin results back in JSON format to the LLM
4. Parsing further plugin invocations as needed
5. Parsing the final message to the user and presenting it in a user-friendly way rather than raw JSON display

## Root Cause

The original implementation in `ollama_manager.py` only handled a single plugin invocation and did not loop to process multiple consecutive plugin calls that might be needed to fully address a user's request.

## Solution Implemented

### 1. Iterative Plugin Processing Loop
- Replaced single plugin invocation with a loop that can handle multiple sequential plugin calls
- Added maximum iteration limit (5) to prevent infinite loops
- Tracks all plugins used during the conversation

### 2. Enhanced System Instructions
Updated `llm_protocol.py` to include detailed usage examples for all available plugins:

**Brave Search Plugin:**
```json
{
  "action": "plugin_invoke",
  "content": {
    "plugin": "brave-search",
    "input": {"query": "latest developments in artificial intelligence 2024"},
    "reason": "User is asking about recent AI developments, need current web search results"
  }
}
```

**CourtListener Plugin:**
```json
{
  "action": "plugin_invoke", 
  "content": {
    "plugin": "courtlistener",
    "input": {"query": "copyright fair use", "court": "supreme"},
    "reason": "User needs legal precedent research on copyright fair use doctrine"
  }
}
```

**Local File I/O Plugin:**
```json
// Reading a file
{
  "action": "plugin_invoke",
  "content": {
    "plugin": "local-fileio", 
    "input": {"operation": "read", "path": "project_notes.txt"},
    "reason": "User wants me to read their project notes file for context"
  }
}

// Writing to a file  
{
  "action": "plugin_invoke",
  "content": {
    "plugin": "local-fileio",
    "input": {"operation": "write", "path": "summary.md", "content": "# Project Summary\n\nThis is the project summary..."},
    "reason": "User requested to save the generated summary to a markdown file"
  }
}

// Listing files
{
  "action": "plugin_invoke", 
  "content": {
    "plugin": "local-fileio",
    "input": {"operation": "list", "path": "."},
    "reason": "User wants to see what files are available in their directory"
  }
}
```

### 3. Multi-Plugin Workflow Support
The system now supports workflows like:
1. First, search for information: invoke brave-search with query
2. Then read related files: invoke local-fileio to read relevant files 
3. Finally respond with message action combining all information

### 4. Improved Plugin Result Handling
- Enhanced follow-up prompts to encourage LLM to continue with more plugin calls if needed
- Better tracking and reporting of all plugins used in a request
- User-friendly final response formatting instead of raw JSON

### 5. Safety Measures
- Maximum iteration protection to prevent infinite plugin loops
- Proper error handling for plugin failures
- Graceful fallbacks when plugins are unavailable

## API Response Changes

The API now returns enhanced information about plugin usage:

```json
{
  "success": true,
  "response": "User-friendly final response text",
  "markdown": false,
  "plugin_count": 2,
  "plugins_used": [
    {
      "id": "brave-search",
      "reason": "Search for current information",
      "input": {"query": "AI developments"}
    },
    {
      "id": "local-fileio", 
      "reason": "Save results to file",
      "input": {"operation": "write", "path": "results.txt", "content": "..."}
    }
  ],
  "request_id": "uuid"
}
```

## Testing

Comprehensive tests were added to verify:
- ✅ Basic plugin parsing functionality
- ✅ System instruction generation with plugin details  
- ✅ Iterative plugin processing with multiple sequential calls
- ✅ Maximum iteration protection (5 iterations limit)
- ✅ All existing functionality remains intact

## Files Modified

1. **`ollama_manager.py`**: Added iterative plugin processing loop in the `/api/generate` endpoint
2. **`llm_protocol.py`**: Enhanced system instructions with detailed plugin examples and updated plugin result prompts

## Benefits

1. **Deterministic Plugin Execution**: Plugins are now reliably invoked and their results properly processed
2. **Multi-Step Workflows**: LLM can chain multiple plugin calls to gather comprehensive information
3. **Better User Experience**: Final responses are user-friendly rather than raw JSON
4. **Comprehensive Plugin Documentation**: LLM has detailed examples for all available plugins
5. **Robust Error Handling**: Proper handling of plugin failures and infinite loop prevention

## Example Workflow

**User Request**: "Find recent AI news and save it to a file"

**System Execution**:
1. LLM responds with brave-search plugin invocation
2. System executes search and feeds results back to LLM
3. LLM responds with local-fileio plugin invocation to save results
4. System executes file write and feeds confirmation back to LLM  
5. LLM responds with user message explaining what was accomplished

**Final Response**: "I've searched for the latest AI news and saved the findings to ai_news.txt. Here's a summary of what I found: [summary of search results]"

This implementation fully addresses the original issue of improper JSON response parsing and provides a robust foundation for plugin-enhanced AI assistance.