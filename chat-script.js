class OllamaChat {
    constructor() {
        this.baseUrl = 'http://localhost:11434';
        this.selectedModel = '';
        this.chatHistory = [];
        this.isLoading = false;
        
        this.initializeElements();
        this.attachEventListeners();
        this.loadModels();
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
            this.loadModels();
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
    
    async loadModels() {
        try {
            this.modelSelect.innerHTML = '<option value="">Loading models...</option>';
            this.modelSelect.disabled = true;
            
            const response = await fetch(`${this.baseUrl}/api/tags`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            this.modelSelect.innerHTML = '<option value="">Select a model...</option>';
            
            if (data.models && data.models.length > 0) {
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = model.name;
                    this.modelSelect.appendChild(option);
                });
            } else {
                this.modelSelect.innerHTML = '<option value="">No models found</option>';
            }
            
        } catch (error) {
            console.error('Error loading models:', error);
            this.modelSelect.innerHTML = '<option value="">Error loading models</option>';
            this.showError('Failed to load models. Make sure Ollama is running on localhost:11434');
        } finally {
            this.modelSelect.disabled = false;
        }
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
        
        try {
            const response = await fetch(`${this.baseUrl}/api/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: this.selectedModel,
                    prompt: prompt,
                    stream: false
                }),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            // Add assistant response
            this.addMessage('assistant', data.response || 'No response received');
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator(typingId);
            this.addMessage('assistant', 'Error: Failed to get response from model. Please check if Ollama is running and the model is available.');
            this.showError('Failed to send message. Please check your connection to Ollama.');
        } finally {
            this.isLoading = false;
            this.updateInputState();
            this.promptInput.focus();
        }
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

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new OllamaChat();
});