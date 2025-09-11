// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAOnboardingFlow extends HTMLElement {
  constructor() {
    super();
    this.step = 0;
    this.isLoading = false;
    this.errorMessage = '';
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--font-family-sans);
          color: var(--color-text);
        }
        [hidden] { display: none; }
        .step {
          padding: var(--spacing-md);
        }
        .progress-bar {
          width: 100%;
          height: 4px;
          background: var(--color-border);
          border-radius: 2px;
          margin-bottom: var(--spacing-md);
          overflow: hidden;
        }
        .progress-fill {
          height: 100%;
          background: var(--color-primary);
          transition: width 0.3s ease;
        }
        .step-info {
          background: var(--color-surface);
          padding: var(--spacing-sm);
          border-radius: var(--radius-sm);
          margin-bottom: var(--spacing-md);
          border-left: 3px solid var(--color-primary);
        }
        .error-message {
          background: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
          padding: var(--spacing-sm);
          border-radius: var(--radius-sm);
          margin: var(--spacing-sm) 0;
        }
        .loading {
          opacity: 0.6;
          pointer-events: none;
        }
        h2 {
          font-size: var(--font-size-lg);
          font-weight: var(--font-weight-bold);
          margin-bottom: var(--spacing-md);
          color: var(--color-text);
        }
        select, input {
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          padding: var(--spacing-sm);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
          background: var(--color-background);
          color: var(--color-text);
          width: 100%;
          max-width: 300px;
        }
        select:focus, input:focus {
          outline: 2px solid var(--color-primary);
          border-color: var(--color-primary);
        }
        p {
          font-size: var(--font-size-base);
          margin: var(--spacing-sm) 0;
          color: var(--color-text);
        }
        .controls {
          display: flex;
          justify-content: space-between;
          margin-top: var(--spacing-md);
        }
        button {
          background-color: var(--color-primary);
          color: var(--color-background);
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          padding: var(--spacing-sm) var(--spacing-md);
          border: none;
          border-radius: var(--radius-md);
          cursor: pointer;
        }
        button:hover:not(:disabled) {
          background-color: var(--color-primary-hover);
        }
        button[disabled] {
          opacity: 0.5;
          cursor: default;
        }
        .btn-loading {
          position: relative;
        }
        .btn-loading::after {
          content: '';
          position: absolute;
          width: 16px;
          height: 16px;
          top: 50%;
          left: 50%;
          margin-left: -8px;
          margin-top: -8px;
          border: 2px solid transparent;
          border-top: 2px solid currentColor;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        ul {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: var(--spacing-sm);
        }
        li {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
        }
        label {
          font-size: var(--font-size-base);
          color: var(--color-text);
          cursor: pointer;
        }
        #summary {
          background: var(--color-surface);
          padding: var(--spacing-md);
          border-radius: var(--radius-sm);
          margin: var(--spacing-md) 0;
        }
        .sr-only {
          position: absolute;
          width: 1px;
          height: 1px;
          padding: 0;
          margin: -1px;
          overflow: hidden;
          clip: rect(0, 0, 0, 0);
          white-space: nowrap;
          border: 0;
        }
      </style>
      <div class="progress-bar" role="progressbar" aria-valuenow="1" aria-valuemin="1" aria-valuemax="6" aria-label="Onboarding progress">
        <div class="progress-fill" id="progress"></div>
      </div>
      <div id="error-container" aria-live="polite" aria-atomic="true"></div>
      <div class="step" data-step="0" role="main" aria-labelledby="step-0-title">
        <h2 id="step-0-title">Step 1: Choose AI Engine</h2>
        <div class="step-info" id="step-0-description">
          <p>Select whether to use cloud-based AI services or local AI models. Cloud providers offer more powerful models but send data externally.</p>
        </div>
        <select id="engine" aria-labelledby="step-0-title" aria-describedby="step-0-description" aria-required="true">

          <option value="">-- Please select --</option>
          <option value="cloud">Cloud (OpenAI, Anthropic, etc.)</option>
          <option value="local">Local (Ollama, etc.)</option>
        </select>
      </div>
      <div class="step" data-step="1" hidden role="main" aria-labelledby="step-1-title">
        <h2 id="step-1-title">Step 2: Provider Setup</h2>
        <div class="step-info" id="step-1-description">
          <p>Enter your API key for the selected provider. This will be securely stored and used to authenticate with the AI service.</p>
        </div>
        <input id="apikey" type="password" placeholder="Enter your API key" aria-labelledby="step-1-title" aria-describedby="step-1-description step-1-security-note" aria-required="true" />
        <p id="step-1-security-note"><small>Your API key is encrypted and stored locally.</small></p>
      </div>
      <div class="step" data-step="2" hidden role="main" aria-labelledby="step-2-title">
        <h2 id="step-2-title">Step 3: Configure Plugins</h2>
        <div class="step-info" id="step-2-description">
          <p>Choose which plugins to enable. Plugins extend LibreAssistant's capabilities but may access additional data.</p>
        </div>
        <ul id="plugin-list" role="group" aria-labelledby="step-2-title" aria-describedby="step-2-description"></ul>
      </div>
      <div class="step" data-step="3" hidden role="main" aria-labelledby="step-3-title">
        <h2 id="step-3-title">Step 4: Review Configuration</h2>
        <div class="step-info" id="step-3-description">
          <p>Review your settings before proceeding. You can modify these later in settings.</p>
        </div>
        <div id="summary" aria-labelledby="step-3-title" aria-describedby="step-3-description"></div>
      </div>
      <div class="step" data-step="4" hidden role="main" aria-labelledby="step-4-title">
        <h2 id="step-4-title">Step 5: Privacy Agreement</h2>
        <div class="step-info" id="step-4-description">
          <p>Please review and accept our privacy policy regarding data handling.</p>
        </div>
        <div style="background: var(--color-surface); padding: var(--spacing-md); border-radius: var(--radius-sm); margin: var(--spacing-md) 0;" id="privacy-policy-content">
          <h3>Data Usage</h3>
          <p>LibreAssistant will:</p>
          <ul>
            <li>Send your messages to your chosen AI provider</li>
            <li>Share data with enabled plugins as needed</li>
            <li>Store conversation history locally</li>
            <li>Never share your data with third parties without consent</li>
          </ul>
        </div>
        <label><input id="privacy" type="checkbox" aria-describedby="privacy-policy-content" aria-required="true" /> I understand and agree to the privacy policy</label>
      </div>
      <div class="step" data-step="5" hidden role="main" aria-labelledby="step-5-title">
        <h2 id="step-5-title">Setup Complete!</h2>
        <div class="step-info" id="step-5-description">
          <p>LibreAssistant is now configured and ready to use.</p>
        </div>
        <div id="completion-summary" aria-labelledby="step-5-title" aria-describedby="step-5-description"></div>

        <p>You can change these settings anytime in the preferences.</p>
      </div>
      <div class="controls">
        <button id="back" aria-label="Go to previous step">Back</button>
        <button id="next" aria-label="Go to next step">Next</button>
      </div>
    `;
  }

  async connectedCallback() {
    this.backBtn = this.shadowRoot.getElementById('back');
    this.nextBtn = this.shadowRoot.getElementById('next');
    this.steps = this.shadowRoot.querySelectorAll('.step');
    this.progressFill = this.shadowRoot.getElementById('progress');
    this.progressBar = this.shadowRoot.querySelector('[role="progressbar"]');
    this.errorContainer = this.shadowRoot.getElementById('error-container');
    this.engineSelect = this.shadowRoot.getElementById('engine');
    this.keyInput = this.shadowRoot.getElementById('apikey');
    this.pluginList = this.shadowRoot.getElementById('plugin-list');
    this.summary = this.shadowRoot.getElementById('summary');
    this.completionSummary = this.shadowRoot.getElementById('completion-summary');
    this.privacyCheck = this.shadowRoot.getElementById('privacy-checkbox');
    
    await this.loadPlugins();
    this.update();
    
    this.backBtn.addEventListener('click', () => {
      if (this.step > 0) {
        this.step -= 1;
        this.clearError();
        this.update();
      }
    });
    
    this.nextBtn.addEventListener('click', async () => {
      if (this.isLoading) return;
      
      this.clearError();
      
      // Validate current step
      if (!this.validateStep()) {
        return;
      }
      
      this.setLoading(true);
      
      try {
        if (this.step === 0) {
          this.provider = this.engineSelect.value;
        } else if (this.step === 1) {
          await this.validateApiKey();
        } else if (this.step === 4) {
          if (!this.privacyCheck.checked) {
            this.showError('Please accept the privacy policy to continue.');
            return;
          }
        }
        
        if (this.step < this.steps.length - 1) {
          this.step += 1;
          if (this.step === 3) {
            this.renderSummary();
          }
          if (this.step === 5) {
            this.renderCompletionSummary();
            this.complete();
          }
          this.update();
        }
      } catch (error) {
        this.showError(error.message || 'An unexpected error occurred. Please try again.');
      } finally {
        this.setLoading(false);
      }
    });

    // Add keyboard navigation support
    this._setupKeyboardNavigation();
  }

  async loadPlugins() {
    try {
      this.setLoading(true);
      const res = await fetch('/api/v1/mcp/servers');
      if (!res.ok) {
        throw new Error(`Failed to load plugins: ${res.status} ${res.statusText}`);
      }
      const data = await res.json();
      this.plugins = data.servers || [];
    } catch (error) {
      this.plugins = [];
      console.warn('Failed to load plugins:', error);
      // Don't show error for plugin loading as it's not critical for setup
    } finally {
      this.setLoading(false);
    }
    this.renderPlugins();
  }

  validateStep() {
    if (this.step === 0) {
      if (!this.engineSelect.value) {
        this.showError('Please select an AI engine to continue.');
        return false;
      }
    } else if (this.step === 1) {
      if (!this.keyInput.value.trim()) {
        this.showError('Please enter your API key to continue.');
        return false;
      }
    }
    return true;
  }

  async validateApiKey() {
    const key = this.keyInput.value.trim();
    if (!key) {
      throw new Error('API key is required');
    }

    const response = await fetch(`/api/v1/providers/${this.provider}/key`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `API key validation failed: ${response.status} ${response.statusText}`);
    }
  }

  setLoading(loading) {
    this.isLoading = loading;
    this.nextBtn.classList.toggle('btn-loading', loading);
    this.nextBtn.disabled = loading;
    this.backBtn.disabled = loading || this.step === 0;
    this.shadowRoot.host.classList.toggle('loading', loading);
  }

  showError(message) {
    this.errorMessage = message;
    this.errorContainer.innerHTML = `<div class="error-message">${message}</div>`;
  }

  clearError() {
    this.errorMessage = '';
    this.errorContainer.innerHTML = '';
  }

  renderPlugins() {
    const list = this.pluginList;
    list.innerHTML = '';
    
    if (this.plugins.length === 0) {
      const li = document.createElement('li');
      li.innerHTML = '<p><em>No plugins available or failed to load plugins.</em></p>';
      list.appendChild(li);
      return;
    }
    
    this.plugins.forEach((p, index) => {
      const li = document.createElement('li');
      const label = document.createElement('label');
      const toggle = document.createElement('input');
      toggle.type = 'checkbox';
      toggle.checked = p.consent;
      toggle.id = `plugin-${index}`;
      
      // Add descriptive aria-label for the toggle
      const toggleLabel = `${p.consent ? 'Disable' : 'Enable'} ${p.name} plugin`;
      toggle.setAttribute('aria-label', toggleLabel);
      
      if (p.description) {
        const descId = `plugin-desc-${index}`;
        toggle.setAttribute('aria-describedby', descId);
      }
      
      toggle.addEventListener('change', async () => {
        p.consent = toggle.checked;
        // Update aria-label based on new state
        const newLabel = `${p.consent ? 'Disable' : 'Enable'} ${p.name} plugin`;
        toggle.setAttribute('aria-label', newLabel);
        
        try {
          const response = await fetch(`/api/v1/mcp/consent/${p.name}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ consent: p.consent })
          });
          
          if (!response.ok) {
            // Revert the change if the request failed
            p.consent = !toggle.checked;
            toggle.checked = p.consent;
            const revertLabel = `${p.consent ? 'Disable' : 'Enable'} ${p.name} plugin`;
            toggle.setAttribute('aria-label', revertLabel);
            throw new Error(`Failed to update consent for ${p.name}`);
          }
        } catch (error) {
          console.error('Plugin consent error:', error);
          this.showError(`Failed to update consent for ${p.name}. Please try again.`);
        }
      });
      label.appendChild(toggle);
      label.appendChild(document.createTextNode(` ${p.name}`));
      
      // Add description if available
      if (p.description) {
        const desc = document.createElement('div');
        desc.id = `plugin-desc-${index}`;
        desc.style.fontSize = 'var(--font-size-sm)';
        desc.style.color = 'var(--color-text-secondary)';
        desc.style.marginLeft = '1.5rem';
        desc.textContent = p.description;
        li.appendChild(label);
        li.appendChild(desc);
      } else {
        li.appendChild(label);
      }
      
      list.appendChild(li);
    });
  }

  renderSummary() {
    const enabled = this.plugins
      .filter(p => p.consent)
      .map(p => p.name)
      .join(', ') || 'None selected';
    this.summary.innerHTML = `
      <div style="background: var(--color-surface); padding: var(--spacing-md); border-radius: var(--radius-sm);">
        <h3>Configuration Summary</h3>
        <p><strong>AI Provider:</strong> ${this.provider === 'cloud' ? 'Cloud-based' : 'Local'} (${this.provider})</p>
        <p><strong>API Key:</strong> ${this.keyInput.value ? 'Configured' : 'Not provided'}</p>
        <p><strong>Enabled Plugins:</strong> ${enabled}</p>
      </div>
    `;
  }

  renderCompletionSummary() {
    const enabled = this.plugins.filter(p => p.consent);
    const pluginList = enabled.length > 0 
      ? enabled.map(p => `<li>${p.name}</li>`).join('') 
      : '<li><em>No plugins enabled</em></li>';
    
    this.completionSummary.innerHTML = `
      <div style="background: var(--color-surface); padding: var(--spacing-md); border-radius: var(--radius-sm); border: 1px solid var(--color-primary);">
        <h3>Your Configuration</h3>
        <p><strong>AI Provider:</strong> ${this.provider === 'cloud' ? 'Cloud-based services' : 'Local AI models'}</p>
        <p><strong>Enabled Plugins:</strong></p>
        <ul style="margin: 0; padding-left: 1.5rem;">
          ${pluginList}
        </ul>
        <p style="margin-top: var(--spacing-md);"><strong>Privacy:</strong> Accepted data usage policy</p>
      </div>
    `;
  }

  update() {
    // Update step visibility
    this.steps.forEach((el, idx) => {
      el.hidden = idx !== this.step;
    });
    
    // Update progress bar
    const progress = ((this.step + 1) / this.steps.length) * 100;
    this.progressFill.style.width = `${progress}%`;
    
    // Update progress bar ARIA attributes
    this.progressBar.setAttribute('aria-valuenow', this.step + 1);
    this.progressBar.setAttribute('aria-label', `Onboarding progress: Step ${this.step + 1} of ${this.steps.length}`);
    
    // Update button states
    this.backBtn.disabled = this.step === 0 || this.isLoading;
    this.nextBtn.disabled = this.step === this.steps.length - 1 || this.isLoading;
    
    // Update button text and aria-label for final step
    if (this.step === this.steps.length - 1) {
      this.nextBtn.textContent = 'Finish';
      this.nextBtn.setAttribute('aria-label', 'Complete onboarding setup');
      this.nextBtn.disabled = true; // Disable on completion step
    } else {
      this.nextBtn.textContent = 'Next';
      this.nextBtn.setAttribute('aria-label', 'Go to next step');
    }
    
    // Announce step change to screen readers
    this.announceStepChange();
  }

  announceStepChange() {
    // Create screen reader announcement for step changes
    const stepTitles = [
      'Choose AI Engine',
      'Provider Setup', 
      'Configure Plugins',
      'Review Configuration',
      'Privacy Agreement',
      'Setup Complete'
    ];
    
    const announcement = `Step ${this.step + 1} of ${this.steps.length}: ${stepTitles[this.step]}`;
    
    // Create a temporary live region for announcements if it doesn't exist
    let announcer = this.shadowRoot.getElementById('step-announcer');
    if (!announcer) {
      announcer = document.createElement('div');
      announcer.id = 'step-announcer';
      announcer.setAttribute('aria-live', 'assertive');
      announcer.setAttribute('aria-atomic', 'true');
      announcer.style.position = 'absolute';
      announcer.style.left = '-10000px';
      announcer.style.width = '1px';
      announcer.style.height = '1px';
      announcer.style.overflow = 'hidden';
      this.shadowRoot.appendChild(announcer);
    }
    
    // Clear and set the announcement
    announcer.textContent = '';
    setTimeout(() => {
      announcer.textContent = announcement;
    }, 100);
  }

  complete() {
    const enabled = this.plugins.filter(p => p.consent).map(p => p.name);
    this.dispatchEvent(
      new CustomEvent('onboarding-complete', {
        detail: { provider: this.provider, plugins: enabled }
      })
    );
  }

  _setupKeyboardNavigation() {
    // Add keyboard event handling for the entire component
    this.addEventListener('keydown', (e) => {
      // Handle Enter key on form elements
      if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey) {
        const activeElement = this.shadowRoot.activeElement;
        
        // For input fields, trigger next button
        if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'SELECT')) {
          e.preventDefault();
          if (!this.nextBtn.disabled) {
            this.nextBtn.click();
          }
        }
      }
      
      // Handle Escape key to go back
      if (e.key === 'Escape') {
        e.preventDefault();
        if (!this.backBtn.disabled && this.step > 0) {
          this.backBtn.click();
        }
      }
    });

    // Ensure proper focus management when step changes
    this._setupStepFocusManagement();
  }

  _setupStepFocusManagement() {
    // Focus the first interactive element when step changes
    const observer = new MutationObserver(() => {
      this._focusFirstInteractiveElement();
    });

    // Observe changes to step visibility
    this.steps.forEach(step => {
      observer.observe(step, { attributes: true, attributeFilter: ['hidden'] });
    });
  }

  _focusFirstInteractiveElement() {
    const currentStep = this.steps[this.step];
    if (!currentStep || currentStep.hidden) return;

    // Find the first focusable element in the current step
    const focusableSelectors = [
      'input:not([disabled]):not([hidden])',
      'select:not([disabled]):not([hidden])',
      'textarea:not([disabled]):not([hidden])',
      'button:not([disabled]):not([hidden])',
      '[tabindex]:not([tabindex="-1"]):not([disabled]):not([hidden])'
    ];

    const focusableElement = currentStep.querySelector(focusableSelectors.join(', '));
    if (focusableElement) {
      // Small delay to ensure element is ready
      setTimeout(() => {
        focusableElement.focus();
      }, 100);
    }
  }
}

customElements.define('la-onboarding-flow', LAOnboardingFlow);

