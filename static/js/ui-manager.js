/**
 * UI Management for LibreAssistant
 * Handles navigation, view switching, and UI updates
 */

class UIManager {
    constructor(stateManager) {
        this.stateManager = stateManager;
        this.validViews = ['models', 'plugins', 'chat', 'monitoring', 'settings', 'plugin_catalogue'];
        this.asyncOperationManager = new AsyncOperationManager(this);
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
        // Show loading state for the view
        DOMUtils.setLoadingState([`${viewName}-content`, 'main-content'], true, `Loading ${viewName}...`);
        
        switch (viewName) {
            case 'models':
                if (window.modelManager) {
                    window.modelManager.loadModels().finally(() => {
                        DOMUtils.setLoadingState([`${viewName}-content`, 'main-content'], false);
                    });
                }
                break;
            case 'monitoring':
                if (window.monitoringManager) {
                    window.monitoringManager.loadRealTimeData().finally(() => {
                        DOMUtils.setLoadingState([`${viewName}-content`, 'main-content'], false);
                    });
                }
                break;
            case 'plugins':
                // Load plugins if plugin manager exists
                if (window.pluginManager) {
                    window.pluginManager.loadPlugins().finally(() => {
                        DOMUtils.setLoadingState([`${viewName}-content`, 'main-content'], false);
                    });
                }
                break;
            default:
                // For other views, just hide loading
                setTimeout(() => {
                    DOMUtils.setLoadingState([`${viewName}-content`, 'main-content'], false);
                }, 500);
        }
    }

    updateActiveNav(viewName) {
        // Remove active class from all nav links using DOM utilities
        const navLinks = DOMUtils.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            DOMUtils.toggleClass(link, 'active', false);
        });

        // Add active class to current view link
        const activeLink = DOMUtils.querySelector(`[data-view="${viewName}"]`);
        if (activeLink) {
            DOMUtils.toggleClass(activeLink, 'active', true);
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
     * Show status message with enhanced UI
     */
    showStatus(message, type = 'info', duration = 5000) {
        const container = this.getOrCreateStatusContainer();
        const statusElement = DOMUtils.createStatusMessage(message, type, duration);
        
        container.appendChild(statusElement);
        
        // Animate in
        statusElement.style.opacity = '0';
        statusElement.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            statusElement.style.transition = 'all 0.3s ease';
            statusElement.style.opacity = '1';
            statusElement.style.transform = 'translateY(0)';
        }, 10);
        
        return statusElement;
    }

    getOrCreateStatusContainer() {
        let container = DOMUtils.getElementById('status-container');
        if (!container) {
            container = DOMUtils.createElement('div', {
                id: 'status-container',
                className: 'status-container'
            });
            document.body.appendChild(container);
        }
        return container;
    }

    /**
     * Show loading state (delegating to DOMUtils)
     */
    showLoading(element, message = 'Loading...') {
        DOMUtils.showLoading(element, message);
    }

    /**
     * Hide loading state (delegating to DOMUtils)
     */
    hideLoading(element) {
        DOMUtils.hideLoading(element);
    }

    /**
     * Show error message (delegating to DOMUtils)
     */
    showError(message, container = null) {
        if (container) {
            DOMUtils.showError(container, message, true);
        } else {
            // Show as status message if no specific container
            this.showStatus(message, 'error');
        }
    }

    /**
     * Set loading state for the application
     */
    setLoading(isLoading) {
        this.stateManager.setLoading(isLoading);
        
        // Update global loading indicator if it exists
        const loadingIndicator = DOMUtils.getElementById('global-loading-indicator');
        if (loadingIndicator) {
            DOMUtils.toggleClass(loadingIndicator, 'active', isLoading);
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIManager;
}

// Make class available globally
window.UIManager = UIManager;