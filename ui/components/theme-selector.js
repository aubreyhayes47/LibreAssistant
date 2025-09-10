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
        select:hover {
          border-color: var(--color-primary);
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
      const response = await fetch(this.catalogUrl);
      if (response.ok) {
        const data = await response.json();
        this.themes = data.themes || data; // Handle both /api/v1/themes and direct catalog formats
      } else {
        // Fallback to built-in themes if catalog fails to load
        this.themes = [
          { id: 'light', name: 'Light', preview: '#f8f9fa' },
          { id: 'dark', name: 'Dark', preview: '#1e1e1e' },
          { id: 'high-contrast', name: 'High Contrast', preview: '#000000' }
        ];
      }
    } catch (error) {
      console.warn('Failed to load theme catalog:', error);
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
      try {
        const response = await fetch(`/api/v1/themes/${themeId}.css`);
        if (response.ok) {
          const css = await response.text();
          const style = document.createElement('style');
          style.id = 'community-theme';
          style.textContent = css;
          document.head.appendChild(style);
          document.documentElement.setAttribute('data-theme', themeId);
        } else {
          console.error('Failed to load theme:', themeId);
          return;
        }
      } catch (error) {
        console.error('Error loading theme:', error);
        return;
      }
    }

    // Save theme preference
    localStorage.setItem('selected-theme', themeId);

    // Update preview
    this.updateUI();

    // Dispatch theme change event
    this.dispatchEvent(new CustomEvent('theme-change', {
      detail: { themeId, theme },
      bubbles: true
    }));
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