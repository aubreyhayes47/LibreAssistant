// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAProviderSelector extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: inline-block;
          font-family: var(--font-family-sans);
        }
        .selector-container {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
        }
        label {
          font-size: var(--font-size-sm);
          color: var(--color-text);
          font-weight: var(--font-weight-normal);
        }
        select {
          background: var(--color-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
          padding: var(--spacing-xs) var(--spacing-sm);
          color: var(--color-text);
          font-family: inherit;
          font-size: var(--font-size-sm);
          cursor: pointer;
          min-width: 7.5rem;
          transition: border-color 0.2s ease;
        }
        select:focus {
          outline: 2px solid var(--color-primary);
          outline-offset: 2px;
        }
        select:hover {
          border-color: var(--color-primary);
        }
        select:disabled {
          background: var(--color-border);
          cursor: not-allowed;
        }
        .status-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--color-border);
          transition: background-color 0.2s ease;
        }
        .status-indicator.connected {
          background: var(--color-success, #22c55e);
        }
        .status-indicator.error {
          background: var(--color-error, #ef4444);
        }
        .status-indicator.loading {
          background: var(--color-warning, #f59e0b);
          animation: pulse 1.5s ease-in-out infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      </style>
      <div class="selector-container">
        <label for="provider-select">Provider:</label>
        <div class="status-indicator" id="status" role="img" aria-label="Provider connection status"></div>
        <select id="provider-select" aria-label="Select AI provider" aria-describedby="status">
          <option value="">Loading providers...</option>
        </select>
      </div>
    `;
    
    this.providers = [];
    this.currentProvider = 'cloud';
    this.statusMap = new Map();
  }

  async connectedCallback() {
    await this.loadProviders();
    this.setupEventListeners();
    this.updateUI();
    this.checkProviderStatus();
  }

  async loadProviders() {
    try {
      // For now, we'll use hardcoded providers since there's no API endpoint
      // In a real implementation, this would fetch from /api/v1/providers
      this.providers = [
        { id: 'cloud', name: 'Cloud (OpenAI)', description: 'OpenAI GPT models' },
        { id: 'local', name: 'Local Model', description: 'Local LLM server' }
      ];
      
      // Get current provider from localStorage or default to cloud
      const saved = localStorage.getItem('selected-provider');
      if (saved && this.providers.some(p => p.id === saved)) {
        this.currentProvider = saved;
      }
    } catch (error) {
      window.notifications?.error(`Failed to load providers: ${error.message}`);
      // Fallback to default providers
      this.providers = [
        { id: 'cloud', name: 'Cloud (OpenAI)', description: 'OpenAI GPT models' }
      ];
    }
  }

  setupEventListeners() {
    const select = this.shadowRoot.getElementById('provider-select');
    select.addEventListener('change', (event) => {
      const selectedProvider = this.providers.find(p => p.id === event.target.value);
      if (selectedProvider) {
        // Update ARIA description for screen readers
        select.setAttribute('aria-description', `Selected provider: ${selectedProvider.name} - ${selectedProvider.description}`);
      }
      this.switchProvider(event.target.value);
    });
  }

  updateUI() {
    const select = this.shadowRoot.getElementById('provider-select');
    
    // Populate select options
    select.innerHTML = '';
    this.providers.forEach(provider => {
      const option = document.createElement('option');
      option.value = provider.id;
      option.textContent = provider.name;
      option.title = provider.description;
      option.selected = provider.id === this.currentProvider;
      select.appendChild(option);
    });

    this.updateStatusIndicator();
  }

  async switchProvider(providerId) {
    if (!providerId || providerId === this.currentProvider) return;

    const provider = this.providers.find(p => p.id === providerId);
    if (!provider) return;

    const select = this.shadowRoot.getElementById('provider-select');
    const statusIndicator = this.shadowRoot.getElementById('status');

    try {
      const loadingId = window.notifications?.loading(`Switching to ${provider.name}...`);
      
      select.disabled = true;
      statusIndicator.className = 'status-indicator loading';
      
      // Test the provider with a simple request
      const testResponse = await fetch('/api/v1/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          provider: providerId, 
          prompt: 'test' 
        })
      });

      if (loadingId) window.notifications?.dismiss(loadingId);

      if (testResponse.ok) {
        this.currentProvider = providerId;
        localStorage.setItem('selected-provider', providerId);
        this.statusMap.set(providerId, 'connected');
        
        window.notifications?.success(`Successfully switched to ${provider.name}`);
        
        // Dispatch provider change event
        this.dispatchEvent(new CustomEvent('provider-change', {
          detail: { providerId, provider },
          bubbles: true
        }));
      } else {
        throw new Error(`Provider ${provider.name} is not available`);
      }
    } catch (error) {
      window.notifications?.error(`Failed to switch provider: ${error.message}`);
      this.statusMap.set(providerId, 'error');
      
      // Revert selection
      select.value = this.currentProvider;
    } finally {
      select.disabled = false;
      this.updateStatusIndicator();
    }
  }

  async checkProviderStatus() {
    const statusIndicator = this.shadowRoot.getElementById('status');
    statusIndicator.className = 'status-indicator loading';

    try {
      // Test current provider
      const response = await fetch('/api/v1/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          provider: this.currentProvider, 
          prompt: 'test' 
        })
      });

      if (response.ok) {
        this.statusMap.set(this.currentProvider, 'connected');
      } else {
        this.statusMap.set(this.currentProvider, 'error');
      }
    } catch (error) {
      this.statusMap.set(this.currentProvider, 'error');
    }

    this.updateStatusIndicator();
  }

  updateStatusIndicator() {
    const statusIndicator = this.shadowRoot.getElementById('status');
    const status = this.statusMap.get(this.currentProvider) || 'unknown';
    
    statusIndicator.className = `status-indicator ${status}`;
    
    const provider = this.providers.find(p => p.id === this.currentProvider);
    const statusText = {
      'connected': 'Connected and ready',
      'error': 'Connection error',
      'loading': 'Checking connection...',
      'unknown': 'Status unknown'
    }[status] || 'Status unknown';
    
    statusIndicator.title = `${provider?.name || 'Unknown'}: ${statusText}`;
    statusIndicator.setAttribute('aria-label', `Provider ${provider?.name || 'Unknown'} status: ${statusText}`);
  }

  // Public API
  getCurrentProvider() {
    return this.currentProvider;
  }

  getAvailableProviders() {
    return [...this.providers];
  }

  setProvider(providerId) {
    const select = this.shadowRoot.getElementById('provider-select');
    select.value = providerId;
    this.switchProvider(providerId);
  }
}

customElements.define('la-provider-selector', LAProviderSelector);