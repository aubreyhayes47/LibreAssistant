<!-- 
  Phase 1B Manual Testing Interface
  Tests all the newly implemented Tauri commands and state management
-->
<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";
  import * as chatStore from '../../lib/stores/chat.js';
  import { browserStore } from '../../lib/stores/browser.js';
  import { database, chat, bookmarks, browser } from '../../lib/services/api.js';

  // Test results
  /** @type {Array<{test: string, success: boolean, message: string, data?: any, timestamp: string}>} */
  let testResults = $state([]);
  let isTestRunning = $state(false);
  
  // Manual test inputs
  let testMessage = $state("Hello, this is a test message for Phase 1B!");
  let testUrl = $state("https://example.com");
  let testTitle = $state("Test Bookmark");
  let testContent = $state("This is test content for bookmarking");
  let searchQuery = $state("test");

  // State display
  let showChatStore = $state(false);
  let showBrowserStore = $state(false);

  /**
   * @param {string} test
   * @param {boolean} success  
   * @param {string} message
   * @param {any} [data]
   */
  function addTestResult(test, success, message, data = null) {
    testResults = [...testResults, {
      test,
      success,
      message,
      data,
      timestamp: new Date().toLocaleTimeString()
    }];
  }

  // Individual test functions
  async function testDatabaseInit() {
    try {
      const response = await invoke('init_database');
      addTestResult('Database Init', response.success, 
        response.success ? 'Database initialized successfully' : response.error, 
        response);
    } catch (error) {
      addTestResult('Database Init', false, `Error: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async function testChatWithLLM() {
    try {
      const response = await invoke('chat_with_llm', { 
        message: testMessage, 
        session_id: 'test-session' 
      });
      addTestResult('Chat with LLM', response.success, 
        response.success ? 'LLM responded successfully' : response.error, 
        response);
    } catch (error) {
      addTestResult('Chat with LLM', false, `Error: ${error.message}`);
    }
  }

  async function testSaveBookmark() {
    try {
      const response = await invoke('save_bookmark', { 
        url: testUrl, 
        title: testTitle, 
        content: testContent 
      });
      addTestResult('Save Bookmark', response.success, 
        response.success ? 'Bookmark saved successfully' : response.error, 
        response);
    } catch (error) {
      addTestResult('Save Bookmark', false, `Error: ${error.message}`);
    }
  }

  async function testGetChatHistory() {
    try {
      const response = await invoke('get_chat_history', { 
        session_id: 'test-session', 
        limit: 10 
      });
      addTestResult('Get Chat History', response.success, 
        response.success ? `Found ${response.history?.length || 0} messages` : response.error, 
        response);
    } catch (error) {
      addTestResult('Get Chat History', false, `Error: ${error.message}`);
    }
  }

  async function testGetBookmarks() {
    try {
      const response = await invoke('get_bookmarks', { search_query: null });
      addTestResult('Get Bookmarks', response.success, 
        response.success ? `Found ${response.bookmarks?.length || 0} bookmarks` : response.error, 
        response);
    } catch (error) {
      addTestResult('Get Bookmarks', false, `Error: ${error.message}`);
    }
  }

  async function testSearchBookmarks() {
    try {
      const response = await invoke('search_bookmarks', { 
        query: searchQuery, 
        limit: 10 
      });
      addTestResult('Search Bookmarks', response.success, 
        response.success ? `Found ${response.results?.length || 0} results` : response.error, 
        response);
    } catch (error) {
      addTestResult('Search Bookmarks', false, `Error: ${error.message}`);
    }
  }

  async function testAddHistoryEntry() {
    try {
      const response = await invoke('add_history_entry', { 
        url: testUrl, 
        title: testTitle 
      });
      addTestResult('Add History Entry', response.success, 
        response.success ? 'History entry added successfully' : response.error, 
        response);
    } catch (error) {
      addTestResult('Add History Entry', false, `Error: ${error.message}`);
    }
  }

  async function testGetBrowserHistory() {
    try {
      const response = await invoke('get_browser_history', { 
        limit: 10, 
        search_query: null 
      });
      addTestResult('Get Browser History', response.success, 
        response.success ? `Found ${response.history?.length || 0} entries` : response.error, 
        response);
    } catch (error) {
      addTestResult('Get Browser History', false, `Error: ${error.message}`);
    }
  }

  // Run all tests
  async function runAllTests() {
    isTestRunning = true;
    testResults = [];
    
    await testDatabaseInit();
    await new Promise(resolve => setTimeout(resolve, 500));
    
    await testChatWithLLM();
    await new Promise(resolve => setTimeout(resolve, 500));
    
    await testSaveBookmark();
    await new Promise(resolve => setTimeout(resolve, 500));
    
    await testGetChatHistory();
    await new Promise(resolve => setTimeout(resolve, 500));
    
    await testGetBookmarks();
    await new Promise(resolve => setTimeout(resolve, 500));
    
    await testSearchBookmarks();
    await new Promise(resolve => setTimeout(resolve, 500));
    
    await testAddHistoryEntry();
    await new Promise(resolve => setTimeout(resolve, 500));
    
    await testGetBrowserHistory();
    
    isTestRunning = false;
  }

  // Store testing functions
  async function testChatStore() {
    try {
      await chatStore.sendMessage(testMessage);
      addTestResult('Chat Store', true, 'Message sent through chat store', 
        { messageCount: chatStore.messages.length });
    } catch (error) {
      addTestResult('Chat Store', false, `Error: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async function testBrowserStore() {
    try {
      await browserStore.navigateTo(testUrl);
      addTestResult('Browser Store', true, 'Navigation completed', 
        { url: browserStore.currentUrl, title: browserStore.currentTitle });
    } catch (error) {
      addTestResult('Browser Store', false, `Error: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  onMount(() => {
    // Initialize with a welcome message
    testResults = [{
      test: 'System',
      success: true,
      message: 'Phase 1B Manual Testing Interface Ready',
      timestamp: new Date().toLocaleTimeString()
    }];
  });
</script>

<main class="test-container">
  <header class="test-header">
    <h1>🧪 Phase 1B Manual Testing</h1>
    <p>Test all the newly implemented Tauri commands and state management</p>
  </header>

  <div class="test-grid">
    <!-- Quick Test Controls -->
    <div class="panel">
      <h2>🚀 Quick Tests</h2>
      <div class="button-group">
        <button onclick={runAllTests} disabled={isTestRunning}>
          {isTestRunning ? 'Running Tests...' : 'Run All Tests'}
        </button>
        <button onclick={() => testResults = []}>Clear Results</button>
      </div>
    </div>

    <!-- Individual Command Tests -->
    <div class="panel">
      <h2>📡 Tauri Commands</h2>
      <div class="test-buttons">
        <button onclick={testDatabaseInit}>Database Init</button>
        <button onclick={testChatWithLLM}>Chat with LLM</button>
        <button onclick={testSaveBookmark}>Save Bookmark</button>
        <button onclick={testGetChatHistory}>Get Chat History</button>
        <button onclick={testGetBookmarks}>Get Bookmarks</button>
        <button onclick={testSearchBookmarks}>Search Bookmarks</button>
        <button onclick={testAddHistoryEntry}>Add History Entry</button>
        <button onclick={testGetBrowserHistory}>Get Browser History</button>
      </div>
    </div>

    <!-- Store Tests -->
    <div class="panel">
      <h2>🏪 State Stores</h2>
      <div class="test-buttons">
        <button onclick={testChatStore}>Test Chat Store</button>
        <button onclick={testBrowserStore}>Test Browser Store</button>
        <button onclick={() => showChatStore = !showChatStore}>
          {showChatStore ? 'Hide' : 'Show'} Chat Store
        </button>
        <button onclick={() => showBrowserStore = !showBrowserStore}>
          {showBrowserStore ? 'Hide' : 'Show'} Browser Store
        </button>
      </div>
    </div>

    <!-- Test Inputs -->
    <div class="panel">
      <h2>⚙️ Test Configuration</h2>
      <div class="input-group">
        <label for="test-message">Test Message:</label>
        <input id="test-message" bind:value={testMessage} placeholder="Enter test message">
        
        <label for="test-url">Test URL:</label>
        <input id="test-url" bind:value={testUrl} placeholder="Enter test URL">
        
        <label for="test-title">Test Title:</label>
        <input id="test-title" bind:value={testTitle} placeholder="Enter test title">
        
        <label for="search-query">Search Query:</label>
        <input id="search-query" bind:value={searchQuery} placeholder="Enter search query">
      </div>
    </div>
  </div>

  <!-- Store State Display -->
  {#if showChatStore}
    <div class="store-display">
      <h3>💬 Chat Store State</h3>
      <pre>{JSON.stringify({
        messageCount: chatStore.messages.length,
        loading: chatStore.isLoading,
        currentSession: chatStore.currentSessionId,
        lastMessage: chatStore.messages[chatStore.messages.length - 1]
      }, null, 2)}</pre>
    </div>
  {/if}

  {#if showBrowserStore}
    <div class="store-display">
      <h3>🌐 Browser Store State</h3>
      <pre>{JSON.stringify({
        currentUrl: browserStore.currentUrl,
        currentTitle: browserStore.currentTitle,
        canGoBack: browserStore.canGoBack,
        canGoForward: browserStore.canGoForward,
        isLoading: browserStore.isLoading,
        historyCount: browserStore.history.length
      }, null, 2)}</pre>
    </div>
  {/if}

  <!-- Test Results -->
  <div class="results-panel">
    <h2>📊 Test Results</h2>
    <div class="results-stats">
      <span class="stat success">✅ {testResults.filter(r => r.success).length} Passed</span>
      <span class="stat failure">❌ {testResults.filter(r => !r.success).length} Failed</span>
      <span class="stat total">📈 {testResults.length} Total</span>
    </div>
    
    <div class="results-list">
      {#each testResults as result}
        <div class="result-item {result.success ? 'success' : 'failure'}">
          <div class="result-header">
            <span class="result-icon">{result.success ? '✅' : '❌'}</span>
            <span class="result-test">{result.test}</span>
            <span class="result-time">{result.timestamp}</span>
          </div>
          <div class="result-message">{result.message}</div>
          {#if result.data}
            <details class="result-details">
              <summary>View Response Data</summary>
              <pre>{JSON.stringify(result.data, null, 2)}</pre>
            </details>
          {/if}
        </div>
      {/each}
    </div>
  </div>
</main>

<style>
  .test-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  }

  .test-header {
    text-align: center;
    margin-bottom: 30px;
  }

  .test-header h1 {
    color: #2563eb;
    margin-bottom: 10px;
  }

  .test-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
  }

  .panel {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border: 1px solid #e5e7eb;
  }

  .panel h2 {
    margin-top: 0;
    color: #1f2937;
    font-size: 1.2rem;
  }

  .button-group, .test-buttons {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  .test-buttons {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 8px;
  }

  button {
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    background: #3b82f6;
    color: white;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s;
  }

  button:hover {
    background: #2563eb;
    transform: translateY(-1px);
  }

  button:disabled {
    background: #9ca3af;
    cursor: not-allowed;
    transform: none;
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .input-group label {
    font-weight: 500;
    color: #374151;
  }

  .input-group input {
    padding: 8px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.9rem;
  }

  .store-display {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
  }

  .store-display h3 {
    margin-top: 0;
    color: #1e293b;
  }

  .store-display pre {
    background: #1e293b;
    color: #e2e8f0;
    padding: 15px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 0.85rem;
  }

  .results-panel {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border: 1px solid #e5e7eb;
  }

  .results-stats {
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
    padding: 15px;
    background: #f9fafb;
    border-radius: 8px;
  }

  .stat {
    font-weight: 600;
    padding: 5px 10px;
    border-radius: 6px;
  }

  .stat.success {
    background: #dcfce7;
    color: #166534;
  }

  .stat.failure {
    background: #fee2e2;
    color: #dc2626;
  }

  .stat.total {
    background: #dbeafe;
    color: #1d4ed8;
  }

  .results-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .result-item {
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
  }

  .result-item.success {
    border-left: 4px solid #10b981;
    background: #f0fdf4;
  }

  .result-item.failure {
    border-left: 4px solid #ef4444;
    background: #fef2f2;
  }

  .result-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 5px;
  }

  .result-test {
    font-weight: 600;
    color: #1f2937;
  }

  .result-time {
    margin-left: auto;
    font-size: 0.8rem;
    color: #6b7280;
  }

  .result-message {
    color: #374151;
    margin-bottom: 10px;
  }

  .result-details {
    margin-top: 10px;
  }

  .result-details summary {
    cursor: pointer;
    font-weight: 500;
    color: #6b7280;
    padding: 5px 0;
  }

  .result-details pre {
    background: #1f2937;
    color: #e5e7eb;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 0.8rem;
    margin-top: 5px;
  }
</style>
