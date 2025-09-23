/**
 * Settings Management for LibreAssistant
 * Handles user preferences and configuration
 */

class SettingsManager {
    constructor() {
        // Use centralized configuration defaults
        this.defaultSettings = window.appConfig.getAllDefaults();
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
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupListeners);
        } else {
            setupListeners();
        }
    }

    // Populate settings form
    populateSettingsForm() {
        Object.keys(this.settings).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = this.settings[key];
                } else {
                    element.value = this.settings[key];
                }
            }
        });
    }

    // Handle settings form submission
    handleSettingsSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const newSettings = {};
        
        // Process form data
        for (const [key, value] of formData.entries()) {
            const element = document.getElementById(key);
            if (element) {
                if (element.type === 'checkbox') {
                    newSettings[key] = element.checked;
                } else if (element.type === 'number') {
                    newSettings[key] = parseInt(value, 10);
                } else {
                    newSettings[key] = value;
                }
            }
        }

        // Handle unchecked checkboxes (they don't appear in FormData)
        const checkboxes = event.target.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            if (!newSettings.hasOwnProperty(checkbox.id)) {
                newSettings[checkbox.id] = false;
            }
        });

        // Save settings
        const merged = { ...this.settings, ...newSettings };
        if (this.saveSettings(merged)) {
            this.applyTheme();
            this.showMessage('Settings saved successfully!', 'success');
        } else {
            this.showMessage('Failed to save settings. Please try again.', 'error');
        }
    }

    // Handle reset button
    handleReset() {
        if (confirm('Are you sure you want to reset all settings to defaults?')) {
            if (this.resetToDefaults()) {
                this.populateSettingsForm();
                this.applyTheme();
                this.showMessage('Settings reset to defaults!', 'success');
            } else {
                this.showMessage('Failed to reset settings. Please try again.', 'error');
            }
        }
    }

    // Test connection to Ollama server
    async testConnection() {
        const testBtn = document.getElementById('test-connection-btn');
        const originalText = testBtn ? testBtn.textContent : '';
        
        if (testBtn) {
            testBtn.textContent = 'Testing...';
            testBtn.disabled = true;
        }

        try {
            const serverUrl = this.getSetting('serverUrl');
            const timeout = this.getSetting('apiTimeout');
            
            const response = await fetch(`${window.appConfig.getBackendBaseUrl()}/api/server/status?server_url=${encodeURIComponent(serverUrl)}&timeout=${timeout}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage('Connection successful! Server is running.', 'success');
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Connection test failed:', error);
            this.showMessage(`Connection failed: ${error.message}`, 'error');
        } finally {
            if (testBtn) {
                testBtn.textContent = originalText;
                testBtn.disabled = false;
            }
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

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SettingsManager;
}

// Make class available globally
window.SettingsManager = SettingsManager;