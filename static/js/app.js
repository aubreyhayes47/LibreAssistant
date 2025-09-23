/**
 * Main Application for LibreAssistant
 * Simplified main script that orchestrates the modular components
 */

class LibreAssistantApp {
    constructor() {
        this.initializeApp();
    }

    async initializeApp() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupApp());
        } else {
            this.setupApp();
        }
    }

    setupApp() {
        try {
            // Initialize core components with enhanced dependencies
            this.stateManager = window.stateManager;
            this.uiManager = new window.UIManager(this.stateManager);
            this.asyncOperationManager = this.uiManager.asyncOperationManager;
            
            // Initialize managers with enhanced dependencies
            this.modelManager = new window.ModelManager(window.apiClient, this.stateManager, this.uiManager);
            this.monitoringManager = new window.MonitoringManager(window.apiClient, this.stateManager, this.uiManager, this.asyncOperationManager);
            
            // Initialize plugin manager if available
            if (window.PluginManager) {
                this.pluginManager = new window.PluginManager(window.apiClient, this.stateManager, this.uiManager, this.asyncOperationManager);
                this.pluginManager.init();
            }
            
            // Initialize settings manager (existing)
            this.settingsManager = new SettingsManager();
            
            // Make managers globally available for backward compatibility
            window.ollamaApp = this; // For compatibility with existing onclick handlers
            window.modelManager = this.modelManager;
            window.monitoringManager = this.monitoringManager;
            window.pluginManager = this.pluginManager;
            window.settingsManager = this.settingsManager;
            window.asyncOperationManager = this.asyncOperationManager;
            
            // Initialize operation status containers
            this.createOperationStatusContainers();
            
            console.log('LibreAssistant initialized successfully with enhanced features');
            
        } catch (error) {
            console.error('Error initializing LibreAssistant:', error);
            this.showInitializationError(error);
        }
    }

    createOperationStatusContainers() {
        // Create operation status container if it doesn't exist
        if (!DOMUtils.getElementById('operation-status-container')) {
            const statusContainer = DOMUtils.createElement('div', {
                id: 'operation-status-container',
                className: 'operation-status-container position-fixed bottom-0 end-0 p-3',
                style: 'z-index: 1060; max-width: 350px;'
            });
            document.body.appendChild(statusContainer);
        }
        
        // Create batch progress container if it doesn't exist
        if (!DOMUtils.getElementById('batch-progress-container')) {
            const batchContainer = DOMUtils.createElement('div', {
                id: 'batch-progress-container',
                className: 'batch-progress-container position-fixed top-0 start-50 translate-middle-x p-3',
                style: 'z-index: 1070; max-width: 400px;'
            });
            document.body.appendChild(batchContainer);
        }
    }

    showInitializationError(error) {
        const errorHtml = `
            <div class="initialization-error">
                <h3>Application Initialization Error</h3>
                <p>LibreAssistant failed to initialize properly:</p>
                <code>${error.message}</code>
                <p>Please refresh the page or contact support if the problem persists.</p>
            </div>
        `;
        
        document.body.insertAdjacentHTML('afterbegin', errorHtml);
    }

    // Legacy method compatibility for existing onclick handlers
    async loadModels() {
        return this.modelManager.loadModels();
    }

    async showModelInfo(modelName) {
        return this.modelManager.showModelInfo(modelName);
    }

    async deleteModel(modelName) {
        return this.modelManager.deleteModel(modelName);
    }

    async fetchServerErrors() {
        return this.monitoringManager.fetchServerErrors();
    }

    displayErrors() {
        return this.monitoringManager.displayErrors();
    }

    displayErrorsError(error) {
        return this.monitoringManager.displayErrorsError(error);
    }
}

// Utility functions for backward compatibility with existing onclick handlers
function openServerTab(evt, tabName) {
    if (window.monitoringManager) {
        window.monitoringManager.openServerTab(evt, tabName);
    }
}

async function refreshLogs() {
    if (window.monitoringManager) {
        await window.monitoringManager.fetchServerLogs();
    }
}

function clearLogs() {
    if (window.monitoringManager) {
        window.monitoringManager.clearLogs();
    }
}

function toggleAutoRefresh() {
    if (window.monitoringManager) {
        window.monitoringManager.toggleAutoRefresh();
    }
}

async function refreshErrors() {
    if (window.monitoringManager) {
        await window.monitoringManager.fetchServerErrors();
    }
}

function clearErrors() {
    if (window.monitoringManager) {
        window.monitoringManager.clearErrors();
    }
}

function filterErrors() {
    if (window.monitoringManager) {
        window.monitoringManager.filterErrors();
    }
}

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

function toggleRawData(responseId) {
    const rawDataElement = document.getElementById(responseId + '-raw');
    if (rawDataElement) {
        rawDataElement.style.display = rawDataElement.style.display === 'none' ? 'block' : 'none';
    }
}

// Initialize the application
const app = new LibreAssistantApp();

// Export for debugging
window.app = app;