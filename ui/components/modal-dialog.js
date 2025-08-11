// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAModalDialog extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: none;
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          align-items: center;
          justify-content: center;
        }
        :host([open]) {
          display: flex;
        }
        .backdrop {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background-color: var(--color-backdrop);
        }
        .dialog {
          position: relative;
          background-color: var(--color-background);
          color: var(--color-text);
          padding: var(--spacing-lg);
          border-radius: var(--radius-md);
          min-width: 300px;
          max-width: 90%;
          font-family: var(--font-family-sans);
        }
        .close {
          position: absolute;
          top: var(--spacing-sm);
          right: var(--spacing-sm);
          background: none;
          border: none;
          font-size: var(--font-size-lg);
          cursor: pointer;
        }
      </style>
      <div class="backdrop" part="backdrop"></div>
      <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="title">
        <button class="close" aria-label="Close">&times;</button>
        <div id="title"><slot name="title"></slot></div>
        <div><slot></slot></div>
      </div>
    `;

    const backdrop = shadow.querySelector('.backdrop');
    const close = shadow.querySelector('.close');
    const hide = () => this.removeAttribute('open');
    backdrop.addEventListener('click', hide);
    close.addEventListener('click', hide);
  }
}

customElements.define('la-modal-dialog', LAModalDialog);
