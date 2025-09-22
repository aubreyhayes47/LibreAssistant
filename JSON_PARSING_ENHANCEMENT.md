# Enhanced JSON Parsing for LibreAssistant

## Issue Summary
Resolved GitHub issue #66: "Robustly parse JSON responses with leading/trailing markdown or extra text"

## Problem
The LLM protocol parser in `llm_protocol.py` could only handle raw JSON responses. Many LLMs wrap their JSON responses in markdown code blocks (```json ... ```) or include explanatory text before/after the JSON, causing parsing failures.

## Solution
Enhanced the JSON parsing functionality with multiple extraction strategies:

### 1. Markdown Code Block Extraction
- Handles both `​```json` and generic `​```` code blocks
- Uses regex patterns to extract JSON content from markdown formatting
- Prioritizes markdown blocks as the most reliable format

### 2. Schema-Aware Extraction  
- When multiple JSON blocks exist, selects the first one that passes schema validation
- Prevents extraction of nested JSON strings that don't represent the main response
- Ensures compatibility with the LLM protocol schema

### 3. Multi-line JSON Detection
- Uses line-by-line parsing to handle complex nested structures
- Tracks brace/bracket counts to identify complete JSON objects/arrays
- More reliable than regex for deeply nested content

### 4. Graceful Fallback
- Maintains backward compatibility with existing raw JSON responses
- Provides detailed error messages for debugging
- Falls back to treating content as plain text when no JSON is found

## Key Features

### Robust Pattern Matching
- **Code blocks**: `​```json ... ​```` and `​``` ... ​````
- **Inline JSON**: Single-line JSON embedded in text
- **Multi-line structures**: Complex nested JSON across multiple lines
- **Whitespace handling**: Flexible whitespace and formatting variations

### Error Handling
- Detailed error messages with context
- Preserves original response text for debugging
- Distinguishes between JSON parse errors and schema validation errors
- Graceful degradation for unsupported formats

### Performance Optimizations
- Direct parsing attempt first (fastest path for raw JSON)
- Prioritized extraction strategies (most reliable first)
- Minimal regex usage to avoid performance issues
- Early termination when valid JSON is found

## Testing Coverage

Comprehensive test suite covering:
- ✅ Basic JSON parsing (backward compatibility)
- ✅ Markdown-wrapped JSON responses
- ✅ JSON with surrounding explanatory text
- ✅ Multiple JSON blocks (schema-aware selection)
- ✅ Complex nested JSON structures
- ✅ Malformed inputs with error handling
- ✅ Edge cases (whitespace, inline JSON, etc.)
- ✅ Real-world LLM response examples
- ✅ Fallback behavior validation

## Files Modified

### `llm_protocol.py`
- Added `_extract_json_from_text()` method for basic JSON extraction
- Added `_extract_valid_json_from_text()` method for schema-aware extraction
- Added `_is_valid_and_schema_compliant_json()` helper method
- Enhanced `parse_response()` to use new extraction logic
- Updated `parse_response_with_fallback()` for improved error handling
- Added regex import for pattern matching

### New Test Files
- `test_llm_protocol_json_extraction.py` - Comprehensive test suite
- `demo_robust_json_parsing.py` - Interactive demonstration

## Backward Compatibility
- ✅ All existing functionality preserved
- ✅ Existing tests continue to pass
- ✅ No breaking changes to API
- ✅ Performance maintained for raw JSON responses

## Examples

### Before (Failed)
```
Input: ```json\n{"action": "message", "content": {"text": "Hello"}}\n```
Error: "Expecting value at line 1, column 1"
```

### After (Success)
```
Input: ```json\n{"action": "message", "content": {"text": "Hello"}}\n```
Result: {"action": "message", "content": {"text": "Hello"}}
```

## Impact
This enhancement makes LibreAssistant compatible with a much wider range of LLM models and response formats, improving reliability and user experience when working with various AI models that format their JSON responses differently.