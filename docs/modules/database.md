# LibreAssistant Database Module

⚠️ **Implementation Status**: This module describes both current SQLAlchemy implementation and planned advanced features.

🟢 **Currently Working**: Basic SQLAlchemy models, simple CRUD operations  
🟡 **Partially Working**: Database initialization, session management  
🔴 **Planned**: Advanced migrations, data encryption, cleanup operations (Phase 1.1)

This module handles all database operations for LibreAssistant using SQLAlchemy and SQLite.

## Current vs Planned Features

**Current Implementation:**
- SQLAlchemy models and basic operations
- SQLite database with simple schema
- Basic CRUD through operations classes
- Manual database initialization

**Planned Enhancements (Phase 1.1):**
- Alembic migrations system
- Advanced data retention policies  
- Encryption for sensitive data
- Automated cleanup operations
- Performance optimizations

See the [Implementation Roadmap](../IMPLEMENTATION_ROADMAP.md) for detailed development timeline.

## Overview

LibreAssistant uses SQLite for local data storage, ensuring all user data stays on device and maintains privacy.

## Database Schema

### Tables

#### `conversations`
Stores chat conversation history:
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    user_message TEXT,
    assistant_response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);
```

#### `user_settings`
Stores user preferences and configuration:
```sql
CREATE TABLE user_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `search_history`
Tracks search queries and results:
```sql
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY,
    query TEXT,
    results JSON,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `content_cache`
Caches extracted web content:
```sql
CREATE TABLE content_cache (
    url TEXT PRIMARY KEY,
    content TEXT,
    title TEXT,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);
```

## Usage Examples

### Database Connection

```python
from backend.db.database import DatabaseManager

# Initialize database
db = DatabaseManager()
await db.initialize()
```

### Conversation Management

```python
# Save conversation
await db.save_conversation(
    session_id="session_123",
    user_message="What is AI?",
    assistant_response="AI stands for..."
)

# Get conversation history
history = await db.get_conversation_history(session_id="session_123")
```

### Settings Management

```python
# Save user setting
await db.save_setting("ollama_model", "llama2")

# Get user setting
model = await db.get_setting("ollama_model", default="llama2")
```

### Content Caching

```python
# Cache content
await db.cache_content(
    url="https://example.com",
    content="Article content...",
    title="Example Article"
)

# Retrieve cached content
cached = await db.get_cached_content("https://example.com")
```

## Data Management

### Cleanup Operations

```python
# Clear old conversations
await db.clear_old_conversations(days=30)

# Clear expired cache
await db.clear_expired_cache()

# Clear all user data (privacy)
await db.clear_all_data()
```

### Migration System

Database migrations are handled automatically:

```python
# Check current version
version = await db.get_schema_version()

# Run migrations
await db.migrate_to_latest()
```

## Privacy Features

### Data Encryption
- **Current**: Basic local storage
- **Planned**: Sensitive data encryption at rest (Phase 1.1)
- **Future**: User settings encryption for privacy (Phase 1.3)

### Data Retention
- **Current**: Manual data management
- **Planned**: Configurable retention periods (Phase 1.1)  
- **Future**: Automatic cleanup of old data (Phase 1.1)

### Backup and Export
- **Current**: Direct SQLite file access
- **Planned**: Local backup functionality (Phase 1.2)
- **Future**: Data export for user control (Phase 1.2)

## Performance Optimization

### Indexing Strategy
```sql
-- Optimized indexes for common queries
CREATE INDEX idx_conversations_session ON conversations(session_id);
CREATE INDEX idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX idx_search_history_timestamp ON search_history(timestamp);
CREATE INDEX idx_content_cache_expires ON content_cache(expires_at);
```

### Connection Pooling
- SQLite connection optimization
- Prepared statement caching
- Transaction management

## API Reference

### DatabaseManager Class

#### Core Methods

**initialize() -> None**
- Sets up database connection
- Runs necessary migrations
- Creates indexes if needed

**close() -> None**
- Closes database connections
- Cleans up resources
- Ensures data integrity

#### Conversation Methods

**save_conversation(session_id: str, user_message: str, assistant_response: str, metadata: dict = None) -> None**
- Saves a conversation exchange
- Associates with session ID
- Includes optional metadata

**get_conversation_history(session_id: str, limit: int = 50) -> list**
- Retrieves conversation history
- Ordered by timestamp (newest first)
- Supports pagination with limit

**delete_conversation(session_id: str) -> None**
- Deletes entire conversation session
- Removes all associated messages
- Cannot be undone

#### Settings Methods

**save_setting(key: str, value: str) -> None**
- Saves user setting
- Overwrites existing values
- Automatically timestamps

**get_setting(key: str, default: any = None) -> any**
- Retrieves user setting
- Returns default if not found
- Handles type conversion

**delete_setting(key: str) -> None**
- Removes user setting
- Silent if key doesn't exist

#### Cache Methods

**cache_content(url: str, content: str, title: str = None, ttl: int = 3600) -> None**
- Caches web content
- Sets expiration time
- Overwrites existing cache

**get_cached_content(url: str) -> dict**
- Retrieves cached content
- Checks expiration
- Returns None if expired

**clear_expired_cache() -> int**
- Removes expired cache entries
- Returns number of entries cleared

## Models

### Conversation Model

```python
from backend.db.models import Conversation

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False)
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)
```

### UserSetting Model

```python
from backend.db.models import UserSetting

class UserSetting(Base):
    __tablename__ = 'user_settings'
    
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

## Configuration

### Database Settings

```python
# In backend/utils/config.py
DATABASE_CONFIG = {
    "path": "data/libreassistant.db",
    "echo": False,  # Set to True for SQL logging
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 3600
}
```

### Migration Settings

```python
MIGRATION_CONFIG = {
    "migrations_path": "backend/db/migrations",
    "auto_migrate": True,
    "backup_before_migration": True
}
```

## Development

### Adding New Tables

1. Create model in `backend/db/models.py`
2. Create migration file
3. Add operations to `database.py`
4. Update tests

### Testing

```bash
# Run database tests
cd backend
python -m pytest db/tests/

# Test with clean database
python -m pytest db/tests/ --clean-db
```

### Migrations

```python
# Create new migration
from backend.db.migrations import create_migration

create_migration("add_new_table", """
CREATE TABLE new_table (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")
```

## Error Handling

### Common Issues

1. **Database Locked:**
   ```python
   try:
       await db.save_conversation(...)
   except sqlite3.OperationalError as e:
       if "database is locked" in str(e):
           await asyncio.sleep(0.1)
           # Retry operation
   ```

2. **Constraint Violations:**
   ```python
   try:
       await db.save_setting(key, value)
   except sqlite3.IntegrityError:
       # Handle duplicate key or constraint violation
       pass
   ```

3. **Connection Issues:**
   ```python
   try:
       await db.initialize()
   except Exception as e:
       logger.error(f"Database initialization failed: {e}")
       # Attempt recovery or fallback
   ```

## Best Practices

### Transaction Management

```python
async def complex_operation():
    async with db.transaction():
        await db.save_conversation(...)
        await db.save_setting(...)
        # If any operation fails, all are rolled back
```

### Resource Cleanup

```python
# Always clean up resources
try:
    db = DatabaseManager()
    await db.initialize()
    # ... perform operations
finally:
    await db.close()
```

### Data Validation

```python
from pydantic import BaseModel

class ConversationData(BaseModel):
    session_id: str
    user_message: str
    assistant_response: str
    
    class Config:
        validate_assignment = True
```

This database module provides reliable, privacy-focused data storage for LibreAssistant while maintaining excellent performance and data integrity.
