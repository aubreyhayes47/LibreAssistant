// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LASystemHealth extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--font-family-sans, sans-serif);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--spacing-md, 1rem);
        }
        h2 {
          margin: 0;
          font-size: var(--font-size-lg, 1.125rem);
          font-weight: var(--font-weight-bold, 700);
          color: var(--color-text, #111827);
        }
        .refresh-button {
          background-color: var(--color-primary, #3b82f6);
          color: var(--color-background, white);
          border: none;
          border-radius: var(--radius-sm, 4px);
          padding: var(--spacing-xs, 0.25rem) var(--spacing-sm, 0.5rem);
          cursor: pointer;
          font-size: var(--font-size-sm, 0.875rem);
          transition: background-color 0.2s ease;
        }
        .refresh-button:hover {
          background-color: var(--color-primary-hover, #2563eb);
        }
        .refresh-button:disabled {
          background-color: var(--color-disabled, #9ca3af);
          cursor: not-allowed;
        }
        .loading {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm, 0.5rem);
          color: var(--color-text-secondary, #6b7280);
          font-style: italic;
        }
        .spinner {
          width: 1rem;
          height: 1rem;
          border: 2px solid var(--color-border, #d1d5db);
          border-top: 2px solid var(--color-primary, #3b82f6);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .status-grid {
          display: grid;
          gap: var(--spacing-md, 1rem);
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          margin-bottom: var(--spacing-lg, 1.5rem);
        }
        .status-item {
          padding: var(--spacing-sm, 0.5rem);
          border-radius: var(--radius-sm, 4px);
          border: 1px solid var(--color-border, #d1d5db);
        }
        .status-item.healthy {
          background-color: var(--color-success-light, #ecfdf5);
          border-color: var(--color-success, #10b981);
        }
        .status-item.warning {
          background-color: var(--color-warning-light, #fffbeb);
          border-color: var(--color-warning, #f59e0b);
        }
        .status-item.error {
          background-color: var(--color-danger-light, #fef2f2);
          border-color: var(--color-danger, #ef4444);
        }
        .status-label {
          font-weight: var(--font-weight-medium, 500);
          margin-bottom: var(--spacing-xs, 0.25rem);
        }
        .status-value {
          font-size: var(--font-size-lg, 1.125rem);
          font-weight: var(--font-weight-bold, 700);
        }
        .status-item.healthy .status-value {
          color: var(--color-success, #10b981);
        }
        .status-item.warning .status-value {
          color: var(--color-warning, #f59e0b);
        }
        .status-item.error .status-value {
          color: var(--color-danger, #ef4444);
        }
        .errors-section {
          margin-top: var(--spacing-lg, 1.5rem);
        }
        .errors-section h3 {
          margin: 0 0 var(--spacing-sm, 0.5rem) 0;
          font-size: var(--font-size-base, 1rem);
          font-weight: var(--font-weight-bold, 700);
          color: var(--color-danger, #ef4444);
        }
        ul {
          list-style: disc;
          padding-left: var(--spacing-md, 1rem);
          margin: 0;
        }
        li {
          margin-bottom: var(--spacing-xs, 0.25rem);
          color: var(--color-text, #111827);
        }
        .no-errors {
          color: var(--color-success, #10b981);
          font-style: italic;
        }
        .error-message {
          background-color: var(--color-danger-light, #fef2f2);
          border: 1px solid var(--color-danger, #ef4444);
          border-radius: var(--radius-sm, 4px);
          padding: var(--spacing-sm, 0.5rem);
          color: var(--color-danger, #ef4444);
          margin-bottom: var(--spacing-md, 1rem);
        }
        .last-updated {
          font-size: var(--font-size-xs, 0.75rem);
          color: var(--color-text-secondary, #6b7280);
          text-align: right;
          margin-top: var(--spacing-sm, 0.5rem);
        }
      </style>
      <div class="header">
        <h2>System Health</h2>
        <button class="refresh-button" id="refresh-btn">Refresh</button>
      </div>
      <div id="content">
        <div class="loading">
          <div class="spinner"></div>
          <span>Loading system health data...</span>
        </div>
      </div>
    `;

    this._refreshBtn = shadow.querySelector('#refresh-btn');
    this._content = shadow.querySelector('#content');
    this._isLoading = false;
    this._lastUpdate = null;
    this._autoRefreshInterval = null;
  }

  connectedCallback() {
    this._refreshBtn.addEventListener('click', () => this.refresh());
    
    // Auto-refresh every 30 seconds if enabled
    const autoRefresh = this.hasAttribute('auto-refresh');
    if (autoRefresh) {
      const interval = parseInt(this.getAttribute('auto-refresh')) || 30000;
      this._autoRefreshInterval = setInterval(() => this.refresh(), interval);
    }

    // Initial load
    this.refresh();
  }

  disconnectedCallback() {
    if (this._autoRefreshInterval) {
      clearInterval(this._autoRefreshInterval);
    }
  }

  async refresh() {
    if (this._isLoading) return;

    this._isLoading = true;
    this._refreshBtn.disabled = true;
    
    try {
      const resp = await fetch('/api/v1/health');
      
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
      }

      const data = await resp.json();
      this._renderHealthData(data);
      this._lastUpdate = new Date();
    } catch (err) {
      this._renderError(err);
    } finally {
      this._isLoading = false;
      this._refreshBtn.disabled = false;
    }
  }

  _renderHealthData(data) {
    const uptime = this._formatUptime(data.uptime || 0);
    const status = this._getOverallStatus(data);
    
    this._content.innerHTML = `
      <div class="status-grid">
        <div class="status-item ${status.class}">
          <div class="status-label">System Status</div>
          <div class="status-value">${data.status || 'Unknown'}</div>
        </div>
        <div class="status-item healthy">
          <div class="status-label">Uptime</div>
          <div class="status-value">${uptime}</div>
        </div>
        <div class="status-item ${data.requests > 1000 ? 'warning' : 'healthy'}">
          <div class="status-label">Total Requests</div>
          <div class="status-value">${(data.requests || 0).toLocaleString()}</div>
        </div>
        <div class="status-item ${this._getErrorStatus(data.errors)}">
          <div class="status-label">Error Count</div>
          <div class="status-value">${(data.errors?.length || 0)}</div>
        </div>
      </div>
      
      <div class="errors-section">
        <h3>Recent Errors</h3>
        ${this._renderErrors(data.errors || [])}
      </div>
      
      <div class="last-updated">
        Last updated: ${this._lastUpdate ? this._lastUpdate.toLocaleTimeString() : 'Never'}
      </div>
    `;

    // Dispatch event
    this.dispatchEvent(new CustomEvent('health-updated', {
      detail: { data, status: status.value },
      bubbles: true
    }));
  }

  _renderError(error) {
    this._content.innerHTML = `
      <div class="error-message">
        <strong>Failed to load system health data:</strong>
        <br>${error.message}
      </div>
      <div class="last-updated">
        Last attempted: ${new Date().toLocaleTimeString()}
      </div>
    `;

    // Dispatch error event
    this.dispatchEvent(new CustomEvent('health-error', {
      detail: { error },
      bubbles: true
    }));
  }

  _renderErrors(errors) {
    if (!errors || errors.length === 0) {
      return '<div class="no-errors">No recent errors reported</div>';
    }

    const errorList = errors
      .slice(0, 10) // Show only last 10 errors
      .map(error => `<li>${this._escapeHtml(error)}</li>`)
      .join('');

    return `<ul>${errorList}</ul>`;
  }

  _getOverallStatus(data) {
    const status = (data.status || '').toLowerCase();
    const errorCount = data.errors?.length || 0;

    if (status === 'healthy' && errorCount === 0) {
      return { value: 'healthy', class: 'healthy' };
    } else if (status === 'degraded' || errorCount > 0) {
      return { value: 'warning', class: 'warning' };
    } else if (status === 'down' || status === 'error') {
      return { value: 'error', class: 'error' };
    }

    return { value: 'unknown', class: 'warning' };
  }

  _getErrorStatus(errors) {
    const count = errors?.length || 0;
    if (count === 0) return 'healthy';
    if (count < 5) return 'warning';
    return 'error';
  }

  _formatUptime(seconds) {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      return `${Math.round(seconds / 60)}m`;
    } else if (seconds < 86400) {
      return `${Math.round(seconds / 3600)}h`;
    } else {
      return `${Math.round(seconds / 86400)}d`;
    }
  }

  _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Public API
  get isLoading() {
    return this._isLoading;
  }

  get lastUpdate() {
    return this._lastUpdate;
  }

  startAutoRefresh(interval = 30000) {
    this.stopAutoRefresh();
    this._autoRefreshInterval = setInterval(() => this.refresh(), interval);
  }

  stopAutoRefresh() {
    if (this._autoRefreshInterval) {
      clearInterval(this._autoRefreshInterval);
      this._autoRefreshInterval = null;
    }
  }

  // Observe attribute changes
  static get observedAttributes() {
    return ['auto-refresh'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === 'auto-refresh') {
      if (newValue !== null) {
        const interval = parseInt(newValue) || 30000;
        this.startAutoRefresh(interval);
      } else {
        this.stopAutoRefresh();
      }
    }
  }
}

customElements.define('la-system-health', LASystemHealth);
