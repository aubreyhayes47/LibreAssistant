"""
SQLAlchemy models for LibreAssistant database.

This module defines the complete database schema for LibreAssistant,
including models for users, conversations, messages, search history,
content caching, and user settings.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index, Integer, 
    String, Text, Float, JSON, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


class User(Base):
    """
    Single user configuration and metadata storage.
    LibreAssistant is single-user, but this allows for user preferences
    and configuration management.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True, default="user")
    display_name = Column(String(200), nullable=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # User preferences stored as JSON
    preferences = Column(JSON, nullable=True, default=dict)
    
    # Privacy and security settings
    data_retention_days = Column(Integer, default=365, nullable=False)
    auto_cleanup_enabled = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_username", "username"),
        Index("idx_last_active", "last_active"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Conversation(Base):
    """
    Conversation sessions with metadata and context preservation.
    Each conversation represents a distinct chat session.
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), nullable=False, unique=True, default=lambda: str(uuid4()))
    title = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Conversation metadata
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=True)
    context_window_size = Column(Integer, default=4096, nullable=False)
    
    # Conversation state
    is_active = Column(Boolean, default=True, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    
    # AI model information
    model_name = Column(String(100), nullable=True)
    model_parameters = Column(JSON, nullable=True, default=dict)
    
    # Context and summary
    context_summary = Column(Text, nullable=True)
    tags = Column(String(1000), nullable=True)  # Comma-separated tags
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message", 
        back_populates="conversation", 
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_user_updated", "user_id", "updated_at"),
        Index("idx_uuid", "uuid"),
        Index("idx_active_conversations", "user_id", "is_active"),
        Index("idx_archived_conversations", "user_id", "is_archived"),
    )
    
    @hybrid_property
    def duration_minutes(self):
        """Calculate conversation duration in minutes."""
        if self.updated_at and self.created_at:
            delta = self.updated_at - self.created_at
            return int(delta.total_seconds() / 60)
        return 0

    def __repr__(self):
        return f"<Conversation(id={self.id}, uuid='{self.uuid}', title='{self.title}')>"


class Message(Base):
    """
    Individual messages within conversations.
    Stores both user messages and AI responses with metadata.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), nullable=False, unique=True, default=lambda: str(uuid4()))
    
    # Foreign key to conversation
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    
    # Message content and metadata
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Message ordering and threading
    sequence_number = Column(Integer, nullable=False)
    parent_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    
    # AI generation metadata (for assistant messages)
    model_name = Column(String(100), nullable=True)
    generation_time_ms = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    
    # Content processing metadata
    content_hash = Column(String(64), nullable=True)
    is_edited = Column(Boolean, default=False, nullable=False)
    edit_count = Column(Integer, default=0, nullable=False)
    
    # Search and web integration
    has_web_search = Column(Boolean, default=False, nullable=False)
    search_queries = Column(JSON, nullable=True)  # List of search queries used
    sources_used = Column(JSON, nullable=True)   # List of sources referenced
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    parent_message = relationship("Message", remote_side=[id], backref="child_messages")
    
    # Indexes
    __table_args__ = (
        Index("idx_conversation_sequence", "conversation_id", "sequence_number"),
        Index("idx_conversation_created", "conversation_id", "created_at"),
        Index("idx_role_created", "role", "created_at"),
        Index("idx_content_hash", "content_hash"),
        UniqueConstraint("conversation_id", "sequence_number", name="uq_conversation_sequence"),
    )
    
    @staticmethod
    def generate_content_hash(content: str) -> str:
        """Generate SHA-256 hash of message content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', seq={self.sequence_number})>"


class SearchHistory(Base):
    """
    Web search queries and results with caching and analytics.
    Tracks search patterns and caches results for performance.
    """
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Search query and metadata
    query = Column(Text, nullable=False)
    query_hash = Column(String(64), nullable=False)
    search_provider = Column(String(50), nullable=False, default="duckduckgo")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Search execution metadata
    execution_time_ms = Column(Integer, nullable=True)
    results_count = Column(Integer, nullable=False, default=0)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Search context
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    
    # Search parameters
    search_parameters = Column(JSON, nullable=True, default=dict)
    
    # Results caching (summary)
    results_summary = Column(Text, nullable=True)
    top_results = Column(JSON, nullable=True)  # Top 5-10 results for quick access
    
    # Relationships
    user = relationship("User", back_populates="search_history")
    conversation = relationship("Conversation")
    message = relationship("Message")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
        Index("idx_query_hash", "query_hash"),
        Index("idx_conversation_search", "conversation_id", "created_at"),
        Index("idx_search_provider", "search_provider"),
    )
    
    @staticmethod
    def generate_query_hash(query: str) -> str:
        """Generate SHA-256 hash of search query for deduplication."""
        normalized_query = query.lower().strip()
        return hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()

    def __repr__(self):
        return f"<SearchHistory(id={self.id}, query='{self.query[:50]}...', provider='{self.search_provider}')>"


class ContentCache(Base):
    """
    Cached web content with expiration and deduplication.
    Stores scraped content to avoid repeated requests.
    """
    __tablename__ = "content_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # URL and content identification
    url = Column(String(2048), nullable=False)
    url_hash = Column(String(64), nullable=False, unique=True)
    content_hash = Column(String(64), nullable=False)
    
    # Content data
    title = Column(String(1000), nullable=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(100), nullable=False, default="text/html")
    content_length = Column(Integer, nullable=False)
    
    # Caching metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    access_count = Column(Integer, default=1, nullable=False)
    
    # Scraping metadata
    scraping_method = Column(String(50), nullable=False, default="requests")
    user_agent = Column(String(500), nullable=True)
    status_code = Column(Integer, nullable=True)
    response_headers = Column(JSON, nullable=True)
    
    # Content processing
    is_processed = Column(Boolean, default=False, nullable=False)
    processing_error = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    content_metadata = Column(JSON, nullable=True, default=dict)
    
    # Indexes
    __table_args__ = (
        Index("idx_url_hash", "url_hash"),
        Index("idx_content_hash", "content_hash"),
        Index("idx_expires_at", "expires_at"),
        Index("idx_last_accessed", "last_accessed"),
        Index("idx_created_at", "created_at"),
    )
    
    @staticmethod
    def generate_url_hash(url: str) -> str:
        """Generate SHA-256 hash of URL for indexing."""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()
    
    @staticmethod
    def generate_content_hash(content: str) -> str:
        """Generate SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    @hybrid_property
    def is_expired(self):
        """Check if cached content is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def extend_expiry(self, hours: int = 24):
        """Extend cache expiry by specified hours."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def touch_access(self):
        """Update last accessed time and increment access count."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1

    def __repr__(self):
        return f"<ContentCache(id={self.id}, url='{self.url[:50]}...', expires='{self.expires_at}')>"


class UserSettings(Base):
    """
    User preferences and configuration key-value storage.
    Provides flexible configuration management with categories and validation.
    """
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Setting identification
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="general")
    
    # Setting metadata
    value_type = Column(String(20), nullable=False, default="string")  # string, int, float, bool, json
    is_encrypted = Column(Boolean, default=False, nullable=False)
    is_user_modifiable = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Validation and constraints
    validation_rules = Column(JSON, nullable=True)  # JSON schema for validation
    default_value = Column(Text, nullable=True)
    description = Column(String(500), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="settings")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_user_key", "user_id", "key"),
        Index("idx_category", "category"),
        Index("idx_user_category", "user_id", "category"),
        UniqueConstraint("user_id", "key", name="uq_user_setting_key"),
    )
    
    def get_typed_value(self) -> Any:
        """
        Return the setting value converted to its proper type.
        """
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes", "on")
        elif self.value_type == "json":
            return json.loads(self.value)
        else:
            return self.value
    
    def set_typed_value(self, value: Any) -> None:
        """
        Set the setting value with automatic type conversion.
        """
        if self.value_type == "json":
            self.value = json.dumps(value)
        else:
            self.value = str(value)
    
    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, key='{self.key}', category='{self.category}')>"


# Additional utility models for specific LibreAssistant features

class BookmarkEntry(Base):
    """
    User bookmarks with metadata and content caching.
    Extends basic bookmark functionality with AI-powered features.
    """
    __tablename__ = "bookmark_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Bookmark data
    url = Column(String(2048), nullable=False)
    title = Column(String(1000), nullable=True)
    description = Column(Text, nullable=True)
    favicon_url = Column(String(2048), nullable=True)
    
    # Organization
    folder = Column(String(200), nullable=True, default="default")
    tags = Column(String(1000), nullable=True)  # Comma-separated tags
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    last_visited = Column(DateTime, nullable=True)
    
    # Content caching reference
    cached_content_id = Column(Integer, ForeignKey("content_cache.id"), nullable=True)
    
    # AI-generated metadata
    ai_summary = Column(Text, nullable=True)
    ai_tags = Column(String(1000), nullable=True)
    content_type = Column(String(100), nullable=True)
    
    # Usage statistics
    visit_count = Column(Integer, default=0, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User")
    cached_content = relationship("ContentCache")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_folder", "user_id", "folder"),
        Index("idx_user_created", "user_id", "created_at"),
        Index("idx_url", "url"),
        Index("idx_tags", "tags"),
    )

    def __repr__(self):
        return f"<BookmarkEntry(id={self.id}, title='{self.title}', folder='{self.folder}')>"


class BrowserHistory(Base):
    """
    Browser navigation history with privacy controls.
    Tracks page visits for context and recommendations.
    """
    __tablename__ = "browser_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Visit data
    url = Column(String(2048), nullable=False)
    title = Column(String(1000), nullable=True)
    visit_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Session and context
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    session_id = Column(String(100), nullable=False, default="default")
    
    # Visit metadata
    visit_duration_seconds = Column(Integer, nullable=True)
    referrer_url = Column(String(2048), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Privacy and cleanup
    is_private = Column(Boolean, default=False, nullable=False)
    auto_delete_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")
    conversation = relationship("Conversation")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_visit_time", "user_id", "visit_time"),
        Index("idx_url_visit_time", "url", "visit_time"),
        Index("idx_session_visit_time", "session_id", "visit_time"),
        Index("idx_auto_delete", "auto_delete_at"),
    )

    def __repr__(self):
        return f"<BrowserHistory(id={self.id}, url='{self.url[:50]}...', visit_time='{self.visit_time}')>"


class PageSummary(Base):
    """
    AI-generated summaries and analysis of web pages.
    Links content analysis to conversations and bookmarks.
    """
    __tablename__ = "page_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Content identification
    url = Column(String(2048), nullable=False)
    content_hash = Column(String(64), nullable=False)
    
    # AI-generated content
    summary = Column(Text, nullable=False)
    key_points = Column(JSON, nullable=True)  # List of key points
    entities = Column(JSON, nullable=True)    # Named entities found
    sentiment = Column(String(20), nullable=True)  # positive, negative, neutral
    
    # Generation metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    model_used = Column(String(100), nullable=True)
    generation_time_ms = Column(Integer, nullable=True)
    
    # Context relationships
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    bookmark_id = Column(Integer, ForeignKey("bookmark_entries.id"), nullable=True)
    cached_content_id = Column(Integer, ForeignKey("content_cache.id"), nullable=True)
    
    # Quality and usage metrics
    quality_score = Column(Float, nullable=True)  # 0.0 to 1.0
    usage_count = Column(Integer, default=0, nullable=False)
    last_used = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation")
    bookmark = relationship("BookmarkEntry", backref="summaries")
    cached_content = relationship("ContentCache")
    
    # Indexes
    __table_args__ = (
        Index("idx_url_hash", "url", "content_hash"),
        Index("idx_content_hash", "content_hash"),
        Index("idx_conversation_summary", "conversation_id", "created_at"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<PageSummary(id={self.id}, url='{self.url[:50]}...', model='{self.model_used}')>"


# Export all models for easy imports
__all__ = [
    "Base",
    "User", 
    "Conversation", 
    "Message", 
    "SearchHistory", 
    "ContentCache", 
    "UserSettings",
    "BookmarkEntry",
    "BrowserHistory", 
    "PageSummary"
]
