// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAInformationCard extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        .card {
          background-color: var(--color-surface);
          color: var(--color-text);
          font-family: var(--font-family-sans);
          padding: var(--spacing-md);
          border-radius: var(--radius-md);
          box-shadow: var(--shadow-card);
        }
        .title {
          font-size: var(--font-size-lg);
          font-weight: var(--font-weight-bold);
          margin-bottom: var(--spacing-sm);
        }
        .content {
          font-size: var(--font-size-base);
        }
      </style>
      <div class="card" role="group" aria-labelledby="title">
        <div id="title" class="title"><slot name="title"></slot></div>
        <div class="content"><slot></slot></div>
      </div>
    `;
  }
}

customElements.define('la-information-card', LAInformationCard);
