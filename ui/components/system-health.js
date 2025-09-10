// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LASystemHealth extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--font-family-sans);
          color: var(--color-text);

        }
        h2 {
          font-size: var(--font-size-lg);
          font-weight: var(--font-weight-bold);
          margin-bottom: var(--spacing-md);
          color: var(--color-text);
          line-height: var(--line-height-tight);
        }
        h3 {
          font-size: var(--font-size-base);
          font-weight: var(--font-weight-bold);
          margin-bottom: var(--spacing-sm);
          margin-top: var(--spacing-md);
          color: var(--color-text);
        }
        p {
          margin: var(--spacing-sm) 0;
          font-size: var(--font-size-base);
          color: var(--color-text);
        }
        ul {
          list-style: disc;
          padding-left: var(--spacing-md);
          margin: 0;
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
        }
        li {
          margin-bottom: var(--spacing-xs);
          color: var(--color-text);
        }
      </style>
      <h2>System Health</h2>
      <div id="content"></div>
    `;
  }

  async connectedCallback() {
    await this.refresh();
  }

  async refresh() {
    try {
      const resp = await fetch('/api/v1/health');
      if (!resp.ok) return;
      const data = await resp.json();
      const content = this.shadowRoot.getElementById('content');
      content.innerHTML = `
        <p>Status: ${data.status}</p>
        <p>Uptime: ${Math.round(data.uptime)}</p>
        <p>Requests: ${data.requests}</p>
        <h3>Errors</h3>
        <ul id="errors"></ul>
      `;
      const list = this.shadowRoot.getElementById('errors');
      data.errors.forEach(e => {
        const li = document.createElement('li');
        li.textContent = e;
        list.appendChild(li);
      });
    } catch (err) {
      // ignore errors for now
    }
  }
}

customElements.define('la-system-health', LASystemHealth);
