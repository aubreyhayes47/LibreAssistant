// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAThemeMarketplace extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--font-family-sans);
        }
        header {
          margin-bottom: var(--spacing-md);
        }
        ul {
          list-style: none;
          padding: 0;
          margin: 0;
          display: grid;
          gap: var(--spacing-md);
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        }
        li {
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
          padding: var(--spacing-sm);
          background: var(--color-surface);
          display: flex;
          flex-direction: column;
          gap: var(--spacing-sm);
        }
        .preview {
          height: 80px;
          border-radius: var(--radius-sm);
        }
        iframe.preview {
          width: 100%;
          border: none;
        }
        button {
          background-color: var(--color-primary);
          color: var(--color-background);
          border: none;
          border-radius: var(--radius-sm);
          padding: var(--spacing-xs) var(--spacing-sm);
          cursor: pointer;
          align-self: start;
          transition: background-color 0.2s ease;
        }
        button:disabled {
          background-color: var(--color-border);
          cursor: not-allowed;
        }
        button.installing {
          position: relative;
        }
        button.installing::after {
          content: '';
          position: absolute;
          width: 12px;
          height: 12px;
          margin: auto;
          border: 2px solid transparent;
          border-top-color: var(--color-background);
          border-radius: 50%;
          animation: spin 1s linear infinite;
          top: 0;
          bottom: 0;
          left: 0;
          right: 0;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .rating {
          display: flex;
          gap: 2px;
          font-size: var(--font-size-lg);
        }
        .rating span {
          cursor: pointer;
          color: var(--color-secondary);
        }
        .rating .active {
          color: var(--color-primary);
        }
      </style>
      <header>
        <la-input-field id="search">
          <span slot="label">Search themes</span>
        </la-input-field>
      </header>
      <ul id="list"></ul>
    `;
    this.catalogUrl = this.getAttribute('catalog') || 'theme-catalog.json';
    this.themes = [];
    this.builtins = ['light', 'dark', 'high-contrast'];
  }

  async connectedCallback() {
    await this.load();
    this.render();
    const search = this.shadowRoot.getElementById('search');
    search.shadowRoot.querySelector('input').addEventListener('input', e => {
      this.filter(e.target.value);
    });
  }

  async load() {
    try {
      const loadingId = window.notifications?.loading('Loading theme catalogue...');
      
      const res = await fetch(this.catalogUrl);
      
      if (loadingId) window.notifications?.dismiss(loadingId);
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      
      this.themes = await res.json();
      
      if (this.themes.length > 0) {
        window.notifications?.success(`Loaded ${this.themes.length} themes`);
      } else {
        window.notifications?.info('No themes found in catalogue');
      }
    } catch (e) {
      window.notifications?.error(`Failed to load theme catalog: ${e.message}`);
      this.themes = [];
    }
  }

  filter(query) {
    const lower = query.toLowerCase();
    this.render(this.themes.filter(t => t.name.toLowerCase().includes(lower)));
  }

  render(list = this.themes) {
    const container = this.shadowRoot.getElementById('list');
    container.innerHTML = '';
    
    // Safety check to ensure list is an array
    if (!Array.isArray(list)) {
      console.warn('Theme list is not an array, using empty array:', list);
      list = [];
    }
    
    list.forEach(theme => this.addItem(theme, container));
  }

  addItem(theme, container) {
    const li = document.createElement('li');
    let preview;
    if (this.builtins.includes(theme.id)) {
      preview = document.createElement('div');
      preview.className = 'preview';
      preview.style.background = theme.preview;
    } else {
      preview = document.createElement('iframe');
      preview.className = 'preview';
      preview.setAttribute('sandbox', '');
      preview.srcdoc = `
        <link rel="stylesheet" href="/api/v1/themes/${theme.id}.css">
        <style>body{margin:0}.box{width:100%;height:100%;background:var(--color-background);}</style>
        <div class="box"></div>`;
    }
    const title = document.createElement('div');
    title.textContent = `${theme.name} by ${theme.author}`;
    const install = document.createElement('button');
    install.textContent = 'Install';
    install.addEventListener('click', () => this.applyTheme(theme, install));
    const rating = document.createElement('div');
    rating.className = 'rating';
    for (let i = 1; i <= 5; i++) {
      const star = document.createElement('span');
      star.textContent = '★';
      if (theme.rating && i <= theme.rating) {
        star.classList.add('active');
      }
      star.addEventListener('click', () => this.rateTheme(theme, i));
      rating.appendChild(star);
    }
    li.append(preview, title, install, rating);
    container.appendChild(li);
  }

  async applyTheme(theme, button) {
    if (button) {
      button.disabled = true;
      button.classList.add('installing');
      button.textContent = 'Installing...';
    }
    
    const loadingId = window.notifications?.loading(`Installing theme ${theme.name}...`);
    
    try {
      // Remove any previously loaded community theme
      const existing = document.getElementById('community-theme');
      if (existing) existing.remove();
      
      if (this.builtins.includes(theme.id)) {
        // For built-in themes, just set the data-theme attribute
        document.documentElement.setAttribute('data-theme', theme.id);
      } else {
        const res = await fetch(`/api/v1/themes/${theme.id}.css`);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        
        const css = await res.text();
        const style = document.createElement('style');
        style.id = 'community-theme';
        style.textContent = css;
        document.head.appendChild(style);
        document.documentElement.setAttribute('data-theme', theme.id);
      }
      
      // Save theme preference
      localStorage.setItem('selected-theme', theme.id);
      
      if (loadingId) window.notifications?.dismiss(loadingId);
      window.notifications?.success(`Theme ${theme.name} installed successfully`);
      
      this.dispatchEvent(new CustomEvent('theme-install', { 
        detail: { id: theme.id, success: true } 
      }));
    } catch (e) {
      if (loadingId) window.notifications?.dismiss(loadingId);
      window.notifications?.error(`Failed to install theme ${theme.name}: ${e.message}`);
      
      this.dispatchEvent(new CustomEvent('theme-install', { 
        detail: { id: theme.id, success: false, error: e.message } 
      }));
    } finally {
      if (button) {
        button.disabled = false;
        button.classList.remove('installing');
        button.textContent = 'Install';
      }
    }
  }

  rateTheme(theme, value) {
    theme.rating = value;
    this.dispatchEvent(new CustomEvent('theme-rate', { detail: { id: theme.id, rating: value } }));
    this.render();
  }
}

customElements.define('la-theme-marketplace', LAThemeMarketplace);
