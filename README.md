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

✅ **Summarization Pipeline** that returns concise answers

✅ **Web Search Command** using DuckDuckGo results

✅ **Search Agent** supporting multiple providers

✅ **Persistent User Settings** with commands to save preferences

✅ **History Cleanup Commands** for chat and browsing data

✅ **Plugin System** for web-focused automation

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

## 🔌 Modular Plugin System

✅ Self-contained Python modules

✅ Register new backend commands and UI components

✅ Supports user-contributed plugins

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

### Clone the Repository

```
git clone https://github.com/aubreyhayes47/LibreAssistant.git
cd LibreAssistant
```

### Quick Setup

Install all Python and Node dependencies with the helper script:

```
./setup.sh
```

This creates a local virtual environment in `.venv/` and runs `npm install` in
`frontend/`. Activate the environment with `source .venv/bin/activate` after the
script finishes.

### Manual Setup Steps

If you prefer a manual approach you can still install each part individually:

```
cd frontend
npm install

cd ../backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🚀 Development

✅ Start Frontend (from `frontend/`):

```
npm run tauri dev
```

✅ Build for Production:

```
npm run tauri build
```

### Development Checks
Run the setup script once in a new environment and activate the virtual environment:

```bash
./setup.sh
source .venv/bin/activate
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

Phase **1C** (chat interface) is complete. Phase **1D** work has begun with a new
embedded browser preview component and a backend command for page summarization.
The app connects to Ollama locally, stores chat, bookmarks and history, and all
tests pass. See [TROUBLESHOOTING_PLAN](.github/TROUBLESHOOTING_PLAN.md) for the
latest progress details.

---

## 🔧 Backend API

The Python backend exposes commands accessible through Tauri:

✅ Sample Commands:

* `hello`: Test connectivity
* `process_url`: Extract web content
* `get_browser_data`: Access history/bookmarks
* `analyze_content`: AI content analysis
* `summarize_page`: Extract content and return a summary
* `search_web`: Query DuckDuckGo for web results

✅ Adding New Commands:

```python
async def new_command(self, payload):
    return { "success": True, "data": result }
```

Register in Tauri Rust:

```rust
#[tauri::command]
async fn new_command(param: String) -> Result<CommandResponse, String> {
    // Implementation
}
```

---

## 🧪 Testing

✅ Frontend:

```
cd frontend
npm test
```

✅ Backend:

```
cd backend
python -m pytest
```

---

## ⚙️ Configuration

✅ `.env` in `backend/`:

```
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

Please open an issue on GitHub or contact the development team.

LibreAssistant — *Your privacy-first AI gateway to the internet. Built with ❤️ and guided by the Beatitudes.*
