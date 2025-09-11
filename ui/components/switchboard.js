// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LASwitchboard extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: grid;
          grid-template-rows: auto auto 1fr;
          gap: var(--spacing-md);
          height: 100%;
        }
        .request { 
          display: flex; 
          gap: var(--spacing-sm); 
          align-items: flex-start;
        }
        .provider-row {
          display: flex;
          gap: var(--spacing-sm);
          align-items: center;
        }
        textarea {
          flex: 1;
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          padding: var(--spacing-sm);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
          min-height: var(--size-card-min-height);
          resize: vertical;
        }
        select {
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          padding: var(--spacing-sm);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
          background: var(--color-background);
          min-width: 8rem;
        }
        button {
          background-color: var(--color-primary);
          color: var(--color-background);
          border: none;
          border-radius: var(--radius-sm);
          padding: var(--spacing-sm) var(--spacing-md);
          cursor: pointer;
          transition: background-color 0.2s ease;
          min-height: var(--size-button-height);
          flex-shrink: 0;
        }
        button:disabled {
          background-color: var(--color-border);
          cursor: not-allowed;
        }
        button.loading {
          position: relative;
        }
        button.loading::after {
          content: '';
          position: absolute;
          width: var(--size-icon-sm);
          height: var(--size-icon-sm);
          margin: auto;
          border: 2px solid transparent;
          border-top-color: var(--color-background);
          border-radius: 50%;
          animation: spin 1s linear infinite;
          top: 0;
          bottom: 0;
          left: 0;
          right: 0;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .activity {
          font-family: var(--font-family-sans);
          overflow-y: auto;
        }
        .activity ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        .activity li {
          padding: var(--spacing-xs) 0;
          border-bottom: 1px solid var(--color-border);
        }
      </style>
      <div class="provider-row">
        <la-provider-selector id="provider"></la-provider-selector>
      </div>
      <div class="request">
        <textarea id="input" aria-label="Request"></textarea>
        <select id="plugin">
          <option value="">No plugin</option>
        </select>
        <button id="send">Send</button>
      </div>
      <div class="activity">
        <ul id="log"></ul>
      </div>
    `;
  }

  async connectedCallback() {
    const send = this.shadowRoot.getElementById('send');
    const input = this.shadowRoot.getElementById('input');
    const log = this.shadowRoot.getElementById('log');
    const plugin = this.shadowRoot.getElementById('plugin');
    const provider = this.shadowRoot.getElementById('provider');

    await this.loadPlugins();

    // Listen for provider changes
    provider.addEventListener('provider-change', (event) => {
      window.notifications?.info(`Switched to ${event.detail.provider.name}`);
    });

    send.addEventListener('click', async () => {
      const value = input.value.trim();
      if (!value) return;

      const loadingId = window.notifications?.loading('Sending request...');
      send.disabled = true;
      send.classList.add('loading');

      const reqItem = document.createElement('li');
      reqItem.textContent = `→ ${value}`;
      reqItem.style.color = 'var(--color-text-secondary)';
      log.appendChild(reqItem);
      input.value = '';

      try {
        let res;
        if (plugin.value) {
          // Check if this is a dangerous operation that needs confirmation
          const isDangerous = await this.isDangerousOperation(plugin.value, value);
          if (isDangerous) {
            const confirmed = await this.showDangerousOperationConfirm(plugin.value, value);
            if (!confirmed) {
              const cancelItem = document.createElement('li');
              cancelItem.textContent = 'Operation cancelled by user';
              cancelItem.style.color = 'orange';
              log.appendChild(cancelItem);
              return;
            }
          }

          // Check consent for server before first invocation
          const hasConsent = await this.checkServerConsent(plugin.value);
          if (!hasConsent) {
            const consentGranted = await this.requestServerConsent(plugin.value);
            if (!consentGranted) {
              const consentItem = document.createElement('li');
              consentItem.textContent = 'Server access denied by user';
              consentItem.style.color = 'red';
              log.appendChild(consentItem);
              return;
            }
          }

          res = await fetch('/api/v1/invoke', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              plugin: plugin.value,
              user_id: 'anonymous',
              payload: { message: value }
            })
          });
        } else {
          const currentProvider = provider.getCurrentProvider();
          res = await fetch('/api/v1/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider: currentProvider, prompt: value })
          });
        }

        if (loadingId) window.notifications?.dismiss(loadingId);

        if (!res.ok) {
          let msg;
          try {
            const err = await res.json();
            msg = err.detail || JSON.stringify(err);
          } catch {
            msg = res.statusText;
          }
          throw new Error(msg);
        }

        const data = await res.json();
        const result = data.result;
        const resItem = document.createElement('li');
        resItem.textContent = `← ${typeof result === 'string' ? result : JSON.stringify(result)}`;
        resItem.style.color = 'var(--color-success, #22c55e)';
        log.appendChild(resItem);

        window.notifications?.success(plugin.value ? 'Plugin executed successfully' : 'Request processed successfully');
      } catch (err) {
        if (loadingId) window.notifications?.dismiss(loadingId);
        
        const errItem = document.createElement('li');
        errItem.textContent = `✗ Error: ${err.message}`;
        errItem.style.color = 'var(--color-error, #ef4444)';
        log.appendChild(errItem);

        window.notifications?.error(`Request failed: ${err.message}`);
      } finally {
        send.disabled = false;
        send.classList.remove('loading');
      }
    });

    // Add keyboard navigation support
    this._setupKeyboardNavigation(input, send);
  }

  _setupKeyboardNavigation(input, send) {
    // Handle keyboard shortcuts in the input area
    input.addEventListener('keydown', (e) => {
      // Ctrl+Enter or Shift+Enter to send
      if ((e.ctrlKey || e.shiftKey) && e.key === 'Enter') {
        e.preventDefault();
        if (!send.disabled && input.value.trim()) {
          send.click();
        }
      }
      
      // Escape to clear input
      if (e.key === 'Escape') {
        e.preventDefault();
        input.value = '';
        input.focus();
      }
    });

    // Ensure proper focus behavior for send button
    send.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (!send.disabled) {
          send.click();
        }
      }
    });
  }

  async loadPlugins() {
    const select = this.shadowRoot.getElementById('plugin');
    try {
      const loadingId = window.notifications?.loading('Loading plugins...');
      
      const res = await fetch('/api/v1/mcp/servers');
      
      if (loadingId) window.notifications?.dismiss(loadingId);
      
      if (!res.ok) {
        window.notifications?.error('Failed to load plugins');
        return;
      }
      
      const data = await res.json();
      (data.servers || []).forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.name;
        opt.textContent = p.name;
        select.appendChild(opt);
      });

      if (data.servers && data.servers.length > 0) {
        window.notifications?.success(`Loaded ${data.servers.length} plugins`);
      } else {
        window.notifications?.info('No plugins available');
      }
    } catch (err) {
      window.notifications?.error(`Failed to load plugins: ${err.message}`);
    }
  }

  /**
   * Check if a server operation is dangerous and requires confirmation
   */
  async isDangerousOperation(serverName, message) {
    // Check for file operations that might be destructive
    const dangerousPatterns = [
      /delete/i, /remove/i, /rm\s/i, /update/i, /modify/i, /write/i, /overwrite/i
    ];
    
    if (serverName === 'files') {
      return dangerousPatterns.some(pattern => pattern.test(message));
    }
    
    return false;
  }

  /**
   * Show confirmation dialog for dangerous operations
   */
  async showDangerousOperationConfirm(serverName, message) {
    if (typeof window.showConsentModal !== 'function') {
      // Fallback to basic confirm if showConsentModal not available
      return confirm(`This operation may be dangerous. Continue with "${message}" on ${serverName}?`);
    }
    
    const confirmMessage = `This operation may modify or delete data.\n\nServer: ${serverName}\nOperation: ${message}\n\nDo you want to proceed?`;
    return await window.showConsentModal(confirmMessage, 'Dangerous Operation');
  }

  /**
   * Check if user has already consented to this server
   */
  async checkServerConsent(serverName) {
    try {
      const res = await fetch(`/api/v1/mcp/consent/${serverName}`);
      if (!res.ok) return false;
      const data = await res.json();
      return data.consent === true;
    } catch {
      return false;
    }
  }

  /**
   * Request consent for server access
   */
  async requestServerConsent(serverName) {
    if (typeof window.showConsentModal !== 'function') {
      // Fallback to basic confirm if showConsentModal not available
      const granted = confirm(`Allow "${serverName}" server access to your data?`);
      if (granted) {
        await this.saveServerConsent(serverName, true);
      }
      return granted;
    }

    const consentMessage = `Allow "${serverName}" server access?\n\nThis server will be able to process your requests and access the data you share with it.`;
    const granted = await window.showConsentModal(consentMessage, 'Server Access');
    
    // Save consent decision to API
    await this.saveServerConsent(serverName, granted);
    
    return granted;
  }

  /**
   * Save consent decision to the API
   */
  async saveServerConsent(serverName, consent) {
    try {
      await fetch(`/api/v1/mcp/consent/${serverName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ consent })
      });
    } catch {
      // Ignore save failures - consent still tracked in memory for this session
    }
  }
}

customElements.define('la-switchboard', LASwitchboard);
