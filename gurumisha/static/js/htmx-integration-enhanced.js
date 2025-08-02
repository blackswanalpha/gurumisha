/**
 * Enhanced HTMX Integration Manager for Gurumisha
 * Handles HTMX + Alpine.js integration with button preservation
 * Version 2.0 - Comprehensive HTMX management
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.htmxIntegrationEnhancedLoaded) {
        console.log('Enhanced HTMX Integration already loaded');
        return;
    }
    window.htmxIntegrationEnhancedLoaded = true;

    class EnhancedHTMXIntegration {
        constructor() {
            this.preservedElements = new Map();
            this.buttonRegistry = new Map();
            this.init();
        }

        init() {
            console.log('🔄 Enhanced HTMX Integration v2.0 initialized');
            this.setupHTMXEventListeners();
            this.setupButtonPreservation();
            this.setupAlpineIntegration();
        }

        /**
         * Setup HTMX event listeners for enhanced integration
         */
        setupHTMXEventListeners() {
            // Before swap - preserve important elements
            document.addEventListener('htmx:beforeSwap', (event) => {
                this.preserveImportantElements(event);
            });

            // After swap - restore and re-hydrate
            document.addEventListener('htmx:afterSwap', (event) => {
                this.restorePreservedElements(event);
                this.rehydrateAlpineComponents(event);
                this.reregisterButtons(event);
            });

            // Before request - track button states
            document.addEventListener('htmx:beforeRequest', (event) => {
                this.trackButtonStates(event);
            });

            // After request - restore button states
            document.addEventListener('htmx:afterRequest', (event) => {
                this.restoreButtonStates(event);
            });

            // Handle errors
            document.addEventListener('htmx:responseError', (event) => {
                console.error('🚨 HTMX Response Error:', event.detail);
                this.handleHTMXError(event);
            });
        }

        /**
         * Preserve important elements before HTMX swap
         */
        preserveImportantElements(event) {
            const target = event.detail.target;
            
            // Find elements to preserve (buttons, modals, etc.)
            const elementsToPreserve = target.querySelectorAll(
                'button[hx-get], button[hx-post], [data-preserve], .modal, [x-data]'
            );

            elementsToPreserve.forEach(element => {
                const id = element.id || `preserved_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                element.id = id;
                
                // Clone the element with all its properties
                const clone = element.cloneNode(true);
                
                // Preserve Alpine.js data if present
                if (element._x_dataStack) {
                    clone._x_dataStack = element._x_dataStack;
                }
                
                this.preservedElements.set(id, {
                    element: clone,
                    parent: element.parentNode,
                    nextSibling: element.nextSibling,
                    alpineData: element._x_dataStack ? Alpine.$data(element) : null
                });
            });
        }

        /**
         * Restore preserved elements after HTMX swap
         */
        restorePreservedElements(event) {
            const target = event.detail.target;
            
            this.preservedElements.forEach((preserved, id) => {
                const existingElement = target.querySelector(`#${id}`);
                
                if (existingElement && preserved.element) {
                    // Replace the new element with the preserved one
                    existingElement.parentNode.replaceChild(preserved.element, existingElement);
                    
                    // Restore Alpine.js data if present
                    if (preserved.alpineData && typeof Alpine !== 'undefined') {
                        try {
                            Alpine.initTree(preserved.element);
                        } catch (error) {
                            console.warn('⚠️ Could not restore Alpine.js data:', error);
                        }
                    }
                }
            });

            // Clear preserved elements
            this.preservedElements.clear();
        }

        /**
         * Setup button preservation system
         */
        setupButtonPreservation() {
            // Register all buttons with HTMX attributes
            this.registerExistingButtons();

            // Watch for new buttons
            const observer = new MutationObserver((mutations) => {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.registerButtonsInElement(node);
                        }
                    });
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }

        /**
         * Register existing buttons
         */
        registerExistingButtons() {
            const buttons = document.querySelectorAll('button[hx-get], button[hx-post]');
            buttons.forEach(button => this.registerButton(button));
        }

        /**
         * Register buttons in a specific element
         */
        registerButtonsInElement(element) {
            const buttons = element.querySelectorAll ? element.querySelectorAll('button[hx-get], button[hx-post]') : [];
            buttons.forEach(button => this.registerButton(button));
        }

        /**
         * Register a single button
         */
        registerButton(button) {
            const id = button.id || `btn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            button.id = id;

            this.buttonRegistry.set(id, {
                element: button,
                hxGet: button.getAttribute('hx-get'),
                hxPost: button.getAttribute('hx-post'),
                hxTarget: button.getAttribute('hx-target'),
                hxSwap: button.getAttribute('hx-swap'),
                classes: button.className,
                innerHTML: button.innerHTML,
                disabled: button.disabled
            });
        }

        /**
         * Track button states before HTMX request
         */
        trackButtonStates(event) {
            const triggeringElement = event.detail.elt;
            
            if (triggeringElement && triggeringElement.tagName === 'BUTTON') {
                const id = triggeringElement.id;
                if (this.buttonRegistry.has(id)) {
                    const buttonData = this.buttonRegistry.get(id);
                    buttonData.wasDisabled = triggeringElement.disabled;
                    buttonData.originalText = triggeringElement.innerHTML;
                    
                    // Show loading state
                    triggeringElement.disabled = true;
                    const loadingText = triggeringElement.getAttribute('data-loading-text') || 'Loading...';
                    triggeringElement.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${loadingText}`;
                }
            }
        }

        /**
         * Restore button states after HTMX request
         */
        restoreButtonStates(event) {
            const triggeringElement = event.detail.elt;
            
            if (triggeringElement && triggeringElement.tagName === 'BUTTON') {
                const id = triggeringElement.id;
                if (this.buttonRegistry.has(id)) {
                    const buttonData = this.buttonRegistry.get(id);
                    
                    // Restore original state
                    triggeringElement.disabled = buttonData.wasDisabled || false;
                    triggeringElement.innerHTML = buttonData.originalText || buttonData.innerHTML;
                }
            }
        }

        /**
         * Re-register buttons after HTMX swap
         */
        reregisterButtons(event) {
            const target = event.detail.target;
            this.registerButtonsInElement(target);
        }

        /**
         * Setup Alpine.js integration
         */
        setupAlpineIntegration() {
            // Ensure Alpine.js is available
            if (typeof Alpine === 'undefined') {
                console.warn('⚠️ Alpine.js not available for HTMX integration');
                return;
            }

            // Setup Alpine.js re-hydration
            this.setupAlpineRehydration();
        }

        /**
         * Setup Alpine.js re-hydration after HTMX swaps
         */
        setupAlpineRehydration() {
            document.addEventListener('htmx:afterSwap', (event) => {
                this.rehydrateAlpineComponents(event);
            });
        }

        /**
         * Re-hydrate Alpine.js components after HTMX swap
         */
        rehydrateAlpineComponents(event) {
            const target = event.detail.target;

            // Use safe Alpine.js utilities if available
            if (window.safeAlpineBatchInit) {
                console.log('🏔️ Re-hydrating Alpine.js components using safe utilities');
                window.safeAlpineBatchInit(target);
                return;
            }

            // Fallback to direct Alpine.js if safe utilities not available
            if (!window.isAlpineReady || !window.isAlpineReady()) {
                console.warn('⚠️ Alpine.js not ready for re-hydration');
                return;
            }

            try {
                // Find Alpine.js components in the swapped content
                const alpineElements = target.querySelectorAll('[x-data]');

                alpineElements.forEach(element => {
                    // Only initialize if not already initialized
                    if (!element._x_dataStack || element._x_dataStack.length === 0) {
                        console.log('🏔️ Re-hydrating Alpine.js component:', element);
                        Alpine.initTree(element);
                    }
                });

                // Also check if target itself has Alpine.js
                if (target.hasAttribute && target.hasAttribute('x-data')) {
                    if (!target._x_dataStack || target._x_dataStack.length === 0) {
                        Alpine.initTree(target);
                    }
                }

            } catch (error) {
                console.error('❌ Error re-hydrating Alpine.js components:', error);
            }
        }

        /**
         * Handle HTMX errors
         */
        handleHTMXError(event) {
            // Restore button states on error
            this.restoreButtonStates(event);
            
            // Show error message
            const errorMessage = event.detail.xhr.status === 500 ? 
                'Server error occurred. Please try again.' : 
                'Request failed. Please check your connection.';
            
            // Use toast if available, otherwise alert
            if (window.showError) {
                window.showError(errorMessage);
            } else {
                console.error('🚨 HTMX Error:', errorMessage);
            }
        }

        /**
         * Get button registry for debugging
         */
        getButtonRegistry() {
            return this.buttonRegistry;
        }

        /**
         * Get preserved elements for debugging
         */
        getPreservedElements() {
            return this.preservedElements;
        }
    }

    // Initialize the enhanced HTMX integration
    window.enhancedHTMXIntegration = new EnhancedHTMXIntegration();

    // Expose utility functions
    window.preserveHTMXButtons = function() {
        return window.enhancedHTMXIntegration.registerExistingButtons();
    };

    window.getHTMXButtonRegistry = function() {
        return window.enhancedHTMXIntegration.getButtonRegistry();
    };

    console.log('✅ Enhanced HTMX Integration loaded and initialized');

})();
