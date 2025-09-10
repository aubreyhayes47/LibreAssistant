// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAOnboardingFlow extends HTMLElement {
  constructor() {
    super();
    this.step = 0;
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
      </style>
      <div class="step" data-step="0">
        <h2>Step 1: Choose AI engine</h2>
        <select id="engine">
          <option value="cloud">Cloud</option>
          <option value="local">Local</option>
        </select>
      </div>
      <div class="step" data-step="1" hidden>
        <h2>Step 2: Provider setup</h2>
        <input id="apikey" type="password" placeholder="API key" />
      </div>
      <div class="step" data-step="2" hidden>
        <h2>Step 3: Configure plugins</h2>
        <ul id="plugin-list"></ul>
      </div>
      <div class="step" data-step="3" hidden>
        <h2>Step 4: Review permissions</h2>
        <div id="summary"></div>
      </div>
      <div class="step" data-step="4" hidden>
        <h2>Step 5: Privacy briefing</h2>
        <p>LibreAssistant sends data to your chosen provider and approved plugins.</p>
        <label><input id="privacy" type="checkbox" /> I understand</label>
      </div>
      <div class="step" data-step="5" hidden>
        <h2>Step 6: Completion</h2>
        <p>You're all set!</p>
      </div>
      <div class="controls">
        <button id="back">Back</button>
        <button id="next">Next</button>
      </div>
    `;
  }

  async connectedCallback() {
    this.backBtn = this.shadowRoot.getElementById('back');
    this.nextBtn = this.shadowRoot.getElementById('next');
    this.steps = this.shadowRoot.querySelectorAll('.step');
    this.engineSelect = this.shadowRoot.getElementById('engine');
    this.keyInput = this.shadowRoot.getElementById('apikey');
    this.pluginList = this.shadowRoot.getElementById('plugin-list');
    this.summary = this.shadowRoot.getElementById('summary');
    this.privacyCheck = this.shadowRoot.getElementById('privacy');
    await this.loadPlugins();
    this.update();
    this.backBtn.addEventListener('click', () => {
      if (this.step > 0) {
        this.step -= 1;
        this.update();
      }
    });
    this.nextBtn.addEventListener('click', async () => {
      if (this.step === 0) {
        this.provider = this.engineSelect.value;
      } else if (this.step === 1) {
        const key = this.keyInput.value.trim();
        try {
          await fetch(`/api/v1/providers/${this.provider}/key`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key })
          });
        } catch {}
      } else if (this.step === 4) {
        if (!this.privacyCheck.checked) {
          return;
        }
      }
      if (this.step < this.steps.length - 1) {
        this.step += 1;
        if (this.step === 3) {
          this.renderSummary();
        }
        if (this.step === 5) {
          this.complete();
        }
        this.update();
      }
    });
  }

  async loadPlugins() {
    try {
      const res = await fetch('/api/v1/mcp/servers');
      const data = await res.json();
      this.plugins = data.servers || [];
    } catch {
      this.plugins = [];
    }
    this.renderPlugins();
  }

  renderPlugins() {
    const list = this.pluginList;
    list.innerHTML = '';
    this.plugins.forEach(p => {
      const li = document.createElement('li');
      const label = document.createElement('label');
      const toggle = document.createElement('input');
      toggle.type = 'checkbox';
      toggle.checked = p.consent;
      toggle.addEventListener('change', async () => {
        p.consent = toggle.checked;
        try {
          await fetch(`/api/v1/mcp/consent/${p.name}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ consent: p.consent })
          });
        } catch {}
      });
      label.appendChild(toggle);
      label.appendChild(document.createTextNode(p.name));
      li.appendChild(label);
      list.appendChild(li);
    });
  }

  renderSummary() {
    const enabled = this.plugins
      .filter(p => p.consent)
      .map(p => p.name)
      .join(', ') || 'None';
    this.summary.innerHTML = `
      <p>Provider: ${this.provider || 'n/a'}</p>
      <p>Plugins: ${enabled}</p>
    `;
  }

  update() {
    this.steps.forEach((el, idx) => {
      el.hidden = idx !== this.step;
    });
    this.backBtn.disabled = this.step === 0;
    this.nextBtn.disabled = this.step === this.steps.length - 1;
  }

  complete() {
    const enabled = this.plugins.filter(p => p.consent).map(p => p.name);
    this.dispatchEvent(
      new CustomEvent('onboarding-complete', {
        detail: { provider: this.provider, plugins: enabled }
      })
    );
  }
}

customElements.define('la-onboarding-flow', LAOnboardingFlow);

