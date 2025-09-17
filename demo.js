class OllamaChatDemo {
    constructor() {
        this.selectedModel = '';
        this.chatHistory = [];
        this.isLoading = false;
        this.demoMode = true;
        
        this.initializeElements();
        this.attachEventListeners();
        this.loadDemoModels();
    }
    
    initializeElements() {
        this.modelSelect = document.getElementById('model-select');
        this.refreshButton = document.getElementById('refresh-models');
        this.chatHistoryDiv = document.getElementById('chat-history');
        this.promptInput = document.getElementById('prompt-input');
        this.sendButton = document.getElementById('send-button');
        this.clearButton = document.getElementById('clear-history');
        this.errorContainer = document.getElementById('error-container');
        this.errorMessage = document.getElementById('error-message');
        this.closeError = document.getElementById('close-error');
    }
    
    attachEventListeners() {
        this.modelSelect.addEventListener('change', (e) => {
            this.selectedModel = e.target.value;
            this.updateInputState();
        });
        
        this.refreshButton.addEventListener('click', () => {
            this.loadDemoModels();
        });
        
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        this.promptInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.clearButton.addEventListener('click', () => {
            this.clearHistory();
        });
        
        this.closeError.addEventListener('click', () => {
            this.hideError();
        });
    }
    
    loadDemoModels() {
        this.modelSelect.innerHTML = '<option value="">Loading models...</option>';
        this.modelSelect.disabled = true;
        
        // Simulate loading delay
        setTimeout(() => {
            this.modelSelect.innerHTML = `
                <option value="">Select a model...</option>
                <option value="llama2">llama2</option>
                <option value="codellama">codellama</option>
                <option value="mistral">mistral</option>
                <option value="neural-chat">neural-chat</option>
            `;
            this.modelSelect.disabled = false;
        }, 1000);
    }
    
    updateInputState() {
        const hasModel = this.selectedModel && this.selectedModel !== '';
        this.promptInput.disabled = !hasModel || this.isLoading;
        this.sendButton.disabled = !hasModel || this.isLoading;
        
        if (hasModel) {
            this.promptInput.placeholder = `Type your prompt for ${this.selectedModel}...`;
        } else {
            this.promptInput.placeholder = 'Select a model first...';
        }
    }
    
    async sendMessage() {
        const prompt = this.promptInput.value.trim();
        
        if (!prompt || !this.selectedModel || this.isLoading) {
            return;
        }
        
        this.isLoading = true;
        this.updateInputState();
        
        // Add user message to chat
        this.addMessage('user', prompt);
        this.promptInput.value = '';
        
        // Add typing indicator
        const typingId = this.addTypingIndicator();
        
        // Simulate API delay
        setTimeout(() => {
            this.removeTypingIndicator(typingId);
            
            // Generate demo response
            const response = this.generateDemoResponse(prompt);
            this.addMessage('assistant', response);
            
            this.isLoading = false;
            this.updateInputState();
            this.promptInput.focus();
        }, 1500 + Math.random() * 2000); // Random delay between 1.5-3.5 seconds
    }
    
    generateDemoResponse(prompt) {
        const responses = [
            "That's an interesting question! In this **demo mode**, I can show you how the chat interface works. The real application would connect to your local Ollama instance to get actual AI responses.\n\nKey features:\n- Markdown rendering\n- Code syntax highlighting\n- Real-time chat",
            "This is a demonstration of the chat functionality. When connected to a real Ollama model, you would get actual AI-generated responses based on your prompts.\n\n> Note: This is just a demo - connect to real Ollama for actual AI responses!",
            "Great prompt! This demo shows how conversations flow in the interface. Each message gets timestamped and the chat history is maintained throughout your session.\n\n### Chat Features:\n1. Real-time messaging\n2. **Markdown support**\n3. Code highlighting\n4. Message history",
            "I can see you're testing the chat interface. The real power comes when you connect this to Ollama running locally with models like:\n\n- `llama2` - General conversation\n- `codellama` - Code assistance  \n- `mistral` - Fast responses\n- `llava` - Vision capabilities",
            "This demo response shows how the AI assistant would reply. The interface handles long conversations, maintains context, and provides a smooth chat experience.\n\n```javascript\n// Example of code rendering\nconst chat = new OllamaChat();\nchat.sendMessage('Hello!');\n```"
        ];
        
        // Simple keyword-based responses for demo
        const lowerPrompt = prompt.toLowerCase();
        if (lowerPrompt.includes('hello') || lowerPrompt.includes('hi')) {
            return "Hello! 👋 Welcome to the **Ollama Wrapper demo**. I'm showing you how the chat interface works!\n\n### Try asking about:\n- `code` or `programming`\n- `help` for instructions\n- Any other topic to see responses";
        } else if (lowerPrompt.includes('code') || lowerPrompt.includes('programming')) {
            return "For coding questions, you'd want to use the **CodeLlama** model. This demo shows how different models can be selected from the dropdown above.\n\n```python\n# Example: Python code with syntax highlighting\ndef greet(name):\n    return f\"Hello, {name}!\"\n\nprint(greet(\"Ollama User\"))\n```\n\n> **Tip**: The real CodeLlama model can help with debugging, explanations, and code generation!";
        } else if (lowerPrompt.includes('help')) {
            return "This is a demo of the chat interface. In real usage:\n\n### Steps to use:\n1. **Select a model** from the dropdown\n2. **Type your prompt** in the text area\n3. **Press Enter** or click Send\n4. **View responses** with timestamps\n5. **Clear history** when needed\n\n### Markdown Features:\n- **Bold** and *italic* text\n- `inline code` and code blocks\n- Lists and quotes\n- Headers and links";
        } else if (lowerPrompt.includes('markdown') || lowerPrompt.includes('format')) {
            return "Great question about **markdown support**! This interface automatically detects and renders markdown in AI responses.\n\n### Supported Elements:\n- **Bold text** with `**text**`\n- *Italic text* with `*text*`\n- `Inline code` with backticks\n- Code blocks with triple backticks\n- Headers with `#`\n- Lists (like this one!)\n- > Blockquotes\n- Links and more!\n\n```javascript\n// Code blocks get syntax highlighting\nfunction example() {\n    console.log('Markdown rendering works!');\n}\n```";
        }
        
        return responses[Math.floor(Math.random() * responses.length)];
    }
    
    addMessage(role, content) {
        const message = {
            role: role,
            content: content,
            timestamp: new Date().toLocaleTimeString()
        };
        
        this.chatHistory.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }
    
    renderMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Use markdown rendering for assistant responses, plain text for user messages
        if (message.role === 'assistant' && window.MarkdownUtils) {
            contentDiv.innerHTML = window.MarkdownUtils.renderChatContent(message.content);
        } else {
            contentDiv.textContent = message.content;
        }
        
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'message-timestamp';
        timestampDiv.textContent = message.timestamp;
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timestampDiv);
        
        // Remove welcome message if it exists
        const welcomeMessage = this.chatHistoryDiv.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.chatHistoryDiv.appendChild(messageDiv);
    }
    
    addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        
        const typingContent = document.createElement('div');
        typingContent.className = 'typing-indicator';
        typingContent.textContent = 'Thinking';
        
        typingDiv.appendChild(typingContent);
        
        const typingId = Date.now().toString();
        typingDiv.id = `typing-${typingId}`;
        
        this.chatHistoryDiv.appendChild(typingDiv);
        this.scrollToBottom();
        
        return typingId;
    }
    
    removeTypingIndicator(typingId) {
        const typingDiv = document.getElementById(`typing-${typingId}`);
        if (typingDiv) {
            typingDiv.remove();
        }
    }
    
    clearHistory() {
        if (this.chatHistory.length === 0) {
            return;
        }
        
        if (confirm('Are you sure you want to clear the chat history?')) {
            this.chatHistory = [];
            this.chatHistoryDiv.innerHTML = `
                <div class="welcome-message">
                    <p>Chat history cleared. Start a new conversation!</p>
                </div>
            `;
        }
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.chatHistoryDiv.scrollTop = this.chatHistoryDiv.scrollHeight;
        }, 100);
    }
    
    showError(message) {
        this.errorMessage.textContent = message;
        this.errorContainer.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideError();
        }, 5000);
    }
    
    hideError() {
        this.errorContainer.style.display = 'none';
    }
}

// Initialize the demo when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new OllamaChatDemo();
});