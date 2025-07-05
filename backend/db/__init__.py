"""
Database package for LibreAssistant.
"""

from .database import DatabaseManager, init_database, get_db_session, close_database
from .models import ChatMessage, BookmarkEntry, BrowserHistory, PageSummary, UserSettings, Base
from .operations import (
    ChatOperations, 
    BookmarkOperations, 
    HistoryOperations, 
    SummaryOperations, 
    SettingsOperations
)

__all__ = [
    'DatabaseManager',
    'init_database',
    'get_db_session',
    'close_database',
    'ChatMessage',
    'BookmarkEntry', 
    'BrowserHistory',
    'PageSummary',
    'UserSettings',
    'Base',
    'ChatOperations',
    'BookmarkOperations',
    'HistoryOperations',
    'SummaryOperations',
    'SettingsOperations'
]