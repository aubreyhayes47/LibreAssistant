/**
 * Monitoring Management for LibreAssistant
 * Handles server logs, errors, and real-time monitoring
 */

class MonitoringManager {
    constructor(apiClient, stateManager, uiManager) {
        this.apiClient = apiClient;
        this.stateManager = stateManager;
        this.uiManager = uiManager;
        this.refreshIntervals = {
            logs: null,
            errors: null
        };
    }

    /**
     * Load real-time monitoring data
     */
    async loadRealTimeData() {
        // Load both logs and errors
        await Promise.all([
            this.fetchServerLogs(),
            this.fetchServerErrors()
        ]);
        
        // Set up auto-refresh if enabled
        this.setupAutoRefresh();
    }

    /**
     * Fetch server logs from API
     */
    async fetchServerLogs() {
        try {
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
            } else {
                console.error('Failed to fetch logs:', data.error);
                this.displayLogsError(data.error);
            }
        } catch (error) {
            console.error('Error fetching logs:', error);
            this.displayLogsError(error.message);
        }
    }

    /**
     * Fetch server errors from API
     */
    async fetchServerErrors() {
        try {
            const data = await this.apiClient.fetchServerErrors();
            if (data.success) {
                this.stateManager.update({
                    errors: data.errors || [],
                    lastErrorUpdate: new Date().toISOString()
                });
                this.displayErrors();
            } else {
                console.error('Failed to fetch errors:', data.error);
                this.displayErrorsError(data.error);
            }
        } catch (error) {
            console.error('Error fetching errors:', error);
            this.displayErrorsError(error.message);
        }
    }

    /**
     * Display logs in the UI
     */
    displayLogs() {
        const logList = document.getElementById('logList');
        if (!logList) return;

        const logs = this.stateManager.get('logs');
        const filter = this.stateManager.get('logFilter');

        if (logs.length === 0) {
            logList.innerHTML = '<div style="text-align: center; color: #a0aec0; padding: 40px;">No logs available</div>';
            return;
        }

        // Filter logs if filter is applied
        const filteredLogs = filter ? 
            logs.filter(log => 
                log.message.toLowerCase().includes(filter.toLowerCase()) ||
                log.level.toLowerCase().includes(filter.toLowerCase())
            ) : logs;

        if (filteredLogs.length === 0) {
            logList.innerHTML = '<div style="text-align: center; color: #a0aec0; padding: 40px;">No logs match the current filter</div>';
            return;
        }

        logList.innerHTML = filteredLogs.map(log => `
            <div class="log-item log-${log.level}">
                <span class="log-time">${this.formatTimestamp(log.timestamp)}</span>
                <span class="log-level">${this.formatLogLevel(log.level)}</span>
                <span class="log-message">${this.escapeHtml(log.message)}</span>
            </div>
        `).join('');

        // Update last update time
        const lastUpdate = document.getElementById('lastLogUpdate');
        if (lastUpdate) {
            const updateTime = this.stateManager.get('lastLogUpdate');
            lastUpdate.textContent = updateTime ? new Date(updateTime).toLocaleTimeString() : 'Never';
        }
    }

    /**
     * Display errors in the UI
     */
    displayErrors() {
        const errorList = document.getElementById('errorList');
        if (!errorList) return;

        const errors = this.stateManager.get('errors');
        const filter = this.stateManager.get('errorFilter');

        if (errors.length === 0) {
            errorList.innerHTML = '<div style="text-align: center; color: #a0aec0; padding: 40px;">No errors found</div>';
            return;
        }

        // Filter errors if filter is applied
        const filteredErrors = filter ? 
            errors.filter(error => 
                error.message.toLowerCase().includes(filter.toLowerCase()) ||
                error.type.toLowerCase().includes(filter.toLowerCase())
            ) : errors;

        if (filteredErrors.length === 0) {
            errorList.innerHTML = '<div style="text-align: center; color: #a0aec0; padding: 40px;">No errors match the current filter</div>';
            return;
        }

        errorList.innerHTML = filteredErrors.map(error => `
            <div class="error-item error-${error.severity || 'medium'}">
                <div class="error-header">
                    <span class="error-time">${this.formatTimestamp(error.timestamp)}</span>
                    <span class="error-type">${error.type}</span>
                    <span class="error-severity severity-${error.severity || 'medium'}">${error.severity || 'Medium'}</span>
                </div>
                <div class="error-message">${this.escapeHtml(error.message)}</div>
                ${error.suggestion ? `<div class="error-suggestion"><i class="fas fa-lightbulb"></i> ${this.escapeHtml(error.suggestion)}</div>` : ''}
            </div>
        `).join('');

        // Update last update time
        const lastUpdate = document.getElementById('lastErrorUpdate');
        if (lastUpdate) {
            const updateTime = this.stateManager.get('lastErrorUpdate');
            lastUpdate.textContent = updateTime ? new Date(updateTime).toLocaleTimeString() : 'Never';
        }
    }

    /**
     * Display logs error message
     */
    displayLogsError(errorMessage) {
        const logList = document.getElementById('logList');
        if (logList) {
            logList.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Failed to load logs: ${this.escapeHtml(errorMessage)}</span>
                </div>
            `;
        }
    }

    /**
     * Display errors error message
     */
    displayErrorsError(errorMessage) {
        const errorList = document.getElementById('errorList');
        if (errorList) {
            errorList.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Failed to load errors: ${this.escapeHtml(errorMessage)}</span>
                </div>
            `;
        }
    }

    /**
     * Clear logs display and optionally server logs
     */
    clearLogs() {
        // Create a custom dialog to clarify client vs server clearing
        const choice = prompt(
            'Choose clearing option:\n' +
            '1 - Clear display only (client-side)\n' +
            '2 - Clear display and server logs\n' +
            'Enter 1 or 2:'
        );
        
        if (choice === '1') {
            this.clearLogsClient();
        } else if (choice === '2') {
            this.clearLogsServer();
        }
    }

    /**
     * Clear logs display only (client-side)
     */
    clearLogsClient() {
        this.stateManager.clearLogs();
        this.displayLogs();
        
        const logList = document.getElementById('logList');
        if (logList) {
            logList.innerHTML = `
                <div style="text-align: center; color: #a0aec0; padding: 40px;">
                    <i class="fas fa-info-circle"></i><br>
                    Client display cleared<br>
                    <small>Server logs remain intact. Refresh to reload from server.</small>
                </div>
            `;
        }
    }

    /**
     * Clear logs on server and client
     */
    async clearLogsServer() {
        try {
            const response = await this.apiClient.post('/api/server/logs/clear');
            
            if (response.success) {
                // Also clear client display
                this.stateManager.clearLogs();
                this.displayLogs();
                
                const logList = document.getElementById('logList');
                if (logList) {
                    logList.innerHTML = `
                        <div style="text-align: center; color: #4ade80; padding: 40px;">
                            <i class="fas fa-check-circle"></i><br>
                            Server logs cleared successfully<br>
                            <small>Both client display and server logs have been cleared.</small>
                        </div>
                    `;
                }
                
                // Refresh logs after a short delay to show the clear action was logged
                setTimeout(() => this.fetchServerLogs(), 2000);
            } else {
                throw new Error(response.error || 'Failed to clear server logs');
            }
        } catch (error) {
            console.error('Failed to clear server logs:', error);
            alert(`Failed to clear server logs: ${error.message}`);
        }
    }

    /**
     * Clear errors display and optionally server errors
     */
    clearErrors() {
        // Create a custom dialog to clarify client vs server clearing
        const choice = prompt(
            'Choose clearing option:\n' +
            '1 - Clear display only (client-side)\n' +
            '2 - Clear display and server errors\n' +
            'Enter 1 or 2:'
        );
        
        if (choice === '1') {
            this.clearErrorsClient();
        } else if (choice === '2') {
            this.clearErrorsServer();
        }
    }

    /**
     * Clear errors display only (client-side)
     */
    clearErrorsClient() {
        this.stateManager.clearErrors();
        this.displayErrors();
        
        const errorList = document.getElementById('errorList');
        if (errorList) {
            errorList.innerHTML = `
                <div style="text-align: center; color: #a0aec0; padding: 40px;">
                    <i class="fas fa-info-circle"></i><br>
                    Client display cleared<br>
                    <small>Server errors remain intact. Refresh to reload from server.</small>
                </div>
            `;
        }
    }

    /**
     * Clear errors on server and client
     */
    async clearErrorsServer() {
        try {
            const response = await this.apiClient.post('/api/server/errors/clear');
            
            if (response.success) {
                // Also clear client display
                this.stateManager.clearErrors();
                this.displayErrors();
                
                const errorList = document.getElementById('errorList');
                if (errorList) {
                    errorList.innerHTML = `
                        <div style="text-align: center; color: #4ade80; padding: 40px;">
                            <i class="fas fa-check-circle"></i><br>
                            Server errors cleared successfully<br>
                            <small>Both client display and server errors have been cleared.</small>
                        </div>
                    `;
                }
                
                // Refresh errors after a short delay to show the clear action was logged
                setTimeout(() => this.fetchServerErrors(), 2000);
            } else {
                throw new Error(response.error || 'Failed to clear server errors');
            }
        } catch (error) {
            console.error('Failed to clear server errors:', error);
            alert(`Failed to clear server errors: ${error.message}`);
        }
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
        const date = new Date(timestamp);
        return date.toISOString().replace('T', ' ').substring(0, 19);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MonitoringManager;
}

// Make class available globally
window.MonitoringManager = MonitoringManager;