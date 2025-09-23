/**
 * State Management for LibreAssistant
 * Centralized state management with proper encapsulation
 */

class StateManager {
    constructor() {
        this.state = {
            // Navigation state
            currentView: 'models',
            
            // Monitoring state
            logs: [],
            errors: [],
            lastLogUpdate: null,
            lastErrorUpdate: null,
            logFilter: '',
            errorFilter: '',
            autoRefreshLogs: false,
            autoRefreshErrors: false,
            
            // Application state
            isLoading: false,
            lastError: null,
            
            // Plugin state
            activePlugins: [],
            pluginActivity: {},
            
            // Model state
            models: [],
            selectedModel: null
        };
        
        this.listeners = new Map();
        this.setupInitialState();
    }

    /**
     * Setup initial state
     */
    setupInitialState() {
        // Initialize monitoring state on window object for compatibility
        // (to be removed in future version)
        window.monitoringState = {
            logs: this.state.logs,
            errors: this.state.errors,
            lastLogUpdate: this.state.lastLogUpdate,
            lastErrorUpdate: this.state.lastErrorUpdate,
            logFilter: this.state.logFilter,
            errorFilter: this.state.errorFilter,
            autoRefreshLogs: this.state.autoRefreshLogs,
            autoRefreshErrors: this.state.autoRefreshErrors
        };
    }

    /**
     * Get current state
     */
    getState() {
        return { ...this.state };
    }

    /**
     * Get specific state value
     */
    get(key) {
        return this.state[key];
    }

    /**
     * Set state value and notify listeners
     */
    set(key, value) {
        const oldValue = this.state[key];
        this.state[key] = value;
        
        // Update window.monitoringState for backward compatibility
        if (window.monitoringState.hasOwnProperty(key)) {
            window.monitoringState[key] = value;
        }
        
        this.notifyListeners(key, value, oldValue);
    }

    /**
     * Update multiple state values
     */
    update(updates) {
        const changes = {};
        for (const [key, value] of Object.entries(updates)) {
            changes[key] = { old: this.state[key], new: value };
            this.state[key] = value;
            
            // Update window.monitoringState for backward compatibility
            if (window.monitoringState.hasOwnProperty(key)) {
                window.monitoringState[key] = value;
            }
        }
        
        for (const [key, { old: oldValue, new: newValue }] of Object.entries(changes)) {
            this.notifyListeners(key, newValue, oldValue);
        }
    }

    /**
     * Subscribe to state changes
     */
    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, new Set());
        }
        this.listeners.get(key).add(callback);
        
        // Return unsubscribe function
        return () => {
            const keyListeners = this.listeners.get(key);
            if (keyListeners) {
                keyListeners.delete(callback);
            }
        };
    }

    /**
     * Notify listeners of state changes
     */
    notifyListeners(key, newValue, oldValue) {
        const keyListeners = this.listeners.get(key);
        if (keyListeners) {
            keyListeners.forEach(callback => {
                try {
                    callback(newValue, oldValue, key);
                } catch (error) {
                    console.error('Error in state listener:', error);
                }
            });
        }
    }

    /**
     * Reset state to initial values
     */
    reset() {
        const initialState = {
            currentView: 'models',
            logs: [],
            errors: [],
            lastLogUpdate: null,
            lastErrorUpdate: null,
            logFilter: '',
            errorFilter: '',
            autoRefreshLogs: false,
            autoRefreshErrors: false,
            isLoading: false,
            lastError: null,
            activePlugins: [],
            pluginActivity: {},
            models: [],
            selectedModel: null
        };
        
        this.update(initialState);
    }

    /**
     * Helper methods for common operations
     */
    setCurrentView(view) {
        this.set('currentView', view);
    }

    addLog(log) {
        const logs = [...this.state.logs, log];
        this.set('logs', logs);
    }

    addError(error) {
        const errors = [...this.state.errors, error];
        this.set('errors', errors);
    }

    clearLogs() {
        this.set('logs', []);
    }

    clearErrors() {
        this.set('errors', []);
    }

    setModels(models) {
        this.set('models', models);
    }

    setLoading(isLoading) {
        this.set('isLoading', isLoading);
    }
}

// Create singleton instance
const stateManager = new StateManager();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = stateManager;
}

// Make available globally
window.stateManager = stateManager;