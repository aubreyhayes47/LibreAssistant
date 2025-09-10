// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAPastRequests extends HTMLElement {
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
          font-family: var(--font-family-mono);
          font-size: var(--font-size-sm);
          word-wrap: break-word;
        }
        ul:empty::before {
          content: "No past requests found.";
          color: var(--color-secondary);
          font-style: italic;
          display: block;
          padding: var(--spacing-md);
          text-align: center;
        }
      </style>
      <ul id="list"></ul>
    `;
  }

  async connectedCallback() {
    const user = this.getAttribute('user-id') || 'anonymous';
    try {
      const res = await fetch(`/api/v1/history/${user}`);
      if (!res.ok) return;
      const data = await res.json();
      const list = this.shadowRoot.getElementById('list');
      data.history.forEach(entry => {
        const li = document.createElement('li');
        li.textContent = `${entry.plugin}: ${JSON.stringify(entry.payload)}`;
        list.appendChild(li);
      });
    } catch (err) {
      // ignore errors for now
    }
  }
}

customElements.define('la-past-requests', LAPastRequests);
