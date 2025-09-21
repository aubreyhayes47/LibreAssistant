// Main JS for LibreAssistant
// Handles model management (legacy), plugin/MCP integration, chat, and UI logic

// Navigation and routing functionality
class LibreAssistantApp {
    constructor() {
        this.currentView = 'models';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupMobileMenu();
        this.showView(this.currentView);
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

        // Update current view
        this.currentView = viewName;

        // Update browser history
        if (updateHistory) {
            const state = { view: viewName };
            const title = this.getViewTitle(viewName);
            history.pushState(state, title, `#${viewName}`);
            document.title = `${title} - LibreAssistant`;
        }

        // Trigger view-specific initialization if needed
        this.initializeView(viewName);
    }

    updateActiveNav(viewName) {
        // Remove active class from all nav links
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
        });

        // Add active class to current nav link
        const activeLink = document.querySelector(`[data-view="${viewName}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    }

    updateURL(viewName) {
        window.location.hash = viewName;
    }

    closeMobileSidebar() {
        if (window.innerWidth <= 768) {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.remove('open');
        }
    }

    isValidView(viewName) {
        const validViews = ['models', 'server', 'requests', 'catalogue', 'settings', 'about'];
        return validViews.includes(viewName);
    }

    getViewTitle(viewName) {
        const titles = {
            'models': 'Models',
            'server': 'Server',
            'requests': 'Requests',
            'catalogue': 'Plugin Catalogue',

            'settings': 'Settings',
            'about': 'About'
        };
        return titles[viewName] || 'LibreAssistant';
    }

    initializeView(viewName) {
        // This method can be extended to initialize specific functionality
        // for each view when it becomes active
        switch (viewName) {
            case 'models':
                this.initModelsView();
                break;
            case 'server':
                this.initServerView();
                break;
            case 'requests':
                this.initRequestsView();
                break;
            case 'catalogue':
                this.initCatalogueView();
                break;
            case 'settings':
                this.initSettingsView();
                break;
            case 'about':
                this.initAboutView();
                break;
        }
    }

    initModelsView() {
        // Initialize models view functionality
        console.log('Models view initialized');
        
        // Set up model management
        this.setupModelsManagement();
        
        // Load models from the server
        this.loadModels();
    }

    initServerView() {
        // Initialize server view functionality
        console.log('Server view initialized');        
        // Initialize monitoring functionality
        this.initServerMonitoring();

    }

    initRequestsView() {
        // Initialize requests view functionality
        console.log('Requests view initialized');
        
        // Setup plugin pills functionality
        this.setupPluginPills();
        this.setupAutoComplete();
        this.setupRequestSubmission();
        this.loadRequestModels();
        
        // Setup new schema controls
        this.setupSchemaControls();
        this.setupSystemInstructions();
    }

    initCatalogueView() {
        // Initialize plugin catalogue view functionality  
        console.log('Plugin catalogue view initialized');
        
        // Setup plugin catalogue functionality
        this.setupPluginCatalogue();
    }

    initSettingsView() {
        // Initialize settings view functionality
        console.log('Settings view initialized');
        
        // Load current settings into the form
        if (window.settingsManager) {
            window.settingsManager.loadSettingsIntoForm();
        }
    }

    initAboutView() {
        // Initialize about view functionality
        console.log('About view initialized');
        // TODO: Load version info and other details
    }

    // Initialize server monitoring functionality
    initServerMonitoring() {
        // Set up server monitoring components
        this.setupServerMonitoring();
        this.loadRealTimeData();
        this.setupRealTimeUpdates();
    }

    // Set up server monitoring event handlers and state
    setupServerMonitoring() {
        // Initialize global monitoring state if not already set
        if (!window.monitoringState) {
            window.monitoringState = {
                autoRefreshInterval: null,
                errorFilter: 'all',
                logs: [],
                errors: [],
                lastLogUpdate: null,
                lastErrorUpdate: null
            };
        }
    }

    // Load real-time data from server
    async loadRealTimeData() {
        await Promise.all([
            this.fetchServerLogs(),
            this.fetchServerErrors()
        ]);
    }

    // Fetch server logs from API
    async fetchServerLogs() {
        try {
            const backendUrl = 'http://localhost:5000'; // Use Flask server
            const response = await fetch(`${backendUrl}/api/server/logs`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                window.monitoringState.logs = data.logs || [];
                window.monitoringState.lastLogUpdate = new Date().toISOString();
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

    // Fetch server errors from API
    async fetchServerErrors() {
        try {
            const backendUrl = 'http://localhost:5000'; // Use Flask server
            const response = await fetch(`${backendUrl}/api/server/errors`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                window.monitoringState.errors = data.errors || [];
                window.monitoringState.lastErrorUpdate = new Date().toISOString();
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

    // Display error when logs can't be loaded
    displayLogsError(errorMessage) {
        const logsContainer = document.getElementById('serverLogs');
        if (!logsContainer) return;

        logsContainer.innerHTML = `
            <div class="log-entry error">
                <span class="timestamp">[${new Date().toISOString().replace('T', ' ').substring(0, 19)}]</span>
                <span class="level">ERROR</span>
                <span class="message">Failed to load server logs: ${errorMessage}</span>
            </div>
        `;
    }

    // Display error when errors can't be loaded
    displayErrorsError(errorMessage) {
        const errorsContainer = document.getElementById('serverErrors');
        if (!errorsContainer) return;

        errorsContainer.innerHTML = `
            <div class="error-entry warning">
                <div class="error-header">
                    <span class="timestamp">[${new Date().toISOString().replace('T', ' ').substring(0, 19)}]</span>
                    <span class="level">WARNING</span>
                    <span class="title">Monitoring System Error</span>
                </div>
                <div class="error-details">
                    <p><strong>Error:</strong> Failed to load server errors: ${errorMessage}</p>
                    <p><strong>Suggestion:</strong> Check that the backend server is running and accessible</p>
                </div>
            </div>
        `;
    }

    // Display logs in the UI
    displayLogs() {
        const logsContainer = document.getElementById('serverLogs');
        if (!logsContainer) return;

        logsContainer.innerHTML = '';
        
        if (!window.monitoringState.logs || window.monitoringState.logs.length === 0) {
            logsContainer.innerHTML = '<div style="text-align: center; color: #a0aec0; padding: 40px;">No logs available</div>';
            return;
        }
        
        window.monitoringState.logs.forEach(log => {
            const logEntry = this.createLogEntry(log);
            logsContainer.appendChild(logEntry);
        });
        
        logsContainer.scrollTop = 0;
    }

    // Create a log entry element
    createLogEntry(log) {
        const entry = document.createElement('div');
        entry.className = `log-entry ${log.level.toLowerCase()}`;
        
        const timestamp = new Date(log.timestamp);
        const formattedTime = timestamp.toISOString().replace('T', ' ').substring(0, 19);
        
        entry.innerHTML = `
            <span class="timestamp">[${formattedTime}]</span>
            <span class="level">${log.level}</span>
            <span class="message">${log.message}</span>
        `;
        
        return entry;
    }

    // Display errors in the UI
    displayErrors() {
        const errorContainer = document.getElementById('errorList');
        if (!errorContainer) return;

        errorContainer.innerHTML = '';
        
        const filteredErrors = window.monitoringState.errorFilter === 'all' 
            ? window.monitoringState.errors 
            : window.monitoringState.errors.filter(error => error.level === window.monitoringState.errorFilter);
        
        if (filteredErrors.length === 0) {
            errorContainer.innerHTML = '<div style="text-align: center; color: #a0aec0; padding: 40px;">No errors matching the current filter</div>';
            return;
        }
        
        filteredErrors.forEach(error => {
            const errorEntry = this.createErrorEntry(error);
            errorContainer.appendChild(errorEntry);
        });
    }

    // Create an error entry element
    createErrorEntry(error) {
        const entry = document.createElement('div');
        entry.className = `error-entry ${error.level}`;
        
        const timestamp = new Date(error.timestamp);
        const formattedTime = timestamp.toISOString().replace('T', ' ').substring(0, 19);
        
        entry.innerHTML = `
            <div class="error-header">
                <span class="timestamp">[${formattedTime}]</span>
                <span class="level ${error.level}">${error.level.toUpperCase()}</span>
                <span class="error-title">${error.title}</span>
            </div>
            <div class="error-details">
                <p><strong>Error:</strong> ${error.error}</p>
                <p><strong>Stack:</strong> ${error.stack}</p>
                <p><strong>Suggestion:</strong> ${error.suggestion}</p>
            </div>
        `;
        
        return entry;
    }

    // Set up real-time updates
    setupRealTimeUpdates() {
        // Refresh data every 30 seconds
        setInterval(async () => {
            const serverView = document.getElementById('server-view');
            const autoRefreshEnabled = document.getElementById('autoRefresh')?.checked;
            
            // Only refresh automatically if we're on the server tab and auto-refresh is enabled
            if (serverView?.classList.contains('active') && autoRefreshEnabled) {
                await this.loadRealTimeData();
            }
        }, 30000);
        
        // Also check for updates every 5 minutes regardless of view
        setInterval(async () => {
            await this.loadRealTimeData();
        }, 300000);
    }

    // Model Management Methods
    setupModelsManagement() {
        // Set up event listeners for model management
        const refreshBtn = document.getElementById('refresh-models-btn');
        const downloadBtn = document.getElementById('download-model-btn');
        const modal = document.getElementById('download-modal');
        const closeModal = modal?.querySelector('.close');
        const cancelBtn = document.getElementById('cancel-download-btn');
        const confirmBtn = document.getElementById('confirm-download-btn');

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadModels());
        }

        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.showDownloadModal());
        }

        if (closeModal) {
            closeModal.addEventListener('click', () => this.hideDownloadModal());
        }

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideDownloadModal());
        }

        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => this.downloadModel());
        }

        // Close modal when clicking outside
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideDownloadModal();
                }
            });
        }
    }

    async loadModels() {
        const modelList = document.getElementById('model-list');
        const backendUrl = 'http://localhost:5000'; // Use Flask backend
        const serverUrl = window.settingsManager ? window.settingsManager.getSetting('serverUrl') : 'http://localhost:11434';
        
        if (!modelList) return;

        // Show loading state
        modelList.innerHTML = `
            <div class="model-item loading">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading models...</span>
            </div>
        `;

        try {
            const timeout = window.settingsManager ? window.settingsManager.getSetting('apiTimeout') : 180;
            const response = await fetch(`${backendUrl}/api/models?server_url=${encodeURIComponent(serverUrl)}&timeout=${timeout}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                this.displayModels(data.models || []);
                this.showStatus('Models loaded successfully', 'success');
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Error loading models:', error);
            this.displayModelsError(error.message);
            this.showStatus('Failed to load models. Make sure Ollama is running.', 'error');
        }
    }

    displayModels(models) {
        const modelList = document.getElementById('model-list');
        if (!modelList) return;

        if (models.length === 0) {
            modelList.innerHTML = `
                <div class="model-item">
                    <div class="model-info">
                        <div class="model-name">No models found</div>
                        <div class="model-details">
                            <span>No models are currently installed. Use the Download Model button to install one.</span>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        const favoriteModel = window.settingsManager ? window.settingsManager.getFavoriteModel() : null;

        modelList.innerHTML = models.map(model => {
            const isFavorite = model.name === favoriteModel;
            return `
                <div class="model-item ${isFavorite ? 'favorite-model' : ''}">
                    <div class="model-info">
                        <div class="model-name">
                            ${model.name}
                            ${isFavorite ? '<i class="fas fa-star favorite-star" title="Favorite Model"></i>' : ''}
                        </div>
                        <div class="model-details">
                            <span><i class="fas fa-hdd"></i> ${this.formatBytes(model.size)}</span>
                            <span><i class="fas fa-calendar"></i> ${this.formatDate(model.modified_at)}</span>
                            <span><i class="fas fa-tag"></i> ${model.details?.family || 'Unknown'}</span>
                        </div>
                    </div>
                    <div class="model-actions">
                        <button class="btn btn-secondary btn-small" onclick="window.ollamaApp.showModelInfo('${model.name}')">
                            <i class="fas fa-info-circle"></i> Info
                        </button>
                        ${!isFavorite ? 
                            `<button class="btn btn-success btn-small" onclick="window.ollamaApp.setFavoriteModel('${model.name}')">
                                <i class="fas fa-star"></i> Set as Favorite
                            </button>` : 
                            `<button class="btn btn-warning btn-small" onclick="window.ollamaApp.unsetFavoriteModel()">
                                <i class="fas fa-star-half-alt"></i> Unset Favorite
                            </button>`
                        }
                        <button class="btn btn-danger btn-small" onclick="window.ollamaApp.deleteModel('${model.name}')">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    displayModelsError(errorMessage) {
        const modelList = document.getElementById('model-list');
        if (!modelList) return;

        modelList.innerHTML = `
            <div class="model-item">
                <div class="model-info">
                    <div class="model-name">Error Loading Models</div>
                    <div class="model-details">
                        <span>${errorMessage}</span>
                    </div>
                </div>
                <div class="model-actions">
                    <button class="btn btn-primary btn-small" onclick="window.ollamaApp.loadModels()">
                        <i class="fas fa-sync-alt"></i> Retry
                    </button>
                </div>
            </div>
        `;
    }

    showDownloadModal() {
        const modal = document.getElementById('download-modal');
        const input = document.getElementById('model-name-input');
        if (modal) {
            modal.style.display = 'block';
            if (input) {
                input.value = '';
                input.focus();
            }
        }
    }

    hideDownloadModal() {
        const modal = document.getElementById('download-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    async downloadModel() {
        const input = document.getElementById('model-name-input');
        const modelName = input?.value.trim();
        
        if (!modelName) {
            alert('Please enter a model name');
            return;
        }

        this.hideDownloadModal();
        this.showStatus(`Downloading model "${modelName}"...`, 'info');

        const backendUrl = 'http://localhost:5000'; // Use Flask backend
        const serverUrl = window.settingsManager ? window.settingsManager.getSetting('serverUrl') : 'http://localhost:11434';
        const timeout = window.settingsManager ? window.settingsManager.getSetting('apiTimeout') : 180;

        try {
            const response = await fetch(`${backendUrl}/api/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    model_name: modelName,
                    server_url: serverUrl,
                    timeout: timeout
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.success) {
                this.showStatus(`Model "${modelName}" downloaded successfully!`, 'success');
                // Refresh the models list
                setTimeout(() => this.loadModels(), 1000);
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Error downloading model:', error);
            this.showStatus(`Failed to download model "${modelName}": ${error.message}`, 'error');
        }
    }

    async deleteModel(modelName) {
        if (!confirm(`Are you sure you want to delete the model "${modelName}"?\n\nThis action cannot be undone.`)) {
            return;
        }

        this.showStatus(`Deleting model "${modelName}"...`, 'info');

        const backendUrl = 'http://localhost:5000'; // Use Flask backend
        const serverUrl = window.settingsManager ? window.settingsManager.getSetting('serverUrl') : 'http://localhost:11434';
        const timeout = window.settingsManager ? window.settingsManager.getSetting('apiTimeout') : 180;

        try {
            const response = await fetch(`${backendUrl}/api/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    model_name: modelName,
                    server_url: serverUrl,
                    timeout: timeout
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.success) {
                // Check if the deleted model was the favorite
                const favoriteModel = window.settingsManager ? window.settingsManager.getFavoriteModel() : null;
                if (favoriteModel === modelName) {
                    window.settingsManager.setFavoriteModel(null);
                    this.showStatus(`Model "${modelName}" deleted successfully! (It was your favorite model, so favorite has been cleared)`, 'success');
                } else {
                    this.showStatus(`Model "${modelName}" deleted successfully!`, 'success');
                }
                // Refresh the models list
                this.loadModels();
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Error deleting model:', error);
            this.showStatus(`Failed to delete model "${modelName}": ${error.message}`, 'error');
        }
    }

    async showModelInfo(modelName) {
        const backendUrl = 'http://localhost:5000'; // Use Flask backend
        const serverUrl = window.settingsManager ? window.settingsManager.getSetting('serverUrl') : 'http://localhost:11434';
        const timeout = window.settingsManager ? window.settingsManager.getSetting('apiTimeout') : 180;

        try {
            const response = await fetch(`${backendUrl}/api/info/${modelName}?server_url=${encodeURIComponent(serverUrl)}&timeout=${timeout}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.success) {
                const info = JSON.stringify(data.info, null, 2);
                alert(`Model Information for "${modelName}":\n\n${info}`);
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Error getting model info:', error);
            alert(`Failed to get model information: ${error.message}`);
        }
    }

    showStatus(message, type) {
        const statusDiv = document.getElementById('model-status');
        const messageDiv = document.getElementById('status-message');
        
        if (statusDiv && messageDiv) {
            messageDiv.textContent = message;
            statusDiv.className = `model-status ${type}`;
            statusDiv.style.display = 'block';
            
            // Auto-hide success messages after 5 seconds
            if (type === 'success') {
                setTimeout(() => {
                    statusDiv.style.display = 'none';
                }, 5000);
            }
        }
    }

    setFavoriteModel(modelName) {
        if (window.settingsManager) {
            if (window.settingsManager.setFavoriteModel(modelName)) {
                this.showStatus(`"${modelName}" set as favorite model`, 'success');
                // Refresh the models display to show the favorite indicator
                this.loadModels();
            } else {
                this.showStatus('Failed to set favorite model', 'error');
            }
        }
    }

    unsetFavoriteModel() {
        if (window.settingsManager) {
            if (window.settingsManager.setFavoriteModel(null)) {
                this.showStatus('Favorite model unset', 'success');
                // Refresh the models display to remove the favorite indicator
                this.loadModels();
            } else {
                this.showStatus('Failed to unset favorite model', 'error');
            }
        }
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        } catch {
            return 'Unknown';
        }
    }

    // Request Models Management Methods
    async loadRequestModels() {
        const modelSelect = document.getElementById('request-model-select');
        const backendUrl = 'http://localhost:5000'; // Use Flask backend
        const serverUrl = window.settingsManager ? window.settingsManager.getSetting('serverUrl') : 'http://localhost:11434';
        
        if (!modelSelect) return;

        // Show loading state
        modelSelect.innerHTML = '<option value="">Loading models...</option>';
        modelSelect.disabled = true;

        try {
            const timeout = window.settingsManager ? window.settingsManager.getSetting('apiTimeout') : 180;
            const response = await fetch(`${backendUrl}/api/models?server_url=${encodeURIComponent(serverUrl)}&timeout=${timeout}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                this.displayRequestModels(data.models || []);
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Error loading request models:', error);
            modelSelect.innerHTML = '<option value="">Error loading models</option>';
        } finally {
            modelSelect.disabled = false;
        }
    }

    displayRequestModels(models) {
        const modelSelect = document.getElementById('request-model-select');
        if (!modelSelect) return;

        modelSelect.innerHTML = '<option value="">Select a model...</option>';
        
        if (models.length === 0) {
            modelSelect.innerHTML = '<option value="">No models found</option>';
            return;
        }

        const favoriteModel = window.settingsManager ? window.settingsManager.getFavoriteModel() : null;

        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            option.textContent = model.name + (model.name === favoriteModel ? ' ⭐' : '');
            modelSelect.appendChild(option);
        });

        // Auto-select favorite model if it exists
        if (favoriteModel) {
            modelSelect.value = favoriteModel;
        }
    }

    // Chat Management Methods
    setupChatFunctionality() {
        // Set up event listeners for chat
        const modelSelect = document.getElementById('chat-model-select');
        const refreshBtn = document.getElementById('refresh-chat-models');
        const sendBtn = document.getElementById('send-chat-button');
        const clearBtn = document.getElementById('clear-chat-history');
        const promptInput = document.getElementById('chat-prompt-input');
        const closeErrorBtn = document.getElementById('close-chat-error');

        if (modelSelect) {
            modelSelect.addEventListener('change', () => this.onChatModelChange());
        }

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadChatModels());
        }

        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendChatMessage());
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearChatHistory());
        }

        if (promptInput) {
            promptInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });
        }

        if (closeErrorBtn) {
            closeErrorBtn.addEventListener('click', () => this.hideChatError());
        }

        // Initialize chat state
        this.chatHistory = [];
        this.selectedChatModel = '';
        this.isChatLoading = false;
    }

    async loadChatModels() {
        const modelSelect = document.getElementById('chat-model-select');
        const backendUrl = 'http://localhost:5000'; // Use Flask backend
        const serverUrl = window.settingsManager ? window.settingsManager.getSetting('serverUrl') : 'http://localhost:11434';
        
        if (!modelSelect) return;

        // Show loading state
        modelSelect.innerHTML = '<option value="">Loading models...</option>';
        modelSelect.disabled = true;

        try {
            const timeout = window.settingsManager ? window.settingsManager.getSetting('apiTimeout') : 180;
            const response = await fetch(`${backendUrl}/api/models?server_url=${encodeURIComponent(serverUrl)}&timeout=${timeout}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                this.displayChatModels(data.models || []);
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Error loading chat models:', error);
            modelSelect.innerHTML = '<option value="">Error loading models</option>';
            this.showChatError('Failed to load models. Make sure Ollama is running.');
        } finally {
            modelSelect.disabled = false;
        }
    }

    displayChatModels(models) {
        const modelSelect = document.getElementById('chat-model-select');
        if (!modelSelect) return;

        modelSelect.innerHTML = '<option value="">Select a model...</option>';
        
        if (models.length === 0) {
            modelSelect.innerHTML = '<option value="">No models found</option>';
            return;
        }

        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            option.textContent = model.name;
            modelSelect.appendChild(option);
        });
    }

    onChatModelChange() {
        const modelSelect = document.getElementById('chat-model-select');
        const promptInput = document.getElementById('chat-prompt-input');
        const sendBtn = document.getElementById('send-chat-button');
        
        this.selectedChatModel = modelSelect?.value || '';
        
        if (promptInput && sendBtn) {
            const hasModel = this.selectedChatModel !== '';
            promptInput.disabled = !hasModel;
            sendBtn.disabled = !hasModel;
            
            if (hasModel) {
                promptInput.placeholder = `Type your message for ${this.selectedChatModel}...`;
            } else {
                promptInput.placeholder = 'Select a model first...';
            }
        }
    }

    async sendChatMessage() {
        const promptInput = document.getElementById('chat-prompt-input');
        const prompt = promptInput?.value.trim();
        
        if (!prompt || !this.selectedChatModel || this.isChatLoading) {
            return;
        }

        // Clear input and disable while processing
        promptInput.value = '';
        this.setButtonsDisabled(true);
        this.isChatLoading = true;

        // Add user message to chat and update history
        this.addChatMessage('user', prompt);

        // Add typing indicator
        const typingId = this.addTypingIndicator();

        const backendUrl = 'http://localhost:5000'; // Use Flask backend

        try {
            // Send the full chat history to the backend
            const timeout = window.settingsManager ? window.settingsManager.getSetting('apiTimeout') : 180;
            const pluginRetries = window.settingsManager ? window.settingsManager.getSetting('pluginRetries') : 2;
            const response = await fetch(`${backendUrl}/api/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: this.selectedChatModel,
                    prompt: prompt,
                    stream: false,
                    history: this.chatHistory, // send the full conversation history
                    timeout: timeout,
                    pluginRetries: pluginRetries
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Remove typing indicator
            this.removeTypingIndicator(typingId);

            // Add assistant response
            this.addChatMessage('assistant', data.response || 'No response received');

        } catch (error) {
            console.error('Error sending chat message:', error);
            this.removeTypingIndicator(typingId);
            this.addChatMessage('error', `Error: ${error.message}`);
            this.showChatError(`Failed to send message: ${error.message}`);
        } finally {
            this.isChatLoading = false;
            this.setButtonsDisabled(false);
        }
    }

    addChatMessage(role, content) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        // Remove welcome message if it exists
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        const messageElement = document.createElement('div');
        messageElement.className = `message ${role}`;
        
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        
        // Use markdown rendering for assistant responses, plain text for user messages
        if (role === 'assistant' && window.MarkdownUtils) {
            contentElement.innerHTML = window.MarkdownUtils.renderChatContent(content);
        } else {
            contentElement.textContent = content;
        }
        
        messageElement.appendChild(contentElement);
        messagesContainer.appendChild(messageElement);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Store in history
        this.chatHistory.push({ role, content });
    }

    addTypingIndicator() {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return null;

        const typingElement = document.createElement('div');
        const typingId = 'typing-' + Date.now();
        typingElement.id = typingId;
        typingElement.className = 'message assistant typing-indicator';
        typingElement.innerHTML = `
            <div class="message-content">
                <span>Thinking</span>
                <div class="dots">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(typingElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return typingId;
    }

    removeTypingIndicator(typingId) {
        if (typingId) {
            const typingElement = document.getElementById(typingId);
            if (typingElement) {
                typingElement.remove();
            }
        }
    }

    clearChatHistory() {
        if (this.chatHistory.length === 0) return;
        
        if (!confirm('Are you sure you want to clear the chat history?')) {
            return;
        }

        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <p>Welcome to the Ollama Chat Console! Select a model above and start chatting.</p>
                </div>
            `;
        }
        
        this.chatHistory = [];
    }

    setButtonsDisabled(disabled) {
        const sendBtn = document.getElementById('send-chat-button');
        const promptInput = document.getElementById('chat-prompt-input');
        
        if (sendBtn) {
            sendBtn.disabled = disabled;
        }
        
        if (promptInput) {
            promptInput.disabled = disabled || !this.selectedChatModel;
        }
    }

    showChatError(message) {
        const errorContainer = document.getElementById('chat-error-container');
        const errorMessage = document.getElementById('chat-error-message');
        
        if (errorContainer && errorMessage) {
            errorMessage.textContent = message;
            errorContainer.style.display = 'flex';
        }
    }

    hideChatError() {
        const errorContainer = document.getElementById('chat-error-container');
        if (errorContainer) {
            errorContainer.style.display = 'none';
        }
    }

    // Plugin pills functionality for requests view
    setupPluginPills() {
        const refreshButton = document.getElementById('refresh-plugins');
        const pluginStatus = document.getElementById('plugin-status');
        
        const loadPlugins = () => {
            fetch('/api/plugins/list')
                .then(res => res.json())
                .then(data => {
                    const pillsContainer = document.getElementById('plugin-pills');
                    if (!pillsContainer) return;
                    
                    if (data.success && data.plugins && data.plugins.length > 0) {
                        pillsContainer.innerHTML = '';
                        const runningPlugins = data.plugins.filter(p => p.running);
                        
                        runningPlugins.forEach(plugin => {
                            const pill = document.createElement('span');
                            pill.className = 'plugin-pill';
                            pill.innerHTML = `<i class="fas fa-plug"></i> ${plugin.name}`;
                            pill.title = plugin.description;
                            pill.onclick = function() {
                                this.showPluginInfo(plugin);
                            }.bind(this);
                            pillsContainer.appendChild(pill);
                        });
                        
                        if (pluginStatus) {
                            pluginStatus.textContent = `${runningPlugins.length} active plugin(s)`;
                        }
                    } else {
                        pillsContainer.innerHTML = '<span style="color: #7f8c8d;">No active plugins</span>';
                        if (pluginStatus) {
                            pluginStatus.textContent = 'No plugins running';
                        }
                    }
                })
                .catch(err => {
                    console.error('Could not load plugin pills:', err);
                    const pillsContainer = document.getElementById('plugin-pills');
                    if (pillsContainer) {
                        pillsContainer.innerHTML = '<span style="color: #e74c3c;">Error loading plugins</span>';
                    }
                    if (pluginStatus) {
                        pluginStatus.textContent = 'Error loading plugins';
                    }
                });
        };
        
        // Setup refresh button
        if (refreshButton) {
            refreshButton.addEventListener('click', loadPlugins);
        }
        
        // Load plugins initially
        loadPlugins();
    }
    
    showPluginInfo(plugin) {
        alert(`Plugin: ${plugin.name}\nID: ${plugin.id}\nDescription: ${plugin.description}\nStatus: ${plugin.status}\nVersion: ${plugin.version}`);
    }

    // Setup schema controls functionality
    setupSchemaControls() {
        const viewSchemaButton = document.getElementById('view-schema');
        const schemaModal = document.getElementById('schema-modal');
        const schemaContent = document.getElementById('schema-content');
        const validateButton = document.getElementById('validate-response');
        const downloadButton = document.getElementById('download-schema');
        
        if (!viewSchemaButton) return;
        
        viewSchemaButton.addEventListener('click', () => {
            schemaContent.textContent = 'Loading schema...';
            schemaModal.style.display = 'block';
            
            fetch('/api/llm/schema')
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        schemaContent.textContent = JSON.stringify(data.schema, null, 2);
                    } else {
                        schemaContent.textContent = 'Error loading schema: ' + (data.error || 'Unknown error');
                    }
                })
                .catch(err => {
                    schemaContent.textContent = 'Network error: ' + err.message;
                });
        });
        
        if (validateButton) {
            validateButton.addEventListener('click', () => {
                // Test validation with a sample response
                const sampleResponse = {
                    "action": "message",
                    "content": {
                        "text": "This is a test message",
                        "markdown": false
                    }
                };
                
                fetch('/api/llm/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ response: sampleResponse })
                })
                .then(res => res.json())
                .then(data => {
                    alert(data.success && data.valid ? 'Sample validation passed!' : 'Validation failed: ' + (data.error || 'Unknown error'));
                })
                .catch(err => {
                    alert('Validation test failed: ' + err.message);
                });
            });
        }
        
        if (downloadButton) {
            downloadButton.addEventListener('click', () => {
                fetch('/api/llm/schema')
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            const blob = new Blob([JSON.stringify(data.schema, null, 2)], { type: 'application/json' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'llm-response-schema.json';
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            URL.revokeObjectURL(url);
                        }
                    })
                    .catch(err => {
                        alert('Failed to download schema: ' + err.message);
                    });
            });
        }
    }

    // Setup system instructions functionality
    setupSystemInstructions() {
        const viewInstructionsButton = document.getElementById('view-system-instructions');
        const instructionsModal = document.getElementById('instructions-modal');
        const instructionsContent = document.getElementById('instructions-content');
        const refreshInstructionsButton = document.getElementById('refresh-instructions');
        const pluginCountSpan = document.getElementById('plugin-count');
        
        if (!viewInstructionsButton) return;
        
        const loadSystemInstructions = () => {
            instructionsContent.textContent = 'Loading system instructions...';
            
            fetch('/api/llm/system_instructions')
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        instructionsContent.textContent = data.instructions;
                        if (pluginCountSpan) {
                            pluginCountSpan.textContent = `Available plugins: ${data.plugins ? data.plugins.length : 0}`;
                        }
                    } else {
                        instructionsContent.textContent = 'Error loading instructions: ' + (data.error || 'Unknown error');
                    }
                })
                .catch(err => {
                    instructionsContent.textContent = 'Network error: ' + err.message;
                });
        };
        
        viewInstructionsButton.addEventListener('click', () => {
            instructionsModal.style.display = 'block';
            loadSystemInstructions();
        });
        
        if (refreshInstructionsButton) {
            refreshInstructionsButton.addEventListener('click', loadSystemInstructions);
        }
    }

    // Setup autocomplete functionality for requests
    setupAutoComplete() {
        const input = document.getElementById('request-input');
        const list = document.getElementById('autocomplete-list');
        
        if (!input || !list) return;
        
        const suggestions = [
            'Search for recent AI research',
            'Find legal cases about privacy',
            'What are the latest tech trends?',
            'Search for court opinions on data protection',
            'Help me find information about...',
            'What is the current status of...'
        ];

        input.addEventListener('input', function() {
            const value = this.value.toLowerCase();
            list.innerHTML = '';
            
            if (value.length > 0) {
                const matches = suggestions.filter(s => s.toLowerCase().includes(value));
                if (matches.length > 0) {
                    matches.forEach(match => {
                        const item = document.createElement('div');
                        item.className = 'autocomplete-item';
                        item.textContent = match;
                        item.onclick = function() {
                            input.value = match;
                            list.style.display = 'none';
                        };
                        list.appendChild(item);
                    });
                    list.style.display = 'block';
                } else {
                    list.style.display = 'none';
                }
            } else {
                list.style.display = 'none';
            }
        });

        // Hide autocomplete when clicking outside
        document.addEventListener('click', function(e) {
            if (!input.contains(e.target) && !list.contains(e.target)) {
                list.style.display = 'none';
            }
        });
    }

    // Setup request submission functionality
    setupRequestSubmission() {
        const input = document.getElementById('request-input');
        const button = document.getElementById('request-submit');
        const responseBox = document.getElementById('response-box');
        const modelSelect = document.getElementById('request-model-select');
        const refreshButton = document.getElementById('refresh-request-models');
        const useSchemaCheckbox = document.getElementById('use-schema');
        
        if (!input || !button || !responseBox) return;

        // Setup refresh models button
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.loadRequestModels());
        }
        
        const submitRequest = () => {
            const query = input.value.trim();
            const selectedModel = modelSelect ? modelSelect.value : '';
            const useSchema = useSchemaCheckbox ? useSchemaCheckbox.checked : true;
            
            if (!query) return;
            
            if (!selectedModel) {
                responseBox.innerHTML = `
                    <div class="error-response">
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>Error:</strong> Please select a model before sending your request.
                    </div>
                `;
                return;
            }
            
            // Show loading state
            responseBox.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    Processing your request with ${selectedModel}...
                </div>
            `;
            
            // Use the /api/generate endpoint with schema support instead of /api/request
            fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: selectedModel,
                    prompt: query,
                    use_schema: useSchema,
                    stream: false
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Extract user-friendly content from the response
                    let displayText = data.response;
                    let responseRawData = null;
                    let pluginInfo = null;
                    
                    // Handle enhanced plugin tracking from refactored prompts
                    if (data.plugins_used && Array.isArray(data.plugins_used)) {
                        pluginInfo = {
                            plugins: data.plugins_used,
                            count: data.plugin_count || data.plugins_used.length
                        };
                    }
                    
                    // If the response looks like JSON, try to parse it for better content
                    if (typeof displayText === 'string' && 
                        (displayText.trim().startsWith('{') || displayText.trim().startsWith('['))) {
                        try {
                            const parsedResponse = JSON.parse(displayText);
                            const extractedContent = this.extractMainContent(parsedResponse);
                            
                            if (extractedContent) {
                                displayText = extractedContent;
                                responseRawData = parsedResponse; // Store raw data for toggle
                            }
                        } catch (e) {
                            // If parsing fails, use the original text
                            console.log('Response parsing failed, using original text:', e);
                        }
                    }
                    
                    // Also check if the raw response data is complex and needs parsing
                    if (!responseRawData && typeof data.response === 'object') {
                        const extractedContent = this.extractMainContent(data.response);
                        if (extractedContent) {
                            displayText = extractedContent;
                            responseRawData = data.response;
                        }
                    }
                    
                    // Prepare plugin display information
                    let pluginDisplay = null;
                    let pluginReason = null;
                    
                    if (pluginInfo && pluginInfo.plugins.length > 0) {
                        if (pluginInfo.plugins.length === 1) {
                            const plugin = pluginInfo.plugins[0];
                            pluginDisplay = plugin.id || plugin;
                            pluginReason = plugin.reason || 'Plugin execution';
                        } else {
                            pluginDisplay = `${pluginInfo.count} plugins`;
                            pluginReason = `Used: ${pluginInfo.plugins.map(p => p.id || p).join(', ')}`;
                        }
                    } else if (data.plugin_used) {
                        // Fallback to legacy plugin info
                        pluginDisplay = data.plugin_used;
                        pluginReason = data.plugin_reason;
                    }
                    
                    this.showResponse({
                        text: displayText,
                        markdown: data.markdown,
                        plugin_used: pluginDisplay,
                        plugin_reason: pluginReason,
                        schema_used: useSchema,
                        schema_error: data.schema_error,
                        warning: data.warning,
                        rawData: responseRawData,
                        pluginInfo: pluginInfo
                    });
                    // Refresh plugin pills to show any newly accessed plugins
                    this.setupPluginPills();
                } else {
                    this.showResponse({error: data.error || 'Request failed'});
                }
            })
            .catch(error => {
                this.showResponse({error: 'Network error: ' + error.message});
            });
            
            input.value = '';
        };
        
        button.addEventListener('click', submitRequest);
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                submitRequest();
            }
        });
    }

    // Enhanced extractMainContent function for robust response parsing
    // Handles nested JSON structures, structured prompts, and various response patterns
    extractMainContent(data) {
        // Handle null/undefined
        if (data == null) return null;
        
        // Handle primitive types (string, number, boolean)
        if (typeof data !== 'object') {
            return String(data);
        }
        
        // Handle arrays - try to extract meaningful content from first elements
        if (Array.isArray(data)) {
            if (data.length === 0) return null;
            
            // For search results or similar arrays
            if (data.length > 0 && typeof data[0] === 'object') {
                return this.formatArrayResults(data);
            }
            
            // For simple arrays, join them
            return data.map(item => this.extractMainContent(item)).filter(Boolean).join('\n');
        }
        
        // Handle improved structured responses from refactored prompts
        const structuredContent = this.extractFromStructuredResponse(data);
        if (structuredContent) return structuredContent;
        
        // Recursive search for common text fields at all depths
        const textContent = this.findTextContentRecursively(data);
        if (textContent) return textContent;
        
        // Handle known patterns (including JSON schema response patterns)
        const knownPattern = this.handleKnownPatterns(data);
        if (knownPattern) return knownPattern;
        
        // For search results, try to extract meaningful content
        if (data.results && Array.isArray(data.results)) {
            return this.formatSearchResults(data.results, data);
        }
        
        // For other structured data, try to create a readable summary
        if (typeof data === 'object' && data !== null) {
            const summary = this.createReadableSummary(data);
            if (summary) return summary;
            
            // If it's a simple object with few fields, create a readable format
            const keys = Object.keys(data);
            if (keys.length <= 5 && keys.length > 0) {
                return keys.map(key => `${key}: ${data[key]}`).join('\n');
            }
        }
        
        // Fallback: return null to indicate we should show raw JSON
        return null;
    }

    // Extract content from structured responses that use section markers
    // This handles responses from the refactored prompt construction
    extractFromStructuredResponse(data) {
        // Check for structured plugin response with section markers
        if (typeof data === 'string' && data.includes('[USER REQUEST]') && data.includes('[PLUGIN OUTPUT]')) {
            // This looks like a structured prompt - extract the meaningful parts
            const sections = this.parseStructuredSections(data);
            if (sections.userRequest && sections.pluginOutput) {
                return `User asked: ${sections.userRequest}\n\nPlugin result: ${sections.pluginOutput}`;
            }
        }
        
        // Check for enhanced plugin tracking data
        if (data.plugins_used && Array.isArray(data.plugins_used) && data.response) {
            let content = data.response;
            if (data.plugins_used.length > 0) {
                content += `\n\nPlugins used: ${data.plugins_used.map(p => p.id || p).join(', ')}`;
            }
            return content;
        }
        
        // Check for plugin result summaries
        if (data.plugin_summary && data.raw_data) {
            return data.plugin_summary;
        }
        
        return null;
    }
    
    // Parse structured sections from prompt responses
    parseStructuredSections(text) {
        const sections = {};
        
        // Extract user request
        const userMatch = text.match(/\[USER REQUEST\]\s*=+\s*(.*?)\s*=+\s*\[/s);
        if (userMatch) {
            sections.userRequest = userMatch[1].trim();
        }
        
        // Extract plugin output summary (before raw data)
        const outputMatch = text.match(/\[PLUGIN OUTPUT\]\s*=+\s*(.*?)\s*---\s*Raw Data/s);
        if (outputMatch) {
            sections.pluginOutput = outputMatch[1].trim();
        }
        
        // Extract error details if present
        const errorMatch = text.match(/\[ERROR DETAILS\]\s*=+\s*(.*?)\s*---\s*Technical Details/s);
        if (errorMatch) {
            sections.errorDetails = errorMatch[1].trim();
        }
        
        return sections;
    }

    // Helper function to recursively search for text content (enhanced for plugin responses)
    findTextContentRecursively(obj, visited = new WeakSet()) {
        // Prevent infinite recursion
        if (visited.has(obj)) return null;
        visited.add(obj);
        
        // Common text field names to search for (in order of preference)
        // Enhanced to include plugin-related fields from refactored prompts
        const textFields = [
            'text', 'content', 'message', 'response', 'description', 'body', 'value',
            'plugin_summary', 'user_message', 'assistant_response', 'summary'
        ];
        
        // First, check direct properties
        for (const field of textFields) {
            if (obj[field] && typeof obj[field] === 'string' && obj[field].trim()) {
                return obj[field].trim();
            }
        }
        
        // Then check nested objects
        for (const key in obj) {
            if (obj.hasOwnProperty(key) && typeof obj[key] === 'object' && obj[key] !== null) {
                if (!Array.isArray(obj[key])) {
                    const nested = this.findTextContentRecursively(obj[key], visited);
                    if (nested) return nested;
                }
            }
        }
        
        return null;
    }

    // Handle known response patterns (enhanced for improved LLM responses)
    handleKnownPatterns(data) {
        // Pattern: { action: 'message', content: { text: ... } } - Standard JSON schema response
        if (data.action === 'message' && data.content && data.content.text) {
            return data.content.text;
        }
        
        // Pattern: { action: 'message', content: 'direct text' }
        if (data.action === 'message' && typeof data.content === 'string') {
            return data.content;
        }
        
        // Pattern: Enhanced plugin response with metadata
        if (data.action === 'message' && data.content && data.plugin_metadata) {
            let response = data.content.text || data.content;
            if (data.plugin_metadata.plugins_used) {
                response += `\n\nPlugins used: ${data.plugin_metadata.plugins_used.join(', ')}`;
            }
            return response;
        }
        
        // Pattern: { type: 'response', data: { content: { text: ... } } }
        if (data.type === 'response' && data.data && data.data.content && data.data.content.text) {
            return data.data.content.text;
        }
        
        // Pattern: plugin response with nested content
        if (data.success && data.data && typeof data.data === 'object') {
            const nested = this.findTextContentRecursively(data.data);
            if (nested) return nested;
        }
        
        // Pattern: Response with plugin tracking information
        if (data.response && data.plugins_used) {
            let content = data.response;
            if (data.plugins_used && data.plugins_used.length > 0) {
                content += `\n\n🔌 Plugins used: ${data.plugins_used.map(p => p.id || p).join(', ')}`;
                if (data.plugin_count) {
                    content += ` (${data.plugin_count} total)`;
                }
            }
            return content;
        }
        
        // Pattern: Error response with helpful context
        if (data.error && data.llm_error_recovery_failed) {
            return `Error: ${data.error}\n\nThe AI assistant attempted to handle this error but was unable to provide a recovery response.`;
        }
        
        return null;
    }

    // Format array results (for search results, etc.)
    formatArrayResults(arr) {
        if (arr.length === 0) return null;
        
        let summary = `Found ${arr.length} results:\n\n`;
        arr.slice(0, 5).forEach((result, index) => {
            summary += `${index + 1}. `;
            
            // Try to get a title/name
            const title = result.title || result.name || result.label || 'Result';
            summary += title + '\n';
            
            // Try to get a description/snippet
            const desc = result.snippet || result.description || result.summary || result.text;
            if (desc) {
                summary += `   ${desc}\n`;
            }
            
            // Try to get a URL/link
            const url = result.url || result.link || result.href;
            if (url) {
                summary += `   ${url}\n`;
            }
            
            summary += '\n';
        });
        
        if (arr.length > 5) {
            summary += `... and ${arr.length - 5} more results\n`;
        }
        
        return summary;
    }

    // Format search results specifically
    formatSearchResults(results, parentData = null) {
        if (!results || results.length === 0) return null;
        
        let summary = '';
        
        // Include parent data context if available
        if (parentData && parentData.query) {
            summary += `Search results for: "${parentData.query}"\n\n`;
        } else {
            summary += `Found ${results.length} results:\n\n`;
        }
        
        results.slice(0, 5).forEach((result, index) => {
            summary += `${index + 1}. ${result.title || result.name || 'Result'}\n`;
            if (result.snippet || result.description) {
                summary += `   ${result.snippet || result.description}\n`;
            }
            if (result.url || result.link) {
                summary += `   ${result.url || result.link}\n`;
            }
            summary += '\n';
        });
        
        if (results.length > 5) {
            summary += `... and ${results.length - 5} more results\n`;
        }
        
        return summary;
    }

    // Create readable summary for structured data
    createReadableSummary(data) {
        // Try to find title and description patterns
        const title = data.title || data.name || data.label || data.subject;
        const desc = data.description || data.summary || data.abstract || data.details;
        const url = data.url || data.link || data.href;
        
        if (title || desc) {
            let summary = '';
            if (title) summary += title;
            if (desc) {
                if (title) summary += '\n\n';
                summary += desc;
            }
            if (url) {
                summary += '\n\nURL: ' + url;
            }
            return summary;
        }
        
        return null;
    }

    // Show response in the response box with enhanced formatting
    showResponse({text, markdown, error, plugin_used, plugin_reason, schema_used, schema_error, warning, rawData, pluginInfo}) {
        const responseBox = document.getElementById('response-box');
        if (!responseBox) return;
        
        if (error) {
            responseBox.innerHTML = `<div class="error-response"><i class="fas fa-exclamation-triangle"></i> <strong>Error:</strong> ${error}</div>`;
            return;
        }
        
        let content = '';
        
        // Schema status indicator
        if (schema_used) {
            if (schema_error) {
                content += `<div class="schema-warning">
                    <i class="fas fa-exclamation-triangle"></i> <strong>Schema Warning:</strong> ${schema_error}
                </div>`;
            } else {
                content += `<div class="schema-success">
                    <i class="fas fa-check-circle"></i> <strong>Schema Validation:</strong> Response validated successfully
                </div>`;
            }
        }
        
        // Warning message display
        if (warning) {
            content += `<div class="schema-warning">
                <i class="fas fa-exclamation-triangle"></i> <strong>Processing Warning:</strong> ${warning}
            </div>`;
        }
        
        // Enhanced plugin usage indicator
        if (plugin_used) {
            if (pluginInfo && pluginInfo.plugins.length > 1) {
                // Multiple plugins used
                content += `<div class="plugin-indicator">
                    <i class="fas fa-plug"></i> <strong>Plugins Used:</strong> ${plugin_used}`;
                if (plugin_reason) content += ` - ${plugin_reason}`;
                content += `
                    <div class="plugin-details" style="margin-top: 0.5rem; font-size: 0.9em; color: #6c757d;">
                        ${pluginInfo.plugins.map(p => {
                            const name = p.id || p;
                            const reason = p.reason ? ` (${p.reason})` : '';
                            return `• ${name}${reason}`;
                        }).join('<br>')}
                    </div>
                </div>`;
            } else {
                // Single plugin used (legacy format)
                content += `<div class="plugin-indicator"><i class="fas fa-plug"></i> <strong>Plugin Used:</strong> ${plugin_used}`;
                if (plugin_reason) content += ` - ${plugin_reason}`;
                content += '</div>';
            }
        }
        
        // Response content with unique ID for potential raw data toggle
        const responseId = 'response-' + Date.now();
        
        // Use markdown rendering if specified
        let displayText = text || 'No response received';
        if (markdown && window.renderMarkdown) {
            displayText = window.renderMarkdown(displayText);
            content += `<div class="response-text markdown-content" id="${responseId}" style="line-height: 1.6;">${displayText}</div>`;
        } else {
            content += `<div class="response-text" id="${responseId}" style="white-space: pre-wrap; line-height: 1.6;">${displayText}</div>`;
        }
        
        // Add toggle for raw JSON if rawData is provided
        if (rawData) {
            content += `
                <div class="response-controls" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #dee2e6;">
                    <button class="btn btn-link btn-sm" onclick="toggleRawData('${responseId}')" style="color: #6c757d; font-size: 0.8rem; text-decoration: none; padding: 0.25rem 0.5rem; border: 1px solid #dee2e6; border-radius: 4px; background: #f8f9fa;">
                        <i class="fas fa-code"></i> View Raw JSON
                    </button>
                    <div id="${responseId}-raw" class="raw-data" style="display: none; margin-top: 0.5rem; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 1rem; font-family: 'Courier New', monospace; font-size: 0.8rem; white-space: pre; max-height: 400px; overflow-y: auto; color: #495057;">
                        ${JSON.stringify(rawData, null, 2)}
                    </div>
                </div>
            `;
        }
        
        responseBox.innerHTML = content;
    }

    // Setup plugin catalogue functionality
    setupPluginCatalogue() {
        this.loadPlugins();
        this.setupPluginSearch();
        this.setupPluginRefresh();
    }

    // Load and display plugins with enhanced information
    loadPlugins() {
        const catalogueList = document.getElementById('catalogue-list');
        if (!catalogueList) return;
        
        catalogueList.innerHTML = `
            <div class="loading-plugins">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading plugins...</span>
            </div>
        `;
        
        // Load plugins from multiple sources for comprehensive information
        Promise.all([
            fetch('/api/plugins').then(r => r.json()),
            fetch('/api/plugin/status').then(r => r.json()).catch(() => ({ statuses: {} }))
        ])
        .then(([pluginsData, statusData]) => {
            if (pluginsData.success && pluginsData.plugins) {
                // Enhance plugins with status information
                const enhancedPlugins = pluginsData.plugins.map(plugin => ({
                    ...plugin,
                    status: statusData.statuses?.[plugin.id] || { running: false, enabled: false }
                }));
                this.displayPlugins(enhancedPlugins);
            } else {
                catalogueList.innerHTML = `
                    <div class="empty-catalogue">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h3>Failed to Load Plugins</h3>
                        <p>Unable to retrieve plugin information. Please check your connection and try again.</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading plugins:', error);
            catalogueList.innerHTML = `
                <div class="empty-catalogue">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error Loading Plugins</h3>
                    <p>${error.message}</p>
                </div>
            `;
        });
    }

    // Display plugins in the catalogue with enhanced UI
    displayPlugins(plugins) {
        const catalogueList = document.getElementById('catalogue-list');
        if (!catalogueList) return;
        
        if (plugins.length === 0) {
            catalogueList.innerHTML = `
                <div class="empty-catalogue">
                    <i class="fas fa-puzzle-piece"></i>
                    <h3>No Plugins Found</h3>
                    <p>No plugins are currently available or match your search criteria.</p>
                </div>
            `;
            return;
        }
        
        catalogueList.innerHTML = '';
        
        plugins.forEach(plugin => {
            const pluginCard = this.createEnhancedPluginCard(plugin);
            catalogueList.appendChild(pluginCard);
        });
    }

    // Create enhanced plugin card with rich information
    createEnhancedPluginCard(plugin) {
        const isRunning = plugin.status?.running || plugin.running || false;
        const isEnabled = plugin.status?.enabled || plugin.enabled || false;
        
        const pluginCard = document.createElement('div');
        pluginCard.className = `plugin-card ${isRunning ? 'enabled' : 'disabled'}`;
        
        // Extract capabilities for display
        const capabilities = plugin.capabilities || {};
        const capabilityList = [];
        
        Object.entries(capabilities).forEach(([category, funcs]) => {
            Object.keys(funcs).forEach(funcName => {
                capabilityList.push(funcName.replace(/_/g, ' '));
            });
        });

        // Extract usage examples
        const usageExamples = [];
        Object.entries(capabilities).forEach(([category, funcs]) => {
            Object.entries(funcs).forEach(([funcName, funcInfo]) => {
                if (funcInfo.use_cases && Array.isArray(funcInfo.use_cases)) {
                    usageExamples.push(...funcInfo.use_cases.slice(0, 2)); // Limit to 2 per function
                }
            });
        });

        pluginCard.innerHTML = `
            <div class="plugin-header">
                <div class="plugin-info">
                    <h3 class="plugin-title">${plugin.name || 'Unknown Plugin'}</h3>
                    <p class="plugin-author">${plugin.author || 'Unknown Author'}</p>
                </div>
                <div class="plugin-status-badge ${isRunning ? 'running' : 'stopped'}">
                    <span class="status-indicator"></span>
                    ${isRunning ? 'Running' : 'Stopped'}
                </div>
            </div>
            
            <p class="plugin-description">${plugin.description || 'No description available'}</p>
            
            ${capabilityList.length > 0 ? `
                <div class="plugin-capabilities">
                    <h4 class="capabilities-title">Capabilities</h4>
                    <div class="capability-tags">
                        ${capabilityList.slice(0, 4).map(cap => `<span class="capability-tag">${cap}</span>`).join('')}
                        ${capabilityList.length > 4 ? `<span class="capability-tag">+${capabilityList.length - 4} more</span>` : ''}
                    </div>
                </div>
            ` : ''}
            
            <div class="plugin-meta">
                <span class="meta-item">
                    <i class="fas fa-tag"></i>
                    <span>v${plugin.version || '1.0.0'}</span>
                </span>
                <span class="meta-item">
                    <i class="fas fa-shield-alt"></i>
                    <span>${plugin.permissions?.length || 0} permissions</span>
                </span>
                <span class="meta-item">
                    <i class="fas fa-network-wired"></i>
                    <span>Port ${plugin.mcp_port || 'Unknown'}</span>
                </span>
                ${plugin.license ? `
                    <span class="meta-item">
                        <i class="fas fa-certificate"></i>
                        <span>${plugin.license}</span>
                    </span>
                ` : ''}
            </div>
            
            ${usageExamples.length > 0 ? `
                <div class="plugin-usage-examples">
                    <h4 class="usage-title">
                        <i class="fas fa-lightbulb"></i>
                        Usage Examples
                    </h4>
                    <div class="usage-examples">
                        ${usageExamples.slice(0, 3).map(example => `
                            <div class="usage-example">${example}</div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            <div class="plugin-actions">
                <button class="plugin-btn plugin-btn-details" onclick="window.ollamaApp.showPluginDetails('${plugin.id}')">
                    <i class="fas fa-info-circle"></i>
                    Details
                </button>
                <button class="plugin-btn ${isRunning ? 'plugin-btn-disable' : 'plugin-btn-enable'}" 
                        onclick="window.ollamaApp.togglePlugin('${plugin.id}', ${!isRunning})">
                    <i class="fas ${isRunning ? 'fa-stop' : 'fa-play'}"></i>
                    ${isRunning ? 'Disable' : 'Enable'}
                </button>
            </div>
        `;
        
        return pluginCard;
    }

    // Setup plugin search functionality
    setupPluginSearch() {
        const searchInput = document.getElementById('plugin-search');
        const filterSelect = document.getElementById('plugin-filter');
        
        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterPlugins());
        }
        
        if (filterSelect) {
            filterSelect.addEventListener('change', () => this.filterPlugins());
        }
    }

    // Setup plugin refresh functionality
    setupPluginRefresh() {
        const refreshButton = document.getElementById('refresh-plugins-catalogue');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.loadPlugins());
        }
    }

    // Filter plugins based on search and filter criteria
    filterPlugins() {
        console.log('Filtering plugins...');
        // Implementation for filtering plugins would go here
    }

    // Show plugin details
    showPluginDetails(pluginName) {
        console.log(`Showing details for plugin: ${pluginName}`);
        alert(`Plugin details for ${pluginName} - Feature coming soon!`);
    }

    // Toggle plugin enabled/disabled state
    togglePlugin(pluginId, enable) {
        console.log(`${enable ? 'Enabling' : 'Disabling'} plugin: ${pluginId}`);
        
        const endpoint = enable ? '/api/plugin/enable' : '/api/plugin/disable';
        
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ plugin_id: pluginId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.loadPlugins(); // Refresh the plugin list
            } else {
                alert(`Failed to ${enable ? 'enable' : 'disable'} plugin: ${data.error}`);
            }
        })
        .catch(error => {
            alert(`Error ${enable ? 'enabling' : 'disabling'} plugin: ${error.message}`);
        });
    }
}

// Settings manager for configuration and preferences
class SettingsManager {
    constructor() {
        this.defaultSettings = {
            serverUrl: 'http://localhost:11434',
            apiTimeout: 180,
            maxRetries: 3,
            pluginRetries: 2,
            theme: 'light',
            autoConnect: false,
            saveLogs: false,
            modelCacheSize: 1000,
            favoriteModel: null
        };
        this.settings = this.loadSettings();
        this.initializeSettings();
    }

    // Load settings from localStorage
    loadSettings() {
        try {
            const stored = localStorage.getItem('ollamaWrapperSettings');
            if (stored) {
                const parsed = JSON.parse(stored);
                return { ...this.defaultSettings, ...parsed };
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
        return { ...this.defaultSettings };
    }

    // Save settings to localStorage
    saveSettings(newSettings = null) {
        try {
            const settingsToSave = newSettings || this.settings;
            localStorage.setItem('ollamaWrapperSettings', JSON.stringify(settingsToSave));
            this.settings = settingsToSave;
            return true;
        } catch (error) {
            console.error('Error saving settings:', error);
            return false;
        }
    }

    // Get a specific setting
    getSetting(key) {
        return this.settings[key];
    }

    // Set a specific setting
    setSetting(key, value) {
        this.settings[key] = value;
        return this.saveSettings();
    }

    // Reset to default settings
    resetToDefaults() {
        this.settings = { ...this.defaultSettings };
        return this.saveSettings();
    }

    // Set favorite model
    setFavoriteModel(modelName) {
        return this.setSetting('favoriteModel', modelName);
    }

    // Get favorite model
    getFavoriteModel() {
        return this.getSetting('favoriteModel');
    }

    // Initialize settings functionality
    initializeSettings() {
        this.applyTheme();
        this.setupSettingsEventListeners();
        // Delay form population to ensure DOM is ready
        setTimeout(() => this.populateSettingsForm(), 100);
        if (this.settings.autoConnect) {
            // Auto-connect functionality
            setTimeout(() => this.testConnection(), 1000);
        }
    }

    // Apply theme setting
    applyTheme() {
        const theme = this.settings.theme;
        if (theme === 'auto') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
    }

    // Setup settings event listeners
    setupSettingsEventListeners() {
        // Wait for DOM to be ready, then set up listeners
        const setupListeners = () => {
            // Settings form submission
            const settingsForm = document.getElementById('settings-form');
            if (settingsForm) {
                settingsForm.addEventListener('submit', (e) => this.handleSettingsSubmit(e));
            }

            // Reset button
            const resetBtn = document.getElementById('reset-btn');
            if (resetBtn) {
                resetBtn.addEventListener('click', () => this.handleReset());
            }

            // Connection test button
            const testConnectionBtn = document.getElementById('test-connection-btn');
            if (testConnectionBtn) {
                testConnectionBtn.addEventListener('click', () => this.testConnection());
            }

            // Theme change listener
            const themeSelect = document.getElementById('theme');
            if (themeSelect) {
                themeSelect.addEventListener('change', (e) => {
                    this.setSetting('theme', e.target.value);
                    this.applyTheme();
                });
            }

            // Real-time validation
            this.setupValidation();

            // Listen for system theme changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
                if (this.settings.theme === 'auto') {
                    this.applyTheme();
                }
            });
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupListeners);
        } else {
            setupListeners();
        }
    }

    // Setup form validation
    setupValidation() {
        const inputs = document.querySelectorAll('#settings-form input, #settings-form select');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearError(input));
        });
    }

    // Load current settings into form (public interface)
    loadSettingsIntoForm() {
        this.populateSettingsForm();
    }

    // Populate settings form with current values
    populateSettingsForm() {
        Object.keys(this.settings).forEach(key => {
            const element = document.getElementById(this.camelToKebab(key));
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = this.settings[key];
                } else {
                    element.value = this.settings[key];
                }
            }
        });
    }

    // Convert camelCase to kebab-case
    camelToKebab(str) {
        return str.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase();
    }

    // Convert kebab-case to camelCase
    kebabToCamel(str) {
        return str.replace(/-([a-z])/g, (g) => g[1].toUpperCase());
    }

    // Validate individual field
    validateField(input) {
        const value = input.type === 'checkbox' ? input.checked : input.value;
        const name = input.name;
        let isValid = true;
        let errorMessage = '';

        switch (name) {
            case 'serverUrl':
                isValid = this.validateUrl(value);
                errorMessage = isValid ? '' : 'Please enter a valid URL (e.g., http://localhost:11434)';
                break;
            case 'apiTimeout':
                isValid = value >= 1 && value <= 300;
                errorMessage = isValid ? '' : 'Timeout must be between 1 and 300 seconds';
                break;
            case 'maxRetries':
                isValid = value >= 0 && value <= 10;
                errorMessage = isValid ? '' : 'Retries must be between 0 and 10';
                break;
            case 'pluginRetries':
                isValid = value >= 0 && value <= 5;
                errorMessage = isValid ? '' : 'Plugin retries must be between 0 and 5';
                break;
            case 'modelCacheSize':
                isValid = !value || (value >= 100 && value <= 10000);
                errorMessage = isValid ? '' : 'Cache size must be between 100 and 10000 MB';
                break;
        }

        this.showFieldError(input, isValid ? '' : errorMessage);
        return isValid;
    }

    // Validate URL format
    validateUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    // Show field error
    showFieldError(input, message) {
        const errorElement = document.getElementById(`${input.id}-error`);
        if (errorElement) {
            errorElement.textContent = message;
        }
        input.classList.toggle('error', !!message);
    }

    // Clear field error
    clearError(input) {
        this.showFieldError(input, '');
    }

    // Handle settings form submission
    handleSettingsSubmit(e) {
        e.preventDefault();
        
        // Validate all fields
        const form = e.target;
        const inputs = form.querySelectorAll('input, select');
        let isValid = true;

        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });

        if (!isValid) {
            this.showMessage('Please fix the validation errors above.', 'error');
            return;
        }

        // Collect form data
        const formData = new FormData(form);
        const newSettings = {};

        for (const [key, value] of formData.entries()) {
            const camelKey = this.kebabToCamel(key);
            if (key === 'autoConnect' || key === 'saveLogs') {
                newSettings[camelKey] = true; // Checkbox is only in FormData if checked
            } else if (key === 'apiTimeout' || key === 'maxRetries' || key === 'pluginRetries' || key === 'modelCacheSize') {
                newSettings[camelKey] = parseInt(value, 10);
            } else {
                newSettings[camelKey] = value;
            }
        }

        // Handle unchecked checkboxes
        ['autoConnect', 'saveLogs'].forEach(field => {
            if (!(field in newSettings)) {
                newSettings[field] = false;
            }
        });

        // Save settings
        if (this.saveSettings({ ...this.settings, ...newSettings })) {
            this.showMessage('Settings saved successfully!', 'success');
            this.applyTheme(); // Reapply theme in case it changed
        } else {
            this.showMessage('Failed to save settings. Please try again.', 'error');
        }
    }

    // Handle reset to defaults
    handleReset() {
        if (confirm('Are you sure you want to reset all settings to their default values?')) {
            if (this.resetToDefaults()) {
                this.populateSettingsForm();
                this.applyTheme();
                this.showMessage('Settings reset to defaults.', 'success');
            } else {
                this.showMessage('Failed to reset settings. Please try again.', 'error');
            }
        }
    }

    // Test connection to Ollama server
    async testConnection() {
        const statusIndicator = document.getElementById('connection-status');
        const statusText = statusIndicator?.querySelector('.status-text');
        const testButton = document.getElementById('test-connection-btn');
        
        if (!statusIndicator || !statusText) return;
        
        // Update UI to show testing state
        statusText.textContent = 'Testing...';
        statusIndicator.className = 'status-indicator testing';
        if (testButton) testButton.disabled = true;

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.settings.apiTimeout * 1000);
            const backendUrl = 'http://localhost:5000'; // Use Flask backend
            const serverUrl = this.settings.serverUrl;

            const response = await fetch(`${backendUrl}/api/server/status?server_url=${encodeURIComponent(serverUrl)}&timeout=${this.settings.apiTimeout}`, {
                method: 'GET',
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.status === 'running') {
                    statusText.textContent = 'Connected';
                    statusIndicator.className = 'status-indicator connected';
                    this.showMessage('Successfully connected to Ollama server!', 'success');
                } else {
                    statusText.textContent = 'Disconnected';
                    statusIndicator.className = 'status-indicator disconnected';
                    this.showMessage(`Ollama server is ${data.status || 'unavailable'}: ${data.error || 'Unknown error'}`, 'error');
                }
            } else {
                throw new Error(`Server responded with status: ${response.status}`);
            }
        } catch (error) {
            statusText.textContent = 'Disconnected';
            statusIndicator.className = 'status-indicator disconnected';
            
            let errorMessage = 'Failed to connect to Ollama server. ';
            if (error.name === 'AbortError') {
                errorMessage += 'Request timed out.';
            } else if (error.message.includes('fetch')) {
                errorMessage += 'Please check that LibreAssistant backend is running and Ollama is available.';
            } else {
                errorMessage += error.message;
            }
            
            this.showMessage(errorMessage, 'error');
        } finally {
            if (testButton) testButton.disabled = false;
        }
    }

    // Show temporary message
    showMessage(text, type = 'info') {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.message');
        existingMessages.forEach(msg => msg.remove());

        // Create new message
        const message = document.createElement('div');
        message.className = `message ${type}`;
        message.textContent = text;

        // Insert message at the top of the settings view
        const settingsView = document.getElementById('settings-view');
        const viewContent = settingsView?.querySelector('.view-content');
        if (viewContent) {
            viewContent.insertBefore(message, viewContent.firstElementChild);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (message.parentNode) {
                    message.remove();
                }
            }, 5000);
        }
    }
}

// Utility functions for future enhancements
const Utils = {
    // Format file sizes
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
};

// Global functions for monitoring (needed for onclick handlers)
function openServerTab(evt, tabName) {
    // Hide all tab content
    const tabContent = document.getElementsByClassName('server-tab-content');
    for (let i = 0; i < tabContent.length; i++) {
        tabContent[i].classList.remove('active');
    }

    // Remove active class from all tab buttons
    const tabButtons = document.getElementsByClassName('server-tab-button');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }

    // Show the selected tab content and mark button as active
    document.getElementById(tabName).classList.add('active');
    evt.currentTarget.classList.add('active');
}

async function refreshLogs() {
    if (!window.monitoringState || !window.ollamaApp) return;
    
    const refreshBtn = event.target;
    const originalText = refreshBtn.textContent;
    
    // Show loading state
    refreshBtn.textContent = 'Refreshing...';
    refreshBtn.disabled = true;
    
    try {
        await window.ollamaApp.fetchServerLogs();
        
        // Show success feedback
        refreshBtn.textContent = 'Refreshed!';
        refreshBtn.style.background = '#38a169';
        
    } catch (error) {
        // Show error feedback
        refreshBtn.textContent = 'Error!';
        refreshBtn.style.background = '#e53e3e';
        console.error('Error refreshing logs:', error);
    }
    
    setTimeout(() => {
        refreshBtn.textContent = originalText;
        refreshBtn.style.background = '';
        refreshBtn.disabled = false;
    }, 2000);
}

function clearLogs() {
    if (confirm('Are you sure you want to clear the logs display?')) {
        // Clear the local display (this doesn't clear server logs, just the UI)
        window.monitoringState.logs = [];
        window.ollamaApp.displayLogs();
        
        // Add a clear notification
        const now = new Date().toISOString().replace('T', ' ').substring(0, 19);
        document.getElementById('serverLogs').innerHTML = `
            <div class="log-entry info">
                <span class="timestamp">[${now}]</span>
                <span class="level">INFO</span>
                <span class="message">Logs display cleared (refresh to reload from server)</span>
            </div>
        `;
    }
}

function toggleAutoRefresh() {
    if (!window.monitoringState) return;
    
    const checkbox = document.getElementById('autoRefresh');
    
    if (checkbox.checked) {
        // Refresh both logs and errors every 10 seconds when auto-refresh is enabled
        window.monitoringState.autoRefreshInterval = setInterval(async () => {
            if (window.ollamaApp) {
                try {
                    await window.ollamaApp.loadRealTimeData();
                } catch (error) {
                    console.error('Auto-refresh error:', error);
                }
            }
        }, 10000);
        console.log('Auto-refresh enabled (10 second interval)');
    } else {
        if (window.monitoringState.autoRefreshInterval) {
            clearInterval(window.monitoringState.autoRefreshInterval);
            window.monitoringState.autoRefreshInterval = null;
        }
        console.log('Auto-refresh disabled');
    }
}

async function refreshErrors() {
    if (!window.monitoringState || !window.ollamaApp) return;
    
    const refreshBtn = event.target;
    const originalText = refreshBtn.textContent;
    
    // Show loading state
    refreshBtn.textContent = 'Refreshing...';
    refreshBtn.disabled = true;
    
    try {
        await window.ollamaApp.fetchServerErrors();
        
        // Show success feedback
        refreshBtn.textContent = 'Refreshed!';
        refreshBtn.style.background = '#38a169';
        
    } catch (error) {
        // Show error feedback
        refreshBtn.textContent = 'Error!';
        refreshBtn.style.background = '#e53e3e';
        console.error('Error refreshing errors:', error);
    }
    
    setTimeout(() => {
        refreshBtn.textContent = originalText;
        refreshBtn.style.background = '';
        refreshBtn.disabled = false;
    }, 2000);
}

function clearErrors() {
    if (confirm('Are you sure you want to clear the errors display?')) {
        // Clear the local display (this doesn't clear server errors, just the UI)
        window.monitoringState.errors = [];
        window.ollamaApp.displayErrors();
        
        // Show no errors message
        document.getElementById('errorList').innerHTML = '<div style="text-align: center; color: #a0aec0; padding: 40px;">Errors display cleared (refresh to reload from server)</div>';
    }
}

function filterErrors() {
    if (!window.monitoringState) return;
    
    const filterValue = document.getElementById('errorFilter').value;
    window.monitoringState.errorFilter = filterValue;
    window.ollamaApp.displayErrors();
}

// Utility functions for potential API integration
function formatLogLevel(level) {
    const levelMap = {
        'debug': 'DEBUG',
        'info': 'INFO',
        'warn': 'WARNING',
        'error': 'ERROR',
        'fatal': 'CRITICAL'
    };
    return levelMap[level.toLowerCase()] || level.toUpperCase();
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toISOString().replace('T', ' ').substring(0, 19);
}

// Global function to toggle raw data display
function toggleRawData(responseId) {
    const rawDataElement = document.getElementById(responseId + '-raw');
    if (rawDataElement) {
        rawDataElement.style.display = rawDataElement.style.display === 'none' ? 'block' : 'none';
    }
}

// Plugin-specific functions for Brave Search
async function braveSearch() {
    const query = document.getElementById('brave-search-query').value.trim();
    if (!query) return;

    document.getElementById('brave-status').textContent = 'Searching...';
    
    try {
        // Call Brave Search plugin directly
        const res = await fetch('http://localhost:5103/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await res.json();
        
        if (data.success) {
            // Extract main content for user-friendly display
            const mainContent = extractMainContent(data);
            const displayText = mainContent || 'Search completed successfully. View raw data for details.';
            
            if (window.ollamaApp && window.ollamaApp.showResponse) {
                window.ollamaApp.showResponse({
                    text: displayText, 
                    markdown: false, 
                    plugin_used: 'Brave Search',
                    plugin_reason: `Search query: "${query}"`,
                    rawData: data
                });
            }
            document.getElementById('brave-modal').style.display = 'none';
        } else {
            document.getElementById('brave-status').textContent = 'Error: ' + (data.error || 'Search failed');
        }
    } catch (e) {
        document.getElementById('brave-status').textContent = 'Error: ' + e.message;
    }
}

// Plugin-specific functions for CourtListener
async function courtlistenerSearch() {
    const query = document.getElementById('cl-search-query').value.trim();
    if (!query) return;

    document.getElementById('cl-status').textContent = 'Searching...';
    
    try {
        // Call CourtListener search endpoint directly
        const res = await fetch('http://localhost:5102/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await res.json();
        
        if (data.success) {
            // Extract main content for user-friendly display
            const mainContent = extractMainContent(data);
            const displayText = mainContent || 'Search completed successfully. View raw data for details.';
            
            if (window.ollamaApp && window.ollamaApp.showResponse) {
                window.ollamaApp.showResponse({
                    text: displayText, 
                    markdown: false, 
                    plugin_used: 'CourtListener',
                    plugin_reason: `Search query: "${query}"`,
                    rawData: data
                });
            }
            document.getElementById('courtlistener-modal').style.display = 'none';
        } else {
            document.getElementById('cl-status').textContent = 'Error: ' + (data.error || 'Search failed');
        }
    } catch (e) {
        document.getElementById('cl-status').textContent = 'Error: ' + e.message;
    }
}

async function courtlistenerOpinion() {
    const id = document.getElementById('cl-opinion-id').value.trim();
    if (!id) return;

    document.getElementById('cl-status').textContent = 'Fetching opinion...';
    
    try {
        // Call CourtListener opinion endpoint directly
        const res = await fetch('http://localhost:5102/opinion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ opinion_id: id })
        });
        const data = await res.json();
        
        if (data.success) {
            // Extract main content for user-friendly display
            const mainContent = extractMainContent(data);
            const displayText = mainContent || 'Opinion fetched successfully. View raw data for details.';
            
            if (window.ollamaApp && window.ollamaApp.showResponse) {
                window.ollamaApp.showResponse({
                    text: displayText, 
                    markdown: false, 
                    plugin_used: 'CourtListener',
                    plugin_reason: `Opinion ID: ${id}`,
                    rawData: data
                });
            }
            document.getElementById('courtlistener-modal').style.display = 'none';
        } else {
            document.getElementById('cl-status').textContent = 'Error: ' + (data.error || 'Fetch failed');
        }
    } catch (e) {
        document.getElementById('cl-status').textContent = 'Error: ' + e.message;
    }
}

async function courtlistenerDocket() {
    const id = document.getElementById('cl-docket-id').value.trim();
    if (!id) return;

    document.getElementById('cl-status').textContent = 'Fetching docket...';
    
    try {
        // Call CourtListener docket endpoint directly
        const res = await fetch('http://localhost:5102/docket', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ docket_id: id })
        });
        const data = await res.json();
        
        if (data.success) {
            // Extract main content for user-friendly display
            const mainContent = extractMainContent(data);
            const displayText = mainContent || 'Docket fetched successfully. View raw data for details.';
            
            if (window.ollamaApp && window.ollamaApp.showResponse) {
                window.ollamaApp.showResponse({
                    text: displayText, 
                    markdown: false, 
                    plugin_used: 'CourtListener',
                    plugin_reason: `Docket ID: ${id}`,
                    rawData: data
                });
            }
            document.getElementById('courtlistener-modal').style.display = 'none';
        } else {
            document.getElementById('cl-status').textContent = 'Error: ' + (data.error || 'Fetch failed');
        }
    } catch (e) {
        document.getElementById('cl-status').textContent = 'Error: ' + e.message;
    }
}

// Helper function to extract main content from plugin responses
function extractMainContent(data) {
    if (!data || !data.content) return null;
    
    // Try to extract meaningful content based on plugin response structure
    if (Array.isArray(data.content)) {
        return data.content.map(item => {
            if (typeof item === 'string') return item;
            if (item.title || item.name) return `${item.title || item.name}: ${item.description || item.summary || ''}`;
            return JSON.stringify(item);
        }).join('\n\n');
    }
    
    if (typeof data.content === 'object') {
        if (data.content.text) return data.content.text;
        if (data.content.summary) return data.content.summary;
        if (data.content.description) return data.content.description;
    }
    
    if (typeof data.content === 'string') {
        return data.content;
    }
    
    return null;
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.ollamaApp = new LibreAssistantApp();
    window.settingsManager = new SettingsManager();
});

// Handle window resize for responsive behavior
window.addEventListener('resize', () => {
    const sidebar = document.querySelector('.sidebar');
    if (window.innerWidth > 768) {
        sidebar.classList.remove('open');
    }
});

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OllamaWrapperApp, Utils };
}