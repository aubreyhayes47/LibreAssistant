// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAInformationCard extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: block;
        }
        .card {
          background-color: var(--color-surface, #f9fafb);
          color: var(--color-text, #111827);
          font-family: var(--font-family-sans, sans-serif);
          padding: var(--spacing-md, 1rem);
          border-radius: var(--radius-md, 8px);
          box-shadow: var(--shadow-card, 0 1px 3px rgba(0, 0, 0, 0.1));
          border: 1px solid var(--color-border, #e5e7eb);
          transition: box-shadow 0.2s ease, transform 0.2s ease;
        }
        :host([clickable]) .card {
          cursor: pointer;
        }
        :host([clickable]) .card:hover {
          box-shadow: var(--shadow-card-hover, 0 4px 12px rgba(0, 0, 0, 0.15));
          transform: translateY(-1px);
        }
        .title {
          font-size: var(--font-size-lg, 1.125rem);
          font-weight: var(--font-weight-bold, 700);
          margin-bottom: var(--spacing-sm, 0.5rem);
          color: var(--color-text, #111827);
          display: flex;
          align-items: center;
          gap: var(--spacing-xs, 0.25rem);
        }
        .title:empty {
          display: none;
        }
        .content {
          font-size: var(--font-size-base, 1rem);
          line-height: 1.6;
          color: var(--color-text, #111827);
        }
        .actions {
          margin-top: var(--spacing-md, 1rem);
          padding-top: var(--spacing-sm, 0.5rem);
          border-top: 1px solid var(--color-border, #e5e7eb);
          display: flex;
          gap: var(--spacing-sm, 0.5rem);
          justify-content: flex-end;
        }
        .actions:empty {
          display: none;
        }
        .icon {
          width: 1.25rem;
          height: 1.25rem;
          flex-shrink: 0;
        }
        .status-indicator {
          width: 0.5rem;
          height: 0.5rem;
          border-radius: 50%;
          flex-shrink: 0;
        }
        :host([status="success"]) .status-indicator {
          background-color: var(--color-success, #10b981);
        }
        :host([status="warning"]) .status-indicator {
          background-color: var(--color-warning, #f59e0b);
        }
        :host([status="error"]) .status-indicator {
          background-color: var(--color-danger, #ef4444);
        }
        :host([status="info"]) .status-indicator {
          background-color: var(--color-primary, #3b82f6);
        }
        :host([variant="success"]) .card {
          background-color: var(--color-success-light, #ecfdf5);
          border-color: var(--color-success, #10b981);
        }
        :host([variant="warning"]) .card {
          background-color: var(--color-warning-light, #fffbeb);
          border-color: var(--color-warning, #f59e0b);
        }
        :host([variant="error"]) .card {
          background-color: var(--color-danger-light, #fef2f2);
          border-color: var(--color-danger, #ef4444);
        }
        :host([variant="info"]) .card {
          background-color: var(--color-primary-light, #eff6ff);
          border-color: var(--color-primary, #3b82f6);
        }
        :host([size="small"]) .card {
          padding: var(--spacing-sm, 0.5rem);
        }
        :host([size="small"]) .title {
          font-size: var(--font-size-base, 1rem);
          margin-bottom: var(--spacing-xs, 0.25rem);
        }
        :host([size="large"]) .card {
          padding: var(--spacing-lg, 1.5rem);
        }
        :host([size="large"]) .title {
          font-size: var(--font-size-xl, 1.25rem);
          margin-bottom: var(--spacing-md, 1rem);

        }
      </style>
      <div class="card" role="group" aria-labelledby="title">
        <div id="title" class="title">
          <div class="status-indicator" hidden></div>
          <slot name="icon"></slot>
          <slot name="title"></slot>
        </div>
        <div class="content">
          <slot></slot>
        </div>
        <div class="actions">
          <slot name="actions"></slot>
        </div>
      </div>
    `;

    this._card = shadow.querySelector('.card');
    this._statusIndicator = shadow.querySelector('.status-indicator');
  }

  connectedCallback() {
    this._updateStatusIndicator();
    
    // Add click handling if clickable
    if (this.hasAttribute('clickable')) {
      this._card.addEventListener('click', this._handleClick.bind(this));
      this._card.addEventListener('keydown', this._handleKeydown.bind(this));
      this._card.setAttribute('tabindex', '0');
      this._card.setAttribute('role', 'button');
    }
  }

  _handleClick() {
    this.dispatchEvent(new CustomEvent('card-click', {
      bubbles: true,
      detail: { card: this }
    }));
  }

  _handleKeydown(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      this._handleClick();
    }
  }

  _updateStatusIndicator() {
    const status = this.getAttribute('status');
    if (status && ['success', 'warning', 'error', 'info'].includes(status)) {
      this._statusIndicator.hidden = false;
    } else {
      this._statusIndicator.hidden = true;
    }
  }

  // Public API
  get clickable() {
    return this.hasAttribute('clickable');
  }

  set clickable(value) {
    if (value) {
      this.setAttribute('clickable', '');
    } else {
      this.removeAttribute('clickable');
    }
  }

  get status() {
    return this.getAttribute('status');
  }

  set status(value) {
    if (value) {
      this.setAttribute('status', value);
    } else {
      this.removeAttribute('status');
    }
  }

  get variant() {
    return this.getAttribute('variant');
  }

  set variant(value) {
    if (value) {
      this.setAttribute('variant', value);
    } else {
      this.removeAttribute('variant');
    }
  }

  get size() {
    return this.getAttribute('size') || 'medium';
  }

  set size(value) {
    this.setAttribute('size', value);
  }

  // Observe attribute changes
  static get observedAttributes() {
    return ['clickable', 'status', 'variant', 'size'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === 'status') {
      this._updateStatusIndicator();
    } else if (name === 'clickable') {
      if (newValue !== null) {
        this._card.addEventListener('click', this._handleClick.bind(this));
        this._card.addEventListener('keydown', this._handleKeydown.bind(this));
        this._card.setAttribute('tabindex', '0');
        this._card.setAttribute('role', 'button');
      } else {
        this._card.removeEventListener('click', this._handleClick);
        this._card.removeEventListener('keydown', this._handleKeydown);
        this._card.removeAttribute('tabindex');
        this._card.removeAttribute('role');
      }
    }
  }
}

customElements.define('la-information-card', LAInformationCard);
