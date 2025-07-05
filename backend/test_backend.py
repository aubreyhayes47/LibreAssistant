import json
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import CommandHandler

async def test_backend():
    handler = CommandHandler()
    
    # Test hello command
    payload = {"name": "Test User", "timestamp": "123456"}
    result = await handler.handle_command("hello", payload)
    print("Hello command result:")
    print(json.dumps(result, indent=2))
    
    # Test process_url command
    payload = {"url": "https://example.com"}
    result = await handler.handle_command("process_url", payload)
    print("\nProcess URL command result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(test_backend())
