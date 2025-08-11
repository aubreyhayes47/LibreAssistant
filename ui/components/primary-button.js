// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAPrimaryButton extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        button {
          background-color: var(--color-primary);
          color: var(--color-background);
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          font-weight: var(--font-weight-bold);
          padding: var(--spacing-sm) var(--spacing-md);
          border: none;
          border-radius: var(--radius-md);
          cursor: pointer;
        }
        button:hover,
        button:focus {
          background-color: var(--color-primary-hover);
          outline: none;
        }
      </style>
      <button type="button"><slot></slot></button>
    `;
  }
}

customElements.define('la-primary-button', LAPrimaryButton);
