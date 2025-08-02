/**
 * Modal Manager for Gurumisha
 * Handles modal lifecycle, focus management, and proper cleanup
 * Integrates with Alpine.js and HTMX for seamless modal experiences
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.modalManagerLoaded) {
        console.log('Modal manager already loaded');
        return;
    }
    window.modalManagerLoaded = true;

    class ModalManager {
        constructor() {
            this.activeModals = new Set();
            this.modalStack = [];
            this.originalFocus = null;
            this.init();
        }

        init() {
            console.log('🪟 Modal Manager initialized (v2.0 - Fixed DOMNodeInserted)');
            this.setupEventListeners();
            this.setupKeyboardHandling();
            this.setupFocusManagement();
        }

        /**
         * Setup event listeners for modal management
         */
        setupEventListeners() {
            // Listen for modal creation via HTMX
            document.addEventListener('htmx:afterSwap', (event) => {
                const target = event.detail.target;
                this.checkForNewModals(target);
            });

            // Listen for modal creation via direct DOM manipulation using MutationObserver
            this.setupMutationObserver();

            // Listen for custom modal events
            document.addEventListener('modal:show', (event) => {
                this.showModal(event.detail.modalId);
            });

            document.addEventListener('modal:hide', (event) => {
                this.hideModal(event.detail.modalId);
            });

            document.addEventListener('modal:close-all', () => {
                this.closeAllModals();
            });
        }

        /**
         * Setup keyboard handling for modals
         */
        setupKeyboardHandling() {
            document.addEventListener('keydown', (event) => {
                if (this.activeModals.size === 0) return;

                switch (event.key) {
                    case 'Escape':
                        event.preventDefault();
                        this.closeTopModal();
                        break;
                    case 'Tab':
                        this.handleTabNavigation(event);
                        break;
                }
            });
        }

        /**
         * Setup MutationObserver for modal creation detection
         */
        setupMutationObserver() {
            // Check if document.body is available
            if (!document.body) {
                // Silently wait for DOM to be ready instead of warning
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', () => {
                        this.setupMutationObserver();
                    });
                } else {
                    // Try again after a short delay
                    setTimeout(() => {
                        this.setupMutationObserver();
                    }, 50);
                }
                return;
            }

            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                this.checkForNewModals(node);
                            }
                        });
                    }
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }

        /**
         * Setup focus management for accessibility
         */
        setupFocusManagement() {
            // Store original focus when modal opens
            document.addEventListener('focusin', (event) => {
                if (this.activeModals.size === 0) {
                    this.originalFocus = event.target;
                }
            });
        }

        /**
         * Check for new modals in the given element
         */
        checkForNewModals(element) {
            if (!element || element.nodeType !== Node.ELEMENT_NODE) return;

            // Check if the element itself is a modal
            if (this.isModal(element)) {
                this.registerModal(element);
            }

            // Check for modals within the element
            const modals = element.querySelectorAll('[role="dialog"], .modal, [id*="modal"]');
            modals.forEach(modal => {
                if (this.isModal(modal)) {
                    this.registerModal(modal);
                }
            });
        }

        /**
         * Check if an element is a modal
         */
        isModal(element) {
            return element.hasAttribute('role') && element.getAttribute('role') === 'dialog' ||
                   element.classList.contains('modal') ||
                   element.id.includes('modal') ||
                   element.hasAttribute('x-data') && element.getAttribute('x-data').includes('modal');
        }

        /**
         * Register a new modal
         */
        registerModal(modal) {
            if (this.activeModals.has(modal.id)) return;

            console.log('🪟 Registering modal:', modal.id);
            
            this.activeModals.add(modal.id);
            this.modalStack.push(modal.id);

            // Setup modal-specific event listeners
            this.setupModalEventListeners(modal);

            // Initialize modal state
            this.initializeModal(modal);

            // Handle focus
            this.handleModalFocus(modal);

            // Prevent body scroll
            this.preventBodyScroll();
        }

        /**
         * Setup event listeners for a specific modal
         */
        setupModalEventListeners(modal) {
            // Close button handlers
            const closeButtons = modal.querySelectorAll('[data-modal-close], .modal-close, [aria-label*="close" i]');
            closeButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.hideModal(modal.id);
                });
            });

            // Backdrop click handler
            modal.addEventListener('click', (e) => {
                if (e.target === modal || e.target.classList.contains('modal-backdrop')) {
                    this.hideModal(modal.id);
                }
            });

            // Form submission handlers
            const forms = modal.querySelectorAll('form');
            forms.forEach(form => {
                form.addEventListener('submit', (e) => {
                    this.handleFormSubmission(form, modal);
                });
            });
        }

        /**
         * Initialize modal state and Alpine.js components
         */
        initializeModal(modal) {
            // Ensure Alpine.js is initialized for the modal
            if (window.hydrationManager) {
                window.hydrationManager.hydrateElement(modal);
            }

            // Set initial ARIA attributes
            modal.setAttribute('aria-modal', 'true');
            modal.setAttribute('tabindex', '-1');

            // Show the modal if it has Alpine.js show state
            setTimeout(() => {
                if (typeof Alpine !== 'undefined') {
                    const alpineData = Alpine.$data(modal);
                    if (alpineData && typeof alpineData.show !== 'undefined') {
                        alpineData.show = true;
                    }
                }
            }, 50);
        }

        /**
         * Handle modal focus management
         */
        handleModalFocus(modal) {
            // Focus the modal itself initially
            modal.focus();

            // Then focus the first focusable element
            setTimeout(() => {
                const firstFocusable = this.getFirstFocusableElement(modal);
                if (firstFocusable) {
                    firstFocusable.focus();
                }
            }, 100);
        }

        /**
         * Get the first focusable element in a modal
         */
        getFirstFocusableElement(modal) {
            const focusableSelectors = [
                'input:not([disabled]):not([type="hidden"])',
                'select:not([disabled])',
                'textarea:not([disabled])',
                'button:not([disabled])',
                'a[href]',
                '[tabindex]:not([tabindex="-1"])'
            ];

            const focusableElements = modal.querySelectorAll(focusableSelectors.join(', '));
            return focusableElements[0] || null;
        }

        /**
         * Handle tab navigation within modals
         */
        handleTabNavigation(event) {
            const topModal = this.getTopModal();
            if (!topModal) return;

            const focusableElements = this.getFocusableElements(topModal);
            if (focusableElements.length === 0) return;

            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            if (event.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstElement) {
                    event.preventDefault();
                    lastElement.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastElement) {
                    event.preventDefault();
                    firstElement.focus();
                }
            }
        }

        /**
         * Get all focusable elements in a modal
         */
        getFocusableElements(modal) {
            const focusableSelectors = [
                'input:not([disabled]):not([type="hidden"])',
                'select:not([disabled])',
                'textarea:not([disabled])',
                'button:not([disabled])',
                'a[href]',
                '[tabindex]:not([tabindex="-1"])'
            ];

            return Array.from(modal.querySelectorAll(focusableSelectors.join(', ')))
                .filter(element => {
                    return element.offsetWidth > 0 && element.offsetHeight > 0;
                });
        }

        /**
         * Show a modal by ID
         */
        showModal(modalId) {
            const modal = document.getElementById(modalId);
            if (modal && !this.activeModals.has(modalId)) {
                this.registerModal(modal);
            }
        }

        /**
         * Hide a modal by ID
         */
        hideModal(modalId) {
            const modal = document.getElementById(modalId);
            if (!modal || !this.activeModals.has(modalId)) return;

            console.log('🪟 Hiding modal:', modalId);

            // Trigger Alpine.js hide animation
            if (typeof Alpine !== 'undefined') {
                const alpineData = Alpine.$data(modal);
                if (alpineData && typeof alpineData.show !== 'undefined') {
                    alpineData.show = false;
                }
            }

            // Remove from active modals
            this.activeModals.delete(modalId);
            this.modalStack = this.modalStack.filter(id => id !== modalId);

            // Clean up modal
            setTimeout(() => {
                this.cleanupModal(modal);
            }, 300); // Wait for animations to complete
        }

        /**
         * Close the top modal in the stack
         */
        closeTopModal() {
            if (this.modalStack.length > 0) {
                const topModalId = this.modalStack[this.modalStack.length - 1];
                this.hideModal(topModalId);
            }
        }

        /**
         * Close all active modals
         */
        closeAllModals() {
            const modalIds = Array.from(this.activeModals);
            modalIds.forEach(modalId => {
                this.hideModal(modalId);
            });
        }

        /**
         * Get the top modal element
         */
        getTopModal() {
            if (this.modalStack.length === 0) return null;
            const topModalId = this.modalStack[this.modalStack.length - 1];
            return document.getElementById(topModalId);
        }

        /**
         * Clean up modal after hiding
         */
        cleanupModal(modal) {
            // Remove the modal from DOM if it was dynamically created
            if (modal.dataset.dynamic === 'true') {
                modal.remove();
            }

            // Restore body scroll if no more modals
            if (this.activeModals.size === 0) {
                this.restoreBodyScroll();
                this.restoreFocus();
            }
        }

        /**
         * Prevent body scroll when modal is open
         */
        preventBodyScroll() {
            // Store original scroll position if not already stored
            if (!window.modalScrollState) {
                window.modalScrollState = {
                    scrollTop: window.pageYOffset || document.documentElement.scrollTop,
                    scrollLeft: window.pageXOffset || document.documentElement.scrollLeft,
                    originalOverflow: document.body.style.overflow,
                    originalOverflowY: document.body.style.overflowY
                };
            }

            // Apply comprehensive scroll lock
            document.body.style.overflow = 'hidden';
            document.body.style.overflowY = 'hidden';
            document.body.classList.add('modal-open');
            document.documentElement.style.overflow = 'hidden';

            console.log('🔒 Modal Manager: Body scroll locked');
        }

        /**
         * Restore body scroll when all modals are closed
         */
        restoreBodyScroll() {
            // Only restore if no active modals remain
            if (this.activeModals.size === 0) {
                // Call global restoreScroll() function if available
                if (typeof window.restoreScroll === 'function') {
                    window.restoreScroll();
                } else {
                    // Fallback to direct restoration
                    document.body.style.overflow = '';
                    document.body.style.overflowY = '';
                    document.body.classList.remove('modal-open');
                    document.documentElement.style.overflow = '';

                    // Clear stored scroll state
                    if (window.modalScrollState) {
                        delete window.modalScrollState;
                    }

                    // Force browser reflow
                    document.body.offsetHeight;
                }

                console.log('✅ Modal Manager: Body scroll fully restored');
            } else {
                console.log('⏸️ Modal Manager: Keeping scroll locked - active modals:', this.activeModals.size);
            }
        }

        /**
         * Restore focus to the original element
         */
        restoreFocus() {
            if (this.originalFocus && typeof this.originalFocus.focus === 'function') {
                this.originalFocus.focus();
                this.originalFocus = null;
            }
        }

        /**
         * Handle form submission in modals
         */
        handleFormSubmission(form, modal) {
            // Add loading state to submit buttons
            const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
            submitButtons.forEach(button => {
                button.setAttribute('aria-busy', 'true');
                button.disabled = true;
            });

            // Listen for HTMX response
            form.addEventListener('htmx:afterRequest', (event) => {
                submitButtons.forEach(button => {
                    button.setAttribute('aria-busy', 'false');
                    button.disabled = false;
                });

                // Close modal on successful submission (status 200-299)
                if (event.detail.xhr.status >= 200 && event.detail.xhr.status < 300) {
                    // Check if response indicates modal should stay open
                    const keepOpen = event.detail.xhr.getResponseHeader('X-Keep-Modal-Open');
                    if (!keepOpen) {
                        setTimeout(() => {
                            this.hideModal(modal.id);
                        }, 1000); // Give time for success message
                    }
                }
            }, { once: true });
        }

        /**
         * Get modal manager instance
         */
        static getInstance() {
            if (!window.modalManagerInstance) {
                window.modalManagerInstance = new ModalManager();
            }
            return window.modalManagerInstance;
        }
    }

    // Initialize modal manager
    const modalManager = ModalManager.getInstance();

    // Expose globally
    window.modalManager = modalManager;
    window.showModal = (modalId) => modalManager.showModal(modalId);
    window.hideModal = (modalId) => modalManager.hideModal(modalId);
    window.closeAllModals = () => modalManager.closeAllModals();

    console.log('✅ Modal Manager loaded and active');

})();
