# LibreAssistant User Guide

Welcome to LibreAssistant! This guide will help you get started with your privacy-first AI assistant.

## What is LibreAssistant?

LibreAssistant is a desktop AI assistant that runs entirely on your computer. Unlike cloud-based assistants, LibreAssistant:

- **Keeps your data private** - All processing happens locally
- **Works offline** - No internet required for AI features (after initial setup)
- **Gives you control** - You own your data and conversations
- **Respects your privacy** - No tracking, no data collection

**Current Status**: LibreAssistant is currently a proof-of-concept (15-20% complete) with basic AI chat and web scraping capabilities. Many advanced features described in this guide are planned but not yet implemented. See the [Implementation Roadmap](../IMPLEMENTATION_ROADMAP.md) for development progress.

## Getting Started

### System Requirements

**Minimum:**
- 8GB RAM
- 10GB free disk space
- Modern CPU (2017 or newer)
- Ollama installed and running

**Current Limitations:**
- No conversation persistence (data lost on restart)
- Basic web scraping only (no JavaScript rendering)
- No user settings persistence
- Limited error handling

**Recommended:**
- 16GB RAM
- 50GB free disk space
- Dedicated GPU (optional, for faster AI)

## Main Interface

### Chat Panel

The main area where you interact with the AI:

- **Message Input** - Type your questions at the bottom
- **Conversation History** - All messages displayed chronologically
- **Context Indicators** - Shows when AI is thinking or searching web

### Browser Panel

Integrated web browsing capabilities:

- **Address Bar** - Navigate to any website
- **Content Extraction** - AI can read and summarize pages
- **Search Integration** - Search results automatically analyzed
- **Privacy Mode** - No cookies or tracking stored

### Settings Panel

Customize your LibreAssistant experience:

- **AI Model Selection** - Choose between different models
- **Privacy Controls** - Manage data retention
- **Interface Preferences** - Themes, font size, etc.
- **Performance Settings** - Memory usage, cache settings

## Basic Features (Currently Available)

### Asking Questions

Simply type your question and press Enter:

```
You: "What is machine learning?"
AI: "Machine learning is a branch of artificial intelligence..."
```

**Current Capabilities:**
- Basic AI chat through Ollama integration
- Simple web search via DuckDuckGo
- Basic content extraction from web pages
- Structured JSON responses

**Limitations:**
- No conversation history (resets on restart)
- Basic web scraping (no JavaScript support)
- No session management
- Limited error recovery

### Web Search and Analysis (Basic)

LibreAssistant can perform basic web searches:

```
You: "Search for latest developments in renewable energy"
AI: [Searches web, provides basic analysis]
"Based on search results, here are the key developments..."
```

**Current Features:**
- DuckDuckGo search integration
- Basic content extraction
- Simple result processing

**Planned Features (Not Yet Implemented):**
- Advanced content analysis
- Multi-source verification
- Intelligent summarization
- Content caching

## Advanced Features (Planned - Not Yet Implemented)

The following features are planned but not currently available. See the [Implementation Roadmap](../IMPLEMENTATION_ROADMAP.md) for development timeline.

### Conversation Context (Planned)
- Session-based conversation memory
- Context preservation across restarts
- Conversation threading and branching

### Content Summarization (Planned)
- Advanced web page analysis
- Multi-source content aggregation
- Intelligent content extraction

### Personal Preferences (Planned)
- Persistent user settings
- Custom prompt templates
- Interface customization

### Data Management (Planned)
- Conversation export/import
- Privacy controls
- Data retention policies

## AI Models (Current Implementation)

### Available Integration

LibreAssistant works with Ollama for local AI processing:

**Current Implementation:**
- Basic Ollama client integration
- Simple model communication
- Local processing (privacy-preserving)

**Model Requirements:**
- Ollama must be installed and running
- Models downloaded via Ollama CLI
- Sufficient RAM for model operation

### Model Selection (Planned)

**Future Capabilities (Not Yet Implemented):**
- In-app model management
- Automatic model switching
- Performance optimization
- Model health monitoring

### Performance (Current Limitations)

**Current State:**
- Basic connection to Ollama
- No connection pooling
- Limited error handling
- No response optimization

**Planned Improvements:**
- Connection pooling for better performance
- Response caching
- Streaming responses
- Advanced error recovery

## Privacy and Security (Current Implementation)

### What Data is Currently Stored

LibreAssistant currently stores minimal data:

- **Session Data** - Only during current session (lost on restart)
- **No Persistent Storage** - No database persistence implemented
- **Local Processing** - AI operations happen on your device
- **No External Transmission** - Data doesn't leave your computer

### Current Privacy Features

- **Local Processing**: All AI operations happen locally
- **No Cloud Dependencies**: No external API calls for AI
- **Session-Only Storage**: Data cleared when application closes
- **Open Source**: Code is publicly auditable

### Current Limitations

- **No Data Persistence**: Conversations not saved between sessions
- **No Privacy Controls**: Basic implementation only
- **No Encryption**: No encryption at rest implemented
- **No Data Management**: No export/import capabilities

### Planned Privacy Features (Not Yet Implemented)

See the [Implementation Roadmap](../IMPLEMENTATION_ROADMAP.md) for planned privacy enhancements:

- **Database Encryption**: At-rest encryption with SQLCipher
- **Secure Deletion**: Cryptographic data wiping
- **Privacy Controls**: Granular data management
- **Audit Logging**: Privacy-preserving activity logs
- **Data Export**: User-controlled data portability

## Troubleshooting (Current Issues)

### Common Issues

**AI Not Responding:**
1. Check if Ollama is running
2. Verify model is downloaded via `ollama list`
3. Restart Ollama service
4. Restart LibreAssistant

**Application Crashes:**
1. Check console logs for errors
2. Verify all dependencies installed
3. Try running from terminal for debug output
4. Report issues on GitHub

**Web Search Not Working:**
1. Check internet connection
2. Verify firewall settings allow connections
3. Try different search terms
4. Check for proxy interference

**Performance Issues:**
1. Close other applications to free RAM
2. Ensure Ollama has sufficient resources
3. Try smaller AI models if available
4. Monitor system resource usage

### Current Limitations to Expect

- **Data Loss on Restart**: No conversation persistence
- **Basic Error Messages**: Limited error handling
- **No Settings Persistence**: Preferences reset on restart
- **Limited Web Scraping**: Some sites may not work properly
- **No Session Recovery**: Cannot resume previous conversations

### Getting Help

**For Current Issues:**
- Check [Troubleshooting Guide](../../TROUBLESHOOTING.md)
- Search [GitHub Issues](https://github.com/yourusername/LibreAssistant/issues)
- Create new issue if problem persists

**For Development Progress:**
- See [Implementation Roadmap](../IMPLEMENTATION_ROADMAP.md)
- Check [Current TODO](../../TODO.md)
- Follow project updates

## Tips and Best Practices

### Effective Prompts

**Be Specific:**
```
❌ "Tell me about AI"
✅ "Explain how neural networks learn from data"
```

**Provide Context:**
```
❌ "How do I fix this?"
✅ "How do I fix a Python ImportError when using pandas?"
```

**Ask Follow-ups:**
```
"Can you give me an example?"
"What are the advantages and disadvantages?"
"How does this compare to alternatives?"
```

### Workflow Tips

**Research Tasks:**
1. Start with broad search
2. Ask for specific aspects
3. Request comparisons
4. Get practical examples

**Learning:**
1. Ask for explanations
2. Request examples
3. Test understanding with questions
4. Ask for practice exercises

**Problem Solving:**
1. Describe the problem clearly
2. Share what you've tried
3. Ask for step-by-step solutions
4. Verify understanding

### Privacy Best Practices

- **Review Settings** - Regularly check privacy settings
- **Clear Data** - Remove old conversations periodically
- **Update Regularly** - Keep LibreAssistant updated
- **Monitor Usage** - Be aware of what you're sharing

## Keyboard Shortcuts

### Chat Interface

- **Ctrl+Enter** - Send message
- **Ctrl+K** - Clear current conversation
- **Ctrl+H** - Show/hide chat history
- **Ctrl+/** - Show help overlay

### Browser Panel

- **Ctrl+L** - Focus address bar
- **Ctrl+R** - Refresh page
- **Ctrl+F** - Find in page
- **Ctrl+T** - New tab

### General

- **Ctrl+,** - Open settings
- **Ctrl+Q** - Quit application
- **F11** - Toggle fullscreen
- **Ctrl+Shift+I** - Developer tools (debug mode)

## Customization

### Themes

LibreAssistant supports multiple themes:

- **Light Theme** - Clean, bright interface
- **Dark Theme** - Easy on the eyes
- **High Contrast** - Better accessibility
- **Custom Themes** - Create your own

### Font Settings

Adjust text appearance:

- **Font Size** - From 12px to 24px
- **Font Family** - System fonts or custom
- **Line Height** - For better readability
- **Code Font** - Monospace for code blocks

### Layout Options

Customize the interface:

- **Panel Arrangement** - Side-by-side or stacked
- **Chat Bubble Style** - Different conversation styles
- **Sidebar Width** - Adjust panel sizes
- **Toolbar Visibility** - Show/hide UI elements

## Updates and Maintenance

### Automatic Updates

LibreAssistant checks for updates:

- **Security Updates** - Automatic installation
- **Feature Updates** - User notification
- **Model Updates** - Ollama model updates
- **Settings Backup** - Before major updates

### Manual Maintenance

Regular maintenance tasks:

- **Clear Cache** - Free up disk space
- **Update Models** - Get latest AI improvements
- **Backup Data** - Export important conversations
- **Check Logs** - Monitor for issues

### Version Information

Check your version:

1. Go to Settings → About
2. View current version number
3. Check for available updates
4. Review changelog for new features

This user guide helps you make the most of LibreAssistant while maintaining your privacy and security. For additional help, consult the troubleshooting section or reach out to our community.
