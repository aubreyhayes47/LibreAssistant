/**
 * UI Management for LibreAssistant
 * Handles navigation, view switching, and UI updates
 */

class UIManager {
    constructor(stateManager) {
        this.stateManager = stateManager;
        this.validViews = ['models', 'plugins', 'chat', 'monitoring', 'settings', 'plugin_catalogue'];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupMobileMenu();
        this.showView(this.stateManager.get('currentView'));
    }

    setupEventListeners() {
        // Navigation click handlers
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const viewName = link.getAttribute('data-view');
                this.navigateToView(viewName);
            });
        });

        // Handle browser back/forward
        window.addEventListener('popstate', (e) => {
            const state = e.state;
            if (state && state.view) {
                this.showView(state.view, false);
            }
        });

        // Handle initial page load with hash
        window.addEventListener('load', () => {
            const hash = window.location.hash.substring(1);
            if (hash && this.isValidView(hash)) {
                this.navigateToView(hash);
            }
        });
    }

    setupMobileMenu() {
        // Create mobile menu button if it doesn't exist
        if (!document.querySelector('.mobile-menu-btn')) {
            const menuBtn = document.createElement('button');
            menuBtn.className = 'mobile-menu-btn';
            menuBtn.innerHTML = '<i class="fas fa-bars"></i>';
            document.body.appendChild(menuBtn);

            // Toggle sidebar on mobile
            menuBtn.addEventListener('click', () => {
                const sidebar = document.querySelector('.sidebar');
                sidebar.classList.toggle('open');
            });

            // Close sidebar when clicking outside on mobile
            document.addEventListener('click', (e) => {
                const sidebar = document.querySelector('.sidebar');
                const menuBtn = document.querySelector('.mobile-menu-btn');
                
                if (window.innerWidth <= 768 && 
                    !sidebar.contains(e.target) && 
                    !menuBtn.contains(e.target) &&
                    sidebar.classList.contains('open')) {
                    sidebar.classList.remove('open');
                }
            });
        }
    }

    navigateToView(viewName) {
        if (!this.isValidView(viewName)) {
            console.warn(`Invalid view: ${viewName}`);
            return;
        }

        this.showView(viewName);
        this.updateURL(viewName);
        this.closeMobileSidebar();
    }

    showView(viewName, updateHistory = true) {
        // Hide all views
        const allViews = document.querySelectorAll('.view');
        allViews.forEach(view => {
            view.classList.remove('active');
        });

        // Show selected view
        const targetView = document.getElementById(`${viewName}-view`);
        if (targetView) {
            targetView.classList.add('active');
        }

        // Update navigation active state
        this.updateActiveNav(viewName);

        // Update state
        this.stateManager.setCurrentView(viewName);

        // Update browser history if needed
        if (updateHistory) {
            history.pushState({ view: viewName }, '', `#${viewName}`);
        }

        // Load view-specific content
        this.loadViewContent(viewName);
    }

    loadViewContent(viewName) {
        switch (viewName) {
            case 'models':
                if (window.modelManager) {
                    window.modelManager.loadModels();
                }
                break;
            case 'monitoring':
                if (window.monitoringManager) {
                    window.monitoringManager.loadRealTimeData();
                }
                break;
            case 'plugins':
                // Load plugins if plugin manager exists
                if (window.pluginManager) {
                    window.pluginManager.loadPlugins();
                }
                break;
            // Add other view-specific loading logic here
        }
    }

    updateActiveNav(viewName) {
        // Remove active class from all nav links
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
        });

        // Add active class to current view link
        const activeLink = document.querySelector(`[data-view="${viewName}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    }

    updateURL(viewName) {
        history.pushState({ view: viewName }, '', `#${viewName}`);
    }

    closeMobileSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.remove('open');
        }
    }

    isValidView(viewName) {
        return this.validViews.includes(viewName);
    }

    /**
     * Show status message
     */
    showStatus(message, type = 'info', duration = 5000) {
        const statusContainer = this.getOrCreateStatusContainer();
        
        const statusElement = document.createElement('div');
        statusElement.className = `status-message status-${type}`;
        statusElement.textContent = message;
        
        statusContainer.appendChild(statusElement);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (statusElement.parentNode) {
                    statusElement.remove();
                }
            }, duration);
        }
        
        return statusElement;
    }

    getOrCreateStatusContainer() {
        let container = document.getElementById('status-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'status-container';
            container.className = 'status-container';
            document.body.appendChild(container);
        }
        return container;
    }

    /**
     * Show loading state
     */
    showLoading(element, message = 'Loading...') {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (element) {
            element.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>${message}</span>
                </div>
            `;
        }
    }

    /**
     * Hide loading state
     */
    hideLoading(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (element) {
            const loadingState = element.querySelector('.loading-state');
            if (loadingState) {
                loadingState.remove();
            }
        }
    }

    /**
     * Show error message
     */
    showError(message, container = null) {
        if (container) {
            if (typeof container === 'string') {
                container = document.getElementById(container);
            }
            
            if (container) {
                container.innerHTML = `
                    <div class="error-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>${message}</span>
                    </div>
                `;
            }
        } else {
            this.showStatus(message, 'error');
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIManager;
}

// Make class available globally
window.UIManager = UIManager;