# LibreAssistant Agents Module

⚠️ **Implementation Status**: This module describes current basic implementations and planned advanced features.

🟢 **Currently Working**: Basic web search via DuckDuckGo, simple content extraction  
🟡 **Partially Working**: Content cleaning, Playwright scraping  
🔴 **Planned**: Multi-provider search, advanced content analysis, intelligent agents

This module contains the search and web automation agents for LibreAssistant.

## Current vs Planned Features

**Current Implementation:**
- Basic DuckDuckGo search integration
- Simple content extraction with Playwright
- Manual result processing
- Basic content cleaning

**Planned Enhancements:**
- **Phase 1.2**: Multi-provider search aggregation
- **Phase 1.3**: Intelligent result ranking and filtering
- **Phase 1.4**: Advanced content analysis and categorization  
- **Phase 2**: Autonomous research agents, browser automation

See the [Implementation Roadmap](../IMPLEMENTATION_ROADMAP.md) for detailed development timeline.

## Overview

The agents module provides intelligent web search and content extraction capabilities while maintaining LibreAssistant's privacy-first approach.

## Components

### Search Agent (`search_agent.py`)

Handles web search operations using multiple providers:

```python
# Example usage
from backend.agents.search_agent import search_web

results = await search_web("AI privacy tools", max_results=5)
```

**Features:**
- DuckDuckGo search integration
- Result filtering and ranking
- Privacy-preserving search (no tracking)
- Configurable result limits

**Configuration:**
- `SEARCH_MAX_RESULTS`: Maximum search results (default: 10)
- `SEARCH_TIMEOUT`: Request timeout in seconds (default: 30)

### Content Extractor (`content_extractor.py`)

Extracts clean content from web pages:

```python
# Example usage
from backend.agents.content_extractor import extract_content

content = await extract_content("https://example.com")
```

**Features:**
- Playwright-based scraping
- Readability fallback for difficult pages
- Content cleaning and formatting
- Image and media handling

## Integration Points

### With LLM Module
- Search results feed into summarization pipeline
- Content extraction provides context for AI responses

### With Database
- Search history and preferences stored locally
- Content caching for performance

### With Frontend
- Tauri commands expose agent functionality
- Real-time progress updates during operations

## Privacy Considerations

- No user data sent to external services
- Search queries not logged or tracked
- Content processing happens locally
- No persistent cookies or sessions

## Development

### Adding New Search Providers

1. Create provider class implementing `SearchProvider` interface
2. Add provider configuration to settings
3. Register provider in search agent
4. Update tests and documentation

### Testing

```bash
# Run agent tests
cd backend
python -m pytest agents/tests/
```

## Error Handling

All agent operations return structured responses:

```python
{
    "success": True,
    "data": {...},
    "error": None
}
```

Common error scenarios:
- Network timeouts
- Invalid URLs
- Content extraction failures
- Rate limiting

## API Reference

### SearchAgent Class

#### Methods

**search_web(query: str, max_results: int = 10) -> dict**
- Performs web search using configured providers
- Returns structured search results
- Handles pagination and filtering

**get_search_suggestions(query: str) -> list**
- Returns search query suggestions
- Based on query patterns and history
- Privacy-preserving implementation

### ContentExtractor Class

#### Methods

**extract_content(url: str) -> dict**
- Extracts main content from web page
- Returns cleaned text and metadata
- Handles various content types

**extract_with_context(url: str, context: str) -> dict**
- Context-aware content extraction
- Focuses on relevant sections
- Enhanced accuracy for specific queries

## Configuration

### Environment Variables

```bash
# Search configuration
SEARCH_PROVIDER=duckduckgo
SEARCH_MAX_RESULTS=10
SEARCH_TIMEOUT=30

# Content extraction
EXTRACTION_TIMEOUT=60
READABILITY_FALLBACK=true
CONTENT_CACHE_TTL=3600
```

### Agent Settings

```python
# In backend/utils/config.py
AGENT_CONFIG = {
    "search": {
        "providers": ["duckduckgo"],
        "max_results": 10,
        "timeout": 30,
        "rate_limit": {
            "requests_per_minute": 30,
            "burst_size": 5
        }
    },
    "extraction": {
        "timeout": 60,
        "fallback_enabled": True,
        "cache_ttl": 3600,
        "max_content_length": 1000000
    }
}
```

## Performance Optimization

### Caching Strategy

- Search results cached for repeat queries
- Content extraction cached by URL
- Configurable TTL for different content types

### Rate Limiting

- Built-in rate limiting for external requests
- Respectful crawling practices
- Backoff strategies for failed requests

### Resource Management

- Connection pooling for HTTP requests
- Memory-efficient content processing
- Cleanup of temporary files

## Security Features

### Input Validation

- URL validation and sanitization
- Query parameter filtering
- Content-length limits

### Sandboxing

- Isolated browsing environment
- No execution of external scripts
- Safe content processing

## Examples

### Basic Search

```python
from backend.agents.search_agent import SearchAgent

agent = SearchAgent()
results = await agent.search_web("machine learning tutorials")

for result in results['data']:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Snippet: {result['snippet']}")
```

### Content Extraction with Caching

```python
from backend.agents.content_extractor import ContentExtractor

extractor = ContentExtractor()

# First call - extracts and caches
content = await extractor.extract_content("https://example.com/article")

# Second call - returns cached content
cached_content = await extractor.extract_content("https://example.com/article")
```

### Combined Search and Extract

```python
async def search_and_extract(query: str, num_results: int = 3):
    # Search for relevant pages
    search_agent = SearchAgent()
    search_results = await search_agent.search_web(query, num_results)
    
    # Extract content from top results
    extractor = ContentExtractor()
    extracted_content = []
    
    for result in search_results['data']:
        content = await extractor.extract_content(result['url'])
        if content['success']:
            extracted_content.append({
                'title': result['title'],
                'url': result['url'],
                'content': content['data']['text']
            })
    
    return extracted_content
```

This module enables LibreAssistant to intelligently search and extract web content while maintaining privacy and providing reliable, structured data for AI processing.
