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
            const response = await fetch(`${backendUrl}/api/models?server_url=${encodeURIComponent(serverUrl)}`);
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

        try {
            const response = await fetch(`${backendUrl}/api/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    model_name: modelName,
                    server_url: serverUrl
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

        try {
            const response = await fetch(`${backendUrl}/api/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    model_name: modelName,
                    server_url: serverUrl
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

        try {
            const response = await fetch(`${backendUrl}/api/info/${modelName}?server_url=${encodeURIComponent(serverUrl)}`);

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
            const response = await fetch(`${backendUrl}/api/models?server_url=${encodeURIComponent(serverUrl)}`);
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
            const response = await fetch(`${backendUrl}/api/models?server_url=${encodeURIComponent(serverUrl)}`);
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
            const response = await fetch(`${backendUrl}/api/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: this.selectedChatModel,
                    prompt: prompt,
                    stream: false,
                    history: this.chatHistory // send the full conversation history
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
        fetch('/api/plugins/accessed')
            .then(res => res.json())
            .then(data => {
                const pillsContainer = document.getElementById('plugin-pills');
                if (!pillsContainer) return;
                
                if (data.plugins && data.plugins.length > 0) {
                    data.plugins.forEach(plugin => {
                        const pill = document.createElement('span');
                        pill.className = 'plugin-pill';
                        pill.textContent = plugin;
                        pill.onclick = function() {
                            console.log(`Plugin ${plugin} clicked`);
                            // Future: Add plugin-specific actions
                        };
                        pillsContainer.appendChild(pill);
                    });
                } else {
                    pillsContainer.innerHTML = '<span style="color: #7f8c8d;">No plugins accessed yet</span>';
                }
            })
            .catch(err => {
                console.log('Could not load plugin pills:', err);
                const pillsContainer = document.getElementById('plugin-pills');
                if (pillsContainer) {
                    pillsContainer.innerHTML = '<span style="color: #e74c3c;">Failed to load plugins</span>';
                }
            });
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
        
        if (!input || !button || !responseBox) return;

        // Setup refresh models button
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.loadRequestModels());
        }
        
        const submitRequest = () => {
            const query = input.value.trim();
            const selectedModel = modelSelect ? modelSelect.value : '';
            
            if (!query) return;
            
            if (!selectedModel) {
                responseBox.innerHTML = `
                    <div style="color: #e74c3c; padding: 1rem;">
                        <h4>Error:</h4>
                        <p>Please select a model before sending your request.</p>
                    </div>
                `;
                return;
            }
            
            // Show loading state
            responseBox.innerHTML = `
                <div style="text-align: center; padding: 2rem;">
                    <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #3498db;"></i>
                    <p>Processing your request with ${selectedModel}...</p>
                </div>
            `;
            
            const serverUrl = window.settingsManager ? window.settingsManager.getSetting('serverUrl') : 'http://localhost:11434';
            
            // Make request to API
            fetch('/api/request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    query: query,
                    model: selectedModel,
                    server_url: serverUrl
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    responseBox.innerHTML = `
                        <div class="response-content">
                            <h4>Response from ${selectedModel}:</h4>
                            <div class="response-text">${data.response || 'No response received'}</div>
                        </div>
                    `;
                } else {
                    responseBox.innerHTML = `
                        <div style="color: #e74c3c; padding: 1rem;">
                            <h4>Error:</h4>
                            <p>${data.error || 'Request failed'}</p>
                            ${data.suggestion ? `<p style="color: #7f8c8d; font-style: italic; margin-top: 0.5rem;"><strong>Suggestion:</strong> ${data.suggestion}</p>` : ''}
                        </div>
                    `;
                }
            })
            .catch(error => {
                responseBox.innerHTML = `
                    <div style="color: #e74c3c; padding: 1rem;">
                        <h4>Error:</h4>
                        <p>Failed to process request: ${error.message}</p>
                    </div>
                `;
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

    // Setup plugin catalogue functionality
    setupPluginCatalogue() {
        this.loadPlugins();
        this.setupPluginSearch();
        this.setupPluginRefresh();
    }

    // Load and display plugins
    loadPlugins() {
        const catalogueList = document.getElementById('catalogue-list');
        if (!catalogueList) return;
        
        catalogueList.innerHTML = `
            <div class="loading-plugins">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading plugins...</span>
            </div>
        `;
        
        fetch('/api/plugins/list')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.plugins) {
                    this.displayPlugins(data.plugins);
                } else {
                    catalogueList.innerHTML = `
                        <div class="loading-plugins">
                            <i class="fas fa-exclamation-triangle" style="color: #e74c3c;"></i>
                            <span>Failed to load plugins</span>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading plugins:', error);
                catalogueList.innerHTML = `
                    <div class="loading-plugins">
                        <i class="fas fa-exclamation-triangle" style="color: #e74c3c;"></i>
                        <span>Error loading plugins: ${error.message}</span>
                    </div>
                `;
            });
    }

    // Display plugins in the catalogue
    displayPlugins(plugins) {
        const catalogueList = document.getElementById('catalogue-list');
        if (!catalogueList) return;
        
        if (plugins.length === 0) {
            catalogueList.innerHTML = `
                <div class="loading-plugins">
                    <i class="fas fa-puzzle-piece" style="color: #7f8c8d;"></i>
                    <span>No plugins found</span>
                </div>
            `;
            return;
        }
        
        catalogueList.innerHTML = '';
        
        plugins.forEach(plugin => {
            const pluginCard = document.createElement('div');
            pluginCard.className = `plugin-card ${plugin.enabled ? 'enabled' : 'disabled'}`;
            
            pluginCard.innerHTML = `
                <div class="plugin-header">
                    <div class="plugin-info">
                        <h3>${plugin.name}</h3>
                        <p>${plugin.description || 'No description available'}</p>
                    </div>
                    <div class="plugin-status">
                        <span class="status-badge ${plugin.enabled ? 'enabled' : 'disabled'}">
                            ${plugin.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                    </div>
                </div>
                <div class="plugin-details">
                    <p><strong>Type:</strong> ${plugin.type || 'Unknown'}</p>
                    <p><strong>Status:</strong> ${plugin.running ? 'Running' : 'Stopped'}</p>
                </div>
                <div class="plugin-actions">
                    <button class="btn btn-primary" onclick="window.ollamaApp.showPluginDetails('${plugin.name}')">
                        Details
                    </button>
                    <button class="btn ${plugin.enabled ? 'btn-danger' : 'btn-success'}" 
                            onclick="window.ollamaApp.togglePlugin('${plugin.name}', ${!plugin.enabled})">
                        ${plugin.enabled ? 'Disable' : 'Enable'}
                    </button>
                </div>
            `;
            
            catalogueList.appendChild(pluginCard);
        });
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
        const refreshButton = document.getElementById('refresh-plugins');
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
    togglePlugin(pluginName, enable) {
        console.log(`${enable ? 'Enabling' : 'Disabling'} plugin: ${pluginName}`);
        
        const endpoint = enable ? '/api/plugin/enable' : '/api/plugin/disable';
        
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ plugin_id: pluginName })
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
            apiTimeout: 30,
            maxRetries: 3,
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
            } else if (key === 'apiTimeout' || key === 'maxRetries' || key === 'modelCacheSize') {
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

            const response = await fetch(`${backendUrl}/api/server/status?server_url=${encodeURIComponent(serverUrl)}`, {
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