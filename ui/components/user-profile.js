// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAUserProfile extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host { display: block; }
        label { display: flex; align-items: center; gap: var(--spacing-sm); }
      </style>
      <label><input type="checkbox" id="consent"> Allow data storage</label>
      <la-data-vault></la-data-vault>
    `;
  }

  connectedCallback() {
    const user = this.getAttribute('user') || 'default';
    const checkbox = this.shadowRoot.getElementById('consent');
    fetch(`/api/v1/consent/${user}`).then(r => r.json()).then(j => {
      checkbox.checked = j.consent;
    });
    checkbox.addEventListener('change', async () => {
      await fetch(`/api/v1/consent/${user}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ consent: checkbox.checked })
      });
    });
  }
}

customElements.define('la-user-profile', LAUserProfile);
