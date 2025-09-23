/**
 * Model Management for LibreAssistant
 * Handles all model-related operations
 */

class ModelManager {
    constructor(apiClient, stateManager, uiManager) {
        this.apiClient = apiClient;
        this.stateManager = stateManager;
        this.uiManager = uiManager;
    }

    /**
     * Load models from backend
     */
    async loadModels() {
        const modelList = document.getElementById('model-list');
        
        if (!modelList) return;

        // Show loading state
        this.uiManager.showLoading(modelList, 'Loading models...');

        try {
            const serverUrl = window.settingsManager ? 
                window.settingsManager.getSetting('serverUrl') : 
                window.appConfig.getDefault('serverUrl');
            const timeout = window.settingsManager ? 
                window.settingsManager.getSetting('apiTimeout') : 
                window.appConfig.getDefault('apiTimeout');

            const data = await this.apiClient.loadModels(serverUrl, timeout);
            
            if (data.success) {
                this.stateManager.setModels(data.models || []);
                this.displayModels(data.models || []);
                this.uiManager.showStatus('Models loaded successfully', 'success');
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Error loading models:', error);
            this.uiManager.showError(`Failed to load models: ${error.message}`, modelList);
            this.uiManager.showStatus(`Failed to load models: ${error.message}`, 'error');
        }
    }

    /**
     * Display models in the UI
     */
    displayModels(models) {
        const modelList = document.getElementById('model-list');
        if (!modelList) return;

        if (models.length === 0) {
            modelList.innerHTML = `
                <div class="no-models">
                    <i class="fas fa-info-circle"></i>
                    <p>No models found. Please ensure Ollama is running and has models installed.</p>
                </div>
            `;
            return;
        }

        modelList.innerHTML = '';
        models.forEach(model => {
            const modelElement = this.createModelElement(model);
            modelList.appendChild(modelElement);
        });
    }

    /**
     * Create DOM element for a model
     */
    createModelElement(model) {
        const modelDiv = document.createElement('div');
        modelDiv.className = 'model-item';
        
        const sizeFormatted = model.size_formatted || this.formatBytes(model.size || 0);
        const modifiedDate = model.modified_at || '';
        const family = model.details?.family || model.family || 'Unknown';

        modelDiv.innerHTML = `
            <div class="model-header">
                <h3 class="model-name">${model.name}</h3>
                <div class="model-actions">
                    <button class="btn-icon" onclick="window.modelManager.showModelInfo('${model.name}')" title="Show Info">
                        <i class="fas fa-info-circle"></i>
                    </button>
                    <button class="btn-icon favorite-btn" onclick="window.modelManager.toggleFavorite('${model.name}')" title="Add to Favorites">
                        <i class="far fa-star"></i>
                    </button>
                    <button class="btn-icon delete-btn" onclick="window.modelManager.deleteModel('${model.name}')" title="Delete Model">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
            <div class="model-details">
                <span class="model-size"><i class="fas fa-hard-drive"></i> ${sizeFormatted}</span>
                <span class="model-family"><i class="fas fa-tag"></i> ${family}</span>
                ${modifiedDate ? `<span class="model-date"><i class="fas fa-calendar"></i> ${modifiedDate}</span>` : ''}
            </div>
        `;

        return modelDiv;
    }

    /**
     * Show model information
     */
    async showModelInfo(modelName) {
        const serverUrl = window.settingsManager ? 
            window.settingsManager.getSetting('serverUrl') : 
            window.appConfig.getDefault('serverUrl');
        const timeout = window.settingsManager ? 
            window.settingsManager.getSetting('apiTimeout') : 
            window.appConfig.getDefault('apiTimeout');

        try {
            const data = await this.apiClient.getModelInfo(modelName, serverUrl, timeout);
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

    /**
     * Delete a model
     */
    async deleteModel(modelName) {
        if (!confirm(`Are you sure you want to delete the model "${modelName}"? This action cannot be undone.`)) {
            return;
        }

        try {
            // Show loading status
            this.uiManager.showStatus(`Deleting model ${modelName}...`, 'info');

            const serverUrl = window.settingsManager ? 
                window.settingsManager.getSetting('serverUrl') : 
                window.appConfig.getDefault('serverUrl');

            // Make API call to delete model
            const response = await fetch(`${window.appConfig.getBackendBaseUrl()}/api/model/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model_name: modelName,
                    server_url: serverUrl
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.uiManager.showStatus(`Model "${modelName}" deleted successfully`, 'success');
                // Reload models to reflect the change
                await this.loadModels();
            } else {
                throw new Error(data.error || 'Failed to delete model');
            }
        } catch (error) {
            console.error('Error deleting model:', error);
            this.uiManager.showStatus(`Failed to delete model: ${error.message}`, 'error');
        }
    }

    /**
     * Toggle favorite status of a model
     */
    toggleFavorite(modelName) {
        if (window.settingsManager) {
            const currentFavorite = window.settingsManager.getFavoriteModel();
            
            if (currentFavorite === modelName) {
                // Remove from favorites
                window.settingsManager.setFavoriteModel(null);
                this.uiManager.showStatus(`Removed "${modelName}" from favorites`, 'info');
            } else {
                // Set as favorite
                window.settingsManager.setFavoriteModel(modelName);
                this.uiManager.showStatus(`Added "${modelName}" to favorites`, 'success');
            }
            
            // Update UI to reflect favorite status
            this.updateFavoriteIcons();
        }
    }

    /**
     * Update favorite icons in the UI
     */
    updateFavoriteIcons() {
        if (!window.settingsManager) return;
        
        const favoriteModel = window.settingsManager.getFavoriteModel();
        const favoriteButtons = document.querySelectorAll('.favorite-btn');
        
        favoriteButtons.forEach(button => {
            const icon = button.querySelector('i');
            const modelName = button.getAttribute('onclick').match(/'([^']+)'/)[1];
            
            if (modelName === favoriteModel) {
                icon.className = 'fas fa-star'; // Filled star
                button.title = 'Remove from Favorites';
            } else {
                icon.className = 'far fa-star'; // Empty star
                button.title = 'Add to Favorites';
            }
        });
    }

    /**
     * Download/pull a new model
     */
    async downloadModel() {
        const modelName = prompt('Enter the model name to download (e.g., llama2:7b):');
        if (!modelName) return;

        try {
            this.uiManager.showStatus(`Starting download of ${modelName}...`, 'info');

            const serverUrl = window.settingsManager ? 
                window.settingsManager.getSetting('serverUrl') : 
                window.appConfig.getDefault('serverUrl');

            const response = await fetch(`${window.appConfig.getBackendBaseUrl()}/api/model/pull`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model_name: modelName,
                    server_url: serverUrl
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.uiManager.showStatus(`Model "${modelName}" download started. Check the monitoring tab for progress.`, 'success');
                // Reload models after a delay to allow for download
                setTimeout(() => this.loadModels(), 5000);
            } else {
                throw new Error(data.error || 'Failed to start download');
            }
        } catch (error) {
            console.error('Error downloading model:', error);
            this.uiManager.showStatus(`Failed to download model: ${error.message}`, 'error');
        }
    }

    /**
     * Format bytes to human readable format
     */
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModelManager;
}

// Make class available globally
window.ModelManager = ModelManager;