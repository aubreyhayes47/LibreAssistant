# Phase 1D Development Plan

This document outlines the initial goals and tasks for Phase 1D of the LibreAssistant MVP. Phase 1D introduces an embedded browser panel and server-side page summarization.

## Goals

1. **BrowserPanel Component**
   - Embed a simple web view using an `iframe` for now.
   - Provide navigation controls and the ability to request a page summary.
   - Save visited pages to the history database via the `add_history_entry` command.

2. **Summarization Backend**
   - Implement a new `summarize_page` command in the Python backend.
   - Reuse the existing `ContentExtractor` agent to fetch page text.
   - Generate an LLM summary and store it using `SummaryOperations`.

3. **Tauri Integration**
   - Expose the `summarize_page` command from Rust and add it to the invoke handler list.
   - Wire the new command into the BrowserPanel component so users can request summaries.

This plan establishes the foundation for deeper browser features and paves the way for Phase 1E data persistence improvements.
