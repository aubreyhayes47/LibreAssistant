// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAInputField extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        label {
          display: flex;
          flex-direction: column;
          font-family: var(--font-family-sans);
          font-size: var(--font-size-sm);
          line-height: var(--line-height-base);
          color: var(--color-text);
        }
        input {
          padding: var(--spacing-sm);
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          line-height: var(--line-height-base);
          border: 1px solid var(--color-secondary);
          border-radius: var(--radius-sm);
          background-color: var(--color-background);
          color: var(--color-text);
        }
        input:focus {
          outline: var(--focus-ring);
          outline-offset: var(--focus-ring-offset);
          border-color: var(--color-primary);
        }
      </style>
      <label>
        <span><slot name="label"></slot></span>
        <input type="text" />
      </label>
    `;
  }

  get value() {
    return this.shadowRoot.querySelector('input').value;
  }

  set value(val) {
    this.shadowRoot.querySelector('input').value = val;
  }
}

customElements.define('la-input-field', LAInputField);
