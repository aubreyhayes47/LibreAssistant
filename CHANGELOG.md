# Changelog

## [Unreleased]
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
