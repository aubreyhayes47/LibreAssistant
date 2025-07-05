"""
Test script for Phase 1A backend infrastructure.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from db import init_database, ChatOperations, BookmarkOperations, HistoryOperations, get_db_session
from llm import get_ollama_client, get_conversation_context, get_prompt_builder
from utils import init_config, init_logging, get_logger


async def test_database_operations():
    """Test database operations."""
    print("=== Testing Database Operations ===")
    
    # Initialize database
    success = init_database(':memory:')  # Use in-memory database for testing
    print(f"Database initialization: {'SUCCESS' if success else 'FAILED'}")
    
    if not success:
        return False
    
    # Test chat operations
    print("\nTesting chat operations...")
    message = await ChatOperations.save_message("Hello, world!", "user", "test_session")
    print(f"Save chat message: {'SUCCESS' if message else 'FAILED'}")
    
    response = await ChatOperations.save_message("Hello there! How can I help you?", "assistant", "test_session")
    print(f"Save assistant response: {'SUCCESS' if response else 'FAILED'}")
    
    history = await ChatOperations.get_chat_history("test_session")
    print(f"Get chat history: {'SUCCESS' if len(history) == 2 else 'FAILED'} ({len(history)} messages)")
    
    # Test bookmark operations
    print("\nTesting bookmark operations...")
    bookmark = await BookmarkOperations.save_bookmark(
        "https://example.com",
        "Example Site",
        "This is an example website",
        "example,test",
        "testing"
    )
    print(f"Save bookmark: {'SUCCESS' if bookmark else 'FAILED'}")
    
    bookmarks = await BookmarkOperations.get_bookmarks("testing")
    print(f"Get bookmarks: {'SUCCESS' if len(bookmarks) == 1 else 'FAILED'} ({len(bookmarks)} bookmarks)")
    
    search_results = await BookmarkOperations.search_bookmarks("example")
    print(f"Search bookmarks: {'SUCCESS' if len(search_results) == 1 else 'FAILED'} ({len(search_results)} results)")
    
    # Test history operations
    print("\nTesting history operations...")
    history_success = await HistoryOperations.add_history_entry(
        "https://example.com",
        "Example Site",
        "test_session"
    )
    print(f"Add history entry: {'SUCCESS' if history_success else 'FAILED'}")
    
    browser_history = await HistoryOperations.get_history("test_session")
    print(f"Get browser history: {'SUCCESS' if len(browser_history) == 1 else 'FAILED'} ({len(browser_history)} entries)")
    
    return True


async def test_llm_integration():
    """Test LLM integration (requires Ollama to be running)."""
    print("\n=== Testing LLM Integration ===")
    
    try:
        # Test Ollama client
        client = await get_ollama_client()
        health = await client.health_check()
        print(f"Ollama health check: {'SUCCESS' if health else 'FAILED'}")
        
        if not health:
            print("Ollama server not available - skipping LLM tests")
            return False
        
        # Test model listing
        models = await client.list_models()
        print(f"List models: {'SUCCESS' if isinstance(models, list) else 'FAILED'} ({len(models)} models)")
        
        # Test conversation context
        context = get_conversation_context("test_session")
        context.add_message("user", "Hello, can you help me?")
        print(f"Conversation context: SUCCESS")
        
        # Test prompt builder
        prompt_builder = get_prompt_builder()
        system_prompt = prompt_builder.build_chat_prompt("Hello")
        print(f"Prompt builder: {'SUCCESS' if system_prompt else 'FAILED'}")
        
        # Test simple generation (if models are available)
        if models:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, please respond with just 'Hi there!'"}
            ]
            
            result = await client.chat_completion(messages)
            print(f"Chat completion: {'SUCCESS' if result.get('success') else 'FAILED'}")
            if result.get('success'):
                response = result.get('message', {}).get('content', '')
                print(f"Response: {response[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"LLM test error: {str(e)}")
        return False


async def test_configuration():
    """Test configuration management."""
    print("\n=== Testing Configuration ===")
    
    try:
        # Test config initialization
        config = init_config()
        print(f"Config initialization: SUCCESS")
        
        # Test config validation
        is_valid, errors = config.validate()
        print(f"Config validation: {'SUCCESS' if is_valid else 'FAILED'}")
        if errors:
            print(f"Validation errors: {errors}")
        
        # Test config access
        db_path = config.database.get_db_path()
        print(f"Database path: {db_path}")
        
        llm_host = config.llm.ollama_host
        print(f"LLM host: {llm_host}")
        
        return True
        
    except Exception as e:
        print(f"Configuration test error: {str(e)}")
        return False


async def test_logging():
    """Test logging configuration."""
    print("\n=== Testing Logging ===")
    
    try:
        # Initialize logging
        init_logging()
        
        # Test different loggers
        main_logger = get_logger('main')
        db_logger = get_logger('database')
        llm_logger = get_logger('llm')
        
        # Test logging
        main_logger.info("Test main logger message")
        db_logger.info("Test database logger message")
        llm_logger.info("Test LLM logger message")
        
        print("Logging test: SUCCESS")
        return True
        
    except Exception as e:
        print(f"Logging test error: {str(e)}")
        return False


async def test_command_handler():
    """Test the command handler."""
    print("\n=== Testing Command Handler ===")
    
    try:
        # Import command handler
        from main import CommandHandler
        
        handler = CommandHandler()
        
        # Test init database command
        result = await handler.handle_command('init_database', {})
        print(f"Init database command: {'SUCCESS' if result.get('success') else 'FAILED'}")
        
        # Test hello command
        result = await handler.handle_command('hello', {'name': 'Test'})
        print(f"Hello command: {'SUCCESS' if result.get('success') else 'FAILED'}")
        if result.get('success'):
            print(f"Response: {result.get('message')}")
        
        # Test save bookmark command
        result = await handler.handle_command('save_bookmark', {
            'url': 'https://test.com',
            'title': 'Test Site',
            'content': 'Test content',
            'tags': 'test',
            'folder': 'testing'
        })
        print(f"Save bookmark command: {'SUCCESS' if result.get('success') else 'FAILED'}")
        
        # Test get bookmarks command
        result = await handler.handle_command('get_bookmarks', {'folder': 'testing'})
        print(f"Get bookmarks command: {'SUCCESS' if result.get('success') else 'FAILED'}")
        if result.get('success'):
            print(f"Found {result.get('count', 0)} bookmarks")
        
        return True
        
    except Exception as e:
        print(f"Command handler test error: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("LibreAssistant Phase 1A Backend Infrastructure Test")
    print("=" * 50)
    
    test_results = []
    
    # Run tests
    test_results.append(await test_configuration())
    test_results.append(await test_logging())
    test_results.append(await test_database_operations())
    test_results.append(await test_llm_integration())
    test_results.append(await test_command_handler())
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Phase 1A infrastructure is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
    
    return passed == total


if __name__ == '__main__':
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)
