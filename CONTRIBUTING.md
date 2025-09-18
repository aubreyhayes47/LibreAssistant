# Contributing to LibreAssistant

Thank you for your interest in contributing to LibreAssistant! LibreAssistant is a privacy-first, fully local AI assistant built with Flask. It provides model management and plugin capabilities through a modern web interface.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Contributing New Plugins](#contributing-new-plugins)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) to keep our community welcoming and inclusive.

## Getting Started

### Prerequisites

1. **Python 3.8+** with pip
2. **Git** for version control
3. **[Ollama](https://ollama.ai/)** installed and running locally

### Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/LibreAssistant.git
   cd LibreAssistant
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the development server:
   ```bash
   python main.py
   ```

4. Open your browser to `http://localhost:5000`

## Development Workflow

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make your changes** and test locally

3. **Run tests** to ensure nothing is broken:
   ```bash
   python test_ollama_manager.py
   ```

4. **Commit your changes** with clear messages:
   ```bash
   git commit -m "Add: description of your changes"
   ```

5. **Push to your fork** and submit a pull request

## Contributing New Plugins

LibreAssistant supports a robust plugin system (MCP servers). To contribute a new plugin:

1. **Structure:** Place your plugin in `plugins/your-plugin-name/`
2. **Manifest:** Include a `plugin-manifest.json` file (see [PLUGIN_API.md](./PLUGIN_API.md))
3. **Server:** Provide a `server.py` implementing the MCP server protocol
4. **Testing:** Add tests for your plugin functionality
5. **Documentation:** Document endpoints, configuration, and permissions
6. **Security:** Validate input and implement appropriate access controls

For full details, see the [PLUGIN_API.md](./PLUGIN_API.md) file.

## Testing Guidelines

### Running Tests

```bash
# Run all tests
python test_ollama_manager.py

# Test specific functionality
python -m pytest tests/ -v  # if using pytest
```

### Writing Tests

- Write tests for new features and bug fixes
- Follow existing test patterns in `test_ollama_manager.py`
- Test both success and error cases
- Mock external dependencies (Ollama API calls)

## Pull Request Process

1. **Update documentation** if your changes affect user-facing features
2. **Add tests** for new functionality
3. **Ensure all tests pass** before submitting
4. **Write a clear PR description** explaining your changes
5. **Link relevant issues** using GitHub keywords
6. **Be responsive** to review feedback

### PR Checklist

- [ ] Tests pass: `python test_ollama_manager.py`
- [ ] Code follows project style
- [ ] Documentation updated if needed
- [ ] No sensitive information committed
- [ ] Feature works in Flask web interface

## Project Structure

```
LibreAssistant/
├── static/                 # Static assets (CSS, JS)
├── templates/              # Flask templates
├── plugins/               # Plugin directory
├── main.py                # Flask application entry
├── ollama_manager.py      # Core Flask app
├── requirements.txt       # Python dependencies
└── tests/                 # Test files
```

## Coding Standards

### Python Code

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings for public functions
- Handle errors gracefully
- Use type hints where appropriate

### Frontend Code (JavaScript/CSS)

- Use modern JavaScript (ES6+)
- Follow consistent naming conventions
- Comment complex logic
- Ensure responsive design
- Test in multiple browsers

## Getting Help

If you need help or have questions:

1. Check existing [issues](https://github.com/aubreyhayes47/LibreAssistant/issues)
2. Review the [README](./README.md) and documentation
3. Create a new issue with detailed information
4. Join discussions in existing issues

## Recognition

Contributors will be recognized in our [README](./README.md) and release notes. Thank you for helping make LibreAssistant better!