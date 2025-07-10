# LibreAssistant Development TODO

**Current Status**: Proof of Concept (15-20% complete)
**Next Phase**: Core Infrastructure Foundation

This TODO list is organized by the [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md) phases.

## 🚨 CRITICAL - Phase 1: Core Infrastructure (Weeks 1-3)

### 1.1 Database Layer Implementation (PRIORITY: CRITICAL)
- [ ] Create SQLAlchemy models in `backend/db/models.py`
  - [ ] User model (single user configuration)
  - [ ] Conversation model (chat sessions)
  - [ ] Message model (individual messages)
  - [ ] SearchHistory model (web queries)
  - [ ] ContentCache model (scraped content)
  - [ ] UserSettings model (preferences)
- [ ] Implement DatabaseManager in `backend/db/database.py`
  - [ ] Connection pooling and management
  - [ ] CRUD operations for all models
  - [ ] Transaction management with rollback
  - [ ] Data encryption for sensitive fields
- [ ] Create migration system in `backend/db/migrations/`
  - [ ] Versioned schema migrations
  - [ ] Migration runner with rollback
  - [ ] Initial schema migration
- [ ] Database service layer in `backend/services/database_service.py`

### 1.2 FastAPI Backend Architecture (PRIORITY: CRITICAL)
- [ ] Replace CLI backend with FastAPI
  - [ ] Create `backend/api/main.py` FastAPI application
  - [ ] Remove current CLI processing from `backend/main.py`
  - [ ] Add middleware (CORS, logging, error handling)
  - [ ] Health check and status endpoints
- [ ] Implement API routers in `backend/api/routers/`
  - [ ] `chat.py` - conversation endpoints
  - [ ] `search.py` - web search operations
  - [ ] `content.py` - content analysis endpoints
  - [ ] `settings.py` - user preferences
  - [ ] `health.py` - system status
- [ ] Create Pydantic models in `backend/api/models/`
  - [ ] Request/response schemas
  - [ ] Validation rules and error schemas
  - [ ] Type hints throughout
- [ ] Add authentication and security
  - [ ] API key validation for Tauri commands
  - [ ] Request rate limiting
  - [ ] Input sanitization and validation

## 🔴 HIGH PRIORITY - Phase 2: Advanced Web Capabilities (Weeks 4-6)

### 2.1 Playwright Web Scraping Engine
- [ ] Replace basic scraping with Playwright
  - [ ] Remove requests/BeautifulSoup from `backend/agents/`
  - [ ] Create `backend/agents/playwright_scraper.py`
  - [ ] Browser pool management
  - [ ] JavaScript rendering support
  - [ ] Dynamic content handling

## Previously Completed ✅

- ~~Integrate the search agent with multiple providers and feed results into the summarization pipeline.~~ ✅
- ~~Persist local preferences in `user_settings` and add quick ways to clear history and memory.~~ ✅
- ~~Complete comprehensive documentation review and fix all discrepancies between docs and implementation.~~ ✅
- ~~Ensure all backend Python commands have corresponding Tauri wrappers.~~ ✅
- ~~Create comprehensive API documentation, setup guides, and troubleshooting docs.~~ ✅

## Current Immediate Actions (This Week)

1. **Start Phase 1.1**: Begin SQLAlchemy model implementation
2. **Database Setup**: Install SQLAlchemy, Alembic for migrations
3. **FastAPI Setup**: Install FastAPI, Uvicorn, prepare for CLI replacement
4. **Architecture Planning**: Finalize database schema design

See [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md) for the complete development plan.

