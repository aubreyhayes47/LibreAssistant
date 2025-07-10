# 📜 LibreAssistant

An open-source, **single-user** and privacy-first interface to the internet powered by Tauri, Svelte, Rust, and Python. LibreAssistant fetches and summarizes web content so you rarely need to open cluttered pages yourself. The app focuses on **local-first AI**, **web automation**, and **customizable Flavors** that serve real communities—especially those most overlooked.

---

## ✝️ Mission

LibreAssistant is your private, local-first AI gateway to the internet—an assistant that reads the web for you, summarizes what matters, and protects your privacy.

Our focus is helping individuals and small organizations reclaim the web without sacrificing privacy or control.

> *“Serve the least, the last, and the lost—locally and globally.”*

---

## 🚀 Features

✅ **Local AI Chat** with Ollama for private, on-device conversations

✅ **Embedded Browser Panel** for optional page previews

✅ **Web Scraping & Extraction** to pull clean text from sites
✅ **Readability Fallback** for difficult pages
✅ **Summarization Pipeline** that returns concise answers
✅ **Summary Caching** to avoid duplicate processing

✅ **Web Search Command** using DuckDuckGo results

✅ **Search Agent** supporting multiple providers

✅ **Persistent User Settings** with commands to save preferences

✅ **History Cleanup Commands** for chat and browsing data

🚧 **Plugin System** for web-focused automation *(simplified, single-user)*

✅ **Flavor System** for single-user plugin bundles

✅ **Offline Distribution** via USB/SD (optional)

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

## 🏗️ Architecture Overview

```
LibreAssistant/
├── frontend/          # Tauri + Svelte UI
│   ├── src/
│   ├── src-tauri/
│   └── static/
├── backend/           # Python backend
│   ├── agents/
│   ├── db/
│   ├── llm/
│   ├── utils/
│   └── main.py
└── shared/            # Shared configs
```

✅ **Frontend:** Tauri + Svelte for native desktop UI

✅ **Backend:** Python (FastAPI, SQLAlchemy)

✅ **Communication:** Native Rust ↔ Python bridge

✅ **AI Engine:** Ollama integration for local LLM

✅ **Database:** SQLite for encrypted local data

---

## 🔌 Modular Plugin System *(In Development)*

The plugin framework is currently being simplified for a single-user setup.
It will allow:

✅ Self-contained Python modules

✅ Registration of new backend commands and UI components

✅ User-contributed plugins

Examples:

* Note-taking / Reading plans
* Consent log management
* Recovery curriculum manager
* Scripture reference tools
* Web scraping and URL analysis
* Language phrasebook / translation helper

---

## 🧭 Flavor Configuration

Each Flavor is defined by a **config file** (e.g. `flavor.json`):

* Default plugins
* UI layout and components
* Localization and language settings

Example `flavor.json`:

```
{
  "name": "Faith & Community Memphis Edition",
  "plugins": ["note_manager", "reading_plan", "consent_log", "phrasebook"],
  "locale": "en-US"
}
```

✅ Fully offline

✅ USB/SD deployable (optional)

✅ Low-spec hardware friendly

✅ Supports local language customization

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
