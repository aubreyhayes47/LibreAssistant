// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAConfirmDialog extends HTMLElement {
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
          z-index: 1000;
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
          background-color: var(--color-backdrop, rgba(0, 0, 0, 0.5));
        }
        .dialog {
          position: relative;
          background-color: var(--color-background, white);
          color: var(--color-text, black);
          padding: var(--spacing-lg, 1.5rem);
          border-radius: var(--radius-md, 8px);
          min-width: var(--size-modal-min-width, 20rem);
          max-width: 90%;
          font-family: var(--font-family-sans, sans-serif);
          box-shadow: var(--shadow-modal, 0 4px 12px rgba(0, 0, 0, 0.15));
          /* Use CSS Grid for better layout */
          display: grid;
          grid-template-rows: auto 1fr auto;
          gap: var(--spacing-sm, 0.5rem);
        }
        .close {
          position: absolute;
          top: var(--spacing-sm, 0.5rem);
          right: var(--spacing-sm, 0.5rem);
          background: none;
          border: none;
          font-size: var(--font-size-lg, 1.25rem);
          cursor: pointer;
          color: var(--color-text, black);
        }
        .title {
          font-size: var(--font-size-lg, 1.25rem);
          font-weight: var(--font-weight-bold, bold);
          margin-bottom: var(--spacing-md, 1rem);
        }
        .message {
          margin-bottom: var(--spacing-lg, 1.5rem);
          line-height: 1.5;
        }
        .actions {
          display: flex;
          justify-content: flex-end;
          gap: var(--spacing-sm, 0.5rem);
        }
        button {
          font-family: var(--font-family-sans, sans-serif);
          font-size: var(--font-size-base, 1rem);
          padding: var(--spacing-sm, 0.5rem) var(--spacing-md, 1rem);
          border: none;
          border-radius: var(--radius-sm, 4px);
          cursor: pointer;
          transition: background-color 0.2s ease;
        }
        .cancel {
          background-color: var(--color-secondary, #6b7280);
          color: var(--color-background, white);
        }
        .cancel:hover {
          background-color: var(--color-secondary-hover, #4b5563);
        }
        .confirm {
          background-color: var(--color-primary, #3b82f6);
          color: var(--color-background, white);
        }
        .confirm:hover {
          background-color: var(--color-primary-hover, #2563eb);
        }
      </style>
      <div class="backdrop" part="backdrop"></div>
      <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="title" aria-describedby="message">
        <button class="close" aria-label="Close">&times;</button>
        <div id="title" class="title"><slot name="title">Confirm</slot></div>
        <div id="message" class="message"><slot></slot></div>
        <div class="actions">
          <button class="cancel" id="cancel-btn">Cancel</button>
          <button class="confirm" id="confirm-btn">OK</button>
        </div>
      </div>
    `;

    this._resolvePromise = null;
    this._rejectPromise = null;
    this._lastFocusedElement = null;
    this._focusableElements = [];

    // Event listeners
    const backdrop = shadow.querySelector('.backdrop');
    const closeBtn = shadow.querySelector('.close');
    const cancelBtn = shadow.querySelector('#cancel-btn');
    const confirmBtn = shadow.querySelector('#confirm-btn');

    const hide = (result = false) => {
      this.removeAttribute('open');
      
      // Restore focus
      if (this._lastFocusedElement && this._lastFocusedElement.focus) {
        this._lastFocusedElement.focus();
      }
      
      if (this._resolvePromise) {
        this._resolvePromise(result);
        this._resolvePromise = null;
        this._rejectPromise = null;
      }
    };

    backdrop.addEventListener('click', () => hide(false));
    closeBtn.addEventListener('click', () => hide(false));
    cancelBtn.addEventListener('click', () => hide(false));
    confirmBtn.addEventListener('click', () => hide(true));

    // Handle escape key and focus trapping
    this.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        hide(false);
      } else if (e.key === 'Tab') {
        this._handleTabKey(e);
      }
    });
  }

  _handleTabKey(e) {
    this._updateFocusableElements();
    
    if (this._focusableElements.length === 0) return;

    const firstElement = this._focusableElements[0];
    const lastElement = this._focusableElements[this._focusableElements.length - 1];

    if (e.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      }
    } else {
      // Tab
      if (document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  }

  _updateFocusableElements() {
    const selectors = [
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      'a[href]',
      '[tabindex]:not([tabindex="-1"])'
    ];

    const dialog = this.shadowRoot.querySelector('.dialog');
    this._focusableElements = Array.from(
      dialog.querySelectorAll(selectors.join(', '))
    ).filter(el => {
      return el.offsetWidth > 0 || el.offsetHeight > 0 || el === document.activeElement;
    });
  }

  connectedCallback() {
    // Focus management
    if (this.hasAttribute('open')) {
      this.shadowRoot.querySelector('#confirm-btn').focus();
    }
  }

  // Set custom button text
  setCancelText(text) {
    this.shadowRoot.querySelector('#cancel-btn').textContent = text;
  }

  setConfirmText(text) {
    this.shadowRoot.querySelector('#confirm-btn').textContent = text;
  }

  // Show the dialog and return a promise
  show(message, title = 'Confirm') {
    return new Promise((resolve, reject) => {
      this._resolvePromise = resolve;
      this._rejectPromise = reject;

      // Store current focus before opening dialog
      this._lastFocusedElement = document.activeElement;

      // Set content if provided
      if (message) {
        this.textContent = message;
      }
      if (title && title !== 'Confirm') {
        const titleSlot = this.querySelector('[slot="title"]');
        if (titleSlot) {
          titleSlot.textContent = title;
        } else {
          const titleEl = document.createElement('span');
          titleEl.setAttribute('slot', 'title');
          titleEl.textContent = title;
          this.appendChild(titleEl);
        }
      }

      this.setAttribute('open', '');
      
      // Focus management
      requestAnimationFrame(() => {
        this._updateFocusableElements();
        if (this._focusableElements.length > 0) {
          this._focusableElements[0].focus();
        } else {
          this.shadowRoot.querySelector('#confirm-btn').focus();
        }
      });
    });
  }

  hide() {
    this.removeAttribute('open');
    
    // Restore focus
    if (this._lastFocusedElement && this._lastFocusedElement.focus) {
      this._lastFocusedElement.focus();
    }
    
    if (this._resolvePromise) {
      this._resolvePromise(false);
      this._resolvePromise = null;
      this._rejectPromise = null;
    }
  }
}

customElements.define('la-confirm-dialog', LAConfirmDialog);

// Utility function for backward compatibility
window.showConsentModal = function (message, title = 'Confirm') {
  const dialog = document.createElement('la-confirm-dialog');
  document.body.appendChild(dialog);
  return dialog.show(message, title).finally(() => {
    dialog.remove();
  });
};
