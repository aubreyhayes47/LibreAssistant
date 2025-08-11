// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LADataVault extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        textarea {
          width: 100%;
          min-height: 6rem;
          font-family: var(--font-family-mono);
          margin-bottom: var(--spacing-sm);
        }
        button {
          margin-right: var(--spacing-sm);
        }
        pre {
          background: var(--color-surface);
          padding: var(--spacing-sm);
        }
      </style>
      <textarea id="data" placeholder="{}"></textarea>
      <div>
        <button id="save">Save</button>
        <button id="export">Export</button>
        <button id="delete">Delete</button>
      </div>
      <pre id="output"></pre>
    `;
  }

  connectedCallback() {
    const user = this.getAttribute('user') || 'default';
    const textarea = this.shadowRoot.getElementById('data');
    const output = this.shadowRoot.getElementById('output');

    this.shadowRoot.getElementById('save').addEventListener('click', async () => {
      let data = {};
      try {
        data = JSON.parse(textarea.value || '{}');
      } catch (e) {
        return;
      }
      await fetch(`/api/v1/vault/${user}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data })
      });
    });

    this.shadowRoot.getElementById('export').addEventListener('click', async () => {
      const resp = await fetch(`/api/v1/vault/${user}/export`);
      const json = await resp.json();
      output.textContent = JSON.stringify(json.data, null, 2);
    });

    this.shadowRoot.getElementById('delete').addEventListener('click', async () => {
      await fetch(`/api/v1/vault/${user}`, { method: 'DELETE' });
      output.textContent = '';
      textarea.value = '';
    });
  }
}

customElements.define('la-data-vault', LADataVault);
