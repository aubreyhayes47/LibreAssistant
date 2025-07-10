# LibreAssistant Testing Guide

⚠️ **Testing Status**: LibreAssistant is in proof-of-concept state with basic testing infrastructure.

🟢 **Currently Working**: Basic backend tests with pytest  
🟡 **Partially Working**: Manual integration testing  
🔴 **Planned**: Comprehensive test suite, automated CI/CD testing

This guide covers testing strategies, tools, and best practices for LibreAssistant development.

## Current vs Planned Testing

**Current Implementation:**
- Basic pytest backend tests (`test_backend_simple.py`, `test_backend.py`)
- Manual integration testing through UI
- Simple command validation tests

**Planned Testing Infrastructure:**
- **Phase 1.2**: Comprehensive unit test suite
- **Phase 1.3**: Automated integration testing  
- **Phase 1.4**: End-to-end test automation with Playwright
- **Phase 2**: Performance and security testing suites

See the [Implementation Roadmap](../IMPLEMENTATION_ROADMAP.md) for detailed testing development timeline.

## Testing Strategy

LibreAssistant uses a multi-layered testing approach:

1. **Unit Tests** - Individual function/component testing
2. **Integration Tests** - Module interaction testing
3. **End-to-End Tests** - Full user workflow testing
4. **Performance Tests** - Speed and resource usage testing
5. **Security Tests** - Privacy and vulnerability testing

## Test Structure

### Backend Testing

```
backend/tests/
├── unit/
│   ├── test_agents.py
│   ├── test_db.py
│   ├── test_llm.py
│   └── test_utils.py
├── integration/
│   ├── test_command_handlers.py
│   ├── test_agent_pipeline.py
│   └── test_db_operations.py
├── e2e/
│   ├── test_full_workflow.py
│   └── test_user_scenarios.py
└── fixtures/
    ├── sample_data.json
    └── mock_responses.py
```

### Frontend Testing

```
frontend/src/tests/
├── unit/
│   ├── components/
│   ├── services/
│   └── utils/
├── integration/
│   ├── tauri-commands/
│   └── store-integration/
└── e2e/
    ├── user-flows/
    └── browser-automation/
```

## Running Tests

### Backend Tests

**All Tests:**
```bash
cd backend
python -m pytest
```

**Specific Test Categories:**
```bash
# Unit tests only
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# End-to-end tests
python -m pytest tests/e2e/

# With coverage
python -m pytest --cov=. --cov-report=html

# Parallel execution
python -m pytest -n auto
```

### Frontend Tests

**All Tests:**
```bash
cd frontend
npm test
```

**Specific Test Types:**
```bash
# Unit tests
npm run test:unit

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# Watch mode
npm run test:watch
```

### Full Test Suite

**Complete Testing:**
```bash
# Run all tests across the project
make test

# Or manually:
cd backend && python -m pytest
cd frontend && npm test
```

## Unit Testing

### Backend Unit Tests

**Testing Agents:**
```python
# tests/unit/test_agents.py
import pytest
from unittest.mock import Mock, patch
from backend.agents.search_agent import SearchAgent

class TestSearchAgent:
    @pytest.fixture
    def search_agent(self):
        return SearchAgent()
    
    @patch('backend.agents.search_agent.httpx.get')
    async def test_search_web_success(self, mock_get, search_agent):
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {"title": "Test", "url": "http://test.com", "snippet": "Test snippet"}
            ]
        }
        mock_get.return_value = mock_response
        
        # Test search
        result = await search_agent.search_web("test query")
        
        # Assertions
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["title"] == "Test"
    
    async def test_search_web_empty_query(self, search_agent):
        result = await search_agent.search_web("")
        assert result["success"] is False
        assert "empty" in result["error"].lower()
```

**Testing Database Operations:**
```python
# tests/unit/test_db.py
import pytest
import asyncio
from backend.db.database import DatabaseManager

class TestDatabaseManager:
    @pytest.fixture
    async def db_manager(self):
        db = DatabaseManager(":memory:")  # In-memory database for tests
        await db.initialize()
        yield db
        await db.close()
    
    async def test_save_conversation(self, db_manager):
        # Test conversation saving
        await db_manager.save_conversation(
            session_id="test_session",
            user_message="Hello",
            assistant_response="Hi there!"
        )
        
        # Verify saved
        conversations = await db_manager.get_conversation_history("test_session")
        assert len(conversations) == 1
        assert conversations[0]["user_message"] == "Hello"
    
    async def test_user_settings(self, db_manager):
        # Test setting save/retrieve
        await db_manager.save_setting("test_key", "test_value")
        value = await db_manager.get_setting("test_key")
        assert value == "test_value"
        
        # Test default value
        default_value = await db_manager.get_setting("nonexistent", "default")
        assert default_value == "default"
```

### Frontend Unit Tests

**Testing Svelte Components:**
```javascript
// src/tests/unit/components/ChatPanel.test.js
import { render, fireEvent } from '@testing-library/svelte';
import ChatPanel from '$lib/components/ChatPanel.svelte';

describe('ChatPanel', () => {
  test('renders message input', () => {
    const { getByPlaceholderText } = render(ChatPanel);
    const input = getByPlaceholderText('Type your message...');
    expect(input).toBeInTheDocument();
  });
  
  test('sends message on enter', async () => {
    const { getByPlaceholderText, getByRole } = render(ChatPanel);
    const input = getByPlaceholderText('Type your message...');
    
    await fireEvent.input(input, { target: { value: 'Test message' } });
    await fireEvent.keyDown(input, { key: 'Enter' });
    
    // Verify message was processed
    expect(getByRole('log')).toContainHTML('Test message');
  });
  
  test('displays AI response', async () => {
    const { component, getByRole } = render(ChatPanel);
    
    // Simulate AI response
    await component.$set({
      messages: [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hi there!' }
      ]
    });
    
    expect(getByRole('log')).toContainHTML('Hi there!');
  });
});
```

**Testing API Services:**
```javascript
// src/tests/unit/services/api.test.js
import { invoke } from '@tauri-apps/api/core';
import { chatWithAI, searchWeb } from '$lib/services/api.js';

// Mock Tauri invoke
jest.mock('@tauri-apps/api/core');

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('chatWithAI calls correct command', async () => {
    const mockResponse = { success: true, data: { response: 'Test response' } };
    invoke.mockResolvedValue(mockResponse);
    
    const result = await chatWithAI('Test message', 'session_123');
    
    expect(invoke).toHaveBeenCalledWith('chat_with_ai', {
      message: 'Test message',
      sessionId: 'session_123'
    });
    expect(result).toEqual(mockResponse);
  });
  
  test('handles API errors gracefully', async () => {
    invoke.mockRejectedValue(new Error('Connection failed'));
    
    const result = await chatWithAI('Test message');
    
    expect(result.success).toBe(false);
    expect(result.error).toContain('Connection failed');
  });
});
```

## Integration Testing

### Backend Integration Tests

**Testing Command Handlers:**
```python
# tests/integration/test_command_handlers.py
import pytest
import json
from backend.main import handle_command

class TestCommandHandlers:
    async def test_chat_command_flow(self):
        # Test complete chat flow
        command_data = {
            "command": "chat_with_ai",
            "data": {
                "message": "What is AI?",
                "session_id": "test_session"
            }
        }
        
        result = await handle_command(json.dumps(command_data))
        response = json.loads(result)
        
        assert response["success"] is True
        assert "data" in response
        assert len(response["data"]["response"]) > 0
    
    async def test_search_and_analyze_flow(self):
        # Test search + analysis pipeline
        command_data = {
            "command": "search_and_analyze",
            "data": {
                "query": "machine learning basics",
                "max_results": 3
            }
        }
        
        result = await handle_command(json.dumps(command_data))
        response = json.loads(result)
        
        assert response["success"] is True
        assert "search_results" in response["data"]
        assert "analysis" in response["data"]
```

**Testing Agent Pipeline:**
```python
# tests/integration/test_agent_pipeline.py
import pytest
from backend.agents.search_agent import SearchAgent
from backend.agents.content_extractor import ContentExtractor
from backend.llm.ollama_client import OllamaClient

class TestAgentPipeline:
    @pytest.fixture
    async def agents(self):
        return {
            "search": SearchAgent(),
            "extractor": ContentExtractor(),
            "llm": OllamaClient()
        }
    
    async def test_complete_research_pipeline(self, agents):
        # 1. Search for content
        search_results = await agents["search"].search_web("Python tutorials")
        assert search_results["success"] is True
        
        # 2. Extract content from first result
        first_url = search_results["data"][0]["url"]
        content = await agents["extractor"].extract_content(first_url)
        assert content["success"] is True
        
        # 3. Summarize extracted content
        summary = await agents["llm"].generate(
            f"Summarize this content: {content['data']['text'][:1000]}"
        )
        assert "text" in summary
        assert len(summary["text"]) > 0
```

### Frontend Integration Tests

**Testing Tauri Commands:**
```javascript
// src/tests/integration/tauri-commands/chat.test.js
import { invoke } from '@tauri-apps/api/core';

describe('Chat Command Integration', () => {
  test('chat command returns valid response', async () => {
    const result = await invoke('chat_with_ai', {
      message: 'Hello',
      sessionId: 'test_session'
    });
    
    expect(result.success).toBe(true);
    expect(result.data).toHaveProperty('response');
    expect(typeof result.data.response).toBe('string');
  });
  
  test('invalid command returns error', async () => {
    try {
      await invoke('nonexistent_command', {});
    } catch (error) {
      expect(error).toBeDefined();
    }
  });
});
```

## End-to-End Testing

### User Workflow Tests

```python
# tests/e2e/test_user_scenarios.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestUserScenarios:
    @pytest.fixture
    def driver(self):
        # Setup WebDriver for LibreAssistant
        options = webdriver.ChromeOptions()
        options.add_argument("--app=http://localhost:1420")  # Tauri dev server
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()
    
    def test_complete_chat_flow(self, driver):
        # Navigate to app
        driver.get("http://localhost:1420")
        
        # Wait for app to load
        wait = WebDriverWait(driver, 10)
        chat_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='chat-input']"))
        )
        
        # Send message
        chat_input.send_keys("What is machine learning?")
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-button']")
        send_button.click()
        
        # Wait for response
        response = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='ai-response']"))
        )
        
        assert "machine learning" in response.text.lower()
    
    def test_web_search_integration(self, driver):
        driver.get("http://localhost:1420")
        wait = WebDriverWait(driver, 10)
        
        # Open browser panel
        browser_tab = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='browser-tab']"))
        )
        browser_tab.click()
        
        # Search for content
        search_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='search-input']"))
        )
        search_input.send_keys("AI news")
        
        search_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='search-button']")
        search_button.click()
        
        # Verify results loaded
        results = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='search-result']"))
        )
        
        assert len(results) > 0
```

### Playwright E2E Tests

```javascript
// src/tests/e2e/user-flows/chat-flow.spec.js
import { test, expect } from '@playwright/test';

test.describe('Chat Flow', () => {
  test('user can send message and receive response', async ({ page }) => {
    await page.goto('http://localhost:1420');
    
    // Wait for app to load
    await page.waitForSelector('[data-testid="chat-input"]');
    
    // Send message
    await page.fill('[data-testid="chat-input"]', 'Hello, can you help me?');
    await page.click('[data-testid="send-button"]');
    
    // Wait for response
    await page.waitForSelector('[data-testid="ai-response"]', { timeout: 30000 });
    
    const response = await page.textContent('[data-testid="ai-response"]');
    expect(response).toBeTruthy();
    expect(response.length).toBeGreaterThan(0);
  });
  
  test('conversation context is maintained', async ({ page }) => {
    await page.goto('http://localhost:1420');
    
    // First message
    await page.fill('[data-testid="chat-input"]', 'My name is Alice');
    await page.click('[data-testid="send-button"]');
    await page.waitForSelector('[data-testid="ai-response"]');
    
    // Follow-up message
    await page.fill('[data-testid="chat-input"]', 'What is my name?');
    await page.click('[data-testid="send-button"]');
    await page.waitForSelector('[data-testid="ai-response"]:nth-child(4)');
    
    const response = await page.textContent('[data-testid="ai-response"]:nth-child(4)');
    expect(response.toLowerCase()).toContain('alice');
  });
});
```

## Performance Testing

### Load Testing

```python
# tests/performance/test_load.py
import pytest
import asyncio
import time
from backend.main import handle_command

class TestPerformance:
    async def test_concurrent_chat_requests(self):
        """Test handling multiple simultaneous chat requests"""
        
        async def chat_request():
            command_data = {
                "command": "chat_with_ai",
                "data": {
                    "message": "What is 2+2?",
                    "session_id": f"session_{time.time()}"
                }
            }
            start = time.time()
            result = await handle_command(json.dumps(command_data))
            end = time.time()
            return end - start, json.loads(result)
        
        # Run 10 concurrent requests
        tasks = [chat_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify all succeeded
        for duration, response in results:
            assert response["success"] is True
            assert duration < 30  # Should complete within 30 seconds
        
        # Check average response time
        avg_time = sum(r[0] for r in results) / len(results)
        assert avg_time < 10  # Average should be under 10 seconds
    
    async def test_memory_usage(self):
        """Test memory usage under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Generate many chat requests
        for i in range(50):
            command_data = {
                "command": "chat_with_ai",
                "data": {
                    "message": f"Question {i}: What is the meaning of life?",
                    "session_id": f"session_{i}"
                }
            }
            await handle_command(json.dumps(command_data))
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (under 500MB)
        assert memory_increase < 500 * 1024 * 1024
```

### Frontend Performance

```javascript
// src/tests/performance/rendering.test.js
import { render } from '@testing-library/svelte';
import ChatPanel from '$lib/components/ChatPanel.svelte';

describe('Rendering Performance', () => {
  test('renders large conversation efficiently', async () => {
    const largeConversation = Array.from({ length: 1000 }, (_, i) => ({
      role: i % 2 === 0 ? 'user' : 'assistant',
      content: `Message ${i + 1}: This is a test message with some content.`
    }));
    
    const start = performance.now();
    const { component } = render(ChatPanel, { 
      props: { messages: largeConversation } 
    });
    const end = performance.now();
    
    expect(end - start).toBeLessThan(100); // Should render in under 100ms
  });
});
```

## Security Testing

### Input Validation Tests

```python
# tests/security/test_input_validation.py
import pytest
from backend.main import handle_command

class TestInputValidation:
    async def test_sql_injection_prevention(self):
        """Test SQL injection attempts are handled safely"""
        malicious_inputs = [
            "'; DROP TABLE conversations; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM user_settings --"
        ]
        
        for malicious_input in malicious_inputs:
            command_data = {
                "command": "chat_with_ai",
                "data": {
                    "message": malicious_input,
                    "session_id": "test_session"
                }
            }
            
            # Should not crash or leak data
            result = await handle_command(json.dumps(command_data))
            response = json.loads(result)
            
            # Should either succeed safely or fail gracefully
            assert "success" in response
            if not response["success"]:
                assert "error" in response
    
    async def test_command_injection_prevention(self):
        """Test command injection attempts are blocked"""
        malicious_commands = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& curl malicious-site.com",
            "`python -c 'import os; os.system(\"rm important_file\")'`"
        ]
        
        for malicious_command in malicious_commands:
            command_data = {
                "command": "search_web",
                "data": {
                    "query": malicious_command
                }
            }
            
            result = await handle_command(json.dumps(command_data))
            response = json.loads(result)
            
            # Should handle safely without executing commands
            assert isinstance(response, dict)
            assert "success" in response
```

### Privacy Tests

```python
# tests/security/test_privacy.py
import pytest
from backend.db.database import DatabaseManager

class TestPrivacy:
    async def test_data_encryption_at_rest(self):
        """Verify sensitive data is encrypted in database"""
        db = DatabaseManager()
        await db.initialize()
        
        # Save sensitive data
        await db.save_setting("api_key", "secret_key_123")
        
        # Check raw database doesn't contain plaintext
        raw_query = "SELECT value FROM user_settings WHERE key = 'api_key'"
        result = await db.execute_raw_query(raw_query)
        
        # Should not contain plaintext secret
        assert "secret_key_123" not in str(result)
        
        # But should be retrievable through proper method
        retrieved = await db.get_setting("api_key")
        assert retrieved == "secret_key_123"
    
    async def test_no_external_data_leakage(self):
        """Verify no data is sent to external services"""
        import unittest.mock as mock
        
        with mock.patch('httpx.post') as mock_post, \
             mock.patch('httpx.get') as mock_get:
            
            # Perform various operations
            command_data = {
                "command": "chat_with_ai",
                "data": {
                    "message": "This is private data that should not leak",
                    "session_id": "private_session"
                }
            }
            
            await handle_command(json.dumps(command_data))
            
            # Verify no external HTTP calls were made
            mock_post.assert_not_called()
            mock_get.assert_not_called()
```

## Test Configuration

### Pytest Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=backend
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    security: Security tests
    slow: Slow-running tests
```

### Jest Configuration

```javascript
// jest.config.js
export default {
  preset: '@sveltejs/adapter-node',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/tests/setup.js'],
  transform: {
    '^.+\\.svelte$': ['svelte-jester', { preprocess: true }],
    '^.+\\.js$': 'babel-jest'
  },
  moduleNameMapping: {
    '^\\$lib/(.*)$': '<rootDir>/src/lib/$1',
    '^\\$app/(.*)$': '<rootDir>/src/app/$1'
  },
  collectCoverageFrom: [
    'src/**/*.{js,svelte}',
    '!src/tests/**/*',
    '!src/**/*.test.{js,svelte}'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

## Continuous Integration

### GitHub Actions Testing

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
          
      - name: Run tests
        run: |
          cd backend
          pytest --cov=. --cov-report=xml
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
  
  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          
      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./frontend/coverage/lcov.info
  
  e2e-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up environment
        run: |
          # Install Ollama
          curl -fsSL https://ollama.ai/install.sh | sh
          # Pull test model
          ollama pull llama2:7b-chat
          
      - name: Start application
        run: |
          cd frontend
          npm run tauri dev &
          sleep 30  # Wait for app to start
          
      - name: Run E2E tests
        run: |
          cd frontend
          npm run test:e2e
```

## Best Practices

### Test Writing Guidelines

1. **Clear Test Names** - Describe what is being tested
2. **Arrange-Act-Assert** - Structure tests clearly
3. **Independent Tests** - Each test should be isolated
4. **Mock External Dependencies** - Use mocks for external services
5. **Test Edge Cases** - Include boundary conditions and error cases

### Code Coverage

- **Minimum Coverage**: 80% for all modules
- **Critical Paths**: 95% coverage for core functionality
- **Documentation**: Coverage reports in CI/CD
- **Quality over Quantity**: Focus on meaningful tests

### Test Data Management

- **Fixtures**: Use fixtures for consistent test data
- **Cleanup**: Clean up test data after each test
- **Isolation**: Tests should not depend on each other
- **Realistic Data**: Use realistic test scenarios

This comprehensive testing guide ensures LibreAssistant maintains high quality, reliability, and security while providing excellent user experience.
