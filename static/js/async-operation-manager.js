/**
 * Async Operation Manager for LibreAssistant
 * Provides consistent UI feedback for all asynchronous operations
 */

class AsyncOperationManager {
    constructor(uiManager) {
        this.uiManager = uiManager;
        this.activeOperations = new Map();
        this.operationQueue = [];
        this.maxConcurrentOperations = 5;
    }

    /**
     * Execute an async operation with consistent UI feedback
     */
    async executeOperation(config) {
        const operation = {
            id: config.id || this.generateOperationId(),
            name: config.name || 'Operation',
            targetElement: config.targetElement,
            showGlobalLoading: config.showGlobalLoading || false,
            loadingMessage: config.loadingMessage || 'Loading...',
            successMessage: config.successMessage,
            errorRetryable: config.errorRetryable !== false,
            onStart: config.onStart,
            onSuccess: config.onSuccess,
            onError: config.onError,
            onComplete: config.onComplete,
            operation: config.operation
        };

        // Check if we can start immediately or need to queue
        if (this.activeOperations.size >= this.maxConcurrentOperations) {
            this.operationQueue.push(operation);
            this.showQueuedStatus(operation);
            return;
        }

        return this.startOperation(operation);
    }

    /**
     * Start an operation with UI feedback
     */
    async startOperation(operation) {
        this.activeOperations.set(operation.id, operation);
        
        try {
            // Show loading state
            this.showLoadingState(operation);
            
            // Call onStart callback
            if (operation.onStart) {
                await operation.onStart();
            }
            
            // Execute the main operation
            const result = await operation.operation();
            
            // Show success state
            this.showSuccessState(operation, result);
            
            // Call onSuccess callback
            if (operation.onSuccess) {
                await operation.onSuccess(result);
            }
            
            return result;
            
        } catch (error) {
            console.error(`Operation '${operation.name}' failed:`, error);
            
            // Show error state
            this.showErrorState(operation, error);
            
            // Call onError callback
            if (operation.onError) {
                await operation.onError(error);
            }
            
            throw error;
            
        } finally {
            // Hide loading state
            this.hideLoadingState(operation);
            
            // Call onComplete callback
            if (operation.onComplete) {
                await operation.onComplete();
            }
            
            // Remove from active operations
            this.activeOperations.delete(operation.id);
            
            // Process queue
            this.processQueue();
        }
    }

    /**
     * Show loading state for operation
     */
    showLoadingState(operation) {
        // Show global loading if requested
        if (operation.showGlobalLoading && this.uiManager) {
            this.uiManager.setLoading(true);
        }
        
        // Show element-specific loading
        if (operation.targetElement) {
            DOMUtils.showLoading(operation.targetElement, operation.loadingMessage);
        }
        
        // Update operation status
        this.updateOperationStatus(operation.id, 'loading', operation.loadingMessage);
    }

    /**
     * Show success state for operation
     */
    showSuccessState(operation, result) {
        // Hide global loading if it was shown
        if (operation.showGlobalLoading && this.uiManager) {
            this.uiManager.setLoading(false);
        }
        
        // Show success message if configured
        if (operation.successMessage) {
            if (this.uiManager && this.uiManager.showStatus) {
                this.uiManager.showStatus(operation.successMessage, 'success');
            }
        }
        
        // Update operation status
        this.updateOperationStatus(operation.id, 'success', operation.successMessage || 'Completed successfully');
    }

    /**
     * Show error state for operation
     */
    showErrorState(operation, error) {
        // Hide global loading if it was shown
        if (operation.showGlobalLoading && this.uiManager) {
            this.uiManager.setLoading(false);
        }
        
        const errorMessage = error.message || 'An error occurred';
        
        // Show error in target element if specified
        if (operation.targetElement) {
            DOMUtils.showError(operation.targetElement, errorMessage, operation.errorRetryable);
        }
        
        // Show global error message
        if (this.uiManager && this.uiManager.showStatus) {
            this.uiManager.showStatus(`${operation.name} failed: ${errorMessage}`, 'error');
        }
        
        // Update operation status
        this.updateOperationStatus(operation.id, 'error', errorMessage);
    }

    /**
     * Hide loading state for operation
     */
    hideLoadingState(operation) {
        // Hide element-specific loading
        if (operation.targetElement) {
            DOMUtils.hideLoading(operation.targetElement);
        }
    }

    /**
     * Show queued status for operation
     */
    showQueuedStatus(operation) {
        if (this.uiManager && this.uiManager.showStatus) {
            this.uiManager.showStatus(`${operation.name} queued...`, 'info', 2000);
        }
        
        this.updateOperationStatus(operation.id, 'queued', 'Waiting in queue');
    }

    /**
     * Update operation status in UI
     */
    updateOperationStatus(operationId, status, message) {
        const statusContainer = DOMUtils.getElementById('operation-status-container');
        if (statusContainer) {
            let statusElement = DOMUtils.getElementById(`operation-${operationId}`);
            
            if (!statusElement) {
                statusElement = DOMUtils.createElement('div', {
                    id: `operation-${operationId}`,
                    className: 'operation-status'
                });
                statusContainer.appendChild(statusElement);
            }
            
            const statusIcon = this.getStatusIcon(status);
            statusElement.innerHTML = `
                <i class="${statusIcon}"></i>
                <span class="operation-message">${DOMUtils.escapeHtml(message)}</span>
                <small class="operation-time">${DOMUtils.formatTimestamp(new Date(), 'time')}</small>
            `;
            statusElement.className = `operation-status status-${status}`;
            
            // Auto-remove after completion
            if (status === 'success' || status === 'error') {
                setTimeout(() => {
                    if (statusElement.parentElement) {
                        statusElement.remove();
                    }
                }, 5000);
            }
        }
    }

    /**
     * Get appropriate icon for status
     */
    getStatusIcon(status) {
        switch (status) {
            case 'loading': return 'fas fa-spinner fa-spin';
            case 'queued': return 'fas fa-clock';
            case 'success': return 'fas fa-check-circle text-success';
            case 'error': return 'fas fa-exclamation-circle text-danger';
            default: return 'fas fa-info-circle';
        }
    }

    /**
     * Process operation queue
     */
    processQueue() {
        while (this.operationQueue.length > 0 && this.activeOperations.size < this.maxConcurrentOperations) {
            const nextOperation = this.operationQueue.shift();
            this.startOperation(nextOperation);
        }
    }

    /**
     * Cancel an operation
     */
    cancelOperation(operationId) {
        const operation = this.activeOperations.get(operationId);
        if (operation) {
            this.activeOperations.delete(operationId);
            this.hideLoadingState(operation);
            
            if (this.uiManager && this.uiManager.showStatus) {
                this.uiManager.showStatus(`${operation.name} cancelled`, 'warning');
            }
        }
        
        // Remove from queue if present
        this.operationQueue = this.operationQueue.filter(op => op.id !== operationId);
    }

    /**
     * Cancel all operations
     */
    cancelAllOperations() {
        this.activeOperations.forEach((operation, id) => {
            this.cancelOperation(id);
        });
        this.operationQueue = [];
    }

    /**
     * Get operation status
     */
    getOperationStatus(operationId) {
        return this.activeOperations.get(operationId);
    }

    /**
     * Get all active operations
     */
    getActiveOperations() {
        return Array.from(this.activeOperations.values());
    }

    /**
     * Get queue length
     */
    getQueueLength() {
        return this.operationQueue.length;
    }

    /**
     * Generate unique operation ID
     */
    generateOperationId() {
        return `op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Retry an operation
     */
    async retryOperation(operationId) {
        // Implementation for retrying failed operations
        const operation = this.activeOperations.get(operationId);
        if (operation) {
            return this.startOperation(operation);
        }
    }

    /**
     * Batch execute multiple operations
     */
    async executeBatch(operations, options = {}) {
        const batchId = this.generateOperationId();
        const batchConfig = {
            parallel: options.parallel !== false,
            continueOnError: options.continueOnError === true,
            showProgress: options.showProgress !== false
        };

        if (batchConfig.showProgress) {
            this.showBatchProgress(batchId, 0, operations.length);
        }

        const results = [];
        const errors = [];

        if (batchConfig.parallel) {
            // Execute all operations in parallel
            const promises = operations.map(async (op, index) => {
                try {
                    const result = await this.executeOperation(op);
                    results[index] = result;
                    
                    if (batchConfig.showProgress) {
                        this.updateBatchProgress(batchId, results.filter(r => r !== undefined).length, operations.length);
                    }
                    
                    return result;
                } catch (error) {
                    errors[index] = error;
                    if (!batchConfig.continueOnError) {
                        throw error;
                    }
                    return null;
                }
            });

            await Promise.all(promises);
        } else {
            // Execute operations sequentially
            for (let i = 0; i < operations.length; i++) {
                try {
                    const result = await this.executeOperation(operations[i]);
                    results[i] = result;
                    
                    if (batchConfig.showProgress) {
                        this.updateBatchProgress(batchId, i + 1, operations.length);
                    }
                } catch (error) {
                    errors[i] = error;
                    if (!batchConfig.continueOnError) {
                        throw error;
                    }
                }
            }
        }

        if (batchConfig.showProgress) {
            this.hideBatchProgress(batchId);
        }

        return { results, errors };
    }

    /**
     * Show batch progress
     */
    showBatchProgress(batchId, completed, total) {
        const progressContainer = DOMUtils.getElementById('batch-progress-container') || 
            this.createBatchProgressContainer();
        
        let progressElement = DOMUtils.getElementById(`batch-${batchId}`);
        if (!progressElement) {
            progressElement = DOMUtils.createElement('div', {
                id: `batch-${batchId}`,
                className: 'batch-progress'
            });
            progressContainer.appendChild(progressElement);
        }

        const percentage = Math.round((completed / total) * 100);
        progressElement.innerHTML = `
            <div class="progress-info">
                <span>Batch operation: ${completed}/${total}</span>
                <span>${percentage}%</span>
            </div>
            <div class="progress">
                <div class="progress-bar" style="width: ${percentage}%"></div>
            </div>
        `;
    }

    /**
     * Update batch progress
     */
    updateBatchProgress(batchId, completed, total) {
        this.showBatchProgress(batchId, completed, total);
    }

    /**
     * Hide batch progress
     */
    hideBatchProgress(batchId) {
        const progressElement = DOMUtils.getElementById(`batch-${batchId}`);
        if (progressElement) {
            setTimeout(() => progressElement.remove(), 1000);
        }
    }

    /**
     * Create batch progress container if it doesn't exist
     */
    createBatchProgressContainer() {
        let container = DOMUtils.getElementById('batch-progress-container');
        if (!container) {
            container = DOMUtils.createElement('div', {
                id: 'batch-progress-container',
                className: 'batch-progress-container'
            });
            document.body.appendChild(container);
        }
        return container;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AsyncOperationManager;
}

// Make class available globally
window.AsyncOperationManager = AsyncOperationManager;