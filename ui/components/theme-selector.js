// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAThemeSelector extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: inline-block;
          font-family: var(--font-family-sans);
        }
        .selector-container {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
        }
        label {
          font-size: var(--font-size-sm);
          color: var(--color-text);
          font-weight: var(--font-weight-normal);
        }
        select {
          background: var(--color-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
          padding: var(--spacing-xs) var(--spacing-sm);
          color: var(--color-text);
          font-family: inherit;
          font-size: var(--font-size-sm);
          cursor: pointer;
          min-width: 120px;
        }
        select:focus {
          outline: 2px solid var(--color-primary);
          outline-offset: 2px;
        }
        select:disabled {
          background: var(--color-border);
          cursor: not-allowed;
          opacity: 0.6;
        }
        .preview {
          width: 20px;
          height: 20px;
          border-radius: var(--radius-sm);
          border: 1px solid var(--color-border);
          display: inline-block;
          vertical-align: middle;
        }
      </style>
      <div class="selector-container">
        <label for="theme-select">Theme:</label>
        <span class="preview" id="preview"></span>
        <select id="theme-select">
          <option value="">Loading themes...</option>
        </select>
      </div>
    `;
    
    this.catalogUrl = this.getAttribute('catalog') || '/api/v1/themes';
    this.themes = [];
    this.currentTheme = 'light';
  }

  async connectedCallback() {
    await this.loadThemes();
    this.setupEventListeners();
    this.detectCurrentTheme();
    this.updateUI();
  }

  async loadThemes() {
    try {
      const loadingId = window.notifications?.loading('Loading available themes...');
      
      const response = await fetch(this.catalogUrl);
      
      if (loadingId) window.notifications?.dismiss(loadingId);
      
      if (response.ok) {
        const data = await response.json();
        this.themes = data.themes || data; // Handle both /api/v1/themes and direct catalog formats
        
        if (this.themes.length > 0) {
          window.notifications?.success(`Loaded ${this.themes.length} themes`);
        }
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      window.notifications?.error(`Failed to load theme catalog: ${error.message}`);
      // Fallback to built-in themes
      this.themes = [
        { id: 'light', name: 'Light', preview: '#f8f9fa' },
        { id: 'dark', name: 'Dark', preview: '#1e1e1e' },
        { id: 'high-contrast', name: 'High Contrast', preview: '#000000' }
      ];
    }
  }

  setupEventListeners() {
    const select = this.shadowRoot.getElementById('theme-select');
    select.addEventListener('change', (event) => {
      this.applyTheme(event.target.value);
    });
  }

  detectCurrentTheme() {
    // Check for saved theme preference
    const saved = localStorage.getItem('selected-theme');
    if (saved && this.themes.some(t => t.id === saved)) {
      this.currentTheme = saved;
      return;
    }

    // Check data-theme attribute on document
    const dataTheme = document.documentElement.getAttribute('data-theme');
    if (dataTheme && this.themes.some(t => t.id === dataTheme)) {
      this.currentTheme = dataTheme;
      return;
    }

    // Default to light theme
    this.currentTheme = 'light';
  }

  updateUI() {
    const select = this.shadowRoot.getElementById('theme-select');
    const preview = this.shadowRoot.getElementById('preview');
    
    // Populate select options
    select.innerHTML = '';
    this.themes.forEach(theme => {
      const option = document.createElement('option');
      option.value = theme.id;
      option.textContent = theme.name;
      option.selected = theme.id === this.currentTheme;
      select.appendChild(option);
    });

    // Update preview color
    const selectedTheme = this.themes.find(t => t.id === this.currentTheme);
    if (selectedTheme && selectedTheme.preview) {
      preview.style.backgroundColor = selectedTheme.preview;
    }
  }

  async applyTheme(themeId) {
    if (!themeId) return;

    const theme = this.themes.find(t => t.id === themeId);
    if (!theme) return;

    const select = this.shadowRoot.getElementById('theme-select');
    const originalValue = this.currentTheme;
    
    select.disabled = true;
    const loadingId = window.notifications?.loading(`Applying theme ${theme.name}...`);

    try {
      this.currentTheme = themeId;

      // Remove any previously loaded community theme
      const existingStyle = document.getElementById('community-theme');
      if (existingStyle) {
        existingStyle.remove();
      }

      // For built-in themes, just set the data-theme attribute
      const builtinThemes = ['light', 'dark', 'high-contrast'];
      if (builtinThemes.includes(themeId)) {
        document.documentElement.setAttribute('data-theme', themeId);
      } else {
        // For community themes, load the CSS file
        const response = await fetch(`/api/v1/themes/${themeId}.css`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const css = await response.text();
        const style = document.createElement('style');
        style.id = 'community-theme';
        style.textContent = css;
        document.head.appendChild(style);
        document.documentElement.setAttribute('data-theme', themeId);
      }

      // Save theme preference
      localStorage.setItem('selected-theme', themeId);

      // Update preview
      this.updateUI();

      if (loadingId) window.notifications?.dismiss(loadingId);
      window.notifications?.success(`Theme ${theme.name} applied successfully`);

      // Dispatch theme change event
      this.dispatchEvent(new CustomEvent('theme-change', {
        detail: { themeId, theme, success: true },
        bubbles: true
      }));
    } catch (error) {
      if (loadingId) window.notifications?.dismiss(loadingId);
      
      // Revert to original theme on error
      this.currentTheme = originalValue;
      select.value = originalValue;
      
      window.notifications?.error(`Failed to apply theme ${theme.name}: ${error.message}`);
      
      this.dispatchEvent(new CustomEvent('theme-change', {
        detail: { themeId, theme, success: false, error: error.message },
        bubbles: true
      }));
    } finally {
      select.disabled = false;
    }
  }

  // Public API for external theme switching
  setTheme(themeId) {
    const select = this.shadowRoot.getElementById('theme-select');
    select.value = themeId;
    this.applyTheme(themeId);
  }

  getCurrentTheme() {
    return this.currentTheme;
  }

  getAvailableThemes() {
    return [...this.themes];
  }
}

customElements.define('la-theme-selector', LAThemeSelector);