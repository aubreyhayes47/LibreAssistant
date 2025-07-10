# LibreAssistant Database Schema Documentation

## Overview

LibreAssistant uses SQLite with SQLAlchemy ORM for local data persistence. The schema is designed for privacy-first single-user operation with comprehensive data management.

## Implementation Status: ✅ COMPLETED (Phase 1.1 Step 1)

All models have been implemented, tested, and validated as of July 10, 2025.

## Models Implemented

### Core Models

#### 1. **User** (`users` table)
Single user configuration and preferences storage.

**Key Fields:**
- `id` (Primary Key)
- `username` (Unique, default: "user")
- `display_name`, `email` (Optional)
- `preferences` (JSON storage)
- `data_retention_days` (Privacy control)
- `auto_cleanup_enabled` (GDPR compliance)

**Relationships:**
- One-to-many with conversations, search history, settings, bookmarks, browser history

#### 2. **Conversation** (`conversations` table)
Chat sessions with AI models.

**Key Fields:**
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `title` (Auto-generated or user-defined)
- `model_name` (AI model used)
- `system_prompt` (Conversation context)
- `message_count` (Performance tracking)
- `is_archived` (Organization)

**Relationships:**
- Belongs to User
- One-to-many with Messages

#### 3. **Message** (`messages` table)
Individual messages within conversations.

**Key Fields:**
- `id` (Primary Key)
- `conversation_id` (Foreign Key)
- `role` (user/assistant/system)
- `content` (Message text)
- `sequence_number` (Ordering)
- `web_search_id` (Optional link to search)

**Relationships:**
- Belongs to Conversation
- Optional link to SearchHistory

#### 4. **SearchHistory** (`search_history` table)
Web search queries and results caching.

**Key Fields:**
- `id` (Primary Key)
- `user_id`, `conversation_id`, `message_id` (Context linking)
- `query` (Search terms)
- `provider` (Search engine used)
- `results_json` (Cached results)
- `summary` (AI-generated summary)

**Relationships:**
- Belongs to User
- Optional links to Conversation and Message

#### 5. **ContentCache** (`content_cache` table)
Cached web content with deduplication.

**Key Fields:**
- `id` (Primary Key)
- `url` (Source URL)
- `content_hash` (SHA-256 for deduplication)
- `title`, `content`, `metadata` (Extracted content)
- `expires_at` (Cache expiration)
- `access_count` (Usage tracking)

**Features:**
- Automatic content deduplication
- Configurable expiration
- Access tracking for cleanup

#### 6. **UserSettings** (`user_settings` table)
Key-value configuration storage.

**Key Fields:**
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `key` (Setting name)
- `value` (Setting value)
- `data_type` (Type information)
- `is_encrypted` (Security flag)

**Features:**
- Type-aware value conversion
- Encryption flag for sensitive settings
- Default value support

### Extended Models

#### 7. **BookmarkEntry** (`bookmark_entries` table)
Enhanced bookmark management.

**Key Fields:**
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `url`, `title`, `description`
- `folder_path` (Organization)
- `content_cache_id` (Link to cached content)
- `access_count`, `last_accessed`

**Features:**
- Folder-based organization
- Usage statistics
- Integration with content cache

#### 8. **BrowserHistory** (`browser_history` table)
Privacy-controlled browsing history.

**Key Fields:**
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `url`, `title`, `visit_count`
- `last_visit`, `is_private`
- `auto_cleanup_eligible`

**Features:**
- Private browsing support
- Automatic cleanup policies
- Visit frequency tracking

#### 9. **PageSummary** (`page_summaries` table)
AI-generated content analysis.

**Key Fields:**
- `id` (Primary Key)
- `content_cache_id` (Foreign Key)
- `summary_text`, `keywords_json`
- `model_used`, `quality_score`
- `generation_time`, `usage_count`

**Features:**
- AI model tracking
- Quality scoring
- Performance metrics

## Schema Relationships

```
User (1)
├── Conversations (*) ├── Messages (*)
├── SearchHistory (*)
├── UserSettings (*)
├── BookmarkEntries (*) ── ContentCache (*)
├── BrowserHistory (*)
└── [Indirect] PageSummaries (*) ── ContentCache (*)
```

## Privacy Features

### Data Retention Controls
- Per-user retention day settings
- Automatic cleanup flags for GDPR compliance
- Privacy mode support for browser history

### Security Features
- Content deduplication with SHA-256 hashing
- Encryption flags for sensitive settings
- Access tracking for audit trails

### Performance Optimization
- Comprehensive indexing strategy:
  - User-based queries (user_id indexes)
  - Conversation context (conversation_id indexes)
  - Content lookup (url, hash indexes)
  - Time-based queries (timestamp indexes)
- Composite indexes for common filter patterns
- Unique constraints to prevent data duplication

## Usage Status

- **Models**: ✅ Implemented and validated (July 10, 2025)
- **Database Manager**: 🔄 In development (Phase 1.1 Step 2)
- **Migration System**: 📋 Ready for implementation (Phase 1.1 Step 3)
- **Service Layer**: 📋 Planned after database manager (Phase 1.1 Step 4)

## Testing

The schema has been validated using `backend/test_models_validation.py`:
- ✅ Model instantiation testing
- ✅ Relationship verification
- ✅ Constraint validation
- ✅ Index functionality
- ✅ Hash generation methods

## Next Steps

1. **DatabaseManager Implementation** (Phase 1.1 Step 2)
   - Connection pooling and session management
   - CRUD operations for all models
   - Transaction management with rollback

2. **Migration System** (Phase 1.1 Step 3)
   - Alembic integration for schema versioning
   - Initial migration for base schema
   - Rollback capability

3. **Service Layer** (Phase 1.1 Step 4)
   - High-level database operations
   - Business logic for data operations
   - Integration with FastAPI (Phase 1.2)

This schema provides a solid foundation for LibreAssistant's privacy-first, single-user data management needs.
