/**
 * Modal Error Catcher for Gurumisha
 * Comprehensive error handling system for all modal operations
 * Version 1.0 - Complete modal error management
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.modalErrorCatcherLoaded) {
        console.log('Modal Error Catcher already loaded');
        return;
    }
    window.modalErrorCatcherLoaded = true;

    class ModalErrorCatcher {
        constructor() {
            this.errorLog = [];
            this.maxErrorLog = 50;
            this.retryAttempts = new Map();
            this.maxRetries = 3;
            this.init();
        }

        init() {
            console.log('🛡️ Modal Error Catcher v1.0 initialized');
            this.setupGlobalErrorHandlers();
            this.setupHTMXErrorHandlers();
            this.setupModalSpecificHandlers();
            this.setupRecoveryMechanisms();
        }

        /**
         * Setup global error handlers for modal operations
         */
        setupGlobalErrorHandlers() {
            // Catch modal-related JavaScript errors
            window.addEventListener('error', (event) => {
                if (this.isModalRelatedError(event)) {
                    this.handleModalError({
                        type: 'javascript',
                        error: event.error,
                        message: event.message,
                        filename: event.filename,
                        lineno: event.lineno,
                        timestamp: new Date().toISOString()
                    });
                }
            });

            // Catch unhandled promise rejections in modal operations
            window.addEventListener('unhandledrejection', (event) => {
                if (this.isModalRelatedPromiseRejection(event)) {
                    this.handleModalError({
                        type: 'promise_rejection',
                        error: event.reason,
                        message: event.reason?.message || 'Promise rejection in modal operation',
                        timestamp: new Date().toISOString()
                    });
                }
            });
        }

        /**
         * Setup HTMX-specific error handlers for modal loading
         */
        setupHTMXErrorHandlers() {
            // Handle HTMX response errors for modal requests
            document.addEventListener('htmx:responseError', (event) => {
                if (this.isModalHTMXRequest(event)) {
                    this.handleModalHTMXError(event);
                }
            });

            // Handle HTMX network errors for modal requests
            document.addEventListener('htmx:sendError', (event) => {
                if (this.isModalHTMXRequest(event)) {
                    this.handleModalNetworkError(event);
                }
            });

            // Handle HTMX timeout errors for modal requests
            document.addEventListener('htmx:timeout', (event) => {
                if (this.isModalHTMXRequest(event)) {
                    this.handleModalTimeoutError(event);
                }
            });

            // Handle HTMX swap errors for modal content
            document.addEventListener('htmx:swapError', (event) => {
                if (this.isModalHTMXRequest(event)) {
                    this.handleModalSwapError(event);
                }
            });
        }

        /**
         * Setup modal-specific error handlers
         */
        setupModalSpecificHandlers() {
            // Monitor for modal element errors
            const observer = new MutationObserver((mutations) => {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE && this.isModalElement(node)) {
                            this.setupModalElementErrorHandling(node);
                        }
                    });
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });

            // Handle existing modals
            document.querySelectorAll('[role="dialog"], [id*="modal"]').forEach(modal => {
                this.setupModalElementErrorHandling(modal);
            });
        }

        /**
         * Setup error handling for a specific modal element
         */
        setupModalElementErrorHandling(modal) {
            const modalId = modal.id || `modal_${Date.now()}`;
            
            // Catch Alpine.js errors in modal
            if (modal.hasAttribute('x-data')) {
                this.setupAlpineErrorHandling(modal, modalId);
            }

            // Catch form submission errors in modal
            const forms = modal.querySelectorAll('form');
            forms.forEach(form => {
                this.setupFormErrorHandling(form, modalId);
            });

            // Catch button click errors in modal
            const buttons = modal.querySelectorAll('button');
            buttons.forEach(button => {
                this.setupButtonErrorHandling(button, modalId);
            });
        }

        /**
         * Setup Alpine.js error handling for modal
         */
        setupAlpineErrorHandling(modal, modalId) {
            try {
                // Wrap Alpine.js methods with error handling
                if (typeof Alpine !== 'undefined' && modal._x_dataStack) {
                    const alpineData = Alpine.$data(modal);
                    
                    if (alpineData && typeof alpineData.closeModal === 'function') {
                        const originalCloseModal = alpineData.closeModal;
                        alpineData.closeModal = (...args) => {
                            try {
                                return originalCloseModal.apply(alpineData, args);
                            } catch (error) {
                                this.handleModalError({
                                    type: 'alpine_close_error',
                                    modalId: modalId,
                                    error: error,
                                    message: `Error closing modal ${modalId}`,
                                    timestamp: new Date().toISOString()
                                });
                                this.fallbackCloseModal(modal);
                            }
                        };
                    }
                }
            } catch (error) {
                this.handleModalError({
                    type: 'alpine_setup_error',
                    modalId: modalId,
                    error: error,
                    message: `Error setting up Alpine.js error handling for modal ${modalId}`,
                    timestamp: new Date().toISOString()
                });
            }
        }

        /**
         * Setup form error handling in modal
         */
        setupFormErrorHandling(form, modalId) {
            form.addEventListener('submit', (event) => {
                try {
                    // Validate form before submission
                    if (!this.validateModalForm(form)) {
                        event.preventDefault();
                        this.showModalError('Please fill in all required fields correctly.');
                        return;
                    }
                } catch (error) {
                    event.preventDefault();
                    this.handleModalError({
                        type: 'form_validation_error',
                        modalId: modalId,
                        error: error,
                        message: `Form validation error in modal ${modalId}`,
                        timestamp: new Date().toISOString()
                    });
                }
            });

            // Handle form submission errors
            form.addEventListener('error', (event) => {
                this.handleModalError({
                    type: 'form_submission_error',
                    modalId: modalId,
                    error: event.error,
                    message: `Form submission error in modal ${modalId}`,
                    timestamp: new Date().toISOString()
                });
            });
        }

        /**
         * Setup button error handling in modal
         */
        setupButtonErrorHandling(button, modalId) {
            const originalClickHandler = button.onclick;
            
            button.addEventListener('click', (event) => {
                try {
                    // Check if button is in valid state
                    if (button.disabled) {
                        event.preventDefault();
                        return;
                    }

                    // Execute original handler if exists
                    if (originalClickHandler) {
                        originalClickHandler.call(button, event);
                    }
                } catch (error) {
                    event.preventDefault();
                    this.handleModalError({
                        type: 'button_click_error',
                        modalId: modalId,
                        buttonId: button.id || 'unknown',
                        error: error,
                        message: `Button click error in modal ${modalId}`,
                        timestamp: new Date().toISOString()
                    });
                }
            });
        }

        /**
         * Handle modal HTMX errors
         */
        handleModalHTMXError(event) {
            const errorInfo = {
                type: 'htmx_response_error',
                status: event.detail.xhr.status,
                statusText: event.detail.xhr.statusText,
                url: event.detail.requestConfig?.path || 'unknown',
                timestamp: new Date().toISOString()
            };

            this.handleModalError(errorInfo);

            // Attempt recovery based on error type
            if (event.detail.xhr.status === 500) {
                this.showModalError('Server error occurred. Please try again in a moment.');
                this.attemptModalRecovery(event.detail.target);
            } else if (event.detail.xhr.status === 404) {
                this.showModalError('The requested content was not found.');
            } else if (event.detail.xhr.status === 403) {
                this.showModalError('You do not have permission to perform this action.');
            } else {
                this.showModalError('An error occurred while loading the modal. Please try again.');
            }
        }

        /**
         * Handle modal network errors
         */
        handleModalNetworkError(event) {
            this.handleModalError({
                type: 'htmx_network_error',
                error: event.detail.error,
                url: event.detail.requestConfig?.path || 'unknown',
                timestamp: new Date().toISOString()
            });

            this.showModalError('Network error. Please check your connection and try again.');
        }

        /**
         * Handle modal timeout errors
         */
        handleModalTimeoutError(event) {
            this.handleModalError({
                type: 'htmx_timeout_error',
                url: event.detail.requestConfig?.path || 'unknown',
                timestamp: new Date().toISOString()
            });

            this.showModalError('Request timed out. Please try again.');
            this.attemptModalRecovery(event.detail.target);
        }

        /**
         * Handle modal swap errors
         */
        handleModalSwapError(event) {
            this.handleModalError({
                type: 'htmx_swap_error',
                error: event.detail.error,
                timestamp: new Date().toISOString()
            });

            this.showModalError('Error displaying modal content. Please refresh the page.');
        }

        /**
         * Setup recovery mechanisms
         */
        setupRecoveryMechanisms() {
            // Auto-retry failed modal requests
            document.addEventListener('htmx:responseError', (event) => {
                if (this.isModalHTMXRequest(event) && this.shouldRetry(event)) {
                    setTimeout(() => {
                        this.retryModalRequest(event);
                    }, 2000);
                }
            });

            // Clean up orphaned modals
            setInterval(() => {
                this.cleanupOrphanedModals();
            }, 30000);
        }

        /**
         * Check if error is modal-related
         */
        isModalRelatedError(event) {
            const errorMessage = event.message?.toLowerCase() || '';
            const filename = event.filename?.toLowerCase() || '';
            
            return errorMessage.includes('modal') ||
                   filename.includes('modal') ||
                   event.target?.closest('[role="dialog"]') ||
                   event.target?.closest('[id*="modal"]');
        }

        /**
         * Check if promise rejection is modal-related
         */
        isModalRelatedPromiseRejection(event) {
            const reason = event.reason?.message?.toLowerCase() || '';
            return reason.includes('modal') || reason.includes('dialog');
        }

        /**
         * Check if HTMX request is modal-related
         */
        isModalHTMXRequest(event) {
            const url = event.detail.requestConfig?.path || '';
            const target = event.detail.target;
            
            return url.includes('modal') ||
                   target?.closest('[role="dialog"]') ||
                   target?.closest('[id*="modal"]') ||
                   event.detail.elt?.hasAttribute('hx-target') && 
                   event.detail.elt.getAttribute('hx-target') === 'body';
        }

        /**
         * Check if element is a modal
         */
        isModalElement(element) {
            return element.hasAttribute('role') && element.getAttribute('role') === 'dialog' ||
                   element.id && element.id.includes('modal') ||
                   element.classList.contains('modal') ||
                   element.hasAttribute('x-data') && element.getAttribute('x-data').includes('show');
        }

        /**
         * Validate modal form
         */
        validateModalForm(form) {
            const requiredFields = form.querySelectorAll('[required]');
            
            for (const field of requiredFields) {
                if (!field.value.trim()) {
                    field.focus();
                    return false;
                }
            }
            
            return true;
        }

        /**
         * Show modal error to user
         */
        showModalError(message) {
            if (window.showError) {
                window.showError(message);
            } else if (window.toastr) {
                window.toastr.error(message);
            } else {
                // Fallback to custom modal error display
                this.createErrorModal(message);
            }
        }

        /**
         * Create error modal as fallback
         */
        createErrorModal(message) {
            const errorModal = document.createElement('div');
            errorModal.className = 'fixed inset-0 z-[9999] flex items-center justify-center bg-black bg-opacity-50';
            errorModal.innerHTML = `
                <div class="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
                    <div class="flex items-center mb-4">
                        <i class="fas fa-exclamation-triangle text-red-500 text-xl mr-3"></i>
                        <h3 class="text-lg font-semibold text-gray-900">Error</h3>
                    </div>
                    <p class="text-gray-700 mb-4">${message}</p>
                    <button onclick="this.closest('.fixed').remove()" 
                            class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition-colors">
                        Close
                    </button>
                </div>
            `;
            
            document.body.appendChild(errorModal);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (errorModal.parentNode) {
                    errorModal.parentNode.removeChild(errorModal);
                }
            }, 5000);
        }

        /**
         * Fallback modal close method
         */
        fallbackCloseModal(modal) {
            try {
                if (modal.parentNode) {
                    modal.parentNode.removeChild(modal);
                }
            } catch (error) {
                console.error('Failed to close modal with fallback method:', error);
            }
        }

        /**
         * Attempt modal recovery
         */
        attemptModalRecovery(target) {
            // Close any open modals
            document.querySelectorAll('[role="dialog"]').forEach(modal => {
                this.fallbackCloseModal(modal);
            });

            // Reset any loading states
            document.querySelectorAll('[data-loading="true"]').forEach(element => {
                element.removeAttribute('data-loading');
                element.style.opacity = '1';
                element.style.pointerEvents = 'auto';
            });
        }

        /**
         * Check if should retry request
         */
        shouldRetry(event) {
            const url = event.detail.requestConfig?.path || '';
            const retryCount = this.retryAttempts.get(url) || 0;
            
            return retryCount < this.maxRetries && 
                   event.detail.xhr.status >= 500;
        }

        /**
         * Retry modal request
         */
        retryModalRequest(event) {
            const url = event.detail.requestConfig?.path || '';
            const retryCount = this.retryAttempts.get(url) || 0;
            
            this.retryAttempts.set(url, retryCount + 1);
            
            console.log(`🔄 Retrying modal request (${retryCount + 1}/${this.maxRetries}):`, url);
            
            if (typeof htmx !== 'undefined') {
                htmx.ajax('GET', url, {
                    target: 'body',
                    swap: 'beforeend'
                });
            }
        }

        /**
         * Clean up orphaned modals
         */
        cleanupOrphanedModals() {
            document.querySelectorAll('[role="dialog"]').forEach(modal => {
                // Check if modal is properly connected and functional
                if (!modal.isConnected || 
                    (!modal._x_dataStack && modal.hasAttribute('x-data'))) {
                    console.log('🧹 Cleaning up orphaned modal:', modal.id);
                    this.fallbackCloseModal(modal);
                }
            });
        }

        /**
         * Handle modal error
         */
        handleModalError(errorInfo) {
            // Log error
            this.errorLog.push(errorInfo);
            
            // Maintain error log size
            if (this.errorLog.length > this.maxErrorLog) {
                this.errorLog.shift();
            }

            // Log to console
            console.error('🚨 Modal Error:', errorInfo);

            // Trigger custom event for external handlers
            document.dispatchEvent(new CustomEvent('modalError', {
                detail: errorInfo
            }));
        }

        /**
         * Get error statistics
         */
        getErrorStats() {
            const stats = {
                totalErrors: this.errorLog.length,
                errorTypes: {},
                recentErrors: this.errorLog.slice(-10)
            };

            this.errorLog.forEach(error => {
                stats.errorTypes[error.type] = (stats.errorTypes[error.type] || 0) + 1;
            });

            return stats;
        }

        /**
         * Clear error log
         */
        clearErrorLog() {
            this.errorLog = [];
            this.retryAttempts.clear();
        }
    }

    // Initialize the modal error catcher
    window.modalErrorCatcher = new ModalErrorCatcher();

    // Expose utility functions
    window.getModalErrorStats = () => window.modalErrorCatcher.getErrorStats();
    window.clearModalErrors = () => window.modalErrorCatcher.clearErrorLog();

    console.log('✅ Modal Error Catcher loaded and initialized');

})();
