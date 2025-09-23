/**
 * Plugin Manager for LibreAssistant Frontend
 * Provides comprehensive plugin management with enhanced error feedback
 */

class PluginManager {
    constructor(apiClient, stateManager, uiManager, asyncOperationManager) {
        this.apiClient = apiClient;
        this.stateManager = stateManager;
        this.uiManager = uiManager;
        this.asyncOperationManager = asyncOperationManager;
        this.plugins = new Map();
        this.pluginStats = {
            total: 0,
            active: 0,
            failed: 0,
            stopped: 0
        };
        this.refreshInterval = null;
        this.autoRefreshEnabled = false;
    }

    /**
     * Initialize plugin manager
     */
    async init() {
        await this.loadPlugins();
        this.setupEventListeners();
        this.updatePluginStats();
    }

    /**
     * Load all plugins from server
     */
    async loadPlugins() {
        return this.asyncOperationManager.executeOperation({
            id: 'load-plugins',
            name: 'Load Plugins',
            targetElement: 'plugin-list',
            loadingMessage: 'Loading plugins...',
            successMessage: 'Plugins loaded successfully',
            operation: async () => {
                const response = await this.apiClient.get('/api/plugins');
                
                if (response.success) {
                    this.processPluginData(response.plugins || []);
                    this.displayPlugins();
                    this.updatePluginStats();
                    return response.plugins;
                } else {
                    throw new Error(response.error || 'Failed to load plugins');
                }
            },
            onError: (error) => {
                this.displayPluginError(error.message);
            }
        });
    }

    /**
     * Process plugin data from server
     */
    processPluginData(pluginsData) {
        this.plugins.clear();
        
        pluginsData.forEach(plugin => {
            // Enhance plugin data with status information
            const enhancedPlugin = {
                ...plugin,
                lastStatusCheck: new Date(),
                errorHistory: [],
                startAttempts: 0,
                maxStartAttempts: 3
            };
            
            this.plugins.set(plugin.id, enhancedPlugin);
        });
        
        // Update state manager
        this.stateManager.update({
            activePlugins: Array.from(this.plugins.values()).filter(p => p.status === 'running')
        });
    }

    /**
     * Display plugins in UI
     */
    displayPlugins() {
        const pluginList = DOMUtils.getElementById('plugin-list');
        if (!pluginList) return;

        DOMUtils.clearState(pluginList);

        if (this.plugins.size === 0) {
            DOMUtils.showEmpty(pluginList, 'No plugins available', 'fas fa-puzzle-piece');
            return;
        }

        const pluginsArray = Array.from(this.plugins.values());
        
        // Group plugins by status for better organization
        const groupedPlugins = this.groupPluginsByStatus(pluginsArray);
        
        let html = '';
        
        // Display active plugins first
        if (groupedPlugins.running.length > 0) {
            html += this.renderPluginGroup('Active Plugins', groupedPlugins.running, 'success');
        }
        
        if (groupedPlugins.stopped.length > 0) {
            html += this.renderPluginGroup('Stopped Plugins', groupedPlugins.stopped, 'secondary');
        }
        
        if (groupedPlugins.failed.length > 0) {
            html += this.renderPluginGroup('Failed Plugins', groupedPlugins.failed, 'danger');
        }

        pluginList.innerHTML = html;
        this.attachPluginEventListeners();
    }

    /**
     * Group plugins by status
     */
    groupPluginsByStatus(plugins) {
        return {
            running: plugins.filter(p => p.status === 'running'),
            stopped: plugins.filter(p => p.status === 'stopped'),
            failed: plugins.filter(p => p.status === 'failed' || p.status === 'error')
        };
    }

    /**
     * Render a group of plugins
     */
    renderPluginGroup(title, plugins, statusType) {
        if (plugins.length === 0) return '';
        
        return `
            <div class="plugin-group mb-4">
                <h5 class="plugin-group-title text-${statusType}">
                    <i class="fas fa-${this.getStatusIcon(statusType)}"></i>
                    ${title} (${plugins.length})
                </h5>
                <div class="plugin-cards">
                    ${plugins.map(plugin => this.renderPluginCard(plugin)).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Render individual plugin card
     */
    renderPluginCard(plugin) {
        const statusBadge = this.getStatusBadge(plugin.status);
        const actionButtons = this.getActionButtons(plugin);
        const errorInfo = this.getErrorInfo(plugin);
        
        return `
            <div class="plugin-card card" data-plugin-id="${plugin.id}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div class="plugin-info">
                        <h6 class="mb-0">${DOMUtils.escapeHtml(plugin.name)}</h6>
                        <small class="text-muted">${DOMUtils.escapeHtml(plugin.id)}</small>
                    </div>
                    ${statusBadge}
                </div>
                <div class="card-body">
                    <p class="card-text">${DOMUtils.escapeHtml(plugin.description || 'No description available')}</p>
                    
                    <div class="plugin-details">
                        <div class="row">
                            <div class="col-sm-6">
                                <small class="text-muted">Version:</small><br>
                                <span>${DOMUtils.escapeHtml(plugin.version || 'Unknown')}</span>
                            </div>
                            <div class="col-sm-6">
                                <small class="text-muted">Port:</small><br>
                                <span>${plugin.mcp_port || 'Not assigned'}</span>
                            </div>
                        </div>
                    </div>
                    
                    ${errorInfo}
                    
                    <div class="plugin-actions mt-3">
                        ${actionButtons}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Get status badge for plugin
     */
    getStatusBadge(status) {
        const badgeClass = {
            'running': 'success',
            'stopped': 'secondary',
            'failed': 'danger',
            'error': 'danger',
            'starting': 'warning',
            'stopping': 'warning'
        }[status] || 'secondary';
        
        const icon = {
            'running': 'play',
            'stopped': 'stop',
            'failed': 'exclamation-triangle',
            'error': 'exclamation-triangle',
            'starting': 'spinner fa-spin',
            'stopping': 'spinner fa-spin'
        }[status] || 'question';
        
        return `
            <span class="badge bg-${badgeClass}">
                <i class="fas fa-${icon}"></i>
                ${status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
        `;
    }

    /**
     * Get action buttons for plugin
     */
    getActionButtons(plugin) {
        const isRunning = plugin.status === 'running';
        const isStarting = plugin.status === 'starting';
        const isStopping = plugin.status === 'stopping';
        const canStart = !isRunning && !isStarting && plugin.startAttempts < plugin.maxStartAttempts;
        
        let buttons = '';
        
        if (canStart) {
            buttons += `
                <button class="btn btn-sm btn-success me-2" 
                        onclick="window.pluginManager.startPlugin('${plugin.id}')">
                    <i class="fas fa-play"></i> Start
                </button>
            `;
        }
        
        if (isRunning && !isStopping) {
            buttons += `
                <button class="btn btn-sm btn-warning me-2" 
                        onclick="window.pluginManager.stopPlugin('${plugin.id}')">
                    <i class="fas fa-stop"></i> Stop
                </button>
            `;
        }
        
        if (!isRunning && !isStarting) {
            buttons += `
                <button class="btn btn-sm btn-info me-2" 
                        onclick="window.pluginManager.restartPlugin('${plugin.id}')">
                    <i class="fas fa-redo"></i> Restart
                </button>
            `;
        }
        
        buttons += `
            <button class="btn btn-sm btn-outline-secondary me-2" 
                    onclick="window.pluginManager.showPluginDetails('${plugin.id}')">
                <i class="fas fa-info-circle"></i> Details
            </button>
        `;
        
        if (plugin.status === 'failed' || plugin.errorHistory.length > 0) {
            buttons += `
                <button class="btn btn-sm btn-outline-danger" 
                        onclick="window.pluginManager.clearPluginErrors('${plugin.id}')">
                    <i class="fas fa-times"></i> Clear Errors
                </button>
            `;
        }
        
        return buttons;
    }

    /**
     * Get error information for plugin
     */
    getErrorInfo(plugin) {
        if (plugin.status !== 'failed' && plugin.status !== 'error' && !plugin.last_error) {
            return '';
        }
        
        const errorMessage = plugin.last_error || 'Unknown error occurred';
        const errorTime = plugin.lastStatusCheck ? DOMUtils.formatTimestamp(plugin.lastStatusCheck, 'time') : '';
        
        return `
            <div class="alert alert-danger mt-2" role="alert">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>Error:</strong> ${DOMUtils.escapeHtml(errorMessage)}
                        ${errorTime ? `<br><small class="text-muted">Last occurred: ${errorTime}</small>` : ''}
                    </div>
                    <button type="button" class="btn-close btn-sm" 
                            onclick="this.parentElement.parentElement.style.display='none'"></button>
                </div>
            </div>
        `;
    }

    /**
     * Start a plugin
     */
    async startPlugin(pluginId) {
        const plugin = this.plugins.get(pluginId);
        if (!plugin) return;
        
        // Check start attempts
        if (plugin.startAttempts >= plugin.maxStartAttempts) {
            this.uiManager.showStatus(`Plugin ${plugin.name} has exceeded maximum start attempts`, 'error');
            return;
        }
        
        return this.asyncOperationManager.executeOperation({
            id: `start-plugin-${pluginId}`,
            name: `Start ${plugin.name}`,
            loadingMessage: `Starting ${plugin.name}...`,
            successMessage: `${plugin.name} started successfully`,
            operation: async () => {
                // Update UI immediately
                plugin.status = 'starting';
                plugin.startAttempts++;
                this.updatePluginInUI(plugin);
                
                const response = await this.apiClient.post(`/api/plugins/${pluginId}/start`);
                
                if (response.success) {
                    plugin.status = 'running';
                    plugin.mcp_port = response.port;
                    plugin.last_error = null;
                    this.updatePluginStats();
                    this.updatePluginInUI(plugin);
                    return response;
                } else {
                    throw new Error(response.error || 'Failed to start plugin');
                }
            },
            onError: (error) => {
                plugin.status = 'failed';
                plugin.last_error = error.message;
                plugin.errorHistory.push({
                    timestamp: new Date(),
                    error: error.message,
                    action: 'start'
                });
                this.updatePluginInUI(plugin);
                this.updatePluginStats();
            }
        });
    }

    /**
     * Stop a plugin
     */
    async stopPlugin(pluginId) {
        const plugin = this.plugins.get(pluginId);
        if (!plugin) return;
        
        return this.asyncOperationManager.executeOperation({
            id: `stop-plugin-${pluginId}`,
            name: `Stop ${plugin.name}`,
            loadingMessage: `Stopping ${plugin.name}...`,
            successMessage: `${plugin.name} stopped successfully`,
            operation: async () => {
                // Update UI immediately
                plugin.status = 'stopping';
                this.updatePluginInUI(plugin);
                
                const response = await this.apiClient.post(`/api/plugins/${pluginId}/stop`);
                
                if (response.success) {
                    plugin.status = 'stopped';
                    plugin.mcp_port = null;
                    this.updatePluginStats();
                    this.updatePluginInUI(plugin);
                    return response;
                } else {
                    throw new Error(response.error || 'Failed to stop plugin');
                }
            },
            onError: (error) => {
                plugin.status = 'failed';
                plugin.last_error = error.message;
                plugin.errorHistory.push({
                    timestamp: new Date(),
                    error: error.message,
                    action: 'stop'
                });
                this.updatePluginInUI(plugin);
                this.updatePluginStats();
            }
        });
    }

    /**
     * Restart a plugin
     */
    async restartPlugin(pluginId) {
        const plugin = this.plugins.get(pluginId);
        if (!plugin) return;
        
        if (plugin.status === 'running') {
            await this.stopPlugin(pluginId);
            // Wait a moment before starting
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        return this.startPlugin(pluginId);
    }

    /**
     * Update plugin in UI
     */
    updatePluginInUI(plugin) {
        const pluginCard = DOMUtils.querySelector(`[data-plugin-id="${plugin.id}"]`);
        if (pluginCard) {
            // Update the entire card
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = this.renderPluginCard(plugin);
            pluginCard.parentNode.replaceChild(tempDiv.firstElementChild, pluginCard);
            this.attachPluginEventListeners();
        }
    }

    /**
     * Show plugin details modal
     */
    showPluginDetails(pluginId) {
        const plugin = this.plugins.get(pluginId);
        if (!plugin) return;
        
        const modalContent = `
            <div class="modal fade" id="pluginDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${DOMUtils.escapeHtml(plugin.name)} Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${this.renderPluginDetails(plugin)}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = DOMUtils.getElementById('pluginDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalContent);
        
        // Show modal (assuming Bootstrap is available)
        const modal = new bootstrap.Modal(document.getElementById('pluginDetailsModal'));
        modal.show();
    }

    /**
     * Render plugin details
     */
    renderPluginDetails(plugin) {
        const errorHistory = plugin.errorHistory.slice(-5); // Show last 5 errors
        
        return `
            <div class="row">
                <div class="col-md-6">
                    <h6>Basic Information</h6>
                    <table class="table table-sm">
                        <tr><td><strong>ID:</strong></td><td>${DOMUtils.escapeHtml(plugin.id)}</td></tr>
                        <tr><td><strong>Name:</strong></td><td>${DOMUtils.escapeHtml(plugin.name)}</td></tr>
                        <tr><td><strong>Version:</strong></td><td>${DOMUtils.escapeHtml(plugin.version || 'Unknown')}</td></tr>
                        <tr><td><strong>Status:</strong></td><td>${this.getStatusBadge(plugin.status)}</td></tr>
                        <tr><td><strong>Port:</strong></td><td>${plugin.mcp_port || 'Not assigned'}</td></tr>
                        <tr><td><strong>Start Attempts:</strong></td><td>${plugin.startAttempts}/${plugin.maxStartAttempts}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Permissions</h6>
                    <div class="permissions-list">
                        ${plugin.permissions ? plugin.permissions.map(perm => 
                            `<span class="badge bg-secondary me-1">${DOMUtils.escapeHtml(perm)}</span>`
                        ).join('') : '<em>No permissions required</em>'}
                    </div>
                </div>
            </div>
            
            ${plugin.description ? `
                <div class="mt-3">
                    <h6>Description</h6>
                    <p>${DOMUtils.escapeHtml(plugin.description)}</p>
                </div>
            ` : ''}
            
            ${errorHistory.length > 0 ? `
                <div class="mt-3">
                    <h6>Recent Error History</h6>
                    <div class="error-history">
                        ${errorHistory.map(error => `
                            <div class="alert alert-warning py-2">
                                <small class="text-muted">${DOMUtils.formatTimestamp(error.timestamp)}</small><br>
                                <strong>${error.action}:</strong> ${DOMUtils.escapeHtml(error.error)}
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;
    }

    /**
     * Clear plugin errors
     */
    clearPluginErrors(pluginId) {
        const plugin = this.plugins.get(pluginId);
        if (!plugin) return;
        
        plugin.errorHistory = [];
        plugin.last_error = null;
        plugin.startAttempts = 0;
        
        if (plugin.status === 'failed') {
            plugin.status = 'stopped';
        }
        
        this.updatePluginInUI(plugin);
        this.uiManager.showStatus(`Errors cleared for ${plugin.name}`, 'success');
    }

    /**
     * Update plugin statistics
     */
    updatePluginStats() {
        const plugins = Array.from(this.plugins.values());
        
        this.pluginStats = {
            total: plugins.length,
            active: plugins.filter(p => p.status === 'running').length,
            failed: plugins.filter(p => p.status === 'failed' || p.status === 'error').length,
            stopped: plugins.filter(p => p.status === 'stopped').length
        };
        
        this.displayPluginStats();
    }

    /**
     * Display plugin statistics
     */
    displayPluginStats() {
        const statsContainer = DOMUtils.getElementById('plugin-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="row text-center">
                    <div class="col-3">
                        <div class="stat-item">
                            <div class="stat-value text-primary">${this.pluginStats.total}</div>
                            <div class="stat-label">Total</div>
                        </div>
                    </div>
                    <div class="col-3">
                        <div class="stat-item">
                            <div class="stat-value text-success">${this.pluginStats.active}</div>
                            <div class="stat-label">Active</div>
                        </div>
                    </div>
                    <div class="col-3">
                        <div class="stat-item">
                            <div class="stat-value text-secondary">${this.pluginStats.stopped}</div>
                            <div class="stat-label">Stopped</div>
                        </div>
                    </div>
                    <div class="col-3">
                        <div class="stat-item">
                            <div class="stat-value text-danger">${this.pluginStats.failed}</div>
                            <div class="stat-label">Failed</div>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Display plugin error
     */
    displayPluginError(errorMessage) {
        const pluginList = DOMUtils.getElementById('plugin-list');
        if (pluginList) {
            DOMUtils.showError(pluginList, `Failed to load plugins: ${errorMessage}`, true);
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Auto-refresh toggle
        const autoRefreshBtn = DOMUtils.getElementById('plugin-auto-refresh');
        if (autoRefreshBtn) {
            autoRefreshBtn.addEventListener('click', () => this.toggleAutoRefresh());
        }
        
        // Refresh button
        const refreshBtn = DOMUtils.getElementById('plugin-refresh');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadPlugins());
        }
        
        // Start all button
        const startAllBtn = DOMUtils.getElementById('plugin-start-all');
        if (startAllBtn) {
            startAllBtn.addEventListener('click', () => this.startAllPlugins());
        }
        
        // Stop all button
        const stopAllBtn = DOMUtils.getElementById('plugin-stop-all');
        if (stopAllBtn) {
            stopAllBtn.addEventListener('click', () => this.stopAllPlugins());
        }
    }

    /**
     * Attach event listeners to plugin cards
     */
    attachPluginEventListeners() {
        // This is handled by onclick attributes in the HTML for simplicity
        // In a more complex setup, you might want to use event delegation
    }

    /**
     * Toggle auto-refresh
     */
    toggleAutoRefresh() {
        this.autoRefreshEnabled = !this.autoRefreshEnabled;
        
        if (this.autoRefreshEnabled) {
            this.refreshInterval = setInterval(() => this.loadPlugins(), 10000); // Every 10 seconds
            this.uiManager.showStatus('Plugin auto-refresh enabled', 'success');
        } else {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.refreshInterval = null;
            }
            this.uiManager.showStatus('Plugin auto-refresh disabled', 'info');
        }
        
        this.updateAutoRefreshUI();
    }

    /**
     * Update auto-refresh UI
     */
    updateAutoRefreshUI() {
        const autoRefreshBtn = DOMUtils.getElementById('plugin-auto-refresh');
        if (autoRefreshBtn) {
            autoRefreshBtn.textContent = this.autoRefreshEnabled ? 'Disable Auto-refresh' : 'Enable Auto-refresh';
            autoRefreshBtn.className = this.autoRefreshEnabled ? 'btn btn-secondary' : 'btn btn-outline-primary';
        }
    }

    /**
     * Start all stopped plugins
     */
    async startAllPlugins() {
        const stoppedPlugins = Array.from(this.plugins.values()).filter(p => 
            p.status === 'stopped' && p.startAttempts < p.maxStartAttempts
        );
        
        if (stoppedPlugins.length === 0) {
            this.uiManager.showStatus('No plugins available to start', 'info');
            return;
        }
        
        const operations = stoppedPlugins.map(plugin => ({
            id: `start-plugin-${plugin.id}`,
            name: `Start ${plugin.name}`,
            operation: () => this.startPlugin(plugin.id)
        }));
        
        await this.asyncOperationManager.executeBatch(operations, {
            parallel: false, // Start sequentially to avoid port conflicts
            continueOnError: true,
            showProgress: true
        });
    }

    /**
     * Stop all running plugins
     */
    async stopAllPlugins() {
        const runningPlugins = Array.from(this.plugins.values()).filter(p => p.status === 'running');
        
        if (runningPlugins.length === 0) {
            this.uiManager.showStatus('No plugins are currently running', 'info');
            return;
        }
        
        const operations = runningPlugins.map(plugin => ({
            id: `stop-plugin-${plugin.id}`,
            name: `Stop ${plugin.name}`,
            operation: () => this.stopPlugin(plugin.id)
        }));
        
        await this.asyncOperationManager.executeBatch(operations, {
            parallel: true, // Can stop in parallel
            continueOnError: true,
            showProgress: true
        });
    }

    /**
     * Get status icon
     */
    getStatusIcon(statusType) {
        const icons = {
            'success': 'check-circle',
            'secondary': 'stop-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle'
        };
        return icons[statusType] || 'info-circle';
    }

    /**
     * Cleanup
     */
    cleanup() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        this.plugins.clear();
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PluginManager;
}

// Make class available globally
window.PluginManager = PluginManager;