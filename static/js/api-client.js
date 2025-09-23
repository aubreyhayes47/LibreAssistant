/**
 * API Client for LibreAssistant
 * Centralized HTTP client with proper error handling and configuration
 */

class ApiClient {
    constructor(config) {
        this.config = config;
        this.defaultTimeout = 30000; // 30 seconds
    }

    /**
     * Generic HTTP request method with error handling
     */
    async request(method, endpoint, options = {}) {
        const url = typeof endpoint === 'string' && endpoint.startsWith('http') 
            ? endpoint 
            : this.config.getApiUrl(endpoint);
            
        const config = {
            method: method.toUpperCase(),
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            signal: this.createAbortSignal(options.timeout),
            ...options
        };

        if (config.method !== 'GET' && options.body) {
            config.body = typeof options.body === 'string' 
                ? options.body 
                : JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
            
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timed out');
            }
            throw error;
        }
    }

    /**
     * Create abort signal for timeout handling
     */
    createAbortSignal(timeout) {
        const controller = new AbortController();
        setTimeout(() => controller.abort(), timeout || this.defaultTimeout);
        return controller.signal;
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}, options = {}) {
        let url = typeof endpoint === 'string' && endpoint.startsWith('http') 
            ? endpoint 
            : this.config.getApiUrl(endpoint);
            
        if (Object.keys(params).length > 0) {
            const searchParams = new URLSearchParams(params);
            url += `?${searchParams.toString()}`;
        }
        
        return this.request('GET', url, options);
    }

    /**
     * POST request
     */
    async post(endpoint, body = null, options = {}) {
        return this.request('POST', endpoint, { ...options, body });
    }

    /**
     * PUT request
     */
    async put(endpoint, body = null, options = {}) {
        return this.request('PUT', endpoint, { ...options, body });
    }

    /**
     * DELETE request
     */
    async delete(endpoint, options = {}) {
        return this.request('DELETE', endpoint, options);
    }

    // Specific API methods

    /**
     * Load models from backend
     */
    async loadModels(serverUrl, timeout) {
        return this.get('models', {
            server_url: serverUrl,
            timeout: timeout
        });
    }

    /**
     * Get model information
     */
    async getModelInfo(modelName, serverUrl, timeout) {
        const url = `${this.config.getApiUrl('info').replace('/api/info', `/api/info/${modelName}`)}`;
        return this.get(url, {
            server_url: serverUrl,
            timeout: timeout
        });
    }

    /**
     * Fetch server errors
     */
    async fetchServerErrors() {
        return this.get('serverErrors');
    }

    /**
     * Get plugin configuration
     */
    async getPluginConfig(pluginId) {
        const url = `${this.config.getApiUrl('pluginConfig')}/${pluginId}`;
        return this.get(url);
    }

    /**
     * Set plugin configuration
     */
    async setPluginConfig(pluginId, config) {
        const url = `${this.config.getApiUrl('pluginConfig')}/${pluginId}`;
        return this.post(url, { config });
    }

    /**
     * Get plugin status
     */
    async getPluginStatus(pluginId = null) {
        const baseUrl = this.config.getApiUrl('pluginStatus');
        const url = pluginId ? `${baseUrl}/${pluginId}` : baseUrl;
        return this.get(url);
    }

    /**
     * Get plugin activity
     */
    async getPluginActivity() {
        return this.get('pluginActivity');
    }

    /**
     * Health check
     */
    async healthCheck() {
        return this.get('healthz');
    }
}

// Create singleton instance
const apiClient = new ApiClient(window.appConfig);

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = apiClient;
}

// Make available globally
window.apiClient = apiClient;