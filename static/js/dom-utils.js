/**
 * DOM Utilities for LibreAssistant
 * Provides reusable DOM manipulation functions to reduce code duplication
 */

class DOMUtils {
    /**
     * Safely get element by ID
     */
    static getElementById(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Element with ID '${id}' not found`);
        }
        return element;
    }

    /**
     * Safely query selector
     */
    static querySelector(selector) {
        const element = document.querySelector(selector);
        if (!element) {
            console.warn(`Element with selector '${selector}' not found`);
        }
        return element;
    }

    /**
     * Safely query all elements
     */
    static querySelectorAll(selector) {
        return document.querySelectorAll(selector);
    }

    /**
     * Create element with optional attributes and content
     */
    static createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        // Set attributes
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else {
                element.setAttribute(key, value);
            }
        });
        
        // Set content if provided
        if (content) {
            element.innerHTML = content;
        }
        
        return element;
    }

    /**
     * Show loading state in element
     */
    static showLoading(element, message = 'Loading...') {
        if (typeof element === 'string') {
            element = DOMUtils.getElementById(element);
        }
        
        if (element) {
            element.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>${DOMUtils.escapeHtml(message)}</span>
                </div>
            `;
            element.setAttribute('data-loading', 'true');
        }
    }

    /**
     * Hide loading state in element
     */
    static hideLoading(element) {
        if (typeof element === 'string') {
            element = DOMUtils.getElementById(element);
        }
        
        if (element) {
            const loadingState = element.querySelector('.loading-state');
            if (loadingState) {
                loadingState.remove();
            }
            element.removeAttribute('data-loading');
        }
    }

    /**
     * Show error state in element
     */
    static showError(element, errorMessage, showRetry = false) {
        if (typeof element === 'string') {
            element = DOMUtils.getElementById(element);
        }
        
        if (element) {
            const retryButton = showRetry ? 
                `<button class="btn btn-sm btn-outline-primary mt-2" onclick="location.reload()">Retry</button>` : '';
            
            element.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle text-warning"></i>
                    <span class="error-message">${DOMUtils.escapeHtml(errorMessage)}</span>
                    ${retryButton}
                </div>
            `;
            element.setAttribute('data-error', 'true');
        }
    }

    /**
     * Show empty state in element
     */
    static showEmpty(element, message = 'No data available', icon = 'fas fa-inbox') {
        if (typeof element === 'string') {
            element = DOMUtils.getElementById(element);
        }
        
        if (element) {
            element.innerHTML = `
                <div class="empty-state">
                    <i class="${icon}"></i>
                    <span>${DOMUtils.escapeHtml(message)}</span>
                </div>
            `;
            element.setAttribute('data-empty', 'true');
        }
    }

    /**
     * Clear all state attributes from element
     */
    static clearState(element) {
        if (typeof element === 'string') {
            element = DOMUtils.getElementById(element);
        }
        
        if (element) {
            element.removeAttribute('data-loading');
            element.removeAttribute('data-error');
            element.removeAttribute('data-empty');
        }
    }

    /**
     * Add/remove CSS class safely
     */
    static toggleClass(element, className, condition) {
        if (typeof element === 'string') {
            element = DOMUtils.getElementById(element);
        }
        
        if (element) {
            if (condition === undefined) {
                element.classList.toggle(className);
            } else if (condition) {
                element.classList.add(className);
            } else {
                element.classList.remove(className);
            }
        }
    }

    /**
     * Set element content with optional HTML escaping
     */
    static setContent(element, content, escapeHtml = true) {
        if (typeof element === 'string') {
            element = DOMUtils.getElementById(element);
        }
        
        if (element) {
            if (escapeHtml) {
                element.textContent = content;
            } else {
                element.innerHTML = content;
            }
        }
    }

    /**
     * Update multiple elements with loading state
     */
    static setLoadingState(elementIds, isLoading, message = 'Loading...') {
        elementIds.forEach(id => {
            const element = DOMUtils.getElementById(id);
            if (element) {
                if (isLoading) {
                    DOMUtils.showLoading(element, message);
                } else {
                    DOMUtils.hideLoading(element);
                }
            }
        });
    }

    /**
     * Escape HTML to prevent XSS
     */
    static escapeHtml(text) {
        if (typeof text !== 'string') {
            return text;
        }
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Format timestamp consistently
     */
    static formatTimestamp(timestamp, format = 'datetime') {
        const date = new Date(timestamp);
        
        switch (format) {
            case 'time':
                return date.toLocaleTimeString();
            case 'date':
                return date.toLocaleDateString();
            case 'iso':
                return date.toISOString().replace('T', ' ').substring(0, 19);
            case 'datetime':
            default:
                return date.toLocaleString();
        }
    }

    /**
     * Create a status message element
     */
    static createStatusMessage(message, type = 'info', duration = 5000) {
        const statusElement = DOMUtils.createElement('div', {
            className: `status-message status-${type}`,
            innerHTML: `
                <i class="fas fa-${type === 'success' ? 'check-circle' : 
                             type === 'error' ? 'exclamation-circle' : 
                             type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
                <span>${DOMUtils.escapeHtml(message)}</span>
                <button class="btn-close" onclick="this.parentElement.remove()">×</button>
            `
        });

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (statusElement.parentElement) {
                    statusElement.remove();
                }
            }, duration);
        }

        return statusElement;
    }

    /**
     * Animate element change (for smooth transitions)
     */
    static animateChange(element, newContent, escapeHtml = true) {
        if (typeof element === 'string') {
            element = DOMUtils.getElementById(element);
        }
        
        if (element) {
            element.style.opacity = '0.5';
            
            setTimeout(() => {
                DOMUtils.setContent(element, newContent, escapeHtml);
                element.style.opacity = '1';
            }, 150);
        }
    }

    /**
     * Debounce function to prevent excessive calls
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Validate form fields and show feedback
     */
    static validateForm(formElement, validators = {}) {
        if (typeof formElement === 'string') {
            formElement = DOMUtils.getElementById(formElement);
        }
        
        if (!formElement) return false;
        
        let isValid = true;
        
        Object.entries(validators).forEach(([fieldName, validator]) => {
            const field = formElement.querySelector(`[name="${fieldName}"]`);
            if (field) {
                const isFieldValid = validator(field.value);
                DOMUtils.toggleClass(field, 'is-invalid', !isFieldValid);
                DOMUtils.toggleClass(field, 'is-valid', isFieldValid);
                
                if (!isFieldValid) {
                    isValid = false;
                }
            }
        });
        
        return isValid;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DOMUtils;
}

// Make class available globally
window.DOMUtils = DOMUtils;