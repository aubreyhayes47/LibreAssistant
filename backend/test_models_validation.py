#!/usr/bin/env python3
"""
Test script to validate the new SQLAlchemy models for LibreAssistant.
This script checks model structure, relationships, and basic functionality.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add backend to path for testing
sys.path.insert(0, str(Path(__file__).parent))

from db.models import (
    Base, User, Conversation, Message, SearchHistory, 
    ContentCache, UserSettings, BookmarkEntry, BrowserHistory, PageSummary
)


def test_model_structure():
    """Test that all models have the expected structure."""
    print("🔍 Testing model structure...")
    
    # Test User model
    user_columns = [column.name for column in User.__table__.columns]
    expected_user_columns = [
        'id', 'username', 'display_name', 'email', 'created_at', 
        'updated_at', 'last_active', 'preferences', 'data_retention_days', 
        'auto_cleanup_enabled'
    ]
    for col in expected_user_columns:
        assert col in user_columns, f"Missing column '{col}' in User model"
    print("  ✓ User model structure validated")
    
    # Test Conversation model
    conv_columns = [column.name for column in Conversation.__table__.columns]
    expected_conv_columns = [
        'id', 'uuid', 'title', 'created_at', 'updated_at', 'user_id',
        'message_count', 'is_active', 'model_name'
    ]
    for col in expected_conv_columns:
        assert col in conv_columns, f"Missing column '{col}' in Conversation model"
    print("  ✓ Conversation model structure validated")
    
    # Test Message model
    msg_columns = [column.name for column in Message.__table__.columns]
    expected_msg_columns = [
        'id', 'uuid', 'conversation_id', 'content', 'role', 'created_at',
        'sequence_number', 'model_name', 'token_count'
    ]
    for col in expected_msg_columns:
        assert col in msg_columns, f"Missing column '{col}' in Message model"
    print("  ✓ Message model structure validated")
    
    print("✅ All core model structures validated")


def test_relationships():
    """Test that model relationships are properly defined."""
    print("\n🔍 Testing model relationships...")
    
    # Test User relationships
    user_rels = [rel.key for rel in User.__mapper__.relationships]
    expected_user_rels = ['conversations', 'search_history', 'settings']
    for rel in expected_user_rels:
        assert rel in user_rels, f"Missing relationship '{rel}' in User model"
    print("  ✓ User relationships validated")
    
    # Test Conversation relationships
    conv_rels = [rel.key for rel in Conversation.__mapper__.relationships]
    expected_conv_rels = ['user', 'messages']
    for rel in expected_conv_rels:
        assert rel in conv_rels, f"Missing relationship '{rel}' in Conversation model"
    print("  ✓ Conversation relationships validated")
    
    # Test Message relationships
    msg_rels = [rel.key for rel in Message.__mapper__.relationships]
    expected_msg_rels = ['conversation', 'parent_message']
    for rel in expected_msg_rels:
        assert rel in msg_rels, f"Missing relationship '{rel}' in Message model"
    print("  ✓ Message relationships validated")
    
    print("✅ All model relationships validated")


def test_indexes():
    """Test that proper indexes are defined."""
    print("\n🔍 Testing database indexes...")
    
    # Test User indexes
    user_indexes = [idx.name for idx in User.__table__.indexes]
    assert any('username' in idx.name for idx in User.__table__.indexes), "Missing username index"
    print("  ✓ User indexes validated")
    
    # Test Conversation indexes
    conv_indexes = [idx.name for idx in Conversation.__table__.indexes]
    assert any('user' in idx.name for idx in Conversation.__table__.indexes), "Missing user index"
    print("  ✓ Conversation indexes validated")
    
    # Test Message indexes with sequence
    msg_indexes = [idx.name for idx in Message.__table__.indexes]
    assert any('conversation' in idx.name for idx in Message.__table__.indexes), "Missing conversation index"
    print("  ✓ Message indexes validated")
    
    print("✅ All indexes validated")


def test_utility_methods():
    """Test utility methods and properties."""
    print("\n🔍 Testing utility methods...")
    
    # Test hash generation methods
    content_hash = ContentCache.generate_content_hash("test content")
    assert len(content_hash) == 64, "Content hash should be 64 characters (SHA-256)"
    print("  ✓ ContentCache hash generation validated")
    
    url_hash = ContentCache.generate_url_hash("https://example.com")
    assert len(url_hash) == 64, "URL hash should be 64 characters (SHA-256)"
    print("  ✓ ContentCache URL hash generation validated")
    
    message_hash = Message.generate_content_hash("test message")
    assert len(message_hash) == 64, "Message hash should be 64 characters (SHA-256)"
    print("  ✓ Message hash generation validated")
    
    query_hash = SearchHistory.generate_query_hash("test query")
    assert len(query_hash) == 64, "Query hash should be 64 characters (SHA-256)"
    print("  ✓ SearchHistory hash generation validated")
    
    print("✅ All utility methods validated")


def test_model_creation():
    """Test that models can be instantiated with basic data."""
    print("\n🔍 Testing model instantiation...")
    
    # Test User creation
    user = User(
        username="testuser",
        display_name="Test User",
        email="test@example.com"
    )
    assert user.username == "testuser"
    # Note: Default values are set by database, not on instantiation
    print("  ✓ User instantiation validated")
    
    # Test Conversation creation
    conversation = Conversation(
        title="Test Conversation",
        user_id=1
    )
    assert conversation.title == "Test Conversation"
    # Note: Default values are set by database, not on instantiation
    print("  ✓ Conversation instantiation validated")
    
    # Test Message creation
    message = Message(
        conversation_id=1,
        content="Hello, world!",
        role="user",
        sequence_number=1
    )
    assert message.content == "Hello, world!"
    assert message.role == "user"
    # Note: Default values are set by database, not on instantiation
    print("  ✓ Message instantiation validated")
    
    print("✅ All model instantiation validated")


def main():
    """Run all validation tests."""
    print("🚀 Starting LibreAssistant Models Validation")
    print("=" * 50)
    
    try:
        test_model_structure()
        test_relationships()
        test_indexes()
        test_utility_methods()
        test_model_creation()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ LibreAssistant database models are ready for Step 2 of Phase 1.1")
        print("\nNext steps:")
        print("  1. Implement DatabaseManager class (Phase 1.1 Step 2)")
        print("  2. Create migration system (Phase 1.1 Step 3)")
        print("  3. Implement database service layer (Phase 1.1 Step 4)")
        
    except AssertionError as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
