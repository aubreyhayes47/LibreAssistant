/**
 * Configuration management for LibreAssistant frontend
 * Centralizes all endpoint URLs and settings
 */

class AppConfig {
    constructor() {
        this.config = {
            // Backend API Configuration
            backend: {
                baseUrl: this.getBackendUrl(),
                endpoints: {
                    models: '/api/models',
                    info: '/api/info',
                    serverErrors: '/api/server/errors',
                    pluginConfig: '/api/plugin/config',
                    pluginStatus: '/api/plugin/status',
                    pluginActivity: '/api/plugins/activity',
                    healthz: '/api/healthz'
                }
            },
            
            // Default settings that can be overridden
            defaults: {
                serverUrl: 'http://localhost:11434',
                apiTimeout: 180,
                maxRetries: 3,
                pluginRetries: 2,
                theme: 'light',
                autoConnect: false,
                saveLogs: false,
                modelCacheSize: 1000,
                favoriteModel: null
            }
        };
    }

    /**
     * Determine backend URL from various sources
     */
    getBackendUrl() {
        // Priority: 
        // 1. Meta tag in HTML (allows server-side configuration)
        // 2. Environment variable (if available)
        // 3. Window location (same origin)
        // 4. Default localhost
        
        const metaBackend = document.querySelector('meta[name="backend-url"]');
        if (metaBackend && metaBackend.content) {
            return metaBackend.content;
        }
        
        // Use same origin as current page
        if (window.location.protocol && window.location.host) {
            return `${window.location.protocol}//${window.location.host}`;
        }
        
        // Fallback to localhost
        return 'http://localhost:5000';
    }

    /**
     * Get full API endpoint URL
     */
    getApiUrl(endpoint) {
        const endpointPath = this.config.backend.endpoints[endpoint];
        if (!endpointPath) {
            throw new Error(`Unknown API endpoint: ${endpoint}`);
        }
        return `${this.config.backend.baseUrl}${endpointPath}`;
    }

    /**
     * Get backend base URL
     */
    getBackendBaseUrl() {
        return this.config.backend.baseUrl;
    }

    /**
     * Get default setting value
     */
    getDefault(key) {
        return this.config.defaults[key];
    }

    /**
     * Get all defaults
     */
    getAllDefaults() {
        return { ...this.config.defaults };
    }

    /**
     * Update backend URL (useful for dynamic configuration)
     */
    setBackendUrl(url) {
        this.config.backend.baseUrl = url.replace(/\/$/, ''); // Remove trailing slash
    }
}

// Create singleton instance
const appConfig = new AppConfig();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = appConfig;
}

// Also make available globally for immediate usage
window.appConfig = appConfig;