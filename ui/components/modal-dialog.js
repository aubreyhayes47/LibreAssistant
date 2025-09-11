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
          animation: fadeIn 0.2s ease-out;
        }
        .dialog {
          position: relative;
          background-color: var(--color-background, white);
          color: var(--color-text, black);
          padding: var(--spacing-lg, 1.5rem);
          border-radius: var(--radius-md, 8px);
          min-width: var(--size-modal-min-width, 20rem);
          max-width: var(--size-modal-max-width, 90vw);
          max-height: 90vh;
          font-family: var(--font-family-sans, sans-serif);
          box-shadow: var(--shadow-modal, 0 4px 12px rgba(0, 0, 0, 0.15));
          animation: slideIn 0.2s ease-out;
          overflow: auto;
          /* Use CSS Grid for better content layout */
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
          color: var(--color-text-secondary, #6b7280);
          width: var(--size-icon-lg, 1.5rem);
          height: var(--size-icon-lg, 1.5rem);
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: var(--radius-sm, 4px);
          transition: background-color 0.2s ease, color 0.2s ease;
        }
        .close:hover {
          background-color: var(--color-surface, #f3f4f6);
          color: var(--color-text, black);
        }
        .close:focus {
          outline: 2px solid var(--color-primary, #3b82f6);
          outline-offset: 2px;
        }
        .title {
          font-size: var(--font-size-lg, 1.25rem);
          font-weight: var(--font-weight-bold, bold);
          margin-bottom: var(--spacing-md, 1rem);
          padding-right: var(--spacing-lg, 1.5rem);
        }
        .content {
          line-height: 1.6;
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideIn {
          from { 
            opacity: 0;
            transform: translateY(-20px) scale(0.95);
          }
          to { 
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        
        /* Mobile responsive adjustments */
        @media (max-width: 768px) {
          .dialog {
            min-width: 280px;
            margin: var(--mobile-margin, var(--spacing-sm));
            padding: var(--mobile-padding, var(--spacing-md));
            max-width: calc(100vw - 2 * var(--mobile-margin, var(--spacing-sm)));
          }
          .close {
            width: var(--touch-target-min, 44px);
            height: var(--touch-target-min, 44px);
            font-size: var(--font-size-lg);
          }
          .title {
            font-size: var(--font-size-lg);
            padding-right: calc(var(--touch-target-min, 44px) + var(--spacing-sm));
          }
        }
        
        @media (max-width: 480px) {
          .dialog {
            max-width: calc(100vw - var(--spacing-xs));
            max-height: calc(100vh - var(--spacing-xs));
            margin: calc(var(--spacing-xs) / 2);
          }
        }
        
        :host([size="small"]) .dialog {
          min-width: 15rem;
          max-width: 25rem;
        }
        :host([size="large"]) .dialog {
          min-width: 37.5rem;
          max-width: 80vw;
        }
        :host([size="full"]) .dialog {
          width: 95vw;
          height: 95vh;
          max-width: none;
          max-height: none;
        }
        
        /* Mobile overrides for dialog sizes */
        @media (max-width: 768px) {
          :host([size="small"]) .dialog {
            min-width: 280px;
            max-width: calc(100vw - 2 * var(--mobile-margin, var(--spacing-sm)));
          }
          :host([size="large"]) .dialog {
            min-width: 300px;
            max-width: calc(100vw - 2 * var(--mobile-margin, var(--spacing-sm)));
          }
        }
      </style>
      <div class="backdrop" part="backdrop"></div>
      <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="title" aria-describedby="content">
        <button class="close" aria-label="Close dialog">&times;</button>
        <div id="title" class="title"><slot name="title"></slot></div>
        <div id="content" class="content"><slot></slot></div>
      </div>
    `;

    this._backdrop = shadow.querySelector('.backdrop');
    this._closeBtn = shadow.querySelector('.close');
    this._dialog = shadow.querySelector('.dialog');
    this._isOpen = false;
    this._lastFocusedElement = null;
    this._focusableElements = [];

    this._setupEventListeners();
  }

  _setupEventListeners() {
    const hide = () => this.hide();
    
    this._backdrop.addEventListener('click', hide);
    this._closeBtn.addEventListener('click', hide);

    // Handle escape key and focus trapping
    this.addEventListener('keydown', (e) => {
      if (!this._isOpen) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        hide();
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

    this._focusableElements = Array.from(
      this._dialog.querySelectorAll(selectors.join(', '))
    ).filter(el => {
      return el.offsetWidth > 0 || el.offsetHeight > 0 || el === document.activeElement;
    });
  }

  connectedCallback() {
    // Component is now connected to DOM
  }

  // Public API
  show() {
    if (this._isOpen) return;

    this._lastFocusedElement = document.activeElement;
    this._isOpen = true;
    this.setAttribute('open', '');
    
    // Announce to screen readers
    const title = this.querySelector('[slot="title"]')?.textContent || 'Dialog';
    this._announceToScreenReader(`${title} dialog opened`);
    
    // Focus management
    requestAnimationFrame(() => {
      this._updateFocusableElements();
      if (this._focusableElements.length > 0) {
        this._focusableElements[0].focus();
      } else {
        this._closeBtn.focus();
      }
    });

    // Dispatch event
    this.dispatchEvent(new CustomEvent('dialog-open', {
      bubbles: true,
      detail: { dialog: this }
    }));
  }

  hide() {
    if (!this._isOpen) return;

    this._isOpen = false;
    this.removeAttribute('open');

    // Announce to screen readers
    const title = this.querySelector('[slot="title"]')?.textContent || 'Dialog';
    this._announceToScreenReader(`${title} dialog closed`);

    // Restore focus
    if (this._lastFocusedElement && this._lastFocusedElement.focus) {
      this._lastFocusedElement.focus();
    }

    // Dispatch event
    this.dispatchEvent(new CustomEvent('dialog-close', {
      bubbles: true,
      detail: { dialog: this }
    }));
  }

  _announceToScreenReader(message) {
    // Create or update a live region for announcements
    if (!this._liveRegion) {
      this._liveRegion = document.createElement('div');
      this._liveRegion.setAttribute('aria-live', 'polite');
      this._liveRegion.setAttribute('aria-atomic', 'true');
      this._liveRegion.style.position = 'absolute';
      this._liveRegion.style.left = '-10000px';
      this._liveRegion.style.width = '1px';
      this._liveRegion.style.height = '1px';
      this._liveRegion.style.overflow = 'hidden';
      document.body.appendChild(this._liveRegion);
    }
    
    this._liveRegion.textContent = message;
    
    // Clear the message after announcement
    setTimeout(() => {
      if (this._liveRegion) {
        this._liveRegion.textContent = '';
      }
    }, 1000);
  }

  toggle() {
    if (this._isOpen) {
      this.hide();
    } else {
      this.show();
    }
  }

  get open() {
    return this._isOpen;
  }

  set open(value) {
    if (value) {
      this.show();
    } else {
      this.hide();
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
    return ['open', 'size'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === 'open') {
      if (newValue !== null && !this._isOpen) {
        this.show();
      } else if (newValue === null && this._isOpen) {
        this.hide();
      }
    }
  }
}

customElements.define('la-modal-dialog', LAModalDialog);
