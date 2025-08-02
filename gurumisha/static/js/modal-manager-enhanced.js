/**
 * Enhanced Modal Manager for Gurumisha
 * Handles HTMX + Alpine.js modal integration with proper cleanup and accessibility
 * Version 2.0 - Comprehensive modal management
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.enhancedModalManagerLoaded) {
        console.log('Enhanced Modal Manager already loaded');
        return;
    }
    window.enhancedModalManagerLoaded = true;

    class EnhancedModalManager {
        constructor() {
            this.activeModals = new Map();
            this.modalStack = [];
            this.focusStack = [];
            this.init();
        }

        init() {
            console.log('🎭 Enhanced Modal Manager v2.0 initialized');
            this.setupHTMXListeners();
            this.setupGlobalEventListeners();
        }

        /**
         * Setup HTMX event listeners for modal management
         */
        setupHTMXListeners() {
            // Handle modal content loaded via HTMX
            document.addEventListener('htmx:afterSwap', (event) => {
                const target = event.detail.target;
                
                // Check if the swapped content contains a modal
                if (target.tagName === 'BODY' || target.contains(document.body)) {
                    // Content was appended to body, likely a modal
                    this.handleNewModal(target);
                } else {
                    // Check if target itself is a modal
                    const modal = this.findModalInElement(target);
                    if (modal) {
                        this.handleNewModal(modal);
                    }
                }
            });

            // Handle modal removal
            document.addEventListener('htmx:beforeSwap', (event) => {
                // Clean up any modals that might be removed
                this.cleanupRemovedModals();
            });
        }

        /**
         * Find modal elements in a given element
         */
        findModalInElement(element) {
            // Look for common modal patterns
            const modalSelectors = [
                '[id*="modal"]',
                '.fixed.inset-0',
                '[x-data*="show"]',
                '[role="dialog"]'
            ];

            for (const selector of modalSelectors) {
                const modal = element.querySelector ? element.querySelector(selector) : null;
                if (modal && this.isModalElement(modal)) {
                    return modal;
                }
            }

            // Check if element itself is a modal
            if (this.isModalElement(element)) {
                return element;
            }

            return null;
        }

        /**
         * Check if an element is a modal
         */
        isModalElement(element) {
            if (!element || !element.classList) return false;

            return (
                element.classList.contains('fixed') ||
                element.hasAttribute('role') && element.getAttribute('role') === 'dialog' ||
                element.id && element.id.includes('modal') ||
                element.hasAttribute('x-data') && element.getAttribute('x-data').includes('show')
            );
        }

        /**
         * Handle new modal detected
         */
        handleNewModal(modalOrContainer) {
            const modal = this.findModalInElement(modalOrContainer) || modalOrContainer;
            
            if (!modal || !this.isModalElement(modal)) {
                return;
            }

            const modalId = modal.id || `modal_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            
            console.log('🎭 New modal detected:', modalId);

            // Store current focus
            this.focusStack.push(document.activeElement);

            // Initialize the modal
            this.initializeModal(modal, modalId);

            // Add to active modals
            this.activeModals.set(modalId, {
                element: modal,
                initialized: true,
                createdAt: Date.now()
            });

            // Add to modal stack
            this.modalStack.push(modalId);

            // Update z-index
            this.updateModalZIndex(modal);
        }

        /**
         * Initialize a modal with Alpine.js and accessibility
         */
        initializeModal(modal, modalId) {
            try {
                // Ensure Alpine.js is available
                if (typeof Alpine === 'undefined') {
                    console.warn('⚠️ Alpine.js not available for modal initialization');
                    return;
                }

                // Initialize Alpine.js if not already done
                if (!modal._x_dataStack || modal._x_dataStack.length === 0) {
                    console.log('🏔️ Initializing Alpine.js for modal:', modalId);
                    Alpine.initTree(modal);
                }

                // Setup accessibility
                this.setupModalAccessibility(modal, modalId);

                // Setup cleanup handlers
                this.setupModalCleanup(modal, modalId);

                // Setup backdrop click handler
                this.setupBackdropHandler(modal, modalId);

                console.log('✅ Modal initialized successfully:', modalId);

            } catch (error) {
                console.error('❌ Error initializing modal:', error);
            }
        }

        /**
         * Setup modal accessibility
         */
        setupModalAccessibility(modal, modalId) {
            // Set ARIA attributes
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');
            
            // Find and set aria-labelledby
            const title = modal.querySelector('h1, h2, h3, [id*="title"]');
            if (title) {
                if (!title.id) {
                    title.id = `${modalId}-title`;
                }
                modal.setAttribute('aria-labelledby', title.id);
            }

            // Focus management
            setTimeout(() => {
                const focusableElement = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
                if (focusableElement) {
                    focusableElement.focus();
                }
            }, 100);

            // Trap focus within modal
            this.setupFocusTrap(modal);
        }

        /**
         * Setup focus trap for modal
         */
        setupFocusTrap(modal) {
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length === 0) return;

            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            const handleTabKey = (e) => {
                if (e.key !== 'Tab') return;

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
            };

            modal.addEventListener('keydown', handleTabKey);
        }

        /**
         * Setup modal cleanup handlers
         */
        setupModalCleanup(modal, modalId) {
            // Watch for Alpine.js show changes
            if (modal._x_dataStack && modal._x_dataStack.length > 0) {
                const alpineData = Alpine.$data(modal);
                if (alpineData && typeof alpineData.show !== 'undefined') {
                    // Watch for show changes
                    Alpine.effect(() => {
                        if (alpineData.show === false) {
                            setTimeout(() => {
                                this.cleanupModal(modalId);
                            }, 300); // Wait for transition
                        }
                    });
                }
            }

            // Setup escape key handler
            const escapeHandler = (e) => {
                if (e.key === 'Escape' && this.modalStack[this.modalStack.length - 1] === modalId) {
                    this.closeModal(modalId);
                }
            };
            document.addEventListener('keydown', escapeHandler);

            // Store cleanup function
            modal._modalCleanup = () => {
                document.removeEventListener('keydown', escapeHandler);
            };
        }

        /**
         * Setup backdrop click handler
         */
        setupBackdropHandler(modal, modalId) {
            const backdrop = modal.querySelector('.modal-backdrop, [class*="backdrop"]') || modal;
            
            backdrop.addEventListener('click', (e) => {
                if (e.target === backdrop || e.target.classList.contains('modal-backdrop')) {
                    this.closeModal(modalId);
                }
            });
        }

        /**
         * Update modal z-index based on stack position
         */
        updateModalZIndex(modal) {
            const baseZIndex = 1000;
            const stackPosition = this.modalStack.length;
            modal.style.zIndex = baseZIndex + (stackPosition * 10);
        }

        /**
         * Close a specific modal
         */
        closeModal(modalId) {
            const modalData = this.activeModals.get(modalId);
            if (!modalData) return;

            const modal = modalData.element;
            
            // Trigger Alpine.js close if available
            if (modal._x_dataStack && modal._x_dataStack.length > 0) {
                const alpineData = Alpine.$data(modal);
                if (alpineData && typeof alpineData.show !== 'undefined') {
                    alpineData.show = false;
                    return; // Let Alpine.js handle the rest
                }
            }

            // Manual cleanup if Alpine.js not available
            this.cleanupModal(modalId);
        }

        /**
         * Cleanup a modal
         */
        cleanupModal(modalId) {
            const modalData = this.activeModals.get(modalId);
            if (!modalData) return;

            const modal = modalData.element;
            
            console.log('🧹 Cleaning up modal:', modalId);

            // Run modal-specific cleanup
            if (modal._modalCleanup) {
                modal._modalCleanup();
            }

            // Remove from DOM
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }

            // Remove from tracking
            this.activeModals.delete(modalId);
            const stackIndex = this.modalStack.indexOf(modalId);
            if (stackIndex > -1) {
                this.modalStack.splice(stackIndex, 1);
            }

            // Restore focus
            if (this.focusStack.length > 0) {
                const previousFocus = this.focusStack.pop();
                if (previousFocus && previousFocus.focus) {
                    previousFocus.focus();
                }
            }

            console.log('✅ Modal cleanup complete:', modalId);
        }

        /**
         * Clean up removed modals
         */
        cleanupRemovedModals() {
            for (const [modalId, modalData] of this.activeModals.entries()) {
                if (!document.contains(modalData.element)) {
                    this.cleanupModal(modalId);
                }
            }
        }

        /**
         * Setup global event listeners
         */
        setupGlobalEventListeners() {
            // Cleanup on page unload
            window.addEventListener('beforeunload', () => {
                this.activeModals.clear();
                this.modalStack = [];
                this.focusStack = [];
            });
        }

        /**
         * Get active modal count
         */
        getActiveModalCount() {
            return this.activeModals.size;
        }

        /**
         * Get current modal
         */
        getCurrentModal() {
            if (this.modalStack.length === 0) return null;
            const currentModalId = this.modalStack[this.modalStack.length - 1];
            return this.activeModals.get(currentModalId);
        }
    }

    // Initialize the enhanced modal manager
    window.enhancedModalManager = new EnhancedModalManager();

    // Expose utility functions
    window.closeCurrentModal = function() {
        const current = window.enhancedModalManager.getCurrentModal();
        if (current) {
            window.enhancedModalManager.closeModal(current.element.id);
        }
    };

    console.log('✅ Enhanced Modal Manager loaded and initialized');

})();
