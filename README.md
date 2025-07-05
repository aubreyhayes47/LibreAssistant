# LibreAssistant

An open-source AI assistant browser built with Tauri and Python, designed for privacy-focused AI interactions and web automation.

## 🚀 Features

- 🤖 **Local AI Integration**: Powered by Ollama for private AI conversations
- 🌐 **Web Automation**: Built-in web scraping and browser automation
- 📱 **Native Performance**: Tauri-based desktop application with Rust backend
- 🔒 **Privacy First**: All processing happens locally on your machine
- 🔧 **Extensible**: Modular Python backend for custom AI agents
- 💬 **Interactive Chat**: Real-time AI conversations with message history
- 🌍 **URL Processing**: Extract and analyze content from web pages
- 📊 **Browser Data**: Access browser history, bookmarks, and cookies

## 🏗️ Architecture

```
LibreAssistant/
├── frontend/          # Tauri + Svelte frontend
│   ├── src/          # Svelte source files
│   ├── src-tauri/    # Rust backend for Tauri
│   └── static/       # Static assets
├── backend/          # Python backend
│   ├── agents/       # AI agents
│   ├── db/           # Database modules
│   ├── llm/          # LLM integration
│   ├── utils/        # Utility functions
│   └── main.py       # Main entry point
└── shared/           # Shared configurations
```

**Technology Stack:**
- **Frontend**: Tauri + Svelte for native desktop UI
- **Backend**: Python with FastAPI, SQLAlchemy, and AI integrations
- **Communication**: High-performance native commands (Rust ↔ Python)
- **AI Engine**: Ollama integration for local LLM processing
- **Database**: SQLite for local data storage

## � Prerequisites

- **Rust**: Install from [rustup.rs](https://rustup.rs/)
- **Node.js**: LTS version (18+ recommended)
- **Python**: 3.10 or higher
- **Git**: For version control

## �️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/aubreyhayes47/LibreAssistant.git
   cd LibreAssistant
   ```

2. **Setup Frontend**:
   ```bash
   cd frontend
   npm install
   ```

3. **Setup Backend**:
   ```bash
   cd ../backend
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   
   # macOS/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

## 🚀 Development

### Start Development Server

1. **Start Frontend** (from `frontend/` directory):
   ```bash
   npm run tauri dev
   ```

The application will automatically communicate with the Python backend through Tauri native commands.

### Build for Production

```bash
cd frontend
npm run tauri build
```

## 🔧 Backend API

The Python backend provides several commands accessible through Tauri native commands:

### Available Commands

- **`hello`**: Test backend connectivity
- **`process_url`**: Extract content from URLs
- **`get_browser_data`**: Access browser history/bookmarks
- **`analyze_content`**: AI content analysis

### Command Structure

```rust
// Frontend command invocation
let response = invoke("command_name", { param: value }).await;
```

```python
# Backend receives
{
    "param": value,
    "timestamp": "unix_timestamp"
}

# Backend returns
{
    "success": true/false,
    "data": {...},
    "error": "error message if failed"
}
```

## 🧪 Testing

### Frontend Tests
```bash
cd frontend
npm test
```

### Backend Tests
```bash
cd backend
python -m pytest
```

## 📝 Configuration

### Environment Variables

Create `.env` files in the backend directory:

```env
# Backend settings
LOG_LEVEL=INFO
OLLAMA_HOST=http://localhost:11434

# Database settings
DATABASE_URL=sqlite:///./libreassistant.db
```

### Tauri Configuration

Edit `frontend/src-tauri/tauri.conf.json` for app settings:
- Window properties
- Security policies
- Build configurations

## 🔌 Extensions

### Adding New Backend Commands

1. **Add command to Python** (`backend/main.py`):
   ```python
   async def new_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
       # Implementation
       return {"success": True, "data": result}
   ```

2. **Register in command handler**:
   ```python
   self.commands['new_command'] = self.new_command
   ```

3. **Add Rust wrapper** (`frontend/src-tauri/src/lib.rs`):
   ```rust
   #[tauri::command]
   async fn new_command(param: String) -> Result<CommandResponse, String> {
       // Implementation
   }
   ```

4. **Register in Tauri**:
   ```rust
   .invoke_handler(tauri::generate_handler![
       // ... existing commands
       new_command
   ])
   ```

## 🤝 Contributing

LibreAssistant is open source and welcomes contributions! 

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

Please see our [Contributing Guidelines](CONTRIBUTING.md) for detailed information.

## 🚨 Troubleshooting

### Common Issues

1. **Python not found**: Ensure Python is in PATH and virtual environment is activated
2. **Rust compilation errors**: Update Rust toolchain with `rustup update`
3. **Frontend build fails**: Clear node_modules and reinstall dependencies

### Debugging

- **Frontend**: Use browser dev tools in Tauri app
- **Backend**: Check `backend.log` for Python errors
- **Communication**: Enable debug logging in Tauri config

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Tauri](https://tauri.app/) - Modern desktop app framework
- [Svelte](https://svelte.dev/) - Reactive UI framework
- [Ollama](https://ollama.ai/) - Local LLM integration
- [FastAPI](https://fastapi.tiangolo.com/) - Python web framework

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

---

**LibreAssistant** - Your privacy-first AI assistant browser. Built with ❤️ by the open source community.
