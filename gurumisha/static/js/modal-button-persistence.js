/**
 * Modal Button Persistence System for Gurumisha
 * Prevents buttons from disappearing when clicking modal buttons
 * Version 1.0 - Comprehensive button protection during modal operations
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.modalButtonPersistenceLoaded) {
        console.log('Modal Button Persistence already loaded');
        return;
    }
    window.modalButtonPersistenceLoaded = true;

    class ModalButtonPersistence {
        constructor() {
            this.buttonStates = new Map();
            this.modalOperationInProgress = false;
            this.protectedButtons = new Set();
            this.init();
        }

        init() {
            console.log('🔘 Modal Button Persistence v1.0 initialized');
            this.setupButtonProtection();
            this.setupModalEventListeners();
            this.setupHTMXInterception();
        }

        /**
         * Setup button protection system
         */
        setupButtonProtection() {
            // Protect all modal buttons on page load
            this.protectExistingModalButtons();

            // Watch for new modal buttons
            const observer = new MutationObserver((mutations) => {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.protectModalButtonsInElement(node);
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
         * Protect existing modal buttons
         */
        protectExistingModalButtons() {
            const modalButtons = document.querySelectorAll('button[hx-get*="modal"], button[hx-post*="modal"], button[hx-target="body"]');
            modalButtons.forEach(button => this.protectButton(button));
            console.log(`🔘 Protected ${modalButtons.length} existing modal buttons`);
        }

        /**
         * Protect modal buttons in a specific element
         */
        protectModalButtonsInElement(element) {
            const modalButtons = element.querySelectorAll ? 
                element.querySelectorAll('button[hx-get*="modal"], button[hx-post*="modal"], button[hx-target="body"]') : [];
            modalButtons.forEach(button => this.protectButton(button));
            
            if (modalButtons.length > 0) {
                console.log(`🔘 Protected ${modalButtons.length} new modal buttons`);
            }
        }

        /**
         * Protect a specific button
         */
        protectButton(button) {
            const buttonId = button.id || this.generateButtonId(button);
            button.id = buttonId;

            // Store button state
            this.buttonStates.set(buttonId, {
                element: button,
                originalHTML: button.innerHTML,
                originalClasses: button.className,
                originalAttributes: this.getButtonAttributes(button),
                isProtected: true,
                lastClicked: null
            });

            // Add to protected set
            this.protectedButtons.add(buttonId);

            // Add click handler for modal operations
            this.setupButtonClickHandler(button, buttonId);
        }

        /**
         * Generate unique button ID
         */
        generateButtonId(button) {
            const timestamp = Date.now();
            const random = Math.random().toString(36).substr(2, 9);
            const context = button.closest('tr')?.dataset?.orderId || 'unknown';
            return `modal-btn-${context}-${timestamp}-${random}`;
        }

        /**
         * Get button attributes
         */
        getButtonAttributes(button) {
            const attributes = {};
            for (const attr of button.attributes) {
                attributes[attr.name] = attr.value;
            }
            return attributes;
        }

        /**
         * Setup button click handler
         */
        setupButtonClickHandler(button, buttonId) {
            button.addEventListener('click', (event) => {
                console.log(`🔘 Modal button clicked: ${buttonId}`);
                
                // Mark modal operation in progress
                this.modalOperationInProgress = true;
                
                // Store click timestamp
                const buttonState = this.buttonStates.get(buttonId);
                if (buttonState) {
                    buttonState.lastClicked = Date.now();
                }

                // Set loading state
                this.setButtonLoadingState(button, buttonId);

                // Clear modal operation flag after delay
                setTimeout(() => {
                    this.modalOperationInProgress = false;
                }, 5000);
            });
        }

        /**
         * Set button loading state
         */
        setButtonLoadingState(button, buttonId) {
            const buttonState = this.buttonStates.get(buttonId);
            if (!buttonState) return;

            // Store current state
            buttonState.beforeLoadingHTML = button.innerHTML;
            buttonState.beforeLoadingDisabled = button.disabled;

            // Set loading state
            button.disabled = true;
            const loadingText = button.getAttribute('data-loading-text') || 'Loading...';
            button.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${loadingText}`;

            // Auto-restore after timeout
            setTimeout(() => {
                this.restoreButtonState(buttonId);
            }, 10000); // 10 second timeout
        }

        /**
         * Restore button state
         */
        restoreButtonState(buttonId) {
            const buttonState = this.buttonStates.get(buttonId);
            if (!buttonState || !buttonState.element) return;

            const button = buttonState.element;
            
            // Restore original state
            button.disabled = buttonState.beforeLoadingDisabled || false;
            button.innerHTML = buttonState.beforeLoadingHTML || buttonState.originalHTML;

            console.log(`🔘 Restored button state: ${buttonId}`);
        }

        /**
         * Setup modal event listeners
         */
        setupModalEventListeners() {
            // Listen for modal open events
            document.addEventListener('htmx:afterSwap', (event) => {
                // If a modal was loaded, restore button states
                if (this.isModalContent(event.detail.target)) {
                    this.restoreAllButtonStates();
                }
            });

            // Listen for modal close events
            document.addEventListener('htmx:afterRequest', (event) => {
                // Restore button states after any HTMX request
                if (this.modalOperationInProgress) {
                    setTimeout(() => {
                        this.restoreAllButtonStates();
                    }, 500);
                }
            });

            // Listen for custom modal events
            document.addEventListener('modalOpened', () => {
                this.restoreAllButtonStates();
            });

            document.addEventListener('modalClosed', () => {
                this.restoreAllButtonStates();
            });
        }

        /**
         * Setup HTMX interception to prevent button replacement
         */
        setupHTMXInterception() {
            // Intercept HTMX before swap to preserve buttons
            document.addEventListener('htmx:beforeSwap', (event) => {
                const target = event.detail.target;
                
                // If swapping table content, preserve button states
                if (target.id === 'tracking-table-content' || target.closest('#tracking-table-content')) {
                    this.preserveButtonStatesBeforeSwap(target);
                }
            });

            // Restore buttons after swap
            document.addEventListener('htmx:afterSwap', (event) => {
                const target = event.detail.target;
                
                // If table content was swapped, restore and protect buttons
                if (target.id === 'tracking-table-content' || target.closest('#tracking-table-content')) {
                    setTimeout(() => {
                        this.restoreButtonStatesAfterSwap(target);
                        this.protectModalButtonsInElement(target);
                    }, 100);
                }
            });
        }

        /**
         * Preserve button states before HTMX swap
         */
        preserveButtonStatesBeforeSwap(target) {
            const buttons = target.querySelectorAll('button[hx-get], button[hx-post]');
            
            buttons.forEach(button => {
                const buttonId = button.id;
                if (buttonId && this.buttonStates.has(buttonId)) {
                    const buttonState = this.buttonStates.get(buttonId);
                    buttonState.preservedForSwap = {
                        html: button.innerHTML,
                        disabled: button.disabled,
                        classes: button.className
                    };
                }
            });

            console.log(`🔘 Preserved ${buttons.length} button states before swap`);
        }

        /**
         * Restore button states after HTMX swap
         */
        restoreButtonStatesAfterSwap(target) {
            const buttons = target.querySelectorAll('button[hx-get], button[hx-post]');
            
            buttons.forEach(button => {
                const buttonId = button.id;
                if (buttonId && this.buttonStates.has(buttonId)) {
                    const buttonState = this.buttonStates.get(buttonId);
                    
                    if (buttonState.preservedForSwap) {
                        // Restore preserved state
                        button.innerHTML = buttonState.preservedForSwap.html;
                        button.disabled = buttonState.preservedForSwap.disabled;
                        button.className = buttonState.preservedForSwap.classes;
                        
                        // Clean up preserved state
                        delete buttonState.preservedForSwap;
                    }
                }
            });

            console.log(`🔘 Restored ${buttons.length} button states after swap`);
        }

        /**
         * Check if content is modal-related
         */
        isModalContent(element) {
            return element.hasAttribute('role') && element.getAttribute('role') === 'dialog' ||
                   element.id && element.id.includes('modal') ||
                   element.querySelector('[role="dialog"]') ||
                   element.querySelector('[id*="modal"]');
        }

        /**
         * Restore all button states
         */
        restoreAllButtonStates() {
            this.buttonStates.forEach((buttonState, buttonId) => {
                if (buttonState.lastClicked && Date.now() - buttonState.lastClicked < 10000) {
                    this.restoreButtonState(buttonId);
                }
            });
        }

        /**
         * Force restore all buttons
         */
        forceRestoreAllButtons() {
            this.buttonStates.forEach((buttonState, buttonId) => {
                this.restoreButtonState(buttonId);
            });
            console.log('🔘 Force restored all button states');
        }

        /**
         * Get button statistics
         */
        getButtonStats() {
            return {
                totalButtons: this.buttonStates.size,
                protectedButtons: this.protectedButtons.size,
                modalOperationInProgress: this.modalOperationInProgress,
                recentlyClicked: Array.from(this.buttonStates.values())
                    .filter(state => state.lastClicked && Date.now() - state.lastClicked < 30000)
                    .length
            };
        }

        /**
         * Debug button states
         */
        debugButtonStates() {
            console.log('🔘 Button States Debug:', {
                buttonStates: this.buttonStates,
                protectedButtons: this.protectedButtons,
                modalOperationInProgress: this.modalOperationInProgress
            });
        }
    }

    // Initialize the modal button persistence system
    window.modalButtonPersistence = new ModalButtonPersistence();

    // Expose utility functions
    window.getModalButtonStats = () => window.modalButtonPersistence.getButtonStats();
    window.forceRestoreModalButtons = () => window.modalButtonPersistence.forceRestoreAllButtons();
    window.debugModalButtons = () => window.modalButtonPersistence.debugButtonStates();

    console.log('✅ Modal Button Persistence loaded and initialized');

})();
