// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAMainTabs extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--font-family-sans, sans-serif);
        }
        nav {
          display: flex;
          gap: 0;
          border-bottom: 1px solid var(--color-border, #d1d5db);
          background-color: var(--color-background, white);
          overflow-x: auto;
          scrollbar-width: none;
          -ms-overflow-style: none;
        }
        nav::-webkit-scrollbar {
          display: none;
        }
        button[role="tab"] {
          background: none;
          border: none;
          padding: var(--spacing-sm, 0.5rem) var(--spacing-md, 1rem);
          cursor: pointer;
          font-family: var(--font-family-sans, sans-serif);
          font-size: var(--font-size-base, 1rem);
          color: var(--color-text-secondary, #6b7280);
          border-bottom: 2px solid transparent;
          transition: all 0.2s ease;
          white-space: nowrap;
          min-height: 2.5rem;
          display: flex;
          align-items: center;
          gap: var(--spacing-xs, 0.25rem);
          position: relative;
        }
        button[role="tab"]:hover {
          color: var(--color-text, #111827);
          background-color: var(--color-surface, #f9fafb);
        }
        button[role="tab"]:focus {
          outline: 2px solid var(--color-primary, #3b82f6);
          outline-offset: -2px;
          color: var(--color-text, #111827);
        }
        button[aria-selected="true"] {
          border-bottom-color: var(--color-primary, #3b82f6);
          color: var(--color-primary, #3b82f6);
          font-weight: var(--font-weight-bold, 700);
          background-color: var(--color-background, white);
        }
        button[aria-selected="true"]:hover {
          background-color: var(--color-background, white);
        }
        section[role="tabpanel"] {
          display: none;
          padding: var(--spacing-md, 1rem);
          background-color: var(--color-background, white);
          border-radius: 0 0 var(--radius-md, 8px) var(--radius-md, 8px);
        }
        section[role="tabpanel"][data-active="true"] {
          display: block;
        }
        section[role="tabpanel"]:focus {
          outline: 2px solid var(--color-primary, #3b82f6);
          outline-offset: -2px;
        }
        .tab-icon {
          width: 1rem;
          height: 1rem;
          fill: currentColor;
        }
        .tab-badge {
          background-color: var(--color-primary, #3b82f6);
          color: var(--color-background, white);
          font-size: var(--font-size-xs, 0.75rem);
          padding: 0.125rem 0.375rem;
          border-radius: 9999px;
          min-width: 1rem;
          text-align: center;
          line-height: 1.2;
        }
        .close-button {
          background: none;
          border: none;
          cursor: pointer;
          padding: 0.125rem;
          margin-left: var(--spacing-xs, 0.25rem);
          color: var(--color-text-secondary, #6b7280);
          border-radius: var(--radius-sm, 4px);
          display: flex;
          align-items: center;
          justify-content: center;
          width: 1rem;
          height: 1rem;
          font-size: 0.75rem;
        }
        .close-button:hover {
          background-color: var(--color-danger-light, #fef2f2);
          color: var(--color-danger, #ef4444);
        }
      </style>
      <nav role="tablist" aria-label="Main navigation"></nav>
      <div class="panels"></div>
    `;

    this._tabList = shadow.querySelector('[role="tablist"]');
    this._panelsContainer = shadow.querySelector('.panels');
    this._tabs = [];
    this._panels = [];
    this._activeIndex = 0;
  }

  connectedCallback() {
    // Parse initial tabs from attributes or slots
    this._initializeTabs();
    this._setupKeyboardNavigation();
  }

  _initializeTabs() {
    // Check for tab configuration in attributes
    const tabsConfig = this.getAttribute('tabs');
    if (tabsConfig) {
      try {
        const tabs = JSON.parse(tabsConfig);
        tabs.forEach((tab, index) => {
          this.addTab(tab.label, tab.id, tab.content, index === 0);
        });
      } catch (e) {
        console.warn('Invalid tabs configuration:', e);
      }
    } else {
      // Default tabs if none specified
      this._createDefaultTabs();
    }
  }

  _createDefaultTabs() {
    const defaultTabs = [
      { id: 'switchboard', label: 'Switchboard', active: true },
      { id: 'catalogue', label: 'Catalogue' },
      { id: 'past', label: 'Past Requests' },
      { id: 'profile', label: 'User Profile' }
    ];

    defaultTabs.forEach(tab => {
      this.addTab(tab.label, tab.id, '', tab.active);
    });
  }

  _setupKeyboardNavigation() {
    this._tabList.addEventListener('keydown', (e) => {
      const tabs = this._tabs;
      const currentIndex = tabs.findIndex(tab => tab === document.activeElement);

      switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          e.preventDefault();
          const nextIndex = (currentIndex + 1) % tabs.length;
          tabs[nextIndex].focus();
          break;
        case 'ArrowLeft':
        case 'ArrowUp':
          e.preventDefault();
          const prevIndex = (currentIndex - 1 + tabs.length) % tabs.length;
          tabs[prevIndex].focus();
          break;
        case 'Home':
          e.preventDefault();
          tabs[0].focus();
          break;
        case 'End':
          e.preventDefault();
          tabs[tabs.length - 1].focus();
          break;
        case 'Enter':
        case ' ':
          e.preventDefault();
          this._activateTab(currentIndex);
          break;
      }
    });
  }

  addTab(label, id, content = '', active = false, options = {}) {
    const tabButton = document.createElement('button');
    tabButton.setAttribute('role', 'tab');
    tabButton.setAttribute('aria-selected', active ? 'true' : 'false');
    tabButton.setAttribute('aria-controls', `panel-${id}`);
    tabButton.setAttribute('id', `tab-${id}`);
    tabButton.setAttribute('tabindex', active ? '0' : '-1');

    // Build tab content
    if (options.icon) {
      const icon = document.createElement('span');
      icon.className = 'tab-icon';
      icon.innerHTML = options.icon;
      tabButton.appendChild(icon);
    }

    const labelSpan = document.createElement('span');
    labelSpan.textContent = label;
    tabButton.appendChild(labelSpan);

    if (options.badge) {
      const badge = document.createElement('span');
      badge.className = 'tab-badge';
      badge.textContent = options.badge;
      tabButton.appendChild(badge);
    }

    if (options.closable) {
      const closeBtn = document.createElement('button');
      closeBtn.className = 'close-button';
      closeBtn.innerHTML = '×';
      closeBtn.setAttribute('aria-label', `Close ${label} tab`);
      closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.removeTab(id);
      });
      tabButton.appendChild(closeBtn);
    }

    // Add click handler
    tabButton.addEventListener('click', () => {
      const index = this._tabs.indexOf(tabButton);
      this._activateTab(index);
    });

    // Create panel
    const panel = document.createElement('section');
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', `tab-${id}`);
    panel.setAttribute('id', `panel-${id}`);
    panel.setAttribute('tabindex', '0');
    
    if (content) {
      panel.innerHTML = content;
    } else {
      // Create slot for external content
      const slot = document.createElement('slot');
      slot.setAttribute('name', id);
      panel.appendChild(slot);
    }

    if (active) {
      panel.setAttribute('data-active', 'true');
      this._activeIndex = this._tabs.length;
    }

    // Add to DOM
    this._tabList.appendChild(tabButton);
    this._panelsContainer.appendChild(panel);

    // Store references
    this._tabs.push(tabButton);
    this._panels.push(panel);

    return { tab: tabButton, panel };
  }

  removeTab(id) {
    const tabIndex = this._tabs.findIndex(tab => 
      tab.getAttribute('aria-controls') === `panel-${id}`
    );

    if (tabIndex === -1) return;

    const wasActive = this._tabs[tabIndex].getAttribute('aria-selected') === 'true';
    
    // Remove elements
    this._tabs[tabIndex].remove();
    this._panels[tabIndex].remove();

    // Update arrays
    this._tabs.splice(tabIndex, 1);
    this._panels.splice(tabIndex, 1);

    // Handle active tab change
    if (wasActive && this._tabs.length > 0) {
      const newActiveIndex = Math.min(tabIndex, this._tabs.length - 1);
      this._activateTab(newActiveIndex);
    }

    // Dispatch event
    this.dispatchEvent(new CustomEvent('tab-removed', {
      detail: { id, tabIndex },
      bubbles: true
    }));
  }

  _activateTab(index) {
    if (index < 0 || index >= this._tabs.length) return;

    // Update previous active tab
    if (this._activeIndex !== index) {
      if (this._tabs[this._activeIndex]) {
        this._tabs[this._activeIndex].setAttribute('aria-selected', 'false');
        this._tabs[this._activeIndex].setAttribute('tabindex', '-1');
        this._panels[this._activeIndex].removeAttribute('data-active');
      }
    }

    // Update new active tab
    this._tabs[index].setAttribute('aria-selected', 'true');
    this._tabs[index].setAttribute('tabindex', '0');
    this._panels[index].setAttribute('data-active', 'true');

    this._activeIndex = index;

    // Dispatch event
    const tabId = this._tabs[index].getAttribute('aria-controls').replace('panel-', '');
    this.dispatchEvent(new CustomEvent('tab-change', {
      detail: { 
        activeIndex: index, 
        tabId,
        tab: this._tabs[index],
        panel: this._panels[index]
      },
      bubbles: true
    }));
  }

  // Public API
  get activeIndex() {
    return this._activeIndex;
  }

  set activeIndex(index) {
    this._activateTab(index);
  }

  get activeTab() {
    return this._tabs[this._activeIndex];
  }

  get activePanel() {
    return this._panels[this._activeIndex];
  }

  getTabCount() {
    return this._tabs.length;
  }

  updateTabBadge(id, badge) {
    const tab = this._tabs.find(tab => 
      tab.getAttribute('aria-controls') === `panel-${id}`
    );
    
    if (tab) {
      let badgeEl = tab.querySelector('.tab-badge');
      if (badge) {
        if (!badgeEl) {
          badgeEl = document.createElement('span');
          badgeEl.className = 'tab-badge';
          tab.appendChild(badgeEl);
        }
        badgeEl.textContent = badge;
      } else if (badgeEl) {
        badgeEl.remove();
      }
    }
  }

  // Observe attribute changes
  static get observedAttributes() {
    return ['tabs'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === 'tabs' && oldValue !== newValue) {
      // Clear existing tabs and reinitialize
      this._tabs.forEach(tab => tab.remove());
      this._panels.forEach(panel => panel.remove());
      this._tabs = [];
      this._panels = [];
      this._activeIndex = 0;
      this._initializeTabs();
    }
  }
}

customElements.define('la-main-tabs', LAMainTabs);
