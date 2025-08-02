/**
 * Button Disappearing Fix for Gurumisha
 * Comprehensive solution to prevent buttons from disappearing during any operation
 * Version 1.0 - Complete button protection system
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.buttonDisappearingFixLoaded) {
        console.log('Button Disappearing Fix already loaded');
        return;
    }
    window.buttonDisappearingFixLoaded = true;

    class ButtonDisappearingFix {
        constructor() {
            this.protectedButtons = new Map();
            this.operationQueue = [];
            this.isProcessingQueue = false;
            this.init();
        }

        init() {
            console.log('🛡️ Button Disappearing Fix v1.0 initialized');
            this.setupGlobalProtection();
            this.setupHTMXProtection();
            this.setupStatsUpdateProtection();
            this.setupErrorRecovery();
        }

        /**
         * Setup global button protection
         */
        setupGlobalProtection() {
            // Protect all buttons on page load
            this.protectAllButtons();

            // Watch for new buttons
            const observer = new MutationObserver((mutations) => {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.protectButtonsInElement(node);
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
         * Protect all existing buttons
         */
        protectAllButtons() {
            const buttons = document.querySelectorAll('button');
            buttons.forEach(button => this.protectButton(button));
            console.log(`🛡️ Protected ${buttons.length} buttons globally`);
        }

        /**
         * Protect buttons in a specific element
         */
        protectButtonsInElement(element) {
            const buttons = element.querySelectorAll ? element.querySelectorAll('button') : [];
            buttons.forEach(button => this.protectButton(button));
        }

        /**
         * Protect a specific button
         */
        protectButton(button) {
            if (!button.id) {
                button.id = this.generateButtonId(button);
            }

            const buttonId = button.id;
            
            // Skip if already protected
            if (this.protectedButtons.has(buttonId)) {
                return;
            }

            // Store button protection data
            this.protectedButtons.set(buttonId, {
                element: button,
                originalHTML: button.innerHTML,
                originalClasses: button.className,
                originalDisabled: button.disabled,
                originalStyle: button.style.cssText,
                isProtected: true,
                lastSeen: Date.now()
            });

            // Add protection attributes
            button.setAttribute('data-protected', 'true');
            button.setAttribute('data-protection-id', buttonId);
        }

        /**
         * Generate unique button ID
         */
        generateButtonId(button) {
            const timestamp = Date.now();
            const random = Math.random().toString(36).substr(2, 9);
            const context = button.textContent?.trim().replace(/\s+/g, '-').toLowerCase() || 'button';
            return `protected-btn-${context}-${timestamp}-${random}`;
        }

        /**
         * Setup HTMX protection
         */
        setupHTMXProtection() {
            // Before HTMX swap - preserve button states
            document.addEventListener('htmx:beforeSwap', (event) => {
                this.preserveButtonStatesBeforeSwap(event.detail.target);
            });

            // After HTMX swap - restore and protect buttons
            document.addEventListener('htmx:afterSwap', (event) => {
                setTimeout(() => {
                    this.restoreButtonStatesAfterSwap(event.detail.target);
                    this.protectButtonsInElement(event.detail.target);
                }, 50);
            });

            // Before HTMX request - mark button as busy
            document.addEventListener('htmx:beforeRequest', (event) => {
                const button = event.detail.elt;
                if (button && button.tagName === 'BUTTON') {
                    this.setButtonBusyState(button);
                }
            });

            // After HTMX request - restore button state
            document.addEventListener('htmx:afterRequest', (event) => {
                const button = event.detail.elt;
                if (button && button.tagName === 'BUTTON') {
                    this.restoreButtonFromBusyState(button);
                }
            });
        }

        /**
         * Setup stats update protection
         */
        setupStatsUpdateProtection() {
            // Intercept stats updates to prevent conflicts
            const originalFetch = window.fetch;
            window.fetch = (...args) => {
                const url = args[0];
                
                // Check if this is a stats update request
                if (typeof url === 'string' && url.includes('admin-quick-actions')) {
                    // Check if buttons are busy
                    const busyButtons = document.querySelectorAll('button[aria-busy="true"]');
                    if (busyButtons.length > 0) {
                        console.log('🛡️ Delaying stats update - buttons are busy');
                        return new Promise(resolve => {
                            setTimeout(() => {
                                resolve(originalFetch.apply(this, args));
                            }, 2000);
                        });
                    }
                }
                
                return originalFetch.apply(this, args);
            };
        }

        /**
         * Preserve button states before HTMX swap
         */
        preserveButtonStatesBeforeSwap(target) {
            const buttons = target.querySelectorAll('button[data-protected="true"]');
            
            buttons.forEach(button => {
                const buttonId = button.getAttribute('data-protection-id');
                if (buttonId && this.protectedButtons.has(buttonId)) {
                    const protection = this.protectedButtons.get(buttonId);
                    protection.preSwapState = {
                        html: button.innerHTML,
                        classes: button.className,
                        disabled: button.disabled,
                        style: button.style.cssText
                    };
                }
            });
        }

        /**
         * Restore button states after HTMX swap
         */
        restoreButtonStatesAfterSwap(target) {
            const buttons = target.querySelectorAll('button[data-protected="true"]');
            
            buttons.forEach(button => {
                const buttonId = button.getAttribute('data-protection-id');
                if (buttonId && this.protectedButtons.has(buttonId)) {
                    const protection = this.protectedButtons.get(buttonId);
                    
                    if (protection.preSwapState) {
                        // Restore pre-swap state
                        button.innerHTML = protection.preSwapState.html;
                        button.className = protection.preSwapState.classes;
                        button.disabled = protection.preSwapState.disabled;
                        button.style.cssText = protection.preSwapState.style;
                        
                        // Clean up pre-swap state
                        delete protection.preSwapState;
                    }
                }
            });
        }

        /**
         * Set button busy state
         */
        setButtonBusyState(button) {
            const buttonId = button.getAttribute('data-protection-id');
            if (buttonId && this.protectedButtons.has(buttonId)) {
                const protection = this.protectedButtons.get(buttonId);
                
                // Store current state
                protection.busyState = {
                    html: button.innerHTML,
                    disabled: button.disabled
                };
                
                // Set busy state
                button.setAttribute('aria-busy', 'true');
                button.disabled = true;
                
                // Add loading indicator if not present
                if (!button.innerHTML.includes('fa-spinner')) {
                    const loadingText = button.getAttribute('data-loading-text') || 'Loading...';
                    button.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${loadingText}`;
                }
            }
        }

        /**
         * Restore button from busy state
         */
        restoreButtonFromBusyState(button) {
            const buttonId = button.getAttribute('data-protection-id');
            if (buttonId && this.protectedButtons.has(buttonId)) {
                const protection = this.protectedButtons.get(buttonId);
                
                if (protection.busyState) {
                    // Restore original state
                    button.innerHTML = protection.busyState.html;
                    button.disabled = protection.busyState.disabled;
                    button.removeAttribute('aria-busy');
                    
                    // Clean up busy state
                    delete protection.busyState;
                }
            }
        }

        /**
         * Setup error recovery
         */
        setupErrorRecovery() {
            // Periodic button health check
            setInterval(() => {
                this.performButtonHealthCheck();
            }, 30000); // Every 30 seconds

            // Recovery on page visibility change
            document.addEventListener('visibilitychange', () => {
                if (!document.hidden) {
                    this.performButtonHealthCheck();
                }
            });
        }

        /**
         * Perform button health check
         */
        performButtonHealthCheck() {
            let recoveredButtons = 0;
            
            this.protectedButtons.forEach((protection, buttonId) => {
                const button = document.getElementById(buttonId);
                
                if (!button) {
                    // Button disappeared, try to recover
                    console.warn(`🛡️ Button ${buttonId} disappeared, attempting recovery`);
                    this.protectedButtons.delete(buttonId);
                } else if (button.innerHTML === '' || button.style.display === 'none') {
                    // Button is broken, restore it
                    console.log(`🛡️ Recovering broken button: ${buttonId}`);
                    button.innerHTML = protection.originalHTML;
                    button.className = protection.originalClasses;
                    button.disabled = protection.originalDisabled;
                    button.style.cssText = protection.originalStyle;
                    recoveredButtons++;
                }
            });
            
            if (recoveredButtons > 0) {
                console.log(`🛡️ Recovered ${recoveredButtons} buttons`);
            }
        }

        /**
         * Force restore all buttons
         */
        forceRestoreAllButtons() {
            let restoredCount = 0;
            
            this.protectedButtons.forEach((protection, buttonId) => {
                const button = document.getElementById(buttonId);
                if (button) {
                    button.innerHTML = protection.originalHTML;
                    button.className = protection.originalClasses;
                    button.disabled = protection.originalDisabled;
                    button.style.cssText = protection.originalStyle;
                    button.removeAttribute('aria-busy');
                    restoredCount++;
                }
            });
            
            console.log(`🛡️ Force restored ${restoredCount} buttons`);
            return restoredCount;
        }

        /**
         * Get protection statistics
         */
        getProtectionStats() {
            const totalProtected = this.protectedButtons.size;
            const visibleButtons = document.querySelectorAll('button[data-protected="true"]').length;
            const busyButtons = document.querySelectorAll('button[aria-busy="true"]').length;
            
            return {
                totalProtected,
                visibleButtons,
                busyButtons,
                healthRatio: visibleButtons / totalProtected || 0
            };
        }
    }

    // Initialize the button disappearing fix
    window.buttonDisappearingFix = new ButtonDisappearingFix();

    // Expose utility functions
    window.forceRestoreAllButtons = () => window.buttonDisappearingFix.forceRestoreAllButtons();
    window.getButtonProtectionStats = () => window.buttonDisappearingFix.getProtectionStats();
    window.performButtonHealthCheck = () => window.buttonDisappearingFix.performButtonHealthCheck();

    console.log('✅ Button Disappearing Fix loaded and initialized');

})();
