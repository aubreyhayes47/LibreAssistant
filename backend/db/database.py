"""
Database connection and session management for LibreAssistant.
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

# Use absolute imports when running as main module
try:
    from .models import Base
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from db.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connections and sessions."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager with optional custom path."""
        if db_path is None:
            # Default to backend directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(backend_dir, 'libreassistant.db')
        
        self.db_path = db_path
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        
    def initialize(self) -> bool:
        """Initialize database connection and create tables if needed."""
        try:
            # Create SQLite engine with optimizations
            self.engine = create_engine(
                f'sqlite:///{self.db_path}',
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                connect_args={
                    'check_same_thread': False,  # Allow multi-threading
                    'timeout': 30,  # 30 second timeout
                }
            )
            
            # Enable WAL mode and other SQLite optimizations
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                # Enable WAL mode for better concurrent access
                cursor.execute("PRAGMA journal_mode=WAL")
                # Enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys=ON")
                # Optimize SQLite settings
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            logger.info(f"Database initialized successfully at {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            return False
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions with automatic cleanup."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Get a database session for synchronous operations."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.SessionLocal()
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup database: {str(e)}")
            return False
    
    def get_database_info(self) -> dict:
        """Get information about the database."""
        try:
            with self.get_session() as session:
                # Get table counts
                try:
                    from .models import ChatMessage, BookmarkEntry, BrowserHistory, PageSummary, UserSettings
                except ImportError:
                    # Fallback for direct execution
                    import sys
                    from pathlib import Path
                    sys.path.append(str(Path(__file__).parent.parent))
                    from db.models import ChatMessage, BookmarkEntry, BrowserHistory, PageSummary, UserSettings
                
                info = {
                    'database_path': self.db_path,
                    'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
                    'table_counts': {
                        'chat_messages': session.query(ChatMessage).count(),
                        'bookmarks': session.query(BookmarkEntry).count(),
                        'browser_history': session.query(BrowserHistory).count(),
                        'page_summaries': session.query(PageSummary).count(),
                        'user_settings': session.query(UserSettings).count(),
                    }
                }
                return info
        except Exception as e:
            logger.error(f"Failed to get database info: {str(e)}")
            return {'error': str(e)}


# Global database manager instance
db_manager = DatabaseManager()


def init_database(db_path: Optional[str] = None) -> bool:
    """Initialize the global database manager."""
    global db_manager
    if db_path:
        db_manager = DatabaseManager(db_path)
    return db_manager.initialize()


def get_db_session():
    """Get database session context manager."""
    return db_manager.get_session()


def close_database():
    """Close database connections."""
    db_manager.close()
