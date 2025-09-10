// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAPluginCatalogue extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--font-family-sans);
        }
        header {
          margin-bottom: var(--spacing-md);
        }
        ul {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: var(--spacing-sm);
        }
        li {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-sm);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
        }
        label {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          font-size: var(--font-size-base);
          color: var(--color-text);
          cursor: pointer;
        }
        .plugin-item {
          position: relative;
        }
        .plugin-status {
          font-size: var(--font-size-xs);
          color: var(--color-text-secondary);
          margin-left: auto;
          padding: var(--spacing-xs);
          border-radius: var(--radius-xs);
        }
        .plugin-status.enabling {
          color: var(--color-warning, #f59e0b);
          background: rgba(245, 158, 11, 0.1);
        }
        .plugin-status.enabled {
          color: var(--color-success, #22c55e);
          background: rgba(34, 197, 94, 0.1);
        }
        .plugin-status.error {
          color: var(--color-error, #ef4444);
          background: rgba(239, 68, 68, 0.1);
        }
      </style>
      <header>
        <la-input-field id="search">
          <span slot="label">Search plugins</span>
        </la-input-field>
      </header>
      <ul id="list"></ul>
    `;
    this.plugins = [];
  }

  async connectedCallback() {
    await this.loadPlugins();
    this.render();
    const search = this.shadowRoot.getElementById('search');
    search.shadowRoot.querySelector('input').addEventListener('input', e => {
      this.filter(e.target.value);
    });
  }

  async loadPlugins() {
    try {
      const loadingId = window.notifications?.loading('Loading plugin catalogue...');
      
      const res = await fetch('/api/v1/mcp/servers');
      
      if (loadingId) window.notifications?.dismiss(loadingId);
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      
      const data = await res.json();
      this.plugins = data.servers || [];
      
      if (this.plugins.length > 0) {
        window.notifications?.success(`Loaded ${this.plugins.length} plugins`);
      } else {
        window.notifications?.info('No plugins found in catalogue');
      }
    } catch (error) {
      window.notifications?.error(`Failed to load plugins: ${error.message}`);
      this.plugins = [];
    }
  }

  filter(query) {
    const lower = query.toLowerCase();
    this.shadowRoot.getElementById('list').innerHTML = '';
    this.plugins
      .filter(p => p.name.toLowerCase().includes(lower))
      .forEach(p => this.addItem(p));
  }

  render() {
    const list = this.shadowRoot.getElementById('list');
    list.innerHTML = '';
    this.plugins.forEach(p => this.addItem(p));
  }

  addItem(plugin) {
    const li = document.createElement('li');
    li.className = 'plugin-item';
    
    const label = document.createElement('label');
    label.textContent = plugin.name;
    
    const toggle = document.createElement('input');
    toggle.type = 'checkbox';
    toggle.checked = plugin.consent;
    
    const statusSpan = document.createElement('span');
    statusSpan.className = `plugin-status ${plugin.consent ? 'enabled' : ''}`;
    statusSpan.textContent = plugin.consent ? 'Enabled' : 'Disabled';
    
    toggle.addEventListener('change', async () => {
      const wasEnabled = plugin.consent;
      const newState = toggle.checked;
      
      // Update UI optimistically
      plugin.consent = newState;
      statusSpan.className = 'plugin-status enabling';
      statusSpan.textContent = newState ? 'Enabling...' : 'Disabling...';
      toggle.disabled = true;
      
      const loadingId = window.notifications?.loading(
        `${newState ? 'Enabling' : 'Disabling'} plugin ${plugin.name}...`
      );
      
      try {
        const res = await fetch(`/api/v1/mcp/consent/${plugin.name}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ consent: newState })
        });
        
        if (loadingId) window.notifications?.dismiss(loadingId);
        
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        
        // Success
        statusSpan.className = `plugin-status ${newState ? 'enabled' : ''}`;
        statusSpan.textContent = newState ? 'Enabled' : 'Disabled';
        
        window.notifications?.success(
          `Plugin ${plugin.name} ${newState ? 'enabled' : 'disabled'} successfully`
        );
        
        this.dispatchEvent(
          new CustomEvent('plugin-toggle', {
            detail: { name: plugin.name, consent: newState, success: true }
          })
        );
      } catch (error) {
        if (loadingId) window.notifications?.dismiss(loadingId);
        
        // Revert changes on error
        plugin.consent = wasEnabled;
        toggle.checked = wasEnabled;
        statusSpan.className = `plugin-status ${wasEnabled ? 'enabled' : 'error'}`;
        statusSpan.textContent = 'Error';
        
        window.notifications?.error(
          `Failed to ${newState ? 'enable' : 'disable'} plugin ${plugin.name}: ${error.message}`
        );
        
        this.dispatchEvent(
          new CustomEvent('plugin-toggle', {
            detail: { name: plugin.name, consent: wasEnabled, success: false, error: error.message }
          })
        );
      } finally {
        toggle.disabled = false;
      }
    });
    
    label.prepend(toggle);
    li.appendChild(label);
    li.appendChild(statusSpan);
    this.shadowRoot.getElementById('list').appendChild(li);
  }
}

customElements.define('la-plugin-catalogue', LAPluginCatalogue);
