"""
Simple test script for backend functionality
"""

import json
import sys
import os
import asyncio

# Add the backend directory to the path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from main import CommandHandler

async def test_backend():
    """Test basic backend functionality"""
    handler = CommandHandler()
    
    print("🔄 Testing backend functionality...")
    
    # Test 1: Database initialization
    print("\n1. Testing database initialization...")
    result = await handler.init_database_command({})
    print(f"   Result: {result}")
    
    # Test 2: Chat with LLM (will likely fail without Ollama, but tests the flow)
    print("\n2. Testing LLM chat...")
    result = await handler.chat_with_llm_command({
        "message": "Hello, this is a test",
        "session_id": "test"
    })
    print(f"   Result: {result}")
    
    # Test 3: URL processing
    print("\n3. Testing URL processing...")
    result = await handler.process_url({
        "url": "https://example.com"
    })
    print(f"   Result: {result}")
    
    # Test 4: Browser history
    print("\n4. Testing browser history...")
    result = await handler.add_history_entry_command({
        "url": "https://test.com",
        "title": "Test Entry"
    })
    print(f"   Add history result: {result}")
    
    result = await handler.get_browser_history_command({})
    print(f"   Get history result: {result}")
    
    print("\n✅ Backend testing complete!")

if __name__ == "__main__":
    asyncio.run(test_backend())
