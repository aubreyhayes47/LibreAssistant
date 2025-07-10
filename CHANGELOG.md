# Changelog

## [Unreleased]
### Changed
- **Documentation Audit**: Updated all documentation to accurately reflect current proof-of-concept state
- **Project Status Clarity**: Added clear distinction between current and planned features across all docs
- **Implementation Roadmap**: Created comprehensive development plan in `docs/IMPLEMENTATION_ROADMAP.md`
- **Consistent References**: All documentation now references the implementation roadmap for future development

### Added
- Comprehensive API documentation in API.md with current vs planned feature distinctions
- Detailed setup guide in SETUP.md with next development steps
- Missing Tauri commands: `search_web`, `set_user_setting`, `get_user_setting`, `clear_chat_history`, `clear_browser_history`, `clear_conversation_context`
- npm scripts for Tauri development and building (`tauri:dev`, `tauri:build`)
- Status indicators (🟢 working, 🟡 partial, 🔴 planned) throughout module documentation

### Fixed
- Corrected inaccurate claims about FastAPI implementation (currently CLI-based)
- Updated Svelte version references (currently v4, v5 planned for Phase 1.4)
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
