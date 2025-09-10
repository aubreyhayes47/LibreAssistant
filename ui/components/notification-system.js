// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LANotificationSystem extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          position: fixed;
          top: var(--spacing-md);
          right: var(--spacing-md);
          z-index: 1000;
          font-family: var(--font-family-sans);
          pointer-events: none;
        }
        .notification {
          background: var(--color-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
          padding: var(--spacing-sm) var(--spacing-md);
          margin-bottom: var(--spacing-xs);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          max-width: 400px;
          opacity: 0;
          transform: translateX(100%);
          transition: all 0.3s ease;
          pointer-events: auto;
        }
        .notification.show {
          opacity: 1;
          transform: translateX(0);
        }
        .notification.success {
          border-left: 4px solid #22c55e;
          background: #f0fdf4;
        }
        .notification.error {
          border-left: 4px solid #ef4444;
          background: #fef2f2;
        }
        .notification.info {
          border-left: 4px solid #3b82f6;
          background: #eff6ff;
        }
        .notification.loading {
          border-left: 4px solid #f59e0b;
          background: #fffbeb;
        }
        .icon {
          width: 16px;
          height: 16px;
          flex-shrink: 0;
        }
        .content {
          flex: 1;
          font-size: var(--font-size-sm);
          color: var(--color-text);
        }
        .close-btn {
          background: none;
          border: none;
          cursor: pointer;
          color: var(--color-text-secondary);
          padding: 0;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .loading-spinner {
          width: 16px;
          height: 16px;
          border: 2px solid #f3f3f3;
          border-top: 2px solid #f59e0b;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      </style>
      <div id="container"></div>
    `;
    this.notifications = new Map();
    this.counter = 0;
  }

  show(message, type = 'info', duration = 5000) {
    const id = ++this.counter;
    const container = this.shadowRoot.getElementById('container');
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
      ${this.getIcon(type)}
      <div class="content">${message}</div>
      <button class="close-btn" aria-label="Close notification">×</button>
    `;

    // Add to DOM but keep it hidden initially
    container.appendChild(notification);
    this.notifications.set(id, notification);

    // Show notification with animation
    requestAnimationFrame(() => {
      notification.classList.add('show');
    });

    // Set up close button
    const closeBtn = notification.querySelector('.close-btn');
    closeBtn.addEventListener('click', () => this.dismiss(id));

    // Auto dismiss for non-loading notifications
    if (type !== 'loading' && duration > 0) {
      setTimeout(() => this.dismiss(id), duration);
    }

    return id;
  }

  dismiss(id) {
    const notification = this.notifications.get(id);
    if (!notification) return;

    notification.classList.remove('show');
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
      this.notifications.delete(id);
    }, 300);
  }

  update(id, message, type) {
    const notification = this.notifications.get(id);
    if (!notification) return;

    notification.className = `notification ${type} show`;
    notification.innerHTML = `
      ${this.getIcon(type)}
      <div class="content">${message}</div>
      <button class="close-btn" aria-label="Close notification">×</button>
    `;

    // Re-setup close button
    const closeBtn = notification.querySelector('.close-btn');
    closeBtn.addEventListener('click', () => this.dismiss(id));

    // Auto dismiss for non-loading notifications
    if (type !== 'loading') {
      setTimeout(() => this.dismiss(id), 5000);
    }
  }

  getIcon(type) {
    switch (type) {
      case 'success':
        return '<div class="icon">✓</div>';
      case 'error':
        return '<div class="icon">✗</div>';
      case 'loading':
        return '<div class="loading-spinner"></div>';
      case 'info':
      default:
        return '<div class="icon">ℹ</div>';
    }
  }

  // Convenience methods
  success(message, duration = 5000) {
    return this.show(message, 'success', duration);
  }

  error(message, duration = 8000) {
    return this.show(message, 'error', duration);
  }

  info(message, duration = 5000) {
    return this.show(message, 'info', duration);
  }

  loading(message) {
    return this.show(message, 'loading', 0);
  }

  clear() {
    for (const id of this.notifications.keys()) {
      this.dismiss(id);
    }
  }
}

customElements.define('la-notification-system', LANotificationSystem);

// Global notification instance
window.notifications = null;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    if (!window.notifications) {
      window.notifications = document.createElement('la-notification-system');
      document.body.appendChild(window.notifications);
    }
  });
} else {
  if (!window.notifications) {
    window.notifications = document.createElement('la-notification-system');
    document.body.appendChild(window.notifications);
  }
}