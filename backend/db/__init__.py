"""
Database package for LibreAssistant.
"""

from .database import DatabaseManager, close_database, get_db_session, init_database
from .models import (
    Base,
    BookmarkEntry,
    BrowserHistory,
    ChatMessage,
    PageSummary,
    UserSettings,
)
from .operations import (
    BookmarkOperations,
    ChatOperations,
    HistoryOperations,
    SettingsOperations,
    SummaryOperations,
)

__all__ = [
    "DatabaseManager",
    "init_database",
    "get_db_session",
    "close_database",
    "ChatMessage",
    "BookmarkEntry",
    "BrowserHistory",
    "PageSummary",
    "UserSettings",
    "Base",
    "ChatOperations",
    "BookmarkOperations",
    "HistoryOperations",
    "SummaryOperations",
    "SettingsOperations",
]
