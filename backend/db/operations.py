"""
Database CRUD operations for LibreAssistant.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_

# Use absolute imports when running as main module
try:
    from .database import get_db_session
    from .models import (
        BookmarkEntry,
        BrowserHistory,
        ChatMessage,
        PageSummary,
        UserSettings,
    )
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from db.database import get_db_session
    from db.models import (
        BookmarkEntry,
        BrowserHistory,
        ChatMessage,
        PageSummary,
        UserSettings,
    )

logger = logging.getLogger(__name__)


class ChatOperations:
    """CRUD operations for chat messages."""

    @staticmethod
    async def save_message(
        content: str, role: str, session_id: str = "default"
    ) -> Optional[ChatMessage]:
        """Save a chat message to the database."""
        try:
            with get_db_session() as db:
                message = ChatMessage(
                    content=content,
                    role=role,
                    session_id=session_id,
                    timestamp=datetime.utcnow(),
                )
                db.add(message)
                db.flush()  # Get the ID without committing

                # Return a detached copy
                result = ChatMessage(
                    id=message.id,
                    content=message.content,
                    role=message.role,
                    session_id=message.session_id,
                    timestamp=message.timestamp,
                )
                return result
        except Exception as e:
            logger.error(f"Failed to save chat message: {str(e)}")
            return None

    @staticmethod
    async def get_chat_history(
        session_id: str = "default", limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get chat history for a session."""
        try:
            with get_db_session() as db:
                messages = (
                    db.query(ChatMessage)
                    .filter(ChatMessage.session_id == session_id)
                    .order_by(desc(ChatMessage.timestamp))
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "id": msg.id,
                        "content": msg.content,
                        "role": msg.role,
                        "timestamp": msg.timestamp.isoformat(),
                        "session_id": msg.session_id,
                    }
                    for msg in reversed(messages)  # Return in chronological order
                ]
        except Exception as e:
            logger.error(f"Failed to get chat history: {str(e)}")
            return []

    @staticmethod
    async def delete_message(message_id: int) -> bool:
        """Delete a chat message."""
        try:
            with get_db_session() as db:
                message = (
                    db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
                )
                if message:
                    db.delete(message)
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete chat message: {str(e)}")
            return False

    @staticmethod
    async def get_sessions() -> List[Dict[str, Any]]:
        """Get all chat sessions with metadata."""
        try:
            with get_db_session() as db:
                sessions = (
                    db.query(
                        ChatMessage.session_id,
                        func.count(ChatMessage.id).label("message_count"),
                        func.max(ChatMessage.timestamp).label("last_activity"),
                    )
                    .group_by(ChatMessage.session_id)
                    .order_by(desc("last_activity"))
                    .all()
                )

                return [
                    {
                        "session_id": session.session_id,
                        "message_count": session.message_count,
                        "last_activity": session.last_activity.isoformat(),
                    }
                    for session in sessions
                ]
        except Exception as e:
            logger.error(f"Failed to get chat sessions: {str(e)}")
            return []


class BookmarkOperations:
    """CRUD operations for bookmarks."""

    @staticmethod
    async def save_bookmark(
        url: str,
        title: str = None,
        content: str = None,
        tags: str = None,
        folder: str = "default",
    ) -> Optional[BookmarkEntry]:
        """Save a bookmark to the database."""
        try:
            with get_db_session() as db:
                # Check if bookmark already exists
                existing = (
                    db.query(BookmarkEntry).filter(BookmarkEntry.url == url).first()
                )
                if existing:
                    # Update existing bookmark
                    if title:
                        existing.title = title
                    if content:
                        existing.content = content
                    if tags:
                        existing.tags = tags
                    existing.folder = folder
                    existing.timestamp = datetime.utcnow()
                    return existing

                bookmark = BookmarkEntry(
                    url=url,
                    title=title,
                    content=content,
                    tags=tags,
                    folder=folder,
                    timestamp=datetime.utcnow(),
                )
                db.add(bookmark)
                db.flush()

                result = BookmarkEntry(
                    id=bookmark.id,
                    url=bookmark.url,
                    title=bookmark.title,
                    content=bookmark.content,
                    tags=bookmark.tags,
                    folder=bookmark.folder,
                    timestamp=bookmark.timestamp,
                )
                return result
        except Exception as e:
            logger.error(f"Failed to save bookmark: {str(e)}")
            return None

    @staticmethod
    async def get_bookmarks(
        folder: str = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get bookmarks, optionally filtered by folder."""
        try:
            with get_db_session() as db:
                query = db.query(BookmarkEntry)
                if folder:
                    query = query.filter(BookmarkEntry.folder == folder)

                bookmarks = (
                    query.order_by(desc(BookmarkEntry.timestamp)).limit(limit).all()
                )

                return [
                    {
                        "id": bm.id,
                        "url": bm.url,
                        "title": bm.title,
                        "content": (
                            bm.content[:500] if bm.content else None
                        ),  # Truncate content
                        "tags": bm.tags,
                        "folder": bm.folder,
                        "timestamp": bm.timestamp.isoformat(),
                    }
                    for bm in bookmarks
                ]
        except Exception as e:
            logger.error(f"Failed to get bookmarks: {str(e)}")
            return []

    @staticmethod
    async def search_bookmarks(query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search bookmarks by title, content, or tags."""
        try:
            with get_db_session() as db:
                search_term = f"%{query}%"
                bookmarks = (
                    db.query(BookmarkEntry)
                    .filter(
                        or_(
                            BookmarkEntry.title.like(search_term),
                            BookmarkEntry.content.like(search_term),
                            BookmarkEntry.tags.like(search_term),
                        )
                    )
                    .order_by(desc(BookmarkEntry.timestamp))
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "id": bm.id,
                        "url": bm.url,
                        "title": bm.title,
                        "content": bm.content[:500] if bm.content else None,
                        "tags": bm.tags,
                        "folder": bm.folder,
                        "timestamp": bm.timestamp.isoformat(),
                    }
                    for bm in bookmarks
                ]
        except Exception as e:
            logger.error(f"Failed to search bookmarks: {str(e)}")
            return []

    @staticmethod
    async def delete_bookmark(bookmark_id: int) -> bool:
        """Delete a bookmark."""
        try:
            with get_db_session() as db:
                bookmark = (
                    db.query(BookmarkEntry)
                    .filter(BookmarkEntry.id == bookmark_id)
                    .first()
                )
                if bookmark:
                    db.delete(bookmark)
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete bookmark: {str(e)}")
            return False


class HistoryOperations:
    """CRUD operations for browser history."""

    @staticmethod
    async def add_history_entry(
        url: str, title: str = None, session_id: str = "default"
    ) -> bool:
        """Add or update a history entry."""
        try:
            with get_db_session() as db:
                # Check if URL was visited recently (within last hour)
                recent_cutoff = datetime.utcnow() - timedelta(hours=1)
                existing = (
                    db.query(BrowserHistory)
                    .filter(
                        and_(
                            BrowserHistory.url == url,
                            BrowserHistory.session_id == session_id,
                            BrowserHistory.visit_time > recent_cutoff,
                        )
                    )
                    .first()
                )

                if existing:
                    # Update existing entry
                    existing.visit_count += 1
                    existing.visit_time = datetime.utcnow()
                    if title:
                        existing.title = title
                else:
                    # Create new entry
                    history = BrowserHistory(
                        url=url,
                        title=title,
                        session_id=session_id,
                        visit_time=datetime.utcnow(),
                        visit_count=1,
                    )
                    db.add(history)

                return True
        except Exception as e:
            logger.error(f"Failed to add history entry: {str(e)}")
            return False

    @staticmethod
    async def get_history(
        session_id: str = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get browser history."""
        try:
            with get_db_session() as db:
                query = db.query(BrowserHistory)
                if session_id:
                    query = query.filter(BrowserHistory.session_id == session_id)

                history = (
                    query.order_by(desc(BrowserHistory.visit_time)).limit(limit).all()
                )

                return [
                    {
                        "id": h.id,
                        "url": h.url,
                        "title": h.title,
                        "visit_time": h.visit_time.isoformat(),
                        "session_id": h.session_id,
                        "visit_count": h.visit_count,
                    }
                    for h in history
                ]
        except Exception as e:
            logger.error(f"Failed to get history: {str(e)}")
            return []

    @staticmethod
    async def search_history(query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search browser history by URL or title."""
        try:
            with get_db_session() as db:
                search_term = f"%{query}%"
                history = (
                    db.query(BrowserHistory)
                    .filter(
                        or_(
                            BrowserHistory.url.like(search_term),
                            BrowserHistory.title.like(search_term),
                        )
                    )
                    .order_by(desc(BrowserHistory.visit_time))
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "id": h.id,
                        "url": h.url,
                        "title": h.title,
                        "visit_time": h.visit_time.isoformat(),
                        "session_id": h.session_id,
                        "visit_count": h.visit_count,
                    }
                    for h in history
                ]
        except Exception as e:
            logger.error(f"Failed to search history: {str(e)}")
            return []


class SummaryOperations:
    """CRUD operations for page summaries."""

    @staticmethod
    async def save_summary(
        url: str, summary: str, content: str, model_used: str = None
    ) -> Optional[PageSummary]:
        """Save a page summary."""
        try:
            with get_db_session() as db:
                content_hash = PageSummary.generate_content_hash(content)

                # Check if summary already exists for this content
                existing = (
                    db.query(PageSummary)
                    .filter(
                        and_(
                            PageSummary.url == url,
                            PageSummary.content_hash == content_hash,
                        )
                    )
                    .first()
                )

                if existing:
                    return existing

                page_summary = PageSummary(
                    url=url,
                    summary=summary,
                    content_hash=content_hash,
                    model_used=model_used,
                    created_at=datetime.utcnow(),
                )
                db.add(page_summary)
                db.flush()

                result = PageSummary(
                    id=page_summary.id,
                    url=page_summary.url,
                    summary=page_summary.summary,
                    content_hash=page_summary.content_hash,
                    model_used=page_summary.model_used,
                    created_at=page_summary.created_at,
                )
                return result
        except Exception as e:
            logger.error(f"Failed to save summary: {str(e)}")
            return None

    @staticmethod
    async def get_summary(
        url: str, content_hash: str = None
    ) -> Optional[Dict[str, Any]]:
        """Get a page summary by URL and optionally content hash."""
        try:
            with get_db_session() as db:
                query = db.query(PageSummary).filter(PageSummary.url == url)
                if content_hash:
                    query = query.filter(PageSummary.content_hash == content_hash)

                summary = query.order_by(desc(PageSummary.created_at)).first()

                if summary:
                    return {
                        "id": summary.id,
                        "url": summary.url,
                        "summary": summary.summary,
                        "content_hash": summary.content_hash,
                        "model_used": summary.model_used,
                        "created_at": summary.created_at.isoformat(),
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get summary: {str(e)}")
            return None


class SettingsOperations:
    """CRUD operations for user settings."""

    @staticmethod
    async def set_setting(key: str, value: str, category: str = "general") -> bool:
        """Set a user setting."""
        try:
            with get_db_session() as db:
                setting = db.query(UserSettings).filter(UserSettings.key == key).first()
                if setting:
                    setting.value = value
                    setting.category = category
                    setting.updated_at = datetime.utcnow()
                else:
                    setting = UserSettings(
                        key=key,
                        value=value,
                        category=category,
                        updated_at=datetime.utcnow(),
                    )
                    db.add(setting)
                return True
        except Exception as e:
            logger.error(f"Failed to set setting: {str(e)}")
            return False

    @staticmethod
    async def get_setting(key: str, default: str = None) -> Optional[str]:
        """Get a user setting value."""
        try:
            with get_db_session() as db:
                setting = db.query(UserSettings).filter(UserSettings.key == key).first()
                return setting.value if setting else default
        except Exception as e:
            logger.error(f"Failed to get setting: {str(e)}")
            return default

    @staticmethod
    async def get_settings_by_category(category: str) -> Dict[str, str]:
        """Get all settings in a category."""
        try:
            with get_db_session() as db:
                settings = (
                    db.query(UserSettings)
                    .filter(UserSettings.category == category)
                    .all()
                )

                return {setting.key: setting.value for setting in settings}
        except Exception as e:
            logger.error(f"Failed to get settings by category: {str(e)}")
            return {}
