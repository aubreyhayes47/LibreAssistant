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
      const res = await fetch('/api/v1/mcp/servers');
      const data = await res.json();
      this.plugins = data.servers || [];
    } catch {
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
    const label = document.createElement('label');
    label.textContent = plugin.name;
    const toggle = document.createElement('input');
    toggle.type = 'checkbox';
    toggle.checked = plugin.consent;
    toggle.addEventListener('change', async () => {
      plugin.consent = toggle.checked;
      try {
        await fetch(`/api/v1/mcp/consent/${plugin.name}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ consent: plugin.consent })
        });
      } catch {}
      this.dispatchEvent(
        new CustomEvent('plugin-toggle', {
          detail: { name: plugin.name, consent: plugin.consent }
        })
      );
    });
    label.prepend(toggle);
    li.appendChild(label);
    this.shadowRoot.getElementById('list').appendChild(li);
  }
}

customElements.define('la-plugin-catalogue', LAPluginCatalogue);
