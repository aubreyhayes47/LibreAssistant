<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# LibreAssistant - Copilot Instructions

This is a Tauri-based AI assistant application with a Python backend for high-performance native command integration.

## Project Identity

- **Name**: LibreAssistant
- **Purpose**: Privacy-first, single-user AI interface to the internet
- **Focus**: Privacy-first, local AI processing
- **License**: MIT License

## Project Structure

- **Frontend**: Tauri + Svelte in `frontend/` directory
- **Backend**: Python modules in `backend/` directory with FastAPI, SQLAlchemy, and AI integrations
- **Communication**: Tauri native commands (Rust ↔ Python) for optimal performance

## Key Technologies

- **Tauri**: Desktop app framework with Rust backend
- **Svelte**: Reactive frontend framework
- **Python**: Backend with FastAPI, SQLAlchemy, Playwright
- **Ollama**: Local LLM integration
- **SQLite**: Local database storage

## Development Guidelines

### Frontend (Svelte + Tauri)

- Use Svelte 5 runes syntax (`$state`, `$effect`, etc.)
- Tauri commands are invoked with `invoke()` from `@tauri-apps/api/core`
- All backend communication goes through Tauri native commands
- UI components should be responsive and modern
- Brand consistently as "LibreAssistant"

### Backend (Python)

- Main entry point is `backend/main.py`
- Commands are handled asynchronously
- Always return structured JSON responses with `success` field
- Use proper error handling and logging
- Module structure: `agents/`, `db/`, `llm/`, `utils/`

### Tauri Native Commands

- Rust commands in `frontend/src-tauri/src/lib.rs`
- Commands call Python scripts via `std::process::Command`
- Serialize/deserialize JSON payloads using serde
- Handle errors gracefully and return structured responses

## Code Patterns

### Adding New Features

1. **Backend**: Add command handler in `backend/main.py`
2. **Rust**: Add Tauri command wrapper in `lib.rs`
3. **Frontend**: Use `invoke()` to call the command
4. **UI**: Update Svelte components as needed

### Error Handling

- Python: Return `{"success": false, "error": "message"}`
- Rust: Use `Result<CommandResponse, String>`
- Frontend: Check `response.success` before using data

### Performance Considerations

- Use native commands instead of HTTP for backend communication
- Implement proper async/await patterns
- Cache frequently accessed data
- Use efficient data structures

## AI Integration

- LLM interactions through Ollama
- Content analysis and generation
- Web scraping with Playwright/Selenium
- Browser data extraction capabilities

## Security Notes

- Validate all inputs from frontend
- Use proper sanitization for web scraping
- Implement secure storage for sensitive data
- Follow Tauri security best practices
