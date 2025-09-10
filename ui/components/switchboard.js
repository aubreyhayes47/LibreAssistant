// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LASwitchboard extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        .request { 
          display: flex; 
          gap: var(--spacing-sm); 
          margin-bottom: var(--spacing-sm);
        }
        .provider-row {
          display: flex;
          gap: var(--spacing-sm);
          margin-bottom: var(--spacing-sm);
          align-items: center;
        }
        textarea {
          flex: 1;
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          padding: var(--spacing-sm);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
        }
        select {
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          padding: var(--spacing-sm);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
          background: var(--color-background);
        }
        button {
          background-color: var(--color-primary);
          color: var(--color-background);
          border: none;
          border-radius: var(--radius-sm);
          padding: var(--spacing-sm) var(--spacing-md);
          cursor: pointer;
          transition: background-color 0.2s ease;
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
          width: 16px;
          height: 16px;
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
          margin-top: var(--spacing-md);
          font-family: var(--font-family-sans);
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
}

customElements.define('la-switchboard', LASwitchboard);
