// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAMainTabs extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        nav {
          display: flex;
          gap: var(--spacing-md);
          border-bottom: 1px solid var(--color-border);
        }
        button[role="tab"] {
          background: none;
          border: none;
          padding: var(--spacing-sm) var(--spacing-md);
          cursor: pointer;
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
        }
        button[aria-selected="true"] {
          border-bottom: 2px solid var(--color-primary);
          font-weight: var(--font-weight-bold);
        }
        section[role="tabpanel"] {
          display: none;
          padding: var(--spacing-md);
        }
        section[role="tabpanel"][data-active="true"] {
          display: block;
        }
      </style>
      <nav role="tablist">
        <button role="tab" aria-selected="true" id="tab-switchboard">Switchboard</button>
        <button role="tab" aria-selected="false" id="tab-catalogue">Catalogue</button>
        <button role="tab" aria-selected="false" id="tab-past">Past Requests</button>
        <button role="tab" aria-selected="false" id="tab-profile">User Profile</button>
      </nav>
      <section id="panel-switchboard" role="tabpanel" data-active="true"><slot name="switchboard"></slot></section>
      <section id="panel-catalogue" role="tabpanel"><slot name="catalogue"></slot></section>
      <section id="panel-past" role="tabpanel"><slot name="past"></slot></section>
      <section id="panel-profile" role="tabpanel"><slot name="profile"></slot></section>
    `;
  }

  connectedCallback() {
    const tabs = this.shadowRoot.querySelectorAll('[role="tab"]');
    const panels = this.shadowRoot.querySelectorAll('[role="tabpanel"]');
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.setAttribute('aria-selected', 'false'));
        tab.setAttribute('aria-selected', 'true');
        panels.forEach(p => p.removeAttribute('data-active'));
        panels[index].setAttribute('data-active', 'true');
      });
    });
  }
}

customElements.define('la-main-tabs', LAMainTabs);
