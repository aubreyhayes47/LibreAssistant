# 📜 LibreAssistant

An open-source, privacy-first AI assistant platform built with Tauri, Svelte, Rust, and Python. Designed for **local-first AI**, **web automation**, and **customizable Flavors** that serve real communities—especially those most overlooked.

---

## ✝️ Mission

LibreAssistant is more than a single app—it's a **flexible, modular platform** for building secure, local-first AI tools that *respect privacy* and *empower service*.

Our goal is to support **families, churches, schools, clinics, nonprofits, and small businesses**—especially in low-resource or disconnected environments.

> *“Serve the least, the last, and the lost—locally and globally.”*

---

## 🚀 Features

✅ **Local AI Integration** with Ollama for private, on-device conversations

✅ **Web Automation** with scraping and browser control

✅ **Modular Plugin System** for adding custom tools

✅ **Privacy First** with no mandatory cloud

✅ **Role-Based Access Control (RBAC)** for multi-user setups

✅ **Flavor System** for audience-specific configurations

✅ **USB/SD Distribution** for offline use

---

## 🌍 Example Flavors

LibreAssistant is designed to be **configured** for specific audiences and use cases through "Flavors"—predefined bundles of plugins, UI layouts, and permissions.

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
* User roles and permissions
* Localization and language settings

Example `flavor.json`:

```
{
  "name": "Faith & Community Memphis Edition",
  "plugins": ["note_manager", "reading_plan", "consent_log", "phrasebook"],
  "roles": ["Admin", "Guest"],
  "locale": "en-US"
}
```

✅ Fully offline

✅ USB/SD deployable

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
Run the setup script once in a new environment:

```bash
./setup.sh
```

Before committing run:

```bash
cd backend && black . && ruff --fix . && python -m pytest
cd ../frontend && npm install && npm run check
```

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

LibreAssistant — *Your privacy-first, modular AI assistant platform. Built with ❤️ and guided by the Beatitudes.*
