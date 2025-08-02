/**
 * Scroll Manager for Gurumisha
 * Centralized scroll state management for modals, HTMX swaps, and Alpine.js components
 * Prevents scroll issues after modal interactions and dynamic content updates
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.scrollManagerLoaded) {
        console.log('Scroll manager already loaded');
        return;
    }
    window.scrollManagerLoaded = true;

    class ScrollManager {
        constructor() {
            this.scrollState = null;
            this.activeModals = new Set();
            this.init();
        }

        init() {
            console.log('🔄 Scroll Manager initialized');
            this.setupEventListeners();
        }

        /**
         * Setup event listeners for scroll management
         */
        setupEventListeners() {
            // Listen for modal events
            document.addEventListener('modal:show', (event) => {
                this.lockScroll(event.detail.modalId);
            });

            document.addEventListener('modal:hide', (event) => {
                this.unlockScroll(event.detail.modalId);
            });

            // Listen for HTMX events
            document.addEventListener('htmx:afterSwap', (event) => {
                this.handleHTMXSwap(event);
            });

            // Listen for Alpine.js events
            document.addEventListener('alpine:init', () => {
                this.verifyScrollState();
            });

            // Listen for window resize to maintain scroll state
            window.addEventListener('resize', () => {
                this.verifyScrollState();
            });
        }

        /**
         * Lock body scroll and store current state
         */
        lockScroll(modalId = null) {
            // Store original scroll position if not already stored
            if (!this.scrollState) {
                this.scrollState = {
                    scrollTop: window.pageYOffset || document.documentElement.scrollTop,
                    scrollLeft: window.pageXOffset || document.documentElement.scrollLeft,
                    originalOverflow: document.body.style.overflow,
                    originalOverflowY: document.body.style.overflowY,
                    originalDocumentOverflow: document.documentElement.style.overflow
                };
            }

            // Track active modal
            if (modalId) {
                this.activeModals.add(modalId);
            }

            // Apply comprehensive scroll lock
            document.body.style.overflow = 'hidden';
            document.body.style.overflowY = 'hidden';
            document.body.classList.add('modal-open', 'scroll-locked');
            document.documentElement.style.overflow = 'hidden';

            console.log('🔒 Scroll locked', modalId ? `for modal: ${modalId}` : '');
        }

        /**
         * Unlock body scroll if no active modals remain
         */
        unlockScroll(modalId = null) {
            // Remove modal from active set
            if (modalId) {
                this.activeModals.delete(modalId);
            }

            // Only unlock if no active modals remain
            if (this.activeModals.size === 0) {
                this.restoreScroll();
            } else {
                console.log('⏸️ Keeping scroll locked - active modals:', this.activeModals.size);
            }
        }

        /**
         * Force restore scroll state
         */
        restoreScroll() {
            // Comprehensive scroll restoration
            document.body.style.overflow = '';
            document.body.style.overflowY = '';
            document.body.classList.remove('modal-open', 'scroll-locked');
            document.documentElement.style.overflow = '';

            // Clear stored state
            this.scrollState = null;
            this.activeModals.clear();

            // Force browser reflow
            document.body.offsetHeight;

            console.log('✅ Scroll fully restored');
        }

        /**
         * Verify and fix scroll state
         */
        verifyScrollState() {
            setTimeout(() => {
                const visibleModals = document.querySelectorAll('.modal.modal-show, .modal[style*="display: flex"]');
                const hasActiveModals = visibleModals.length > 0;

                if (!hasActiveModals && document.body.classList.contains('scroll-locked')) {
                    console.log('🔧 Fixing orphaned scroll lock');
                    this.restoreScroll();
                } else if (hasActiveModals && !document.body.classList.contains('scroll-locked')) {
                    console.log('🔧 Fixing missing scroll lock');
                    this.lockScroll();
                }
            }, 100);
        }

        /**
         * Handle HTMX swap events
         */
        handleHTMXSwap(event) {
            const target = event.detail.target;

            // If swap target is not modal-related, verify scroll state
            if (target && !target.closest('.modal') && !target.id.includes('modal')) {
                this.verifyScrollState();
            }

            // Restore scroll position for table updates
            if (target && target.dataset.scrollLeft !== undefined) {
                const scrollContainer = target.closest('.overflow-x-auto');
                if (scrollContainer) {
                    scrollContainer.scrollLeft = parseInt(target.dataset.scrollLeft) || 0;
                    scrollContainer.scrollTop = parseInt(target.dataset.scrollTop) || 0;
                }
            }
        }

        /**
         * Emergency scroll restoration (for debugging)
         */
        emergencyRestore() {
            console.log('🚨 Emergency scroll restoration');
            document.body.style.overflow = '';
            document.body.style.overflowY = '';
            document.body.classList.remove('modal-open', 'scroll-locked');
            document.documentElement.style.overflow = '';
            this.scrollState = null;
            this.activeModals.clear();
            document.body.offsetHeight;
        }
    }

    // Initialize scroll manager
    const scrollManager = new ScrollManager();

    // Expose global functions for backward compatibility
    window.setGlobalBodyScrollLock = function(modalId) {
        scrollManager.lockScroll(modalId);
    };

    window.restoreGlobalBodyScroll = function(modalId) {
        scrollManager.unlockScroll(modalId);
    };

    window.finalGlobalScrollCheck = function() {
        scrollManager.verifyScrollState();
    };

    window.emergencyScrollRestore = function() {
        scrollManager.emergencyRestore();
    };

    // GLOBAL restoreScroll() function - called whenever a modal closes
    window.restoreScroll = function() {
        console.log('🔄 Global restoreScroll() called');
        scrollManager.restoreScroll();
    };

    // Expose scroll manager instance
    window.scrollManager = scrollManager;

    // Setup global modal close event listeners to ensure restoreScroll() is always called
    function setupGlobalModalCloseHandlers() {
        // Listen for all possible modal close events
        document.addEventListener('modal:hide', function(event) {
            console.log('🎭 Modal hide event detected:', event.detail.modalId);
            restoreScroll();
        });

        document.addEventListener('modal:hidden', function(event) {
            console.log('🎭 Modal hidden event detected:', event.detail.modalId);
            restoreScroll();
        });

        // Listen for HTMX modal close requests
        document.addEventListener('htmx:afterRequest', function(event) {
            const triggerElement = event.detail.elt;
            const isModalCloseRequest = triggerElement && (
                triggerElement.hasAttribute('data-modal-close') ||
                triggerElement.closest('[data-modal-close]') ||
                (event.detail.xhr.responseURL &&
                 event.detail.xhr.responseURL.includes('modal') &&
                 event.detail.xhr.responseURL.includes('close'))
            );

            if (isModalCloseRequest && event.detail.successful) {
                console.log('🎭 HTMX modal close request detected');
                setTimeout(() => restoreScroll(), 100);
            }
        });

        // Listen for Alpine.js modal close events (when Alpine is available)
        document.addEventListener('alpine:init', function() {
            if (typeof Alpine !== 'undefined') {
                // Watch for Alpine.js show property changes
                Alpine.effect(() => {
                    const modals = document.querySelectorAll('[x-data*="show"]');
                    modals.forEach(modal => {
                        const alpineData = Alpine.$data(modal);
                        if (alpineData && typeof alpineData.show !== 'undefined') {
                            Alpine.effect(() => {
                                if (!alpineData.show && modal.classList.contains('modal')) {
                                    console.log('🎭 Alpine.js modal close detected');
                                    setTimeout(() => restoreScroll(), 100);
                                }
                            });
                        }
                    });
                });
            }
        });

        // Listen for direct DOM modal removals
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    mutation.removedNodes.forEach(function(node) {
                        if (node.nodeType === Node.ELEMENT_NODE &&
                            (node.classList.contains('modal') || node.querySelector('.modal'))) {
                            console.log('🎭 Modal DOM removal detected');
                            setTimeout(() => restoreScroll(), 100);
                        }
                    });
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Listen for escape key modal closes
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                const visibleModals = document.querySelectorAll('.modal.modal-show, .modal[style*="display: flex"]');
                if (visibleModals.length > 0) {
                    console.log('🎭 Escape key modal close detected');
                    setTimeout(() => restoreScroll(), 300); // Wait for modal close animation
                }
            }
        });

        // Listen for backdrop clicks
        document.addEventListener('click', function(event) {
            if (event.target.classList.contains('modal')) {
                console.log('🎭 Backdrop click modal close detected');
                setTimeout(() => restoreScroll(), 300); // Wait for modal close animation
            }
        });

        // Listen for close button clicks
        document.addEventListener('click', function(event) {
            if (event.target.hasAttribute('data-modal-close') ||
                event.target.closest('[data-modal-close]')) {
                console.log('🎭 Close button click detected');
                setTimeout(() => restoreScroll(), 300); // Wait for modal close animation
            }
        });

        console.log('✅ Global modal close handlers setup complete');
    }

    // Initialize global handlers
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupGlobalModalCloseHandlers);
    } else {
        setupGlobalModalCloseHandlers();
    }

    console.log('✅ Scroll Manager loaded with global restoreScroll() handlers');

})();
