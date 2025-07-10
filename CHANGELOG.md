# Changelog

## [Unreleased]
### Added
- Comprehensive API documentation in API.md
- Detailed setup guide in SETUP.md
- Missing Tauri commands: `search_web`, `set_user_setting`, `get_user_setting`, `clear_chat_history`, `clear_browser_history`, `clear_conversation_context`
- npm scripts for Tauri development and building (`tauri:dev`, `tauri:build`)

### Changed
- Updated README with accurate installation instructions for Windows
- Synchronized pyproject.toml dependencies with requirements.txt
- Fixed backend API command list to include all implemented commands
- Improved development setup documentation

### Fixed
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
