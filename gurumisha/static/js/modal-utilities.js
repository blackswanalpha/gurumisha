/**
 * Modal Utilities for Gurumisha
 * Provides utility functions for modal management and accessibility
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.modalUtilitiesLoaded) {
        console.log('Modal utilities already loaded');
        return;
    }
    window.modalUtilitiesLoaded = true;

    /**
     * Global modal utilities
     */
    window.modalUtils = {
        /**
         * Close all open modals
         */
        closeAllModals() {
            const modals = document.querySelectorAll('[role="dialog"], .fixed.inset-0[id*="modal"]');
            modals.forEach(modal => {
                if (modal._x_dataStack && modal._x_dataStack.length > 0) {
                    const alpineData = Alpine.$data(modal);
                    if (alpineData && typeof alpineData.closeModal === 'function') {
                        alpineData.closeModal();
                    } else if (alpineData && typeof alpineData.show !== 'undefined') {
                        alpineData.show = false;
                    }
                } else {
                    // Manual removal
                    if (modal.parentNode) {
                        modal.parentNode.removeChild(modal);
                    }
                }
            });
        },

        /**
         * Get currently open modals
         */
        getOpenModals() {
            return document.querySelectorAll('[role="dialog"]:not([aria-hidden="true"]), .fixed.inset-0[id*="modal"]:not(.hidden)');
        },

        /**
         * Check if any modal is open
         */
        isModalOpen() {
            return this.getOpenModals().length > 0;
        },

        /**
         * Focus first focusable element in modal
         */
        focusFirstElement(modal) {
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            if (focusableElements.length > 0) {
                focusableElements[0].focus();
            }
        },

        /**
         * Setup modal keyboard navigation
         */
        setupKeyboardNavigation(modal) {
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length === 0) return;

            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            modal.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    if (e.shiftKey) {
                        if (document.activeElement === firstElement) {
                            e.preventDefault();
                            lastElement.focus();
                        }
                    } else {
                        if (document.activeElement === lastElement) {
                            e.preventDefault();
                            firstElement.focus();
                        }
                    }
                }
            });
        },

        /**
         * Clean up orphaned modals
         */
        cleanupOrphanedModals() {
            const modals = document.querySelectorAll('[id*="modal"]');
            modals.forEach(modal => {
                // Check if modal is properly connected to Alpine.js or has event listeners
                if (!modal._x_dataStack && !modal.hasAttribute('x-data')) {
                    console.log('🧹 Cleaning up orphaned modal:', modal.id);
                    if (modal.parentNode) {
                        modal.parentNode.removeChild(modal);
                    }
                }
            });
        },

        /**
         * Setup global modal event listeners
         */
        setupGlobalListeners() {
            // Close modals on escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isModalOpen()) {
                    const openModals = this.getOpenModals();
                    if (openModals.length > 0) {
                        const topModal = openModals[openModals.length - 1];
                        if (topModal._x_dataStack && topModal._x_dataStack.length > 0) {
                            const alpineData = Alpine.$data(topModal);
                            if (alpineData && typeof alpineData.closeModal === 'function') {
                                alpineData.closeModal();
                            }
                        }
                    }
                }
            });

            // Cleanup orphaned modals periodically
            setInterval(() => {
                this.cleanupOrphanedModals();
            }, 30000); // Every 30 seconds

            // Cleanup on page unload
            window.addEventListener('beforeunload', () => {
                this.closeAllModals();
            });
        },

        /**
         * Enhance modal accessibility
         */
        enhanceAccessibility(modal) {
            // Set ARIA attributes if not already set
            if (!modal.hasAttribute('role')) {
                modal.setAttribute('role', 'dialog');
            }
            if (!modal.hasAttribute('aria-modal')) {
                modal.setAttribute('aria-modal', 'true');
            }

            // Find and set aria-labelledby
            const title = modal.querySelector('h1, h2, h3, [id*="title"]');
            if (title && !modal.hasAttribute('aria-labelledby')) {
                if (!title.id) {
                    title.id = `${modal.id}-title`;
                }
                modal.setAttribute('aria-labelledby', title.id);
            }

            // Setup keyboard navigation
            this.setupKeyboardNavigation(modal);

            // Focus management
            setTimeout(() => {
                this.focusFirstElement(modal);
            }, 100);
        },

        /**
         * Initialize modal with all enhancements
         */
        initializeModal(modal) {
            console.log('🎭 Initializing modal with utilities:', modal.id);
            
            // Enhance accessibility
            this.enhanceAccessibility(modal);

            // Setup cleanup on Alpine.js show change
            if (modal._x_dataStack && modal._x_dataStack.length > 0) {
                const alpineData = Alpine.$data(modal);
                if (alpineData && typeof alpineData.show !== 'undefined') {
                    Alpine.effect(() => {
                        if (alpineData.show === false) {
                            setTimeout(() => {
                                if (modal.parentNode) {
                                    modal.parentNode.removeChild(modal);
                                }
                            }, 300);
                        }
                    });
                }
            }
        }
    };

    // Initialize global listeners
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.modalUtils.setupGlobalListeners();
        });
    } else {
        window.modalUtils.setupGlobalListeners();
    }

    // Integrate with HTMX
    document.addEventListener('htmx:afterSwap', (event) => {
        const target = event.detail.target;
        
        // Check for new modals
        const modals = target.querySelectorAll('[role="dialog"], [id*="modal"]');
        modals.forEach(modal => {
            window.modalUtils.initializeModal(modal);
        });

        // Check if target itself is a modal
        if (target.hasAttribute('role') && target.getAttribute('role') === 'dialog') {
            window.modalUtils.initializeModal(target);
        }
    });

    console.log('✅ Modal utilities loaded and initialized');

})();
