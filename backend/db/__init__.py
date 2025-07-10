"""
Database package for LibreAssistant.
"""

from .database import DatabaseManager, close_database, get_db_session, init_database
from .models import (
    Base,
    User,
    Conversation,
    Message,
    SearchHistory,
    ContentCache,
    UserSettings,
    BookmarkEntry,
    BrowserHistory,
    PageSummary,
)
# TODO: Operations need to be rewritten for new schema
# from .operations import (
#     BookmarkOperations,
#     ChatOperations,
#     HistoryOperations,
#     SettingsOperations,
#     SummaryOperations,
# )

__all__ = [
    "DatabaseManager",
    "init_database", 
    "get_db_session",
    "close_database",
    "Base",
    "User",
    "Conversation",
    "Message",
    "SearchHistory",
    "ContentCache",
    "UserSettings",
    "BookmarkEntry",
    "BrowserHistory",
    "PageSummary",
    # Operations will be added back after rewriting for new schema
]
