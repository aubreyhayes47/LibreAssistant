// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAPrimaryButton extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: inline-block;
        }
        :host([block]) {
          display: block;
          width: 100%;
        }
        button {
          background-color: var(--color-primary, #3b82f6);
          color: var(--color-background, white);
          font-family: var(--font-family-sans, sans-serif);
          font-size: var(--font-size-base, 1rem);
          font-weight: var(--font-weight-bold, bold);
          padding: var(--spacing-sm, 0.5rem) var(--spacing-md, 1rem);
          border: none;
          border-radius: var(--radius-md, 8px);
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--spacing-xs, 0.25rem);
          min-height: 2.5rem;
          width: 100%;
        }
        button:hover:not(:disabled) {
          background-color: var(--color-primary-hover, #2563eb);
          transform: translateY(-1px);
          box-shadow: var(--shadow-button, 0 4px 8px rgba(0, 0, 0, 0.12));
        }
        button:focus {
          outline: none;
          box-shadow: 0 0 0 3px var(--color-primary-focus, rgba(59, 130, 246, 0.4));
        }
        button:active:not(:disabled) {
          transform: translateY(0);
          box-shadow: var(--shadow-button-pressed, 0 2px 4px rgba(0, 0, 0, 0.12));
        }
        button:disabled {
          background-color: var(--color-disabled, #9ca3af);
          color: var(--color-text-disabled, #d1d5db);
          cursor: not-allowed;
          transform: none;
          box-shadow: none;
        }
        :host([variant="secondary"]) button {
          background-color: var(--color-secondary, #6b7280);
          color: var(--color-background, white);
        }
        :host([variant="secondary"]) button:hover:not(:disabled) {
          background-color: var(--color-secondary-hover, #4b5563);
        }
        :host([variant="outline"]) button {
          background-color: transparent;
          color: var(--color-primary, #3b82f6);
          border: 1px solid var(--color-primary, #3b82f6);
        }
        :host([variant="outline"]) button:hover:not(:disabled) {
          background-color: var(--color-primary, #3b82f6);
          color: var(--color-background, white);
        }
        :host([variant="ghost"]) button {
          background-color: transparent;
          color: var(--color-primary, #3b82f6);
        }
        :host([variant="ghost"]) button:hover:not(:disabled) {
          background-color: var(--color-primary-light, rgba(59, 130, 246, 0.1));
        }
        :host([size="small"]) button {
          padding: var(--spacing-xs, 0.25rem) var(--spacing-sm, 0.5rem);
          font-size: var(--font-size-sm, 0.875rem);
          min-height: 2rem;
        }
        :host([size="large"]) button {
          padding: var(--spacing-md, 1rem) var(--spacing-lg, 1.5rem);
          font-size: var(--font-size-lg, 1.125rem);
          min-height: 3rem;
        }
        .spinner {
          width: 1rem;
          height: 1rem;
          border: 2px solid transparent;
          border-top: 2px solid currentColor;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .icon {
          width: 1rem;
          height: 1rem;
          fill: currentColor;

        }
      </style>
      <button type="button">
        <span class="spinner" hidden></span>
        <slot name="icon"></slot>
        <slot></slot>
      </button>
    `;

    this._button = shadow.querySelector('button');
    this._spinner = shadow.querySelector('.spinner');
  }

  connectedCallback() {
    this._updateButtonAttributes();
    
    // Forward click events
    this._button.addEventListener('click', (e) => {
      if (!this.disabled && !this.loading) {
        this.dispatchEvent(new CustomEvent('click', {
          detail: e,
          bubbles: true
        }));
      }
    });
  }

  _updateButtonAttributes() {
    // Copy relevant attributes to the button
    ['disabled', 'type', 'form', 'formaction', 'formenctype', 'formmethod', 'formnovalidate', 'formtarget'].forEach(attr => {
      if (this.hasAttribute(attr)) {
        this._button.setAttribute(attr, this.getAttribute(attr));
      } else {
        this._button.removeAttribute(attr);
      }
    });

    // Set ARIA attributes
    if (this.hasAttribute('aria-label')) {
      this._button.setAttribute('aria-label', this.getAttribute('aria-label'));
    }
    if (this.hasAttribute('aria-describedby')) {
      this._button.setAttribute('aria-describedby', this.getAttribute('aria-describedby'));
    }
  }

  // Public API
  get disabled() {
    return this.hasAttribute('disabled');
  }

  set disabled(value) {
    if (value) {
      this.setAttribute('disabled', '');
    } else {
      this.removeAttribute('disabled');
    }
  }

  get loading() {
    return this.hasAttribute('loading');
  }

  set loading(value) {
    if (value) {
      this.setAttribute('loading', '');
      this._spinner.hidden = false;
      this._button.disabled = true;
    } else {
      this.removeAttribute('loading');
      this._spinner.hidden = true;
      this._button.disabled = this.disabled;
    }
  }

  get variant() {
    return this.getAttribute('variant') || 'primary';
  }

  set variant(value) {
    this.setAttribute('variant', value);
  }

  get size() {
    return this.getAttribute('size') || 'medium';
  }

  set size(value) {
    this.setAttribute('size', value);
  }

  focus() {
    this._button.focus();
  }

  blur() {
    this._button.blur();
  }

  click() {
    if (!this.disabled && !this.loading) {
      this._button.click();
    }
  }

  // Observe attribute changes
  static get observedAttributes() {
    return ['disabled', 'loading', 'variant', 'size', 'type', 'aria-label', 'aria-describedby'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (this._button) {
      this._updateButtonAttributes();
      
      if (name === 'loading') {
        this.loading = newValue !== null;
      }
    }
  }
}

customElements.define('la-primary-button', LAPrimaryButton);
