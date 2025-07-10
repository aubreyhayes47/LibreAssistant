# Changelog

## [Unreleased] - 2025-07-10

### Major Milestone: Database Foundation Complete ✅
- **Phase 1.1 Step 1 COMPLETED**: Full SQLAlchemy schema implementation (9 models)
- **Database Layer**: Complete user-centric design with privacy controls and performance optimization
- **Model Validation**: Comprehensive testing framework implemented and passing

### Added
- **Complete Database Schema**: User, Conversation, Message, SearchHistory, ContentCache, UserSettings, BookmarkEntry, BrowserHistory, PageSummary models
- **Database Operations**: Basic CRUD operations and session management (legacy operations being rewritten)
- **Model Testing**: Validation script `test_models_validation.py` with full relationship testing
- **Migration Ready**: Database schema ready for Alembic migration system
- **Privacy Architecture**: Built-in data retention controls and encryption flags
- **Performance Optimization**: Comprehensive indexing and hash-based deduplication

### Current Implementation Status
- **Database Models**: ✅ Complete (Phase 1.1 Step 1)
- **Backend Commands**: ✅ 16+ commands implemented via CLI processing
- **Frontend**: ✅ Svelte 5 + Tauri desktop application
- **AI Integration**: ✅ Ollama client with conversation context
- **Web Scraping**: ✅ Basic requests + BeautifulSoup
- **Search**: ✅ DuckDuckGo integration with summarization

### In Progress 🔄
- **Database Integration**: DatabaseManager and service layer (Phase 1.1 Step 2)
- **Operations Rewrite**: Updating operations.py for new schema
- **FastAPI Migration**: Planned transition from CLI to REST API (Phase 1.2)

### Fixed
- Corrected documentation claims about project maturity (25-30% complete, not 15-20%)
- Updated Svelte version references (currently v5, not v4 as some docs claimed)
- Clarified SQLAlchemy usage (basic models implemented, advanced features planned)
- Synchronized all documentation with actual codebase state
- Missing exposure of backend commands through Tauri interface
- Inconsistencies between documentation and actual implementation
- Installation instructions for Windows users

## [Phase 1D] - 2025-07-10
### Added
- `search_web` backend command using DuckDuckGo via new `SearchAgent`.
- Summarization prompt tuned for concise output.
- Multi-provider search with optional result summarization.
- Commands to save and retrieve user settings.
- Commands to clear chat and browser history as well as in-memory context.
- Readability-based extraction fallback for difficult sites.
- Summarization command now reuses saved summaries when available.

### Changed
- Updated README with new feature details.
- Updated troubleshooting plan and Phase 1D plan to reflect current status.
- Clarified plugin system progress in documentation.
- Removed unused multi-user logging fields.
