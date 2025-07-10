# LibreAssistant Development Guide

This guide provides detailed information for developers working on LibreAssistant.

## Project Architecture

LibreAssistant is built with a three-tier architecture:

1. **Frontend**: Svelte 4 + Tauri for the desktop interface
2. **Bridge**: Rust-based Tauri commands for secure communication  
3. **Backend**: Python CLI processing (FastAPI planned)

### Current Communication Flow

```
Frontend (Svelte 4) → Tauri Commands (Rust) → Python CLI Backend
```

**Current Implementation:**
- Frontend uses legacy Svelte 4 store patterns
- Backend processes commands via CLI arguments
- No database persistence (data lost on restart)
- Basic error handling and response formatting

**Target Architecture:**
```
Frontend (Svelte 5) → Tauri Commands (Rust) → FastAPI Backend → SQLite Database
```

All communication between the frontend and backend will happen through Tauri's native command system, ensuring security and performance.

## Development Environment Setup

### Prerequisites

- **Node.js**: 18.17.0 or higher
- **Python**: 3.11 or higher
- **Rust**: Latest stable version
- **Ollama**: For local AI processing

### Initial Setup

1. **Clone and setup the project:**
   ```bash
   git clone https://github.com/yourusername/LibreAssistant.git
   cd LibreAssistant
   ./setup.sh  # or follow manual setup steps
   ```

2. **Verify installation:**
   ```bash
   cd frontend
   npm run tauri dev
   ```

## Code Organization

### Frontend Structure (`frontend/`)

```
src/
├── lib/
│   ├── components/     # Basic Svelte components
│   ├── services/       # API service layers (basic)
│   ├── stores/         # Svelte 4 stores (legacy patterns)
│   └── utils/          # Utility functions
├── routes/             # SvelteKit routes
└── app.html           # Main app template
```

**Current State**: Uses Svelte 4 store patterns, basic component structure
**Target State**: Svelte 5 runes, enhanced component library

### Backend Structure (`backend/`)

```
backend/
├── main.py            # CLI command processor (current)
├── agents/            # Basic search and scraping
├── llm/               # Simple Ollama client
└── utils/             # Shared utilities
```

**Missing Directories** (Planned):
```
backend/
├── api/               # FastAPI application (not implemented)
├── db/                # Database models and operations (not implemented)
├── services/          # Business logic services (not implemented)
└── migrations/        # Database migrations (not implemented)
```

### Tauri Structure (`frontend/src-tauri/`)

```
src/
├── main.rs           # Tauri application setup
└── lib.rs            # Basic command definitions
```

**Current**: Limited command set, basic error handling
**Target**: Comprehensive command interface, proper error propagation

## Development Patterns

### Current Implementation Status

**Working Features:**
- Basic Tauri command structure
- Simple Ollama AI integration  
- CLI-based backend processing
- Structured JSON responses
- Basic web scraping with requests/BeautifulSoup

**Missing Critical Features:**
- Database persistence layer
- FastAPI REST architecture
- Session management
- Advanced error handling
- Svelte 5 modern patterns

### Adding a New Feature (Current Process)

1. **Define the Command Interface**

   In `frontend/src-tauri/src/lib.rs`:
   ```rust
   #[tauri::command]
   async fn new_feature_command(data: String) -> Result<CommandResponse, String> {
       call_python_backend("new_feature", &data).await
   }
   ```

2. **Implement Backend Logic**

   In `backend/main.py`:
   ```python
   # Current CLI-based processing
   if command == "new_feature":
       try:
           # Implementation here
           return json.dumps({"success": True, "data": result})
       except Exception as e:
           return json.dumps({"success": False, "error": str(e)})
   ```

3. **Create Frontend Service**

   In `frontend/src/lib/services/`:
   ```javascript
   import { invoke } from '@tauri-apps/api/core';
   
   export async function callNewFeature(data) {
       return await invoke('new_feature_command', { data });
   }
   ```

4. **Build UI Components**

   In `frontend/src/lib/components/` (Svelte 4 patterns):
   ```svelte
   <script>
   import { callNewFeature } from '$lib/services/api.js';
   import { writable } from 'svelte/store';
   
   let data = '';
   let result = writable(null);
   
   async function handleSubmit() {
       const response = await callNewFeature(data);
       result.set(response);
   }
   </script>
   ```

### Target Development Pattern (Post-Infrastructure)

Once core infrastructure is implemented, the pattern will be:

1. **FastAPI Endpoint** in `backend/api/routers/`
2. **Database Operations** in `backend/services/`
3. **Tauri Command Bridge** in `lib.rs`
4. **Svelte 5 Components** with runes syntax

### State Management (Current vs Target)

**Current (Svelte 4 Stores):**
```javascript
// stores/example.js
import { writable } from 'svelte/store';

export const appState = writable({
    currentView: 'home',
    isLoading: false,
    user: null
});
```

**Target (Svelte 5 Runes):**
```javascript
// state/example.svelte.js
let appState = $state({
    currentView: 'home',
    isLoading: false,
    user: null
});

let loading = $derived(appState.isLoading);

$effect(() => {
    // Reactive effects
    if (appState.isLoading) {
        fetchData();
    }
});
```

### Error Handling Patterns

**Backend (Python):**
```python
async def safe_operation():
    try:
        result = await risky_operation()
        return {"success": True, "data": result}
    except SpecificError as e:
        logger.error(f"Specific error: {e}")
        return {"success": False, "error": "User-friendly message"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"success": False, "error": "An unexpected error occurred"}
```

**Frontend (Svelte):**
```javascript
async function handleAction() {
    try {
        const response = await invoke('command_name', { data });
        if (response.success) {
            // Handle success
        } else {
            showError(response.error);
        }
    } catch (error) {
        showError('Connection error');
    }
}
```

## Testing Strategy

### Unit Tests

**Python Backend:**
```bash
cd backend
python -m pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm test
```

### Integration Tests

**Backend Integration:**
```bash
cd backend
python test_backend.py
```

**E2E Testing:**
```bash
cd frontend
npm run test:e2e
```

### Testing Guidelines

- Write tests for all new backend functions
- Include error condition testing
- Mock external dependencies (Ollama, web requests)
- Maintain >80% code coverage

## Performance Considerations

### Frontend Optimization

- Use Svelte's built-in reactivity efficiently
- Implement virtual scrolling for large lists
- Lazy load components when possible
- Minimize bundle size with tree shaking

### Backend Optimization

- Use async/await patterns consistently
- Implement connection pooling for database
- Cache frequently accessed data
- Optimize AI model loading

### Memory Management

- Clean up resources in Python backend
- Monitor memory usage during development
- Use generators for large data processing
- Implement proper cleanup in Tauri commands

## Security Guidelines

### Data Validation

**Always validate inputs:**
```python
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    query: str
    max_results: int = 10
    
    @validator('query')
    def validate_query(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Query cannot be empty')
        return v.strip()
```

### Secure Communication

- All backend communication goes through Tauri commands
- No direct HTTP endpoints exposed
- Input sanitization at all entry points
- Proper error handling without information leakage

### Privacy Protection

- No user data sent to external services
- Local storage encryption for sensitive data
- Clear data retention policies
- User-controlled data deletion

## Debugging

### Development Tools

**Backend Debugging:**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
cd backend
python main.py
```

**Frontend Debugging:**
```bash
# Start with dev tools
cd frontend
npm run tauri dev
```

**Rust Debugging:**
```bash
# Enable Rust debug logs
export RUST_LOG=debug
```

### Common Issues

1. **Python Module Import Errors:**
   - Ensure virtual environment is activated
   - Check PYTHONPATH in Tauri commands

2. **Tauri Command Failures:**
   - Check Rust compilation errors
   - Verify command registration in main.rs

3. **Frontend Build Issues:**
   - Clear node_modules and reinstall
   - Check for TypeScript errors

## Contributing Workflow

### Branch Strategy

- `main`: Stable release branch
- `develop`: Integration branch for features
- `feature/*`: Individual feature branches
- `hotfix/*`: Critical bug fixes

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered
- [ ] Error handling implemented

### Release Process

1. Feature freeze on `develop`
2. Create release candidate
3. Testing and bug fixes
4. Merge to `main`
5. Tag release version
6. Update documentation

## Resources

### Documentation

- [Tauri Documentation](https://tauri.app/v1/guides/)
- [Svelte 5 Documentation](https://svelte-5-preview.vercel.app/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

### Tools

- **IDE Extensions**: Rust Analyzer, Svelte, Python
- **Debugging**: VS Code debugger, Rust debug tools
- **Profiling**: py-spy for Python, Rust profiling tools
- **Testing**: pytest, Vitest, Playwright

### Community

- GitHub Discussions for questions
- Issue tracker for bugs and features
- Discord server for real-time chat (TBD)

This development guide ensures consistent, high-quality contributions to LibreAssistant while maintaining our privacy-first, single-user focus.
