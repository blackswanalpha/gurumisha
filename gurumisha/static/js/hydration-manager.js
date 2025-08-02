/**
 * Unified Hydration Manager for Gurumisha
 * Handles proper re-initialization of Alpine.js and other JavaScript components
 * after HTMX content swaps and dynamic updates
 * Version 3.0 - Consolidated and optimized
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.hydrationManagerLoaded) {
        console.log('Hydration manager already loaded');
        return;
    }
    window.hydrationManagerLoaded = true;

    class HydrationManager {
        constructor() {
            this.observers = new Map();
            this.componentRegistry = new Map();
            this.htmxProcessThrottle = new Map();
            this.alpineInitQueue = new Set(); // Track Alpine components being initialized
            this.isAlpineReady = false;
            this.pendingHydrations = [];
            this.init();
        }

        init() {
            console.log('🔄 Unified Hydration Manager v3.0 initialized');

            // Wait for Alpine.js to be ready first
            this.waitForAlpine(() => {
                this.isAlpineReady = true;
                console.log('🏔️ Alpine.js ready, setting up hydration system');

                // Setup all systems after Alpine is ready
                this.setupHTMXListeners();
                this.setupDOMObservers();
                this.registerDefaultComponents();
                this.processPendingHydrations();
            });
        }

        /**
         * Wait for Alpine.js to be available
         */
        waitForAlpine(callback) {
            if (typeof Alpine !== 'undefined' && Alpine.version) {
                callback();
            } else {
                setTimeout(() => this.waitForAlpine(callback), 50);
            }
        }

        /**
         * Process any hydrations that were queued before Alpine was ready
         */
        processPendingHydrations() {
            if (this.pendingHydrations.length > 0) {
                console.log(`🔄 Processing ${this.pendingHydrations.length} pending hydrations`);
                this.pendingHydrations.forEach(element => {
                    this.hydrateElement(element);
                });
                this.pendingHydrations = [];
            }
        }

        /**
         * Register a component for automatic hydration
         */
        registerComponent(selector, initFunction) {
            this.componentRegistry.set(selector, initFunction);
            console.log(`📝 Registered component: ${selector}`);
        }

        /**
         * Setup HTMX event listeners for hydration (unified approach)
         */
        setupHTMXListeners() {
            // Prevent duplicate listeners
            if (this.htmxListenersSetup) return;
            this.htmxListenersSetup = true;

            // Primary hydration trigger - after content swap
            document.addEventListener('htmx:afterSwap', (event) => {
                console.log('🔄 HTMX afterSwap - Starting unified hydration');
                this.hydrateElement(event.detail.target);
            });

            // Secondary hydration trigger - after content load
            document.addEventListener('htmx:load', (event) => {
                console.log('🔄 HTMX load - Starting unified hydration');
                this.hydrateElement(event.detail.elt);
            });

            // Final hydration check after all animations complete
            document.addEventListener('htmx:afterSettle', (event) => {
                console.log('🔄 HTMX afterSettle - Final hydration verification');
                this.finalizeHydration(event.detail.target);
            });

            // Out-of-band swap handling
            document.addEventListener('htmx:oobAfterSwap', (event) => {
                console.log('🔄 HTMX OOB swap - Hydrating out-of-band content');
                this.hydrateElement(event.detail.target);
            });

            // Error handling with recovery
            document.addEventListener('htmx:responseError', (event) => {
                console.warn('⚠️ HTMX Response Error - Attempting hydration recovery:', event.detail);
                this.handleHydrationError(event.detail);
            });

            console.log('✅ HTMX listeners setup complete');
        }

        /**
         * Setup DOM observers for dynamic content changes
         */
        setupDOMObservers() {
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    this.setupDOMObservers();
                });
                return;
            }

            // Setup mutation observer for non-HTMX dynamic content
            if (document.body && !this.observers.has('mutation')) {
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        if (mutation.type === 'childList') {
                            mutation.addedNodes.forEach((node) => {
                                if (node.nodeType === Node.ELEMENT_NODE &&
                                    !node.hasAttribute('hx-swap-oob') &&
                                    !node.closest('[hx-target]')) {
                                    // Only hydrate non-HTMX managed content
                                    this.hydrateElement(node);
                                }
                            });
                        }
                    });
                });

                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });

                this.observers.set('mutation', observer);
                console.log('✅ DOM mutation observer setup complete');
            }
        }

        /**
         * Setup Alpine.js specific listeners
         */
        setupAlpineListeners() {
            // Wait for Alpine.js to be available
            const waitForAlpine = () => {
                if (typeof Alpine !== 'undefined') {
                    console.log('🏔️ Alpine.js detected - Setting up hydration hooks');
                    this.setupAlpineHooks();
                } else {
                    setTimeout(waitForAlpine, 100);
                }
            };
            waitForAlpine();
        }

        /**
         * Setup Alpine.js hooks for better hydration
         */
        setupAlpineHooks() {
            // Hook into Alpine's component initialization
            if (Alpine && Alpine.plugin) {
                Alpine.plugin((Alpine) => {
                    Alpine.directive('hydrate', () => {
                        // Custom hydration directive
                        console.log('🏔️ Alpine hydrate directive triggered');
                    });
                });
            }
        }

        /**
         * Register default components that need hydration
         */
        registerDefaultComponents() {
            // Price formatters
            this.registerComponent('.price-format', (element) => {
                if (typeof formatPrice === 'function') {
                    element.addEventListener('input', (e) => formatPrice(e.target));
                }
            });

            // Toast triggers
            this.registerComponent('[data-toast]', (element) => {
                element.addEventListener('click', () => {
                    const message = element.dataset.toastMessage;
                    const type = element.dataset.toastType || 'info';
                    if (window.showToast && message) {
                        window.showToast(message, type);
                    }
                });
            });

            // Lazy loading images
            this.registerComponent('[data-lazy]', (element) => {
                if ('IntersectionObserver' in window) {
                    const imageObserver = new IntersectionObserver((entries) => {
                        entries.forEach(entry => {
                            if (entry.isIntersecting) {
                                const img = entry.target;
                                img.src = img.dataset.lazy;
                                img.classList.remove('lazy');
                                imageObserver.unobserve(img);
                            }
                        });
                    });
                    imageObserver.observe(element);
                }
            });

            // Form validation
            this.registerComponent('form[data-validate]', (element) => {
                element.addEventListener('submit', (e) => {
                    if (!this.validateForm(element)) {
                        e.preventDefault();
                    }
                });
            });
        }

        /**
         * Hydrate a specific element and its children
         */
        hydrateElement(element) {
            if (!element || element.nodeType !== Node.ELEMENT_NODE) {
                return;
            }

            console.log('💧 Hydrating element:', element.tagName, element.id || element.className);

            // Hydrate Alpine.js components
            this.hydrateAlpineComponents(element);

            // Hydrate registered components
            this.hydrateRegisteredComponents(element);

            // Hydrate specific component types
            this.hydrateSpecificComponents(element);
        }

        /**
         * Hydrate Alpine.js components in element (optimized)
         */
        hydrateAlpineComponents(element) {
            if (!this.isAlpineReady) {
                console.log('🏔️ Alpine.js not ready, queuing hydration');
                this.pendingHydrations.push(element);
                return;
            }

            // Find all Alpine components
            const alpineElements = [];

            // Include the element itself if it has x-data
            if (element.hasAttribute && element.hasAttribute('x-data')) {
                alpineElements.push(element);
            }

            // Add child Alpine elements
            element.querySelectorAll('[x-data]').forEach(el => {
                alpineElements.push(el);
            });

            // Initialize each Alpine element
            alpineElements.forEach(alpineElement => {
                this.initializeAlpineElement(alpineElement);
            });
        }

        /**
         * Initialize a single Alpine.js element (improved with better error handling)
         */
        initializeAlpineElement(element) {
            // Prevent duplicate initialization
            const elementId = element.id || `alpine_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

            if (this.alpineInitQueue.has(elementId)) {
                console.log('🏔️ Alpine element already in init queue, skipping');
                return;
            }

            try {
                // Check if already initialized by Alpine
                if (element._x_dataStack && element._x_dataStack.length > 0) {
                    console.log('🏔️ Alpine element already initialized, skipping');
                    return;
                }

                // Pre-validate Alpine.js expressions to prevent errors
                if (!this.validateAlpineExpressions(element)) {
                    console.warn('⚠️ Alpine element has invalid expressions, skipping initialization');
                    return;
                }

                this.alpineInitQueue.add(elementId);
                console.log('🏔️ Initializing Alpine element:', element.tagName, element.className);

                // Initialize with Alpine
                Alpine.initTree(element);

                // Handle modal-specific initialization
                if (element.id && element.id.includes('modal')) {
                    this.initializeModalAlpine(element);
                }

                // Remove from queue after successful initialization
                setTimeout(() => {
                    this.alpineInitQueue.delete(elementId);
                }, 100);

            } catch (error) {
                console.error('❌ Error initializing Alpine element:', error);
                this.alpineInitQueue.delete(elementId);

                // Try to recover by removing problematic attributes
                this.recoverFromAlpineError(element, error);
            }
        }

        /**
         * Validate Alpine.js expressions before initialization
         */
        validateAlpineExpressions(element) {
            const alpineAttributes = [
                'x-data', 'x-show', 'x-if', 'x-for', 'x-text', 'x-html',
                'x-bind', 'x-on', '@click', '@submit', '@change'
            ];

            try {
                // Check for common problematic patterns
                for (const attr of alpineAttributes) {
                    const value = element.getAttribute(attr);
                    if (value && value.includes('isSubmitting') && !value.includes('isSubmitting:')) {
                        // Check if element or parent has isSubmitting in x-data
                        const hasIsSubmitting = this.checkForIsSubmittingScope(element);
                        if (!hasIsSubmitting) {
                            console.warn(`⚠️ Element uses 'isSubmitting' but no scope found:`, element);
                            return false;
                        }
                    }
                }
                return true;
            } catch (error) {
                console.warn('⚠️ Error validating Alpine expressions:', error);
                return false;
            }
        }

        /**
         * Check if element has access to isSubmitting variable
         */
        checkForIsSubmittingScope(element) {
            let current = element;
            while (current && current !== document.body) {
                const xData = current.getAttribute('x-data');
                if (xData && xData.includes('isSubmitting')) {
                    return true;
                }
                current = current.parentElement;
            }
            return false;
        }

        /**
         * Attempt to recover from Alpine.js initialization errors
         */
        recoverFromAlpineError(element, error) {
            try {
                // If error mentions isSubmitting, try to add it to the element
                if (error.message && error.message.includes('isSubmitting')) {
                    console.log('🔧 Attempting to recover from isSubmitting error');

                    // Add isSubmitting to x-data if not present
                    const xData = element.getAttribute('x-data');
                    if (xData && !xData.includes('isSubmitting')) {
                        const newXData = xData.replace('{', '{ isSubmitting: false, ');
                        element.setAttribute('x-data', newXData);
                        console.log('🔧 Added isSubmitting to x-data, retrying initialization');

                        // Retry initialization
                        setTimeout(() => {
                            Alpine.initTree(element);
                        }, 50);
                    }
                }
            } catch (recoveryError) {
                console.warn('⚠️ Recovery attempt failed:', recoveryError);
            }
        }

        /**
         * Special handling for modal Alpine components
         */
        initializeModalAlpine(modalElement) {
            setTimeout(() => {
                try {
                    const alpineData = Alpine.$data(modalElement);
                    if (alpineData) {
                        // Auto-show modal if it has the attribute
                        if (modalElement.hasAttribute('data-auto-show') && typeof alpineData.show !== 'undefined') {
                            alpineData.show = true;
                        }

                        // Initialize modal-specific functions
                        if (typeof alpineData.initModal === 'function') {
                            alpineData.initModal();
                        }
                    }
                } catch (error) {
                    console.warn('⚠️ Modal Alpine initialization warning:', error);
                }
            }, 50);
        }

        /**
         * Hydrate registered components
         */
        hydrateRegisteredComponents(element) {
            this.componentRegistry.forEach((initFunction, selector) => {
                const components = element.querySelectorAll(selector);
                
                // Include the element itself if it matches
                if (element.matches && element.matches(selector)) {
                    initFunction(element);
                }

                // Initialize child components
                components.forEach(component => {
                    try {
                        initFunction(component);
                    } catch (error) {
                        console.error(`❌ Error hydrating component ${selector}:`, error);
                    }
                });
            });
        }

        /**
         * Hydrate specific component types
         */
        hydrateSpecificComponents(element) {
            // Throttle HTMX processing to prevent excessive requests
            const elementId = element.id || element.tagName + '_' + Date.now();
            const now = Date.now();
            const lastProcessed = this.htmxProcessThrottle.get(elementId);

            // Only process if it hasn't been processed in the last 100ms
            if (!lastProcessed || now - lastProcessed > 100) {
                // Re-initialize HTMX for new elements
                if (typeof htmx !== 'undefined') {
                    htmx.process(element);
                }
                this.htmxProcessThrottle.set(elementId, now);
            }

            // Re-initialize any custom components
            this.initializeCustomComponents(element);
        }

        /**
         * Initialize custom components
         */
        initializeCustomComponents(element) {
            // Countdown timers
            const countdowns = element.querySelectorAll('[data-countdown-end]');
            countdowns.forEach(countdown => {
                if (typeof initializeCountdown === 'function') {
                    initializeCountdown(countdown);
                }
            });

            // Image galleries
            const galleries = element.querySelectorAll('.enhanced-image-gallery');
            galleries.forEach(gallery => {
                if (window.galleryImages) {
                    // Re-initialize gallery with current images
                    const alpineData = Alpine.$data(gallery);
                    if (alpineData && alpineData.init) {
                        alpineData.init();
                    }
                }
            });

            // Hot deals components
            const hotDeals = element.querySelectorAll('[data-hot-deal]');
            hotDeals.forEach(hotDeal => {
                if (typeof initializeHotDeal === 'function') {
                    initializeHotDeal(hotDeal);
                }
            });

            // Compare buttons
            const compareButtons = element.querySelectorAll('[data-compare]');
            compareButtons.forEach(button => {
                if (typeof initializeCompareButton === 'function') {
                    initializeCompareButton(button);
                }
            });

            // Notification badges
            const badges = element.querySelectorAll('[data-notification-badge]');
            badges.forEach(badge => {
                if (typeof updateNotificationBadge === 'function') {
                    updateNotificationBadge(badge);
                }
            });

            // Welcome popups
            const popups = element.querySelectorAll('[data-welcome-popup]');
            popups.forEach(popup => {
                if (typeof initializeWelcomePopup === 'function') {
                    initializeWelcomePopup(popup);
                }
            });
        }

        /**
         * Finalize hydration after all processes complete
         */
        finalizeHydration(element) {
            // Trigger any final initialization events
            const event = new CustomEvent('hydration:complete', {
                detail: { element: element },
                bubbles: true
            });
            element.dispatchEvent(event);

            // Log successful hydration
            console.log('✅ Hydration complete for:', element.tagName, element.id || element.className);

            // Update any global state that depends on hydrated content
            this.updateGlobalState(element);
        }

        /**
         * Update global state after hydration
         */
        updateGlobalState(element) {
            // Update notification counts
            if (typeof updateNotificationCounts === 'function') {
                updateNotificationCounts();
            }

            // Update compare widget if compare buttons were hydrated
            if (element.querySelector('[data-compare]') && typeof updateCompareWidget === 'function') {
                updateCompareWidget();
            }

            // Update any other global components that might be affected
            this.triggerGlobalUpdates(element);
        }

        /**
         * Trigger global updates after hydration
         */
        triggerGlobalUpdates(element) {
            // Dispatch global hydration event
            const globalEvent = new CustomEvent('global:hydration:complete', {
                detail: { element: element },
                bubbles: true
            });
            document.dispatchEvent(globalEvent);
        }

        /**
         * Handle hydration errors
         */
        handleHydrationError(detail) {
            console.error('❌ Hydration error:', detail);
            
            // Try to recover by re-initializing the target element
            if (detail.target) {
                setTimeout(() => {
                    this.hydrateElement(detail.target);
                }, 1000);
            }
        }

        /**
         * Basic form validation
         */
        validateForm(form) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('border-red-500');
                    isValid = false;
                } else {
                    field.classList.remove('border-red-500');
                }
            });

            return isValid;
        }

        /**
         * Manually trigger hydration for an element
         */
        triggerHydration(element) {
            this.hydrateElement(element);
        }

        /**
         * Cleanup observers
         */
        destroy() {
            this.observers.forEach(observer => {
                if (observer.disconnect) {
                    observer.disconnect();
                }
            });
            this.observers.clear();
            this.componentRegistry.clear();
        }
    }

    // Initialize hydration manager
    const hydrationManager = new HydrationManager();

    // Expose globally
    window.hydrationManager = hydrationManager;
    window.triggerHydration = (element) => hydrationManager.triggerHydration(element);

    console.log('✅ Hydration Manager loaded and active');

})();
