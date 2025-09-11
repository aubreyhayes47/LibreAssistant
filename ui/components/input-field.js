// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAInputField extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: block;
        }
        label {
          display: flex;
          flex-direction: column;
          font-family: var(--font-family-sans, sans-serif);
          font-size: var(--font-size-sm, 0.875rem);
          color: var(--color-text, black);
          gap: var(--spacing-xs, 0.25rem);
        }
        .label-text {
          font-weight: var(--font-weight-medium, 500);
        }
        input, textarea {
          padding: var(--spacing-sm, 0.5rem);
          font-family: var(--font-family-sans, sans-serif);
          font-size: var(--font-size-base, 1rem);
          border: 1px solid var(--color-border, #d1d5db);
          border-radius: var(--radius-sm, 4px);
          background-color: var(--color-input-background, white);
          color: var(--color-text, black);
          transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        input:focus, textarea:focus {
          outline: none;
          border-color: var(--color-primary, #3b82f6);
          box-shadow: 0 0 0 3px var(--color-primary-focus, rgba(59, 130, 246, 0.1));
        }
        input:invalid, textarea:invalid {
          border-color: var(--color-danger, #ef4444);
        }
        input:disabled, textarea:disabled {
          background-color: var(--color-input-disabled, #f3f4f6);
          color: var(--color-text-disabled, #6b7280);
          cursor: not-allowed;
        }
        .error {
          color: var(--color-danger, #ef4444);
          font-size: var(--font-size-xs, 0.75rem);
          margin-top: var(--spacing-xs, 0.25rem);
        }
        .help {
          color: var(--color-text-secondary, #6b7280);
          font-size: var(--font-size-xs, 0.75rem);
          margin-top: var(--spacing-xs, 0.25rem);
        }
        textarea {
          resize: vertical;
          min-height: var(--size-card-min-height, 3rem);
        }
        /* Touch-friendly sizing */
        @media (hover: none) and (pointer: coarse) {
          input, textarea {
            min-height: 44px; /* WCAG touch target size */
            padding: var(--spacing-md, 1rem);
            font-size: var(--font-size-lg, 1.125rem);
          }
          textarea {
            min-height: 88px; /* Double the minimum for text areas */
          }
        }
        
        /* Mobile responsive adjustments */
        @media (max-width: 768px) {
          input, textarea {
            min-height: var(--touch-target-min, 44px);
            padding: var(--spacing-sm, 0.5rem) var(--spacing-md, 1rem);
            font-size: var(--font-size-base, 1rem);
          }
          
          label {
            font-size: var(--font-size-base, 1rem);
          }
          
          .error, .help {
            font-size: var(--font-size-sm, 0.875rem);
          }
          
          textarea {
            min-height: calc(var(--touch-target-min, 44px) * 2);
          }
        }
      </style>
      <label>
        <span class="label-text"><slot name="label"></slot></span>
        <input type="text" />
        <div class="error" id="error" hidden></div>
        <div class="help" id="help"><slot name="help"></slot></div>
      </label>
    `;

    this._input = shadow.querySelector('input');
    this._error = shadow.querySelector('#error');
    this._help = shadow.querySelector('#help');
  }

  connectedCallback() {
    this._updateInputAttributes();
    this._input.addEventListener('input', this._handleInput.bind(this));
    this._input.addEventListener('blur', this._handleBlur.bind(this));
    
    // Add touch support for better mobile interaction
    this._setupTouchHandlers();
  }

  _setupTouchHandlers() {
    // Improve touch focus behavior
    this._input.addEventListener('touchstart', (e) => {
      // Add slight delay to ensure proper focus on mobile
      setTimeout(() => {
        if (document.activeElement !== this._input) {
          this._input.focus();
        }
      }, 50);
    }, { passive: true });

    // Handle touch interaction for validation feedback
    this._input.addEventListener('touchend', (e) => {
      // Validate on touch end for immediate feedback
      setTimeout(() => this._validate(), 100);
    }, { passive: true });
  }

  _updateInputAttributes() {
    // Handle type attribute
    const type = this.getAttribute('type') || 'text';
    if (type === 'textarea') {
      const textarea = document.createElement('textarea');
      textarea.value = this._input.value;
      this._copyAttributes(this._input, textarea);
      this._input.parentNode.replaceChild(textarea, this._input);
      this._input = textarea;
    } else {
      this._input.type = type;
    }

    // Copy other attributes
    ['placeholder', 'required', 'disabled', 'readonly', 'min', 'max', 'step', 'pattern', 'maxlength', 'minlength'].forEach(attr => {
      if (this.hasAttribute(attr)) {
        this._input.setAttribute(attr, this.getAttribute(attr));
      }
    });

    // Set ARIA attributes
    if (this.hasAttribute('required')) {
      this._input.setAttribute('aria-required', 'true');
    }
    
    const labelText = this.querySelector('[slot="label"]')?.textContent || this.getAttribute('label');
    if (labelText) {
      this._input.setAttribute('aria-label', labelText);
    }
  }

  _copyAttributes(from, to) {
    Array.from(from.attributes).forEach(attr => {
      to.setAttribute(attr.name, attr.value);
    });
  }

  _handleInput(event) {
    this._clearError();
    this.dispatchEvent(new CustomEvent('input', {
      detail: { value: this.value },
      bubbles: true
    }));
  }

  _handleBlur(event) {
    this._validate();
    this.dispatchEvent(new CustomEvent('blur', {
      detail: { value: this.value },
      bubbles: true
    }));
  }

  _validate() {
    if (this._input.checkValidity()) {
      this._clearError();
      return true;
    } else {
      this._showError(this._input.validationMessage);
      return false;
    }
  }

  _showError(message) {
    this._error.textContent = message;
    this._error.hidden = false;
    this._input.setAttribute('aria-invalid', 'true');
    this._input.setAttribute('aria-describedby', 'error help');
    
    // Announce error to screen readers
    this._announceToScreenReader(`Error: ${message}`, true);
  }

  _clearError() {
    this._error.hidden = true;
    this._input.removeAttribute('aria-invalid');
    this._input.setAttribute('aria-describedby', 'help');
  }

  _announceToScreenReader(message, urgent = false) {
    // Create or update a live region for announcements
    if (!this._liveRegion) {
      this._liveRegion = document.createElement('div');
      this._liveRegion.setAttribute('aria-live', urgent ? 'assertive' : 'polite');
      this._liveRegion.setAttribute('aria-atomic', 'true');
      this._liveRegion.style.position = 'absolute';
      this._liveRegion.style.left = '-10000px';
      this._liveRegion.style.width = '1px';
      this._liveRegion.style.height = '1px';
      this._liveRegion.style.overflow = 'hidden';
      document.body.appendChild(this._liveRegion);
    }
    
    // Update aria-live if urgency changed
    this._liveRegion.setAttribute('aria-live', urgent ? 'assertive' : 'polite');
    this._liveRegion.textContent = message;
    
    // Clear the message after announcement
    setTimeout(() => {
      if (this._liveRegion) {
        this._liveRegion.textContent = '';
      }
    }, 1000);
  }

  // Public API
  get value() {
    return this._input.value;
  }

  set value(val) {
    this._input.value = val;
  }

  get validity() {
    return this._input.validity;
  }

  get validationMessage() {
    return this._input.validationMessage;
  }

  checkValidity() {
    return this._validate();
  }

  focus() {
    this._input.focus();
  }

  blur() {
    this._input.blur();
  }

  setCustomValidity(message) {
    this._input.setCustomValidity(message);
    if (message) {
      this._showError(message);
    } else {
      this._clearError();
    }
  }

  // Observe attribute changes
  static get observedAttributes() {
    return ['type', 'placeholder', 'required', 'disabled', 'readonly', 'min', 'max', 'step', 'pattern', 'maxlength', 'minlength'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (this._input) {
      this._updateInputAttributes();
    }
  }
}

customElements.define('la-input-field', LAInputField);
