# User Onboarding Guide for LibreAssistant

## Welcome to LibreAssistant! 🎉

LibreAssistant is your privacy-first, local AI assistant that runs entirely on your machine. This guide will help you get started and make the most of its powerful features.

## Quick Start (5 minutes)

### 1. First Launch ✨
When you first open LibreAssistant:

1. **Check Ollama Connection**: The app will automatically try to connect to Ollama at `http://localhost:11434`
2. **Install Models**: If no models are found, you'll see a helpful guide to install your first model
3. **Plugin Discovery**: Available plugins will be automatically discovered and displayed

### 2. Your First Chat 💬
1. Navigate to the **Chat** section
2. Select a model from the dropdown (e.g., `llama2:latest`)
3. Type your message and press Enter
4. Watch as your local AI responds instantly!

### 3. Enable Your First Plugin 🔌
1. Go to the **Plugin Catalogue**
2. Find the "Local File I/O" plugin
3. Click **Enable** and configure the base directory
4. Now your AI can help you manage files!

## Core Features Overview

### 🤖 Model Management
- **Download Models**: Easy one-click model installation
- **Model Switching**: Switch between different AI models seamlessly
- **Resource Monitoring**: Keep track of model memory usage

### 🔌 Plugin System
- **Local File I/O**: Read, write, and manage files securely
- **Brave Search**: Search the web while maintaining privacy
- **CourtListener**: Access legal documents and case law
- **Custom Plugins**: Install community-created plugins

### 💬 Enhanced Chat
- **Structured Responses**: Plugins seamlessly integrate into conversations
- **Real-time Feedback**: See exactly when and how plugins are being used
- **Rich Formatting**: Support for markdown, code blocks, and more

### 🛡️ Privacy & Security
- **100% Local**: Everything runs on your machine
- **No Data Collection**: Your conversations never leave your device
- **Sandboxed Plugins**: Plugins run in secure, isolated environments
- **Explicit Permissions**: You control exactly what each plugin can access

## Detailed Feature Walkthrough

### Setting Up Ollama Models

#### Installing Your First Model
```bash
# In your terminal, install a lightweight model
ollama pull llama2:7b

# For better performance (if you have enough RAM)
ollama pull llama2:13b

# For coding tasks
ollama pull codellama:7b
```

#### Recommended Models for Different Tasks
- **General Chat**: `llama2:7b` or `llama2:13b`
- **Code Help**: `codellama:7b` or `codellama:13b`
- **Quick Responses**: `orca-mini:3b`
- **Advanced Tasks**: `llama2:70b` (requires significant RAM)

### Configuring Plugins

#### Local File I/O Plugin
**What it does**: Allows the AI to read, write, and manage files on your computer within a sandboxed directory.

**Setup Steps**:
1. Go to **Plugin Catalogue** → **Local File I/O**
2. Click **Configure**
3. Set your **Base Directory** (e.g., `/home/username/Documents/LibreAssistant`)
4. Click **Enable**

**Example Uses**:
- "Please read the content of my todo.txt file"
- "Create a new markdown file with meeting notes"
- "List all files in my projects directory"

#### Brave Search Plugin
**What it does**: Searches the web using Brave's privacy-focused search engine.

**Setup Steps**:
1. Get a free Brave Search API key from [Brave Search API](https://brave.com/search/api/)
2. Go to **Plugin Catalogue** → **Brave Search**
3. Enter your API key in the configuration
4. Click **Enable**

**Example Uses**:
- "What's the current weather in Tokyo?"
- "Find recent news about renewable energy"
- "Search for Python tutorials for beginners"

#### CourtListener Plugin
**What it does**: Searches legal databases for court opinions, cases, and legal documents.

**Setup Steps**:
1. Create a free account at [CourtListener](https://www.courtlistener.com/)
2. Generate an API token in your account settings
3. Configure the plugin with your token
4. Click **Enable**

**Example Uses**:
- "Find Supreme Court cases about privacy rights"
- "Search for recent federal court decisions on contract law"
- "Look up the full text of Brown v. Board of Education"

### Understanding the Interface

#### Navigation Bar
- **Chat**: Main conversation interface
- **Models**: Manage and download Ollama models
- **Plugin Catalogue**: Browse and configure available plugins
- **Monitoring**: View system performance and plugin activity
- **Settings**: Configure application preferences

#### Chat Interface Elements
- **Model Selector**: Choose which AI model to use
- **Plugin Support Toggle**: Enable/disable plugin integration for this conversation
- **Activity Bar**: Real-time display of active plugins during AI responses
- **Message History**: Persistent conversation history

#### Plugin Activity Indicators
- **Green Pill**: Plugin is actively processing
- **Blue Pill**: Plugin has completed successfully
- **Red Pill**: Plugin encountered an error
- **Click Pills**: View detailed logs and information

## Advanced Usage Tips

### 1. Plugin Chaining
LibreAssistant can use multiple plugins in sequence:

**Example**: "Search for Python file handling tutorials, then create a summary document in my notes folder"
1. Brave Search finds relevant tutorials
2. Local File I/O creates the summary file

### 2. Context Awareness
The AI maintains context across plugin operations:

**Example**: "Read my project readme file, then search for any mentioned dependencies that might have security issues"

### 3. Error Recovery
If a plugin fails, the AI gracefully handles the error:
- Explains what went wrong in user-friendly terms
- Suggests alternatives when possible
- Continues the conversation without breaking

### 4. Performance Optimization
- **Close Unused Plugins**: Stop plugins you're not using to free up resources
- **Monitor Resource Usage**: Check the Monitoring tab to see system performance
- **Choose Appropriate Models**: Smaller models for quick tasks, larger for complex reasoning

## Troubleshooting Common Issues

### Ollama Connection Issues
**Problem**: "Cannot connect to Ollama service"

**Solutions**:
1. Ensure Ollama is installed: [Download Ollama](https://ollama.ai/)
2. Start Ollama service: `ollama serve`
3. Check if running: `curl http://localhost:11434/api/tags`
4. Update Ollama host in Settings if using custom configuration

### Plugin Not Starting
**Problem**: Plugin shows "Failed to start"

**Solutions**:
1. Check plugin configuration (API keys, permissions)
2. Restart the plugin from the Plugin Catalogue
3. Check system logs in the Monitoring section
4. Ensure all required dependencies are installed

### Slow Performance
**Problem**: Responses are taking too long

**Solutions**:
1. Switch to a smaller model for faster responses
2. Close unnecessary plugins
3. Check system resources in Monitoring
4. Restart LibreAssistant if memory usage is high

### Plugin Permissions
**Problem**: "Access denied" or permission errors

**Solutions**:
1. Review plugin permissions in Plugin Catalogue
2. Ensure file paths are within configured sandbox directories
3. Check that API keys have sufficient permissions
4. Update plugin configuration if needed

## Security Best Practices

### 1. Plugin Permissions
- Only enable plugins you actually need
- Review what permissions each plugin requests
- Use sandboxed directories for file operations
- Regularly review enabled plugins

### 2. API Key Management
- Store API keys securely
- Use API keys with minimal required permissions
- Regularly rotate API keys
- Never share your LibreAssistant configuration files

### 3. File Access
- Configure restrictive base directories for file plugins
- Don't allow plugins access to system directories
- Regularly review file operations in the monitoring logs
- Backup important files before letting AI modify them

### 4. Network Security
- LibreAssistant only connects to:
  - Your local Ollama instance
  - Configured plugin APIs (with your consent)
- No telemetry or analytics are collected
- All processing happens locally

## Getting Help

### Built-in Resources
- **Help Tooltips**: Hover over UI elements for contextual help
- **Plugin Documentation**: Each plugin includes detailed usage guides
- **Error Messages**: Designed to be helpful and actionable
- **Activity Logs**: Detailed logs of all operations in Monitoring

### Community & Support
- **GitHub Issues**: Report bugs or request features
- **Documentation**: Comprehensive guides and API reference
- **Plugin Development**: Create your own plugins using the Plugin API guide

### Keyboard Shortcuts
- **Ctrl/Cmd + Enter**: Send chat message
- **Ctrl/Cmd + K**: Focus chat input
- **Ctrl/Cmd + ,**: Open settings
- **Ctrl/Cmd + Shift + P**: Toggle plugin support
- **Escape**: Close modals and overlays

## What's Next?

### Immediate Next Steps
1. **Install Additional Models**: Try different models for various tasks
2. **Configure More Plugins**: Enable Brave Search and other plugins
3. **Explore Advanced Features**: Try complex multi-plugin workflows
4. **Customize Settings**: Adjust themes, timeouts, and preferences

### Advanced Features to Explore
- **Custom Plugin Development**: Create plugins for your specific needs
- **Automation Workflows**: Chain multiple operations together
- **Performance Monitoring**: Optimize your setup for your hardware
- **Security Hardening**: Review and tighten security settings

### Stay Updated
- Check for LibreAssistant updates regularly
- Monitor the plugin catalogue for new community plugins
- Follow the project on GitHub for feature announcements
- Join the community discussions for tips and tricks

## Welcome Aboard! 🚀

You're now ready to explore the full power of LibreAssistant. Remember:
- **Your privacy is protected** - everything runs locally
- **Start simple** - begin with basic chat and add plugins gradually
- **Experiment freely** - you can't break anything, it's all sandboxed
- **Ask for help** - both the AI and the community are here to help

Enjoy your journey with LibreAssistant, your powerful, private, and local AI assistant!