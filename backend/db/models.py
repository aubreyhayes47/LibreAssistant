"""
SQLAlchemy models for LibreAssistant database.
"""

import hashlib
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ChatMessage(Base):
    """Stores chat messages between user and assistant."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    session_id = Column(String(100), nullable=False, default="default")

    # Indexes for better query performance
    __table_args__ = (
        Index("idx_session_timestamp", "session_id", "timestamp"),
        Index("idx_role_timestamp", "role", "timestamp"),
    )

    def __repr__(self):
        return (
            f"<ChatMessage(id={self.id}, role='{self.role}', "
            f"session='{self.session_id}')>"
        )


class BookmarkEntry(Base):
    """Stores user bookmarks with metadata."""

    __tablename__ = "bookmark_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)  # Extracted page content
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    folder = Column(String(100), nullable=True, default="default")

    # Indexes for search and organization
    __table_args__ = (
        Index("idx_url", "url"),
        Index("idx_folder_timestamp", "folder", "timestamp"),
        Index("idx_title", "title"),
    )

    def __repr__(self):
        return f"<BookmarkEntry(id={self.id}, title='{self.title}', url='{self.url}')>"


class BrowserHistory(Base):
    """Stores browser navigation history."""

    __tablename__ = "browser_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False)
    title = Column(String(500), nullable=True)
    visit_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    session_id = Column(String(100), nullable=False, default="default")
    visit_count = Column(Integer, default=1, nullable=False)

    # Indexes for history queries
    __table_args__ = (
        Index("idx_url_visit_time", "url", "visit_time"),
        Index("idx_session_visit_time", "session_id", "visit_time"),
        Index("idx_visit_time", "visit_time"),
    )

    def __repr__(self):
        return (
            f"<BrowserHistory(id={self.id}, url='{self.url}', "
            f"visit_time='{self.visit_time}')>"
        )


class PageSummary(Base):
    """Stores AI-generated summaries of web pages."""

    __tablename__ = "page_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False)
    summary = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)  # SHA-256 hash of content
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    model_used = Column(String(100), nullable=True)  # LLM model used for summary

    # Relationship to bookmarks (optional)
    bookmark_id = Column(Integer, ForeignKey("bookmark_entries.id"), nullable=True)
    bookmark = relationship("BookmarkEntry", backref="summaries")

    # Indexes for content deduplication and retrieval
    __table_args__ = (
        Index("idx_url_hash", "url", "content_hash"),
        Index("idx_content_hash", "content_hash"),
        Index("idx_created_at", "created_at"),
    )

    @staticmethod
    def generate_content_hash(content: str) -> str:
        """Generate SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def __repr__(self):
        return (
            f"<PageSummary(id={self.id}, url='{self.url}', "
            f"hash='{self.content_hash[:8]}...')>"
        )


class UserSettings(Base):
    """Stores user preferences and configuration."""

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="general")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Index for fast settings lookup
    __table_args__ = (
        Index("idx_key", "key"),
        Index("idx_category", "category"),
    )

    def __repr__(self):
        return f"<UserSettings(key='{self.key}', category='{self.category}')>"
