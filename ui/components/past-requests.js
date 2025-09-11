// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAPastRequests extends HTMLElement {
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
        .controls {
          display: flex;
          gap: var(--spacing-sm);
          margin-bottom: var(--spacing-md);
          align-items: center;
        }
        .page-size-selector {
          display: flex;
          gap: var(--spacing-xs);
          align-items: center;
        }
        .pagination {
          display: flex;
          gap: var(--spacing-xs);
          margin-top: var(--spacing-md);
          align-items: center;
        }
        button {
          padding: var(--spacing-xs) var(--spacing-sm);
          border: 1px solid var(--color-border);
          background: var(--color-background);
          color: var(--color-text);
          cursor: pointer;
          border-radius: var(--radius-xs);
        }
        button:hover:not(:disabled) {
          background: var(--color-background-hover, #f5f5f5);
        }
        button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        select {
          padding: var(--spacing-xs);
          border: 1px solid var(--color-border);
          background: var(--color-background);
          color: var(--color-text);
          border-radius: var(--radius-xs);
        }
        ul {
          list-style: disc;
          padding-left: var(--spacing-md);
          margin: 0;
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          min-height: 200px;
        }
        li {
          margin-bottom: var(--spacing-xs);
          color: var(--color-text);
          font-family: var(--font-family-mono);
          font-size: var(--font-size-sm);
          word-wrap: break-word;
        }
        .loading {
          text-align: center;
          color: var(--color-secondary);
          font-style: italic;
          padding: var(--spacing-md);
        }
        .page-info {
          color: var(--color-text-secondary);
          font-size: var(--font-size-sm);
        }
        ul:empty::before {
          content: "No past requests found.";
          color: var(--color-secondary);
          font-style: italic;
          display: block;
          padding: var(--spacing-md);
          text-align: center;
        }
      </style>
      <div class="controls">
        <div class="page-size-selector">
          <label for="page-size">Items per page:</label>
          <select id="page-size">
            <option value="10">10</option>
            <option value="25" selected>25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>
        <div class="page-info" id="page-info"></div>
      </div>
      <ul id="list"></ul>
      <div class="pagination">
        <button id="first-page" disabled>First</button>
        <button id="prev-page" disabled>Previous</button>
        <div class="page-info" id="pagination-info"></div>
        <button id="next-page" disabled>Next</button>
        <button id="last-page" disabled>Last</button>
      </div>
    `;
    
    this.currentPage = 0;
    this.pageSize = 25;
    this.totalEntries = 0;
    this.cache = new Map(); // Cache pages for better performance
  }

  async connectedCallback() {
    const user = this.getAttribute('user-id') || 'anonymous';
    this.userId = user;
    
    // Set up event listeners
    this.shadowRoot.getElementById('page-size').addEventListener('change', (e) => {
      this.pageSize = parseInt(e.target.value);
      this.currentPage = 0;
      this.cache.clear();
      this.loadPage();
    });
    
    this.shadowRoot.getElementById('first-page').addEventListener('click', () => {
      this.currentPage = 0;
      this.loadPage();
    });
    
    this.shadowRoot.getElementById('prev-page').addEventListener('click', () => {
      if (this.currentPage > 0) {
        this.currentPage--;
        this.loadPage();
      }
    });
    
    this.shadowRoot.getElementById('next-page').addEventListener('click', () => {
      const maxPage = Math.max(0, Math.ceil(this.totalEntries / this.pageSize) - 1);
      if (this.currentPage < maxPage) {
        this.currentPage++;
        this.loadPage();
      }
    });
    
    this.shadowRoot.getElementById('last-page').addEventListener('click', () => {
      const maxPage = Math.max(0, Math.ceil(this.totalEntries / this.pageSize) - 1);
      this.currentPage = maxPage;
      this.loadPage();
    });
    
    await this.loadPage();
  }

  async loadPage() {
    const cacheKey = `${this.currentPage}-${this.pageSize}`;
    
    // Check cache first
    if (this.cache.has(cacheKey)) {
      const cachedData = this.cache.get(cacheKey);
      this.renderPage(cachedData.history, cachedData.pagination);
      return;
    }
    
    // Show loading state
    this.showLoading();
    
    try {
      const offset = this.currentPage * this.pageSize;
      const url = `/api/v1/history/${this.userId}?limit=${this.pageSize}&offset=${offset}`;
      const res = await fetch(url);
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      
      const data = await res.json();
      
      // Cache the result
      this.cache.set(cacheKey, data);
      
      // Render the page
      this.renderPage(data.history, data.pagination);
      
    } catch (err) {
      console.error('Failed to load history:', err);
      this.showError('Failed to load history');
    }
  }

  showLoading() {
    const list = this.shadowRoot.getElementById('list');
    list.innerHTML = '<li class="loading">Loading...</li>';
    this.updateControls();
  }

  showError(message) {
    const list = this.shadowRoot.getElementById('list');
    list.innerHTML = `<li class="loading">Error: ${message}</li>`;
    this.updateControls();
  }

  renderPage(history, pagination) {
    this.totalEntries = pagination.total;
    
    const list = this.shadowRoot.getElementById('list');
    
    // Use document fragment for efficient DOM manipulation
    const fragment = document.createDocumentFragment();
    
    history.forEach(entry => {
      const li = document.createElement('li');
      li.textContent = `${entry.plugin}: ${JSON.stringify(entry.payload)}`;
      fragment.appendChild(li);
    });
    
    // Single DOM update
    list.innerHTML = '';
    list.appendChild(fragment);
    
    this.updateControls();
  }

  updateControls() {
    const maxPage = Math.max(0, Math.ceil(this.totalEntries / this.pageSize) - 1);
    const startItem = this.currentPage * this.pageSize + 1;
    const endItem = Math.min((this.currentPage + 1) * this.pageSize, this.totalEntries);
    
    // Update page info
    const pageInfo = this.shadowRoot.getElementById('page-info');
    if (this.totalEntries > 0) {
      pageInfo.textContent = `Showing ${startItem}-${endItem} of ${this.totalEntries} entries`;
    } else {
      pageInfo.textContent = 'No entries found';
    }
    
    // Update pagination info
    const paginationInfo = this.shadowRoot.getElementById('pagination-info');
    paginationInfo.textContent = `Page ${this.currentPage + 1} of ${maxPage + 1}`;
    
    // Update button states
    this.shadowRoot.getElementById('first-page').disabled = this.currentPage === 0;
    this.shadowRoot.getElementById('prev-page').disabled = this.currentPage === 0;
    this.shadowRoot.getElementById('next-page').disabled = this.currentPage >= maxPage;
    this.shadowRoot.getElementById('last-page').disabled = this.currentPage >= maxPage;
  }
}

customElements.define('la-past-requests', LAPastRequests);
