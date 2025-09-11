// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAUserProfile extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--font-family-sans);
          color: var(--color-text);
        }
        label {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          font-size: var(--font-size-base);
          margin-bottom: var(--spacing-md);
          cursor: pointer;
        }
        input[type="checkbox"] {
          margin: 0;
          cursor: pointer;
        }
        la-data-vault {
          display: block;
          margin-top: var(--spacing-md);
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
      <label for="consent-checkbox"><input type="checkbox" id="consent-checkbox" aria-describedby="consent-help"> Allow data storage</label>
      <div id="consent-help" class="sr-only">This allows the application to store your preferences and data locally</div>
      <la-data-vault></la-data-vault>
    `;
  }

  connectedCallback() {
    const user = this.getAttribute('user') || 'default';
    const checkbox = this.shadowRoot.getElementById('consent-checkbox');
    const vault = this.shadowRoot.querySelector('la-data-vault');
    fetch(`/api/v1/consent/${user}`).then(r => r.json()).then(j => {
      checkbox.checked = j.consent;
      checkbox.setAttribute('aria-checked', j.consent.toString());
      if (vault && typeof vault.updateConsent === 'function') {
        vault.updateConsent(j.consent);
      }
    });
    checkbox.addEventListener('change', async () => {
      checkbox.setAttribute('aria-checked', checkbox.checked.toString());
      await fetch(`/api/v1/consent/${user}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ consent: checkbox.checked })
      });
      if (vault && typeof vault.updateConsent === 'function') {
        vault.updateConsent(checkbox.checked);
      }
    });
  }
}

customElements.define('la-user-profile', LAUserProfile);
