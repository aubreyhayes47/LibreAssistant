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
            // Initialize core components
            this.stateManager = window.stateManager;
            this.uiManager = new window.UIManager(this.stateManager);
            this.modelManager = new window.ModelManager(window.apiClient, this.stateManager, this.uiManager);
            this.monitoringManager = new window.MonitoringManager(window.apiClient, this.stateManager, this.uiManager);
            
            // Initialize settings manager (existing)
            this.settingsManager = new SettingsManager();
            
            // Make managers globally available for backward compatibility
            window.ollamaApp = this; // For compatibility with existing onclick handlers
            window.modelManager = this.modelManager;
            window.monitoringManager = this.monitoringManager;
            window.settingsManager = this.settingsManager;
            
            console.log('LibreAssistant initialized successfully');
            
        } catch (error) {
            console.error('Error initializing LibreAssistant:', error);
            this.showInitializationError(error);
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