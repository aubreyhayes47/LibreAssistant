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
        button {
          background-color: var(--color-primary);
          color: var(--color-background);
          border: none;
          border-radius: var(--radius-sm);
          padding: var(--spacing-sm) var(--spacing-md);
          cursor: pointer;
        }
        .plugins {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: var(--spacing-sm);
          margin-top: var(--spacing-md);
        }
        .plugins slot {
          border: 1px dashed var(--color-border);
          border-radius: var(--radius-sm);
          min-height: 40px;
        }
        .activity {
          margin-top: var(--spacing-md);
          font-family: var(--font-family-sans);
        }
      </style>
      <div class="request">
        <textarea id="input" aria-label="Request"></textarea>
        <button id="send">Send</button>
      </div>
      <div class="plugins">
        <slot name="plugin-1"></slot>
        <slot name="plugin-2"></slot>
        <slot name="plugin-3"></slot>
        <slot name="plugin-4"></slot>
        <slot name="plugin-5"></slot>
        <slot name="plugin-6"></slot>
        <slot name="plugin-7"></slot>
        <slot name="plugin-8"></slot>
        <slot name="plugin-9"></slot>
        <slot name="plugin-10"></slot>
        <slot name="plugin-11"></slot>
        <slot name="plugin-12"></slot>
      </div>
      <div class="activity">
        <ul id="log"></ul>
      </div>
    `;
  }

  connectedCallback() {
    const send = this.shadowRoot.getElementById('send');
    const input = this.shadowRoot.getElementById('input');
    const log = this.shadowRoot.getElementById('log');
    send.addEventListener('click', () => {
      const value = input.value.trim();
      if (value) {
        const li = document.createElement('li');
        li.textContent = value;
        log.appendChild(li);
        input.value = '';
      }
    });
  }
}

customElements.define('la-switchboard', LASwitchboard);
