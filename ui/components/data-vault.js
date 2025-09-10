// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LADataVault extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--font-family-sans);
        }
        textarea {
          width: 100%;
          min-height: 6rem;
          font-family: var(--font-family-mono);
          font-size: var(--font-size-base);
          line-height: var(--line-height-base);
          padding: var(--spacing-sm);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
          background-color: var(--color-surface);
          color: var(--color-text);
          margin-bottom: var(--spacing-sm);
          box-sizing: border-box;
        }
        textarea:focus {
          outline: var(--focus-ring);
          outline-offset: var(--focus-ring-offset);
          border-color: var(--color-primary);
        }
        button {
          background-color: var(--color-primary);
          color: var(--color-background);
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          font-weight: var(--font-weight-bold);
          padding: var(--spacing-sm) var(--spacing-md);
          border: none;
          border-radius: var(--radius-sm);
          cursor: pointer;
          margin-right: var(--spacing-sm);
        }
        button:hover:not(:disabled) {
          background-color: var(--color-primary-hover);
        }
        button:disabled {
          opacity: var(--disabled-opacity);
          cursor: not-allowed;
        }
        pre {
          background: var(--color-surface);
          color: var(--color-text);
          font-family: var(--font-family-mono);
          font-size: var(--font-size-sm);
          line-height: var(--line-height-base);
          padding: var(--spacing-sm);
          border-radius: var(--radius-sm);
          border: 1px solid var(--color-border);
          overflow-x: auto;
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
    this.user = this.getAttribute('user') || 'default';
    this.textarea = this.shadowRoot.getElementById('data');
    this.output = this.shadowRoot.getElementById('output');
    this.saveBtn = this.shadowRoot.getElementById('save');
    this.exportBtn = this.shadowRoot.getElementById('export');
    this.deleteBtn = this.shadowRoot.getElementById('delete');

    fetch(`/api/v1/consent/${this.user}`)
      .then(r => r.json())
      .then(j => this.updateConsent(j.consent));

    this.saveBtn.addEventListener('click', async () => {
      let data = {};
      try {
        data = JSON.parse(this.textarea.value || '{}');
      } catch (e) {
        return;
      }
      const resp = await fetch(`/api/v1/vault/${this.user}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data })
      });
      if (resp.status === 403) {
        this.output.textContent = 'Consent required';
      }
    });

    this.exportBtn.addEventListener('click', async () => {
      const resp = await fetch(`/api/v1/vault/${this.user}/export`);
      if (resp.status === 403) {
        this.output.textContent = 'Consent required';
        return;
      }
      const json = await resp.json();
      this.output.textContent = JSON.stringify(json.data, null, 2);
    });

    this.deleteBtn.addEventListener('click', async () => {
      const resp = await fetch(`/api/v1/vault/${this.user}`, { method: 'DELETE' });
      if (resp.status === 403) {
        this.output.textContent = 'Consent required';
        return;
      }
      this.output.textContent = '';
      this.textarea.value = '';
    });
  }

  updateConsent(consent) {
    const disabled = !consent;
    this.saveBtn.disabled = disabled;
    this.exportBtn.disabled = disabled;
    this.deleteBtn.disabled = disabled;
    if (disabled) {
      this.output.textContent = 'Consent required';
    } else {
      this.output.textContent = '';
    }
  }
}

customElements.define('la-data-vault', LADataVault);
