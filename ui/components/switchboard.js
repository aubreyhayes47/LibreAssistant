// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LASwitchboard extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        .request { display: flex; gap: var(--spacing-sm); }
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
        }
        .activity {
          margin-top: var(--spacing-md);
          font-family: var(--font-family-sans);
        }
      </style>
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

    await this.loadPlugins();

    send.addEventListener('click', async () => {
      const value = input.value.trim();
      if (!value) return;

      const reqItem = document.createElement('li');
      reqItem.textContent = value;
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
          res = await fetch('/api/v1/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider: 'cloud', prompt: value })
          });
        }

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
        resItem.textContent =
          typeof result === 'string' ? result : JSON.stringify(result);
        log.appendChild(resItem);
      } catch (err) {
        const errItem = document.createElement('li');
        errItem.textContent = `Error: ${err.message}`;
        errItem.style.color = 'red';
        log.appendChild(errItem);
      }
    });
  }

  async loadPlugins() {
    const select = this.shadowRoot.getElementById('plugin');
    try {
      const res = await fetch('/api/v1/mcp/servers');
      if (!res.ok) return;
      const data = await res.json();
      (data.servers || []).forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.name;
        opt.textContent = p.name;
        select.appendChild(opt);
      });
    } catch {
      // ignore errors
    }
  }
}

customElements.define('la-switchboard', LASwitchboard);
