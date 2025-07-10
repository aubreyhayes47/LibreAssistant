# 📜 LibreAssistant

An open-source, **single-user** and privacy-first interface to the internet powered by Tauri, Svelte, Rust, and Python. LibreAssistant fetches and summarizes web content so you rarely need to open cluttered pages yourself. The app focuses on **local-first AI**, **web automation**, and **customizable Flavors** that serve real communities—especially those most overlooked.

---

## ✝️ Mission

LibreAssistant is your private, local-first AI gateway to the internet—an assistant that reads the web for you, summarizes what matters, and protects your privacy.

Our focus is helping individuals and small organizations reclaim the web without sacrificing privacy or control.

> *“Serve the least, the last, and the lost—locally and globally.”*

---

## 🚀 Current Features (Proof of Concept)

✅ **Basic AI Chat** with Ollama integration (simple client)

✅ **Tauri + Svelte Frontend** with native desktop framework

✅ **Basic Web Scraping** using requests and BeautifulSoup

✅ **Simple Search** via DuckDuckGo (basic implementation)

✅ **CLI-based Backend** with command processing

✅ **Structured JSON Responses** for frontend communication

## 🚧 Features In Development

The following features are planned but not yet implemented:

🚧 **Database Layer** - SQLAlchemy models and persistence (not implemented)

🚧 **FastAPI Backend** - REST API architecture (currently CLI-based)

🚧 **Advanced Web Scraping** - Playwright integration (using basic tools)

🚧 **Session Management** - Conversation persistence (not implemented)

🚧 **Privacy Features** - Data encryption and controls (basic local storage)

🚧 **Performance Optimization** - Caching and optimization (not implemented)

🚧 **Comprehensive Testing** - Unit, integration, and E2E tests (minimal)

---

## 🌍 Example Flavors

LibreAssistant is designed to be **configured** for specific audiences through "Flavors"—predefined bundles of plugins and UI layouts.

✅ Solo Private Assistant (Power User)

✅ Developer Console (Plugin Creation)

✅ Household/Family Assistant

✅ School/Homeschool Co-op Suite

✅ Faith & Community Ministry Tool *(Memphis Edition)*

✅ Recovery Curriculum Manager

✅ Volunteer/Incident Management Suite

Each Flavor is fully local, encrypted, and adaptable to local languages and contexts.

---

## 🏗️ Current Architecture

```
LibreAssistant/
├── frontend/          # Tauri + Svelte UI (Svelte 4 patterns)
│   ├── src/
│   ├── src-tauri/     # Basic Tauri commands
│   └── static/
├── backend/           # Python CLI backend
│   ├── agents/        # Basic search and scraping
│   ├── llm/           # Simple Ollama client
│   ├── utils/         # Utility functions
│   └── main.py        # CLI command processor
```

**Current Implementation:**
- **Frontend:** Tauri + Svelte 4 (legacy store patterns)
- **Backend:** Python CLI processing (no FastAPI)
- **Communication:** Basic Rust ↔ Python subprocess calls
- **AI Engine:** Basic Ollama client integration
- **Database:** No persistence layer (data lost on restart)

**Target Architecture:**
- **Frontend:** Tauri + Svelte 5 with runes
- **Backend:** FastAPI with SQLAlchemy
- **Communication:** REST API via Tauri commands
- **AI Engine:** Advanced LLM pipeline with prompt management
- **Database:** SQLite with encryption and session persistence

---

## 🔌 Development Roadmap

LibreAssistant is currently a proof-of-concept with a comprehensive development plan to achieve production-ready status. See the [Complete Implementation Algorithm](#implementation-roadmap) below for detailed next steps.

**Current State:** Basic proof-of-concept with core UI and simple AI integration

**Target State:** Production-ready privacy-first AI assistant with advanced features

## 🗺️ Implementation Roadmap

The following roadmap outlines the complete development plan to implement all missing features:

### Phase 1: Core Infrastructure (Weeks 1-3)
- **Database Layer**: Implement SQLAlchemy models and migrations
- **FastAPI Backend**: Replace CLI with REST API architecture  
- **Enhanced Tauri Commands**: Expand command interface and error handling
- **Session Management**: Add conversation persistence and restoration

### Phase 2: Advanced Web Capabilities (Weeks 4-6)
- **Playwright Integration**: Replace basic scraping with advanced browser automation
- **Enhanced Search**: Multi-provider search with intelligent processing
- **Content Analysis**: Advanced text processing and extraction pipelines

### Phase 3: Comprehensive AI Pipeline (Weeks 7-9)
- **Advanced Ollama Integration**: Connection pooling, streaming, model management
- **Prompt Management**: Template system with context optimization
- **Content Intelligence**: Summarization, entity extraction, analysis

### Phase 4: Session & State Management (Weeks 10-11)
- **Conversation Management**: Threading, branching, cross-session context
- **User Preferences**: Settings management and personalization
- **Data Export/Import**: User data control and portability

### Phase 5: Frontend Modernization (Weeks 12-13)
- **Svelte 5 Migration**: Convert to runes syntax and modern patterns
- **Enhanced UI**: Real-time features, progressive enhancement
- **Accessibility**: Comprehensive accessibility improvements

### Phase 6: Privacy & Security (Weeks 14-15)
- **Data Encryption**: At-rest encryption with secure key management
- **Security Hardening**: Input validation, process isolation, network security
- **Privacy Controls**: Data retention, consent management, audit logging

### Phase 7: Performance Optimization (Weeks 16-17)
- **Caching Systems**: Multi-level caching with intelligent invalidation
- **Resource Management**: Memory, CPU, and disk optimization
- **Async Processing**: Background jobs and streaming responses

### Phase 8: Testing & QA (Weeks 18-19)
- **Comprehensive Testing**: Unit, integration, E2E, performance, security
- **Quality Assurance**: Code coverage, monitoring, observability

### Phase 9: Documentation & Distribution (Weeks 20-21)
- **Complete Documentation**: User guides, API docs, deployment guides
- **Build & Distribution**: Cross-platform packages and auto-updates

For detailed implementation steps, see the [Complete Implementation Algorithm](docs/IMPLEMENTATION_ROADMAP.md).

---

## 🌍 Future Flavors (Post-Production)

Once core infrastructure is complete, LibreAssistant will support "Flavors"—specialized configurations for different use cases:

🔮 **Solo Private Assistant** (Power User)
🔮 **Developer Console** (Plugin Creation)
🔮 **Household/Family Assistant**
🔮 **School/Homeschool Co-op Suite**
🔮 **Faith & Community Ministry Tool**
🔮 **Recovery Curriculum Manager**
🔮 **Volunteer/Incident Management Suite**

Each Flavor will be fully local, encrypted, and adaptable to local languages and contexts.

---

## 🛠️ Installation

### Prerequisites

* Rust: [rustup.rs](https://rustup.rs)
* Node.js: 18+ recommended
* Python: 3.10 or higher
* Git

### Dependencies

The Python backend uses `requirements.txt` for dependency management. While there's also a `pyproject.toml` file (for Poetry support), the setup script and documentation use pip with `requirements.txt` for simplicity.

### Quick Setup

For detailed installation instructions including platform-specific requirements, see [SETUP.md](SETUP.md).

#### Linux/macOS

```bash
git clone https://github.com/aubreyhayes47/LibreAssistant.git
cd LibreAssistant
./setup.sh
source .venv/bin/activate
```

#### Windows

```bash
git clone https://github.com/aubreyhayes47/LibreAssistant.git
cd LibreAssistant
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
cd frontend && npm install && cd ..
```

---

## 🚀 Development

✅ Start Frontend (from `frontend/`):

```bash
npm run tauri:dev
```

✅ Build for Production:

```bash
npm run tauri:build
```

### Development Checks

Run the setup script once in a new environment and activate the virtual environment:

```bash
./setup.sh
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows
```

Before committing run:

```bash
cd backend && black . && ruff --fix . && python -m pytest
cd ../frontend && npm install && npm run check
```

The frontend includes lightweight placeholder stores and utilities under
`src/lib/` so that `svelte-check` can run without additional setup.

---

## 📈 Development Status

Phase **1D** (browser integration) is complete. The app includes an embedded browser panel, a page summarization command, a multi-provider search agent, and persistent user settings. It connects to Ollama locally, stores chat, bookmarks and history, and all tests pass. See [TROUBLESHOOTING_PLAN](.github/TROUBLESHOOTING_PLAN.md) for progress details.

---

## 🔧 Backend API

The Python backend exposes commands accessible through Tauri. For detailed API documentation including parameters and examples, see [API.md](API.md).

✅ Sample Commands:

* `hello`: Test connectivity
* `process_url`: Extract web content  
* `get_browser_data`: Access history/bookmarks
* `analyze_content`: AI content analysis
* `summarize_page`: Extract content and return a summary
* `search_web`: Query DuckDuckGo for web results
* `chat_with_llm`: Chat with local Ollama LLM
* `save_bookmark`: Save a bookmark to database
* `get_chat_history`: Retrieve chat conversation history
* `get_bookmarks`: Get saved bookmarks
* `search_bookmarks`: Search through bookmarks
* `get_browser_history`: Get browsing history
* `add_history_entry`: Add entry to browsing history
* `set_user_setting`: Save user preferences
* `get_user_setting`: Retrieve user preferences
* `clear_chat_history`: Clear chat history
* `clear_browser_history`: Clear browsing history
* `clear_conversation_context`: Clear LLM conversation context

✅ Adding New Commands:

**Python Backend (backend/main.py):**
```python
async def new_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    return { "success": True, "data": result }
```

**Rust Tauri (frontend/src-tauri/src/lib.rs):**
```rust
#[tauri::command]
async fn new_command(param: String) -> Result<CommandResponse, String> {
    let mut payload_data = HashMap::new();
    payload_data.insert("param".to_string(), serde_json::Value::String(param));
    call_python_backend("new_command".to_string(), CommandPayload { data: payload_data }).await
}
```

Don't forget to add the new command to the `invoke_handler` list in the `run()` function.

---

## 🧪 Testing

✅ Backend:

```bash
cd backend
python -m pytest
```

✅ Frontend:

Frontend testing is currently set up with placeholder test utilities. See `src/lib/utils/testData.js` for the current test data generation functionality.

---

## ⚙️ Configuration

✅ `.env` in `backend/` (copy from `.env.example`):

```env
LOG_LEVEL=INFO
OLLAMA_HOST=http://localhost:11434
DATABASE_URL=sqlite:///./libreassistant.db
```

✅ Tauri Config:

* `frontend/src-tauri/tauri.conf.json`

---

## 📚 Documentation

### Quick Start
- **[Setup Guide](SETUP.md)** - Get LibreAssistant running quickly
- **[User Guide](docs/user-guide/getting-started.md)** - Complete user documentation
- **[Build Guide](BUILD.md)** - Building from source

### Development
- **[Development Guide](DEVELOPMENT.md)** - Development patterns and workflows
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to the project
- **[Testing Guide](docs/testing/testing-guide.md)** - Comprehensive testing documentation

### Architecture
- **[Agents Module](docs/modules/agents.md)** - Web search and content extraction
- **[Database Module](docs/modules/database.md)** - Local data storage with SQLite
- **[LLM Module](docs/modules/llm.md)** - Local AI processing with Ollama

### Project Information
- **[API Documentation](API.md)** - Backend API reference
- **[Changelog](CHANGELOG.md)** - Version history and updates
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

---

## ❤️ Contributing

LibreAssistant is **open source** and **Beatitudes-aligned**. We welcome contributions of all kinds:

✅ Plugin developers

✅ Translators

✅ UI/UX designers

✅ Educators and curriculum writers

✅ Mission-minded testers

Please:

* Fork the repo
* Create feature branches
* Write tests
* Submit pull requests

---

## 📜 License

MIT License. See LICENSE file for details.

---

## ✝️ Our Pledge

> *“We will not optimize for profit over mission. We will serve the poor, the meek, those who mourn, the peacemakers, and the persecuted.”*

We aim to enable **ethical, local-first AI** that can be used anywhere—from suburban homes to rural mission schools to refugee ministries.

---

## 📞 Support

For installation help and common issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

Please open an issue on GitHub or contact the development team.

LibreAssistant — *Your privacy-first AI gateway to the internet. Built with ❤️ and guided by the Beatitudes.*
