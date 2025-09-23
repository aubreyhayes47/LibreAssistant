/**
 * Monitoring Management for LibreAssistant
 * Handles server logs, errors, and real-time monitoring
 */

class MonitoringManager {
    constructor(apiClient, stateManager, uiManager, asyncOperationManager) {
        this.apiClient = apiClient;
        this.stateManager = stateManager;
        this.uiManager = uiManager;
        this.asyncOperationManager = asyncOperationManager;
        this.refreshIntervals = {
            logs: null,
            errors: null
        };
    }

    /**
     * Load real-time monitoring data
     */
    async loadRealTimeData() {
        // Use async operation manager for better UI feedback
        return this.asyncOperationManager.executeOperation({
            id: 'load-monitoring-data',
            name: 'Load Monitoring Data',
            showGlobalLoading: true,
            loadingMessage: 'Loading monitoring data...',
            operation: async () => {
                // Load both logs and errors in parallel
                await Promise.all([
                    this.fetchServerLogs(),
                    this.fetchServerErrors()
                ]);
                
                // Set up auto-refresh if enabled
                this.setupAutoRefresh();
                
                return { logs: this.stateManager.get('logs'), errors: this.stateManager.get('errors') };
            },
            onError: (error) => {
                console.error('Failed to load monitoring data:', error);
            }
        });
    }

    /**
     * Fetch server logs from API
     */
    async fetchServerLogs() {
        return this.asyncOperationManager.executeOperation({
            id: 'fetch-logs',
            name: 'Fetch Server Logs',
            targetElement: 'logList',
            loadingMessage: 'Fetching logs...',
            operation: async () => {
                const response = await fetch(`${window.appConfig.getBackendBaseUrl()}/api/server/logs`);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                if (data.success) {
                    this.stateManager.update({
                        logs: data.logs || [],
                        lastLogUpdate: new Date().toISOString()
                    });
                    this.displayLogs();
                    return data.logs;
                } else {
                    throw new Error(data.error || 'Failed to fetch logs');
                }
            },
            onError: (error) => {
                console.error('Error fetching logs:', error);
                this.displayLogsError(error.message);
            }
        });
    }

    /**
     * Fetch server errors from API
     */
    async fetchServerErrors() {
        return this.asyncOperationManager.executeOperation({
            id: 'fetch-errors',
            name: 'Fetch Server Errors',
            targetElement: 'errorList',
            loadingMessage: 'Fetching errors...',
            operation: async () => {
                const data = await this.apiClient.fetchServerErrors();
                if (data.success) {
                    this.stateManager.update({
                        errors: data.errors || [],
                        lastErrorUpdate: new Date().toISOString()
                    });
                    this.displayErrors();
                    return data.errors;
                } else {
                    throw new Error(data.error || 'Failed to fetch errors');
                }
            },
            onError: (error) => {
                console.error('Error fetching errors:', error);
                this.displayErrorsError(error.message);
            }
        });
    }

    /**
     * Display logs in the UI using DOM utilities
     */
    displayLogs() {
        const logList = DOMUtils.getElementById('logList');
        if (!logList) return;

        DOMUtils.clearState(logList);
        
        const logs = this.stateManager.get('logs');
        const filter = this.stateManager.get('logFilter');

        if (logs.length === 0) {
            DOMUtils.showEmpty(logList, 'No logs available', 'fas fa-file-alt');
            return;
        }

        // Filter logs if filter is applied
        const filteredLogs = filter ? 
            logs.filter(log => 
                log.message.toLowerCase().includes(filter.toLowerCase()) ||
                log.level.toLowerCase().includes(filter.toLowerCase())
            ) : logs;

        if (filteredLogs.length === 0) {
            DOMUtils.showEmpty(logList, 'No logs match the current filter', 'fas fa-search');
            return;
        }

        logList.innerHTML = filteredLogs.map(log => `
            <div class="log-item log-${log.level}">
                <span class="log-time">${DOMUtils.formatTimestamp(log.timestamp, 'iso')}</span>
                <span class="log-level">${this.formatLogLevel(log.level)}</span>
                <span class="log-message">${DOMUtils.escapeHtml(log.message)}</span>
            </div>
        `).join('');

        // Update last update time
        this.updateLastUpdateTime('lastLogUpdate', 'lastLogUpdate');
    }

    /**
     * Display errors in the UI using DOM utilities
     */
    displayErrors() {
        const errorList = DOMUtils.getElementById('errorList');
        if (!errorList) return;

        DOMUtils.clearState(errorList);
        
        const errors = this.stateManager.get('errors');
        const filter = this.stateManager.get('errorFilter');

        if (errors.length === 0) {
            DOMUtils.showEmpty(errorList, 'No errors found', 'fas fa-check-circle');
            return;
        }

        // Filter errors if filter is applied
        const filteredErrors = filter ? 
            errors.filter(error => 
                error.message.toLowerCase().includes(filter.toLowerCase()) ||
                error.type.toLowerCase().includes(filter.toLowerCase())
            ) : errors;

        if (filteredErrors.length === 0) {
            DOMUtils.showEmpty(errorList, 'No errors match the current filter', 'fas fa-search');
            return;
        }

        errorList.innerHTML = filteredErrors.map(error => `
            <div class="error-item error-${error.severity || 'medium'}">
                <div class="error-header">
                    <span class="error-time">${DOMUtils.formatTimestamp(error.timestamp, 'iso')}</span>
                    <span class="error-type">${DOMUtils.escapeHtml(error.type)}</span>
                    <span class="error-severity severity-${error.severity || 'medium'}">${error.severity || 'Medium'}</span>
                </div>
                <div class="error-message">${DOMUtils.escapeHtml(error.message)}</div>
                ${error.suggestion ? `<div class="error-suggestion"><i class="fas fa-lightbulb"></i> ${DOMUtils.escapeHtml(error.suggestion)}</div>` : ''}
            </div>
        `).join('');

        // Update last update time
        this.updateLastUpdateTime('lastErrorUpdate', 'lastErrorUpdate');
    }

    /**
     * Display logs error message using DOM utilities
     */
    displayLogsError(errorMessage) {
        const logList = DOMUtils.getElementById('logList');
        if (logList) {
            DOMUtils.showError(logList, errorMessage, true);
        }
    }

    /**
     * Display errors error message using DOM utilities
     */
    displayErrorsError(errorMessage) {
        const errorList = DOMUtils.getElementById('errorList');
        if (errorList) {
            DOMUtils.showError(errorList, errorMessage, true);
        }
    }

    /**
     * Clear logs display and optionally server logs with better UX
     */
    clearLogs() {
        // Show a modal dialog for better UX
        this.showClearConfirmationModal('logs', 'Clear Logs', 
            'Choose how you want to clear the logs:', 
            this.clearLogsClient.bind(this), 
            this.clearLogsServer.bind(this)
        );
    }

    /**
     * Clear logs display only (client-side) with better feedback
     */
    clearLogsClient() {
        this.stateManager.clearLogs();
        
        const logList = DOMUtils.getElementById('logList');
        if (logList) {
            logList.innerHTML = `
                <div class="info-state">
                    <i class="fas fa-info-circle text-info"></i>
                    <div>
                        <strong>Client display cleared</strong><br>
                        <small class="text-muted">Server logs remain intact. Refresh to reload from server.</small>
                    </div>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="window.monitoringManager.fetchServerLogs()">
                        <i class="fas fa-sync"></i> Reload from Server
                    </button>
                </div>
            `;
        }
        
        this.uiManager.showStatus('Client log display cleared', 'info');
    }

    /**
     * Clear logs on server and client with async operation management
     */
    async clearLogsServer() {
        return this.asyncOperationManager.executeOperation({
            id: 'clear-server-logs',
            name: 'Clear Server Logs',
            loadingMessage: 'Clearing server logs...',
            successMessage: 'Server logs cleared successfully',
            operation: async () => {
                const response = await this.apiClient.post('/api/server/logs/clear');
                
                if (response.success) {
                    // Also clear client display
                    this.stateManager.clearLogs();
                    
                    const logList = DOMUtils.getElementById('logList');
                    if (logList) {
                        logList.innerHTML = `
                            <div class="success-state">
                                <i class="fas fa-check-circle text-success"></i>
                                <div>
                                    <strong>Server logs cleared successfully</strong><br>
                                    <small class="text-muted">Both client display and server logs have been cleared.</small>
                                </div>
                            </div>
                        `;
                    }
                    
                    // Refresh logs after a short delay to show the clear action was logged
                    setTimeout(() => this.fetchServerLogs(), 2000);
                    return response;
                } else {
                    throw new Error(response.error || 'Failed to clear server logs');
                }
            },
            onError: (error) => {
                console.error('Failed to clear server logs:', error);
            }
        });
    }

    /**
     * Clear errors display and optionally server errors with better UX
     */
    clearErrors() {
        // Show a modal dialog for better UX
        this.showClearConfirmationModal('errors', 'Clear Errors', 
            'Choose how you want to clear the errors:', 
            this.clearErrorsClient.bind(this), 
            this.clearErrorsServer.bind(this)
        );
    }

    /**
     * Clear errors display only (client-side) with better feedback
     */
    clearErrorsClient() {
        this.stateManager.clearErrors();
        
        const errorList = DOMUtils.getElementById('errorList');
        if (errorList) {
            errorList.innerHTML = `
                <div class="info-state">
                    <i class="fas fa-info-circle text-info"></i>
                    <div>
                        <strong>Client display cleared</strong><br>
                        <small class="text-muted">Server errors remain intact. Refresh to reload from server.</small>
                    </div>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="window.monitoringManager.fetchServerErrors()">
                        <i class="fas fa-sync"></i> Reload from Server
                    </button>
                </div>
            `;
        }
        
        this.uiManager.showStatus('Client error display cleared', 'info');
    }

    /**
     * Clear errors on server and client with async operation management
     */
    async clearErrorsServer() {
        return this.asyncOperationManager.executeOperation({
            id: 'clear-server-errors',
            name: 'Clear Server Errors',
            loadingMessage: 'Clearing server errors...',
            successMessage: 'Server errors cleared successfully',
            operation: async () => {
                const response = await this.apiClient.post('/api/server/errors/clear');
                
                if (response.success) {
                    // Also clear client display
                    this.stateManager.clearErrors();
                    
                    const errorList = DOMUtils.getElementById('errorList');
                    if (errorList) {
                        errorList.innerHTML = `
                            <div class="success-state">
                                <i class="fas fa-check-circle text-success"></i>
                                <div>
                                    <strong>Server errors cleared successfully</strong><br>
                                    <small class="text-muted">Both client display and server errors have been cleared.</small>
                                </div>
                            </div>
                        `;
                    }
                    
                    // Refresh errors after a short delay to show the clear action was logged
                    setTimeout(() => this.fetchServerErrors(), 2000);
                    return response;
                } else {
                    throw new Error(response.error || 'Failed to clear server errors');
                }
            },
            onError: (error) => {
                console.error('Failed to clear server errors:', error);
            }
        });
    }

    /**
     * Filter logs
     */
    filterLogs() {
        const filterInput = document.getElementById('logFilter');
        if (filterInput) {
            const filterValue = filterInput.value;
            this.stateManager.set('logFilter', filterValue);
            this.displayLogs();
        }
    }

    /**
     * Filter errors
     */
    filterErrors() {
        const filterInput = document.getElementById('errorFilter');
        if (filterInput) {
            const filterValue = filterInput.value;
            this.stateManager.set('errorFilter', filterValue);
            this.displayErrors();
        }
    }

    /**
     * Toggle auto-refresh for logs
     */
    toggleAutoRefresh() {
        const autoRefresh = !this.stateManager.get('autoRefreshLogs');
        this.stateManager.set('autoRefreshLogs', autoRefresh);
        
        if (autoRefresh) {
            this.startAutoRefresh('logs');
            this.uiManager.showStatus('Auto-refresh enabled for logs', 'success');
        } else {
            this.stopAutoRefresh('logs');
            this.uiManager.showStatus('Auto-refresh disabled for logs', 'info');
        }
        
        this.updateAutoRefreshUI();
    }

    /**
     * Start auto-refresh for a data type
     */
    startAutoRefresh(type) {
        this.stopAutoRefresh(type); // Clear existing interval
        
        const refreshFunction = type === 'logs' ? 
            () => this.fetchServerLogs() : 
            () => this.fetchServerErrors();
            
        this.refreshIntervals[type] = setInterval(refreshFunction, 5000); // Refresh every 5 seconds
    }

    /**
     * Stop auto-refresh for a data type
     */
    stopAutoRefresh(type) {
        if (this.refreshIntervals[type]) {
            clearInterval(this.refreshIntervals[type]);
            this.refreshIntervals[type] = null;
        }
    }

    /**
     * Setup auto-refresh based on current state
     */
    setupAutoRefresh() {
        if (this.stateManager.get('autoRefreshLogs')) {
            this.startAutoRefresh('logs');
        }
        if (this.stateManager.get('autoRefreshErrors')) {
            this.startAutoRefresh('errors');
        }
        this.updateAutoRefreshUI();
    }

    /**
     * Update auto-refresh UI elements
     */
    updateAutoRefreshUI() {
        const autoRefreshBtn = document.getElementById('autoRefreshBtn');
        if (autoRefreshBtn) {
            const isEnabled = this.stateManager.get('autoRefreshLogs');
            autoRefreshBtn.textContent = isEnabled ? 'Disable Auto-refresh' : 'Enable Auto-refresh';
            autoRefreshBtn.className = isEnabled ? 'btn btn-secondary' : 'btn btn-primary';
        }
    }

    /**
     * Open server monitoring tab
     */
    openServerTab(evt, tabName) {
        // Get all elements with class="monitoring-tabcontent" and hide them
        const tabcontent = document.getElementsByClassName("monitoring-tabcontent");
        for (let i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
        }

        // Get all elements with class="monitoring-tablinks" and remove the class "active"
        const tablinks = document.getElementsByClassName("monitoring-tablinks");
        for (let i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }

        // Show the specific tab content and mark the button as active
        const tabElement = document.getElementById(tabName);
        if (tabElement) {
            tabElement.style.display = "block";
        }
        
        if (evt && evt.currentTarget) {
            evt.currentTarget.className += " active";
        }
    }

    /**
     * Utility methods
     */
    formatLogLevel(level) {
        const levelMap = {
            'debug': 'DEBUG',
            'info': 'INFO',
            'warn': 'WARNING',
            'error': 'ERROR',
            'fatal': 'CRITICAL'
        };
        return levelMap[level.toLowerCase()] || level.toUpperCase();
    }

    formatTimestamp(timestamp) {
        return DOMUtils.formatTimestamp(timestamp, 'iso');
    }

    escapeHtml(text) {
        return DOMUtils.escapeHtml(text);
    }

    /**
     * Update last update time display
     */
    updateLastUpdateTime(stateKey, elementId) {
        const lastUpdate = DOMUtils.getElementById(elementId);
        if (lastUpdate) {
            const updateTime = this.stateManager.get(stateKey);
            DOMUtils.setContent(lastUpdate, updateTime ? DOMUtils.formatTimestamp(updateTime, 'time') : 'Never');
        }
    }

    /**
     * Show clear confirmation modal for better UX
     */
    showClearConfirmationModal(type, title, message, clientCallback, serverCallback) {
        const modalContent = `
            <div class="modal fade" id="clearConfirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                            <div class="alert alert-info">
                                <strong>Client-side only:</strong> Clears the display but keeps server data intact.<br>
                                <strong>Server and client:</strong> Permanently removes data from both server and display.
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-info" onclick="window.monitoringManager.handleClearChoice('client', '${type}'); bootstrap.Modal.getInstance(document.getElementById('clearConfirmModal')).hide();">
                                Clear Display Only
                            </button>
                            <button type="button" class="btn btn-warning" onclick="window.monitoringManager.handleClearChoice('server', '${type}'); bootstrap.Modal.getInstance(document.getElementById('clearConfirmModal')).hide();">
                                Clear Server & Display
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = DOMUtils.getElementById('clearConfirmModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalContent);
        
        // Store callbacks for later use
        this._clearCallbacks = { clientCallback, serverCallback };
        
        // Show modal (check if Bootstrap is available)
        if (typeof bootstrap !== 'undefined') {
            const modal = new bootstrap.Modal(document.getElementById('clearConfirmModal'));
            modal.show();
        } else {
            // Fallback to prompt if Bootstrap is not available
            const choice = prompt(message + '\n1 - Clear display only\n2 - Clear server and display\nEnter 1 or 2:');
            if (choice === '1') {
                clientCallback();
            } else if (choice === '2') {
                serverCallback();
            }
        }
    }

    /**
     * Handle clear choice from modal
     */
    handleClearChoice(choice, type) {
        if (this._clearCallbacks) {
            if (choice === 'client') {
                this._clearCallbacks.clientCallback();
            } else if (choice === 'server') {
                this._clearCallbacks.serverCallback();
            }
            this._clearCallbacks = null;
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MonitoringManager;
}

// Make class available globally
window.MonitoringManager = MonitoringManager;