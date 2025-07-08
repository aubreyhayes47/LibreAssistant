<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";
  import { generateTestData } from '$lib/utils/testData.js';
  import BrowserPanel from '$lib/BrowserPanel.svelte';

  let name = $state("");
  let greetMsg = $state("");
  let backendMsg = $state("");
  let isLoading = $state(false);
  let databaseInitialized = $state(false);
  
  // Chat interface
  let chatInput = $state("");
  /** @type {Array<{id: string, role: 'user'|'assistant', content: string, timestamp: string}>} */
  let chatMessages = $state([]);
  let currentUrl = $state("");
  let extractedContent = $state("");
  
  // Browser data
  /** @type {Array<string>} */
  let browserData = $state([]);
  let dataType = $state("history");

  /**
   * @param {Event} event
   */
  async function greet(event) {
    event.preventDefault();
    if (!name.trim()) return;
    
    isLoading = true;
    try {
      // Test both Rust and Python backends
      greetMsg = await invoke("greet", { name });
      
      const pythonResponse = await invoke("hello_backend", { name });
      if (pythonResponse.success) {
        backendMsg = pythonResponse.message;
      } else {
        backendMsg = `Error: ${pythonResponse.error}`;
      }
    } catch (error) {
      backendMsg = `Error: ${error}`;
    } finally {
      isLoading = false;
    }
  }

  /**
   * @param {Event} event
   */
  async function processUrl(event) {
    event.preventDefault();
    if (!currentUrl.trim()) return;
    
    isLoading = true;
    try {
      const response = await invoke("process_url", { url: currentUrl });
      if (response.success) {
        extractedContent = `Title: ${response.title}\n\nContent: ${response.content}`;
        
        // Add to chat messages
        chatMessages = [...chatMessages, {
          id: `url-${Date.now()}`,
          role: /** @type {'user'} */ ('user'),
          content: `Processed URL: ${currentUrl}`,
          timestamp: new Date().toISOString()
        }];
      } else {
        extractedContent = `Error: ${response.error}`;
      }
    } catch (error) {
      extractedContent = `Error: ${error}`;
    } finally {
      isLoading = false;
    }
  }

  /**
   * @param {Event} event
   */
  async function sendChat(event) {
    event.preventDefault();
    if (!chatInput.trim()) return;
    
    const userMessage = chatInput.trim();
    chatInput = "";
    
    // Add user message
    chatMessages = [...chatMessages, {
      id: `user-${Date.now()}`,
      role: /** @type {'user'} */ ('user'),
      content: userMessage,
      timestamp: new Date().toISOString()
    }];
    
    isLoading = true;
    try {
      const response = await invoke("chat_with_llm", { 
        message: userMessage,
        session_id: 'main-chat'
      });
      
      if (response.success) {
        // Add AI response
        chatMessages = [...chatMessages, {
          id: `ai-${Date.now()}`,
          role: /** @type {'assistant'} */ ('assistant'),
          content: response.response || 'I received your message but had trouble generating a response.',
          timestamp: new Date().toISOString()
        }];
      } else {
        chatMessages = [...chatMessages, {
          id: `error-${Date.now()}`,
          role: /** @type {'assistant'} */ ('assistant'),
          content: `❌ LLM Error: ${response.error}\n\n💡 Make sure Ollama is running locally:\n1. Install Ollama from https://ollama.ai\n2. Run: ollama pull llama2\n3. Start: ollama serve`,
          timestamp: new Date().toISOString()
        }];
      }
    } catch (error) {
      chatMessages = [...chatMessages, {
        id: `error-${Date.now()}`,
        role: /** @type {'assistant'} */ ('assistant'),
        content: `❌ Connection Error: ${error}\n\n🔧 Troubleshooting:\n1. Check that Ollama is running (ollama serve)\n2. Verify backend connection\n3. Check console for detailed errors`,
        timestamp: new Date().toISOString()
      }];
    } finally {
      isLoading = false;
    }
  }

  async function getBrowserData() {
    isLoading = true;
    try {
      // Ensure database is initialized
      if (!databaseInitialized) {
        browserData = ['⚠️ Database not initialized. Please wait for initialization to complete.'];
        return;
      }
      
      const response = await invoke("get_browser_history", { limit: 10 });

      if (response.success && Array.isArray(response.history)) {
        const history = response.history;
        if (history.length > 0) {
          browserData = history.map((/** @type {any} */ item) =>
            `📄 ${item.title || 'Untitled'}\n🔗 ${item.url}\n⏰ ${new Date(item.visit_time).toLocaleString()}\n`
          );
        } else {
          browserData = ['📭 No browser history found.\n\n💡 Click "Generate Test Data" to add some sample entries!'];
        }
      } else if (!response.success) {
        browserData = [`❌ Error: ${response.error}`];
      } else {
        browserData = ['📭 No browser history found.'];
      }
    } catch (error) {
      browserData = [`❌ Error: ${error}`];
    } finally {
      isLoading = false;
    }
  }

  async function generateTestDataLocal() {
    isLoading = true;
    try {
      const result = await generateTestData();
      
      if (result.success) {
        chatMessages = [...chatMessages, {
          id: `success-${Date.now()}`,
          role: /** @type {'assistant'} */ ('assistant'),
          content: `✅ ${result.message}! Generated ${result.results.length} test entries. You can now test browser history and bookmarks.`,
          timestamp: new Date().toISOString()
        }];
      } else {
        chatMessages = [...chatMessages, {
          id: `error-${Date.now()}`,
          role: /** @type {'assistant'} */ ('assistant'),
          content: `❌ Failed to generate test data: ${result.error}`,
          timestamp: new Date().toISOString()
        }];
      }
      
    } catch (error) {
      chatMessages = [...chatMessages, {
        id: `error-${Date.now()}`,
        role: /** @type {'assistant'} */ ('assistant'),
        content: `❌ Failed to generate test data: ${error instanceof Error ? error.message : String(error)}`,
        timestamp: new Date().toISOString()
      }];
    } finally {
      isLoading = false;
    }
  }

  onMount(async () => {
    // Initialize database first
    try {
      console.log('Initializing database...');
      const dbResult = await invoke("init_database");
      console.log('Database initialization result:', dbResult);
      
      if (dbResult.success) {
        console.log('✅ Database initialized successfully');
        databaseInitialized = true;
      } else {
        console.error('❌ Database initialization failed:', dbResult.error);
        databaseInitialized = false;
      }
    } catch (error) {
      console.error('❌ Failed to initialize database:', error);
      databaseInitialized = false;
    }
    
    // Initialize with welcome message
    chatMessages = [{
      id: `welcome-${Date.now()}`,
      role: /** @type {'assistant'} */ ('assistant'),
      content: 'Welcome to LibreAssistant! I can help you process URLs, analyze content, and access browser data. All processing happens locally for your privacy.',
      timestamp: new Date().toISOString()
    }];
  });
</script>

<main class="container">
  <header class="header">
    <div class="header-content">
      <h1>🔧 LibreAssistant</h1>
      <p class="subtitle">Open Source AI Assistant Browser</p>
      <div class="status-indicator">
        {#if databaseInitialized}
          <span class="status-badge success">✅ Database Ready</span>
        {:else}
          <span class="status-badge loading">⏳ Initializing Database...</span>
        {/if}
      </div>
    </div>
  </header>
  
  <div class="app-grid">
    <!-- Backend Connection Test -->
    <div class="panel">
      <h2>🔧 Backend Connection Test</h2>
      <form class="row" onsubmit={greet}>
        <input 
          id="greet-input" 
          placeholder="Enter a name..." 
          bind:value={name}
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Testing...' : 'Test Connection'}
        </button>
      </form>
      {#if greetMsg}
        <p class="result rust-result">🦀 Rust: {greetMsg}</p>
      {/if}
      {#if backendMsg}
        <p class="result python-result">🐍 Python: {backendMsg}</p>
      {/if}
    </div>

    <!-- URL Processor -->
    <div class="panel">
      <h2>🌐 URL Processor</h2>
      <form class="row" onsubmit={processUrl}>
        <input 
          placeholder="Enter URL to process..." 
          bind:value={currentUrl}
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Processing...' : 'Process URL'}
        </button>
      </form>
      {#if extractedContent}
        <div class="extracted-content">
          <h3>Extracted Content:</h3>
          <pre>{extractedContent}</pre>
        </div>
      {/if}
    </div>

    <!-- Chat Interface -->
    <div class="panel chat-panel">
      <h2>💬 AI Chat</h2>
      <div class="chat-messages">
        {#each chatMessages as message}
          <div class="message {message.role}">
            <span class="timestamp">{new Date(message.timestamp).toLocaleTimeString()}</span>
            <div class="content">{message.content}</div>
          </div>
        {/each}
        {#if isLoading}
          <div class="message loading">
            <span class="timestamp">...</span>
            <div class="content">AI is thinking...</div>
          </div>
        {/if}
      </div>
      <form class="chat-input" onsubmit={sendChat}>
        <input 
          placeholder="Ask me anything..." 
          bind:value={chatInput}
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>

    <!-- Embedded Browser -->
    <div class="panel">
      <h2>🕸️ Browser Preview</h2>
      <BrowserPanel />
    </div>

    <!-- Browser Data -->
    <div class="panel">
      <h2>📊 Browser Data</h2>
      <div class="browser-controls">
        <button onclick={generateTestDataLocal} disabled={isLoading}>
          {isLoading ? 'Generating...' : 'Generate Test Data'}
        </button>
        <button onclick={getBrowserData} disabled={isLoading}>
          {isLoading ? 'Loading...' : 'Get History'}
        </button>
      </div>
      {#if browserData.length > 0}
        <div class="browser-data">
          <h3>Browser history:</h3>
          <ul>
            {#each browserData as item}
              <li>{item}</li>
            {/each}
          </ul>
        </div>
      {/if}
    </div>
  </div>
</main>

<style>
:root {
  font-family: Inter, Avenir, Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
  color: #0f0f0f;
  background-color: #f6f6f6;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-text-size-adjust: 100%;
}

.container {
  margin: 0;
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

h1 {
  text-align: center;
  color: white;
  margin: 0;
  font-size: 2.5em;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header-content {
  display: inline-block;
}

.status-indicator {
  margin-top: 10px;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: 500;
}

.status-badge.success {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.status-badge.loading {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.1em;
  margin: 10px 0 0 0;
  font-weight: 300;
}

.app-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.panel {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.2);
}

.panel h2 {
  margin-top: 0;
  color: #333;
  font-size: 1.4em;
  margin-bottom: 15px;
}

.chat-panel {
  grid-column: 1 / -1;
  max-width: 800px;
  margin: 0 auto;
}

.row {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.browser-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

input, button {
  border-radius: 8px;
  border: 1px solid #ddd;
  padding: 10px 15px;
  font-size: 14px;
  font-weight: 500;
  font-family: inherit;
  transition: all 0.25s ease;
}

input {
  flex: 1;
  background: #f9f9f9;
}

input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

button {
  cursor: pointer;
  background: #667eea;
  color: white;
  border: none;
  white-space: nowrap;
  font-weight: 600;
}

button:hover:not(:disabled) {
  background: #5a6fd8;
  transform: translateY(-1px);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.result {
  margin: 10px 0;
  padding: 10px;
  border-radius: 6px;
  font-weight: 500;
}

.rust-result {
  background: #ffe6cc;
  color: #c67e00;
  border-left: 4px solid #f39c12;
}

.python-result {
  background: #e6f3ff;
  color: #0066cc;
  border-left: 4px solid #3498db;
}

.extracted-content {
  margin-top: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.extracted-content h3 {
  margin-top: 0;
  color: #495057;
}

.extracted-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #666;
  max-height: 200px;
  overflow-y: auto;
}

.chat-messages {
  height: 400px;
  overflow-y: auto;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 15px;
  background: #f8f9fa;
  margin-bottom: 15px;
}

.message {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 8px;
  max-width: 80%;
}

.message.user {
  background: #667eea;
  color: white;
  margin-left: auto;
}

.message.assistant {
  background: #e8f5e8;
  color: #2d5a2d;
  border-left: 4px solid #4caf50;
}

.message.ai {
  background: #e8f5e8;
  color: #2d5a2d;
  border-left: 4px solid #4caf50;
}

.message.url {
  background: #fff3cd;
  color: #856404;
  border-left: 4px solid #ffc107;
}

.message.error {
  background: #f8d7da;
  color: #721c24;
  border-left: 4px solid #dc3545;
}

.message.loading {
  background: #d1ecf1;
  color: #0c5460;
  border-left: 4px solid #17a2b8;
}

.timestamp {
  font-size: 11px;
  opacity: 0.7;
  margin-bottom: 5px;
  display: block;
}

.content {
  font-size: 14px;
  line-height: 1.4;
}

.chat-input {
  display: flex;
  gap: 10px;
}

.browser-data {
  margin-top: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.browser-data h3 {
  margin-top: 0;
  color: #495057;
}

.browser-data ul {
  margin: 0;
  padding-left: 20px;
}

.browser-data li {
  margin-bottom: 5px;
  font-size: 14px;
  color: #666;
}

@media (prefers-color-scheme: dark) {
  :root {
    color: #f6f6f6;
    background-color: #2f2f2f;
  }
  
  .panel {
    background: #3a3a3a;
    color: #f6f6f6;
  }
  
  .panel h2 {
    color: #f6f6f6;
  }
  
  input {
    background: #2f2f2f;
    color: #f6f6f6;
    border-color: #555;
  }

  input:focus {
    border-color: #667eea;
  }
  
  .chat-messages {
    background: #2f2f2f;
    border-color: #555;
  }
  
  .extracted-content,
  .browser-data {
    background: #2f2f2f;
    border-color: #555;
  }
  
  .extracted-content h3,
  .browser-data h3 {
    color: #f6f6f6;
  }
}

@media (max-width: 768px) {
  .app-grid {
    grid-template-columns: 1fr;
  }
  
  .container {
    padding: 10px;
  }
  
  h1 {
    font-size: 2em;
  }
  
  .panel {
    padding: 15px;
  }
  
  .chat-messages {
    height: 300px;
  }
  
  .message {
    max-width: 90%;
  }
}
</style>
