<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";

  let name = $state("");
  let greetMsg = $state("");
  let backendMsg = $state("");
  let isLoading = $state(false);
  
  // Chat interface
  let chatInput = $state("");
  let chatMessages = $state([]);
  let currentUrl = $state("");
  let extractedContent = $state("");
  
  // Browser data
  let browserData = $state([]);
  let dataType = $state("history");

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
          type: 'url',
          content: `Processed URL: ${currentUrl}`,
          timestamp: new Date().toLocaleTimeString()
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

  async function sendChat(event) {
    event.preventDefault();
    if (!chatInput.trim()) return;
    
    const userMessage = chatInput.trim();
    chatInput = "";
    
    // Add user message
    chatMessages = [...chatMessages, {
      type: 'user',
      content: userMessage,
      timestamp: new Date().toLocaleTimeString()
    }];
    
    isLoading = true;
    try {
      const response = await invoke("analyze_content", { content: userMessage });
      if (response.success) {
        // Add AI response
        chatMessages = [...chatMessages, {
          type: 'ai',
          content: response.analysis,
          timestamp: new Date().toLocaleTimeString()
        }];
      } else {
        chatMessages = [...chatMessages, {
          type: 'error',
          content: `Error: ${response.error}`,
          timestamp: new Date().toLocaleTimeString()
        }];
      }
    } catch (error) {
      chatMessages = [...chatMessages, {
        type: 'error',
        content: `Error: ${error}`,
        timestamp: new Date().toLocaleTimeString()
      }];
    } finally {
      isLoading = false;
    }
  }

  async function getBrowserData() {
    isLoading = true;
    try {
      const response = await invoke("get_browser_data", { dataType });
      if (response.success) {
        browserData = response.data;
      } else {
        browserData = [`Error: ${response.error}`];
      }
    } catch (error) {
      browserData = [`Error: ${error}`];
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    // Initialize with welcome message
    chatMessages = [{
      type: 'ai',
      content: 'Welcome to LibreAssistant! I can help you process URLs, analyze content, and access browser data. All processing happens locally for your privacy.',
      timestamp: new Date().toLocaleTimeString()
    }];
  });
</script>

<main class="container">
  <header class="header">
    <div class="header-content">
      <h1>🔧 LibreAssistant</h1>
      <p class="subtitle">Open Source AI Assistant Browser</p>
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
          <div class="message {message.type}">
            <span class="timestamp">{message.timestamp}</span>
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

    <!-- Browser Data -->
    <div class="panel">
      <h2>📊 Browser Data</h2>
      <div class="browser-controls">
        <select bind:value={dataType}>
          <option value="history">History</option>
          <option value="bookmarks">Bookmarks</option>
          <option value="cookies">Cookies</option>
        </select>
        <button onclick={getBrowserData} disabled={isLoading}>
          {isLoading ? 'Loading...' : 'Get Data'}
        </button>
      </div>
      {#if browserData.length > 0}
        <div class="browser-data">
          <h3>Browser {dataType}:</h3>
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

input, button, select {
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

select {
  background: #f9f9f9;
  min-width: 120px;
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
  
  input, select {
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
