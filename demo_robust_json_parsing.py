#!/usr/bin/env python3
"""
Demonstration script showing the robust JSON parsing in action.
This script shows how the enhanced LLM protocol can now handle various 
response formats that models commonly produce.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_protocol import LLMProtocol

def demo_parsing():
    """Demonstrate the enhanced JSON parsing capabilities"""
    protocol = LLMProtocol()
    
    print("🔧 LibreAssistant Enhanced JSON Parser Demo")
    print("=" * 50)
    print()
    
    # Example 1: Basic markdown-wrapped JSON (the original issue)
    print("📋 Example 1: Markdown-wrapped JSON (Original Issue)")
    example1 = '''```json
{
  "action": "plugin_invoke",
  "content": {
    "plugin": "local-fileio",
    "input": {"operation": "read", "path": "notes.txt"},
    "reason": "User requested file read"
  }
}
```'''
    
    print("Input:")
    print(example1)
    print("\nResult:")
    try:
        result = protocol.parse_response(example1)
        print(f"✅ Successfully parsed: {result['action']} -> {result['content']['plugin']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    # Example 2: JSON with explanatory text (common LLM behavior)
    print("📋 Example 2: JSON with Explanatory Text")
    example2 = '''I'll help you search for that information. Let me use the search plugin to find current data.

```json
{
  "action": "plugin_invoke",
  "content": {
    "plugin": "brave-search",
    "input": {"query": "artificial intelligence developments 2024"},
    "reason": "User wants current information about AI developments"
  }
}
```

This will help me provide you with the most up-to-date information available.'''
    
    print("Input:")
    print(example2[:200] + "..." if len(example2) > 200 else example2)
    print("\nResult:")
    try:
        result = protocol.parse_response(example2)
        print(f"✅ Successfully parsed: {result['action']} -> {result['content']['plugin']}")
        print(f"   Query: {result['content']['input']['query']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    # Example 3: Generic code block (no 'json' label)
    print("📋 Example 3: Generic Code Block")
    example3 = '''Here's my response:

```
{
  "action": "message",
  "content": {
    "text": "I've processed your request successfully!",
    "markdown": true
  }
}
```'''
    
    print("Input:")
    print(example3)
    print("\nResult:")
    try:
        result = protocol.parse_response(example3)
        print(f"✅ Successfully parsed: {result['action']}")
        print(f"   Message: {result['content']['text']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    # Example 4: Multiple JSON blocks (picks the valid one)
    print("📋 Example 4: Multiple JSON Blocks (Schema-aware selection)")
    example4 = '''Let me try a few approaches. First, here's an invalid structure:

```json
{"incomplete": "missing required fields"}
```

Now here's the correct response:

```json
{
  "action": "message",
  "content": {
    "text": "Found the correct approach!",
    "markdown": false
  }
}
```'''
    
    print("Input:")
    print(example4[:300] + "..." if len(example4) > 300 else example4)
    print("\nResult:")
    try:
        result = protocol.parse_response(example4)
        print(f"✅ Successfully parsed: {result['action']}")
        print(f"   Message: {result['content']['text']}")
        print("   Note: Automatically selected the schema-valid JSON block!")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    # Example 5: Fallback behavior for pure text
    print("📋 Example 5: Fallback Behavior for Pure Text")
    example5 = "This is just plain text with no JSON structure at all."
    
    print("Input:")
    print(example5)
    print("\nResult:")
    try:
        result, error = protocol.parse_response_with_fallback(example5)
        if error:
            print(f"✅ Graceful fallback: {result['action']}")
            print(f"   Fallback message: {result['content']['text']}")
            print(f"   Error type: {error.error_type}")
        else:
            print(f"✅ Parsed normally: {result}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    print("🎉 Demo completed! The enhanced parser can handle:")
    print("   • Markdown-wrapped JSON (```json and ```)")
    print("   • JSON embedded in explanatory text")
    print("   • Multiple JSON blocks (selects valid ones)")
    print("   • Complex nested JSON structures")
    print("   • Graceful fallback for non-JSON content")
    print("   • Full backward compatibility")
    print()
    print("🔗 This fixes the issue described in GitHub #66")

if __name__ == "__main__":
    demo_parsing()