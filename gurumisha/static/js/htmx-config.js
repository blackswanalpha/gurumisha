/**
 * Unified HTMX Configuration and Management for Gurumisha
 * Single source of truth for all HTMX functionality
 * Version 3.0 - Unified and conflict-free
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.unifiedHTMXLoaded) {
        console.log('🔧 Unified HTMX already loaded');
        return;
    }
    window.unifiedHTMXLoaded = true;

    // Clear any existing HTMX configurations
    if (window.htmxConfigLoaded) {
        console.log('🔧 Clearing existing HTMX config');
        delete window.htmxConfigLoaded;
    }

    class UnifiedHTMXManager {
        constructor() {
            this.isInitialized = false;
            this.eventListeners = new Map();
            this.activeRequests = new Set();
            this.preservedElements = new Map();
            this.init();
        }

        init() {
            this.waitForHTMX(() => {
                this.configureHTMX();
                this.setupEventSystem();
                this.setupErrorHandling();
                this.setupComponentIntegration();
                this.isInitialized = true;
                console.log('✅ Unified HTMX Manager v3.0 initialized');
            });
        }

        waitForHTMX(callback) {
            if (typeof htmx !== 'undefined') {
                callback();
            } else {
                setTimeout(() => this.waitForHTMX(callback), 50);
            }
        }

        configureHTMX() {
            // Unified HTMX configuration
            htmx.config.defaultSwapStyle = 'innerHTML';
            htmx.config.defaultSwapDelay = 0;
            htmx.config.defaultSettleDelay = 20;
            htmx.config.includeIndicatorStyles = false;
            htmx.config.requestClass = 'htmx-request';
            htmx.config.addedClass = 'htmx-added';
            htmx.config.settlingClass = 'htmx-settling';
            htmx.config.swappingClass = 'htmx-swapping';
            htmx.config.timeout = 30000; // 30 second timeout
            htmx.config.historyCacheSize = 10;

            // Prefer using response fragments if server responds with a single root node
            htmx.config.useTemplateFragments = true;

            // Expose config loaded flag(s) for validators
            window.htmxConfigLoaded = true;
            window.htmxConfigured = true;

            console.log('🔧 HTMX configuration applied');
        }

        setupEventSystem() {
            // Clear any existing event listeners to prevent conflicts
            this.clearExistingListeners();
            // Global Target safety guard: ensure valid target Element before swapping
            document.addEventListener('htmx:beforeSwap', (e) => {
                try {
                    let t = e.detail && e.detail.target;
                    const resolveFallback = () => {
                        const src = e.detail && e.detail.elt;
                        const fbSel = (src && typeof src.getAttribute === 'function' && src.getAttribute('data-swap-fallback')) || '#resources-content';
                        let fb = null;
                        if (typeof fbSel === 'string') fb = document.querySelector(fbSel);
                        if (!fb) fb = document.getElementById('resources-content');
                        if (!fb) fb = document.body;
                        return fb;
                    };
                    if (!(t instanceof Element) || !t.isConnected || !t.parentNode) {
                        const fb = resolveFallback();
                        if (fb) {
                            e.detail.target = fb;
                            if (!e.detail.swapStyle) e.detail.swapStyle = 'innerHTML';
                            console.warn('HTMX target invalid; using fallback', fb);
                        } else {
                            console.warn('HTMX: no valid target or fallback; canceling swap');
                            e.preventDefault();
                        }
                    }
                } catch (err) {
                    console.warn('HTMX target guard error:', err);
                }
            });


            // Setup unified event handling
            this.setupBeforeRequestHandling();
            this.setupAfterRequestHandling();
            this.setupAfterSwapHandling();
            this.setupResponseErrorHandling();

            console.log('🔧 HTMX event system configured');
        }

        clearExistingListeners() {
            // Remove any existing HTMX event listeners that might conflict
            const existingEvents = ['htmx:beforeRequest', 'htmx:afterRequest', 'htmx:afterSwap', 'htmx:responseError', 'htmx:sendError'];
            existingEvents.forEach(eventName => {
                const listeners = this.eventListeners.get(eventName) || [];
                listeners.forEach(listener => {
                    document.removeEventListener(eventName, listener);
                });
                this.eventListeners.set(eventName, []);
            });
        }

        setupBeforeRequestHandling() {
            const beforeRequestHandler = (event) => {
                const element = event.detail.elt;
                const requestId = this.generateRequestId();

                // Track active request
                this.activeRequests.add(requestId);
                element.setAttribute('data-request-id', requestId);

                // Preserve components before request
                this.preserveComponents(element);

                // Show loading state
                this.showLoadingState(element);

                // Add CSRF token
                this.addCSRFToken(event);

                console.log('🔧 HTMX request started:', requestId);
            };

            document.addEventListener('htmx:beforeRequest', beforeRequestHandler);
            this.eventListeners.set('htmx:beforeRequest', [beforeRequestHandler]);
        }

        setupAfterRequestHandling() {
            const afterRequestHandler = (event) => {
                const element = event.detail.elt;
                const requestId = element.getAttribute('data-request-id');

                // Remove from active requests
                if (requestId) {
                    this.activeRequests.delete(requestId);
                    element.removeAttribute('data-request-id');
                }

                // Hide loading state
                this.hideLoadingState(element);

                console.log('🔧 HTMX request completed:', requestId);
            };

            document.addEventListener('htmx:afterRequest', afterRequestHandler);
            this.eventListeners.set('htmx:afterRequest', [afterRequestHandler]);
        }

        setupAfterSwapHandling() {
            const afterSwapHandler = (event) => {
                const target = event.detail.target;

                // Restore preserved components
                this.restoreComponents(target);

                // Trigger component hydration
                this.hydrateComponents(target);

                // Setup new event listeners

            // (Target safety guard installed globally during setupEventSystem)

                this.setupDynamicEventListeners(target);

                console.log('🔧 HTMX swap completed, components hydrated');
            };

            document.addEventListener('htmx:afterSwap', afterSwapHandler);
            this.eventListeners.set('htmx:afterSwap', [afterSwapHandler]);
        }

        setupResponseErrorHandling() {
            const errorHandler = (event) => {
                const element = event.detail.elt;
                const requestId = element.getAttribute('data-request-id');

                // Clean up request tracking
                if (requestId) {
                    this.activeRequests.delete(requestId);
                    element.removeAttribute('data-request-id');
                }

                // Hide loading state
                this.hideLoadingState(element);

                // Show error message
                this.showErrorMessage(event.detail.xhr);

                console.error('🔧 HTMX request error:', event.detail);
            };

            document.addEventListener('htmx:responseError', errorHandler);
            document.addEventListener('htmx:sendError', errorHandler);
            this.eventListeners.set('htmx:responseError', [errorHandler]);
        }

        setupErrorHandling() {
            // Global error boundary for HTMX operations
            window.addEventListener('error', (event) => {
                if (event.error && event.error.message && event.error.message.includes('htmx')) {
                    console.error('🔧 HTMX Error caught:', event.error);
                    this.handleHTMXError(event.error);
                }
            });
        }

        setupComponentIntegration() {
            // Integration with other systems
            this.setupModalIntegration();
            this.setupFormIntegration();
            this.setupButtonIntegration();
        }

        // Component preservation and restoration
        preserveComponents(element) {
            const target = element.getAttribute('hx-target');
            if (!target) return;

            const targetElement = document.querySelector(target);
            if (!targetElement) return;

            // Preserve Alpine.js components
            const alpineElements = targetElement.querySelectorAll('[x-data]');
            alpineElements.forEach(alpineEl => {
                if (alpineEl.id) {
                    this.preservedElements.set(alpineEl.id, {
                        type: 'alpine',
                        data: alpineEl._x_dataStack ? [...alpineEl._x_dataStack] : null,
                        attributes: this.getElementAttributes(alpineEl)
                    });
                }
            });

            // Preserve buttons and interactive elements
            const buttons = targetElement.querySelectorAll('button[id], [data-preserve="true"]');
            buttons.forEach(button => {
                if (button.id) {
                    this.preservedElements.set(button.id, {
                        type: 'button',
                        innerHTML: button.innerHTML,
                        className: button.className,
                        disabled: button.disabled,
                        attributes: this.getElementAttributes(button)
                    });
                }
            });
        }

        restoreComponents(targetElement) {
            // Restore preserved components
            this.preservedElements.forEach((preserved, elementId) => {
                const element = targetElement.querySelector(`#${elementId}`);
                if (element && preserved.type === 'button') {
                    // Only restore if not intentionally updated
                    if (!element.hasAttribute('data-updated')) {
                        element.innerHTML = preserved.innerHTML;
                        element.className = preserved.className;
                        element.disabled = preserved.disabled;
                    }
                }
            });

            // Clear preserved elements
            this.preservedElements.clear();
        }

        hydrateComponents(targetElement) {
            // If unified hydration manager is already listening to HTMX events,
            // avoid double-hydration from here.
            if (window.unifiedHydrationLoaded) {
                return;
            }

            // Delegate to unified hydration manager if available
            if (window.hydrationManager && window.hydrationManager.hydrateElement) {
                window.hydrationManager.hydrateElement(targetElement);
            } else {
                // Fallback hydration
                this.fallbackHydration(targetElement);
            }
        }

        fallbackHydration(targetElement) {
            // Basic Alpine.js hydration
            if (typeof Alpine !== 'undefined') {
                const alpineElements = targetElement.querySelectorAll('[x-data]');
                alpineElements.forEach(element => {
                    if (!element._x_dataStack || element._x_dataStack.length === 0) {
                        try {
                            Alpine.initTree(element);
                        } catch (error) {
                            console.warn('🔧 Alpine hydration failed:', error);
                        }
                    }
                });
            }
        }

        // Utility methods
        generateRequestId() {
            return 'htmx_' + Date.now() + '_' + Math.random().toString(36).slice(2, 11);
        }

        getElementAttributes(element) {
            const attributes = {};
            Array.from(element.attributes).forEach(attr => {
                attributes[attr.name] = attr.value;
            });
            return attributes;
        }

        showLoadingState(element) {
            element.classList.add('htmx-loading');
            const indicator = element.querySelector('.loading-indicator');
            if (indicator) {
                indicator.style.display = 'block';
            }
        }

        hideLoadingState(element) {
            element.classList.remove('htmx-loading');
            const indicator = element.querySelector('.loading-indicator');
            if (indicator) {
                indicator.style.display = 'none';
            }
        }

        addCSRFToken(event) {
            const token = this.getCSRFToken();
            if (token && event.detail.xhr) {
                event.detail.xhr.setRequestHeader('X-CSRFToken', token);
            }
        }

        getCSRFToken() {
            const metaToken = document.querySelector('meta[name="csrf-token"]');
            if (metaToken) return metaToken.getAttribute('content');

            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrftoken') return value;
            }
            return '';
        }

        showErrorMessage(xhr) {
            if (window.toastManager) {
                window.toastManager.show('Request failed. Please try again.', 'error');
            } else {
                console.error('HTMX Request failed:', xhr.status, xhr.statusText);
            }
        }

        handleHTMXError(error) {
            console.error('🔧 HTMX Error:', error);
            if (window.toastManager) {
                window.toastManager.show('An error occurred. Please refresh the page.', 'error');
            }
        }

        setupDynamicEventListeners(targetElement) {
            // Setup event listeners for dynamically added content
            const buttons = targetElement.querySelectorAll('button[hx-get], button[hx-post]');
            buttons.forEach(button => {
                if (!button.hasAttribute('data-htmx-initialized')) {
                    button.setAttribute('data-htmx-initialized', 'true');
                    // Additional button setup if needed
                }
            });
        }

        setupModalIntegration() {
            // Integration with modal system
            document.addEventListener('htmx:afterSwap', (event) => {
                const target = event.detail.target;
                const modals = target.querySelectorAll('[id*="modal"]');
                modals.forEach(modal => {
                    if (window.modalManager && window.modalManager.initializeModal) {
                        window.modalManager.initializeModal(modal, modal.id);
                    }
                });
            });
        }

        setupFormIntegration() {
            // Integration with form system
            document.addEventListener('htmx:afterSwap', (event) => {
                const target = event.detail.target;
                const forms = target.querySelectorAll('form');
                forms.forEach(form => {
                    if (window.formValidator && window.formValidator.initializeForm) {
                        window.formValidator.initializeForm(form);
                    }
                });
            });
        }

        setupButtonIntegration() {
            // Integration with button persistence system
            document.addEventListener('htmx:beforeSwap', (event) => {
                try {
                    const tgt = event && event.detail ? event.detail.target : null;
                    if (window.buttonPersistenceManager && tgt instanceof Element) {
                        window.buttonPersistenceManager.preserveButtons(tgt);
                    }
                } catch (_) { /* no-op */ }
            });
        }
    }

    // Initialize the unified HTMX manager
    const htmxManager = new UnifiedHTMXManager();

    // Expose globally for other scripts
    window.unifiedHTMXManager = htmxManager;

    // Backward compatibility functions
    window.htmxModalRequest = function(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            target: 'this',
            swap: 'none',
            headers: {
                'X-CSRFToken': htmxManager.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest',
                ...options.headers
            }
        };

        return htmx.ajax(defaultOptions.method, url, {
            ...defaultOptions,
            ...options
        });
    };

    console.log('✅ Unified HTMX Manager loaded and active');

    // Note: keep htmxConfigLoaded for validators and health checks



    // Backward compatibility functions (delegating to unified manager)
    window.preserveButtonStates = function(triggerElement) {
        if (htmxManager) {
            htmxManager.preserveComponents(triggerElement);
        }
    };

    window.restoreButtonStates = function(targetElement) {
        if (htmxManager) {
            htmxManager.restoreComponents(targetElement);
        }
    };

    window.hydrateAlpineComponents = function(targetElement) {
        if (htmxManager) {
            htmxManager.hydrateComponents(targetElement);
        }
    };

    // Global fallback for old references
    window.waitForHTMX = window.waitForHTMX || function(cb){
        if (typeof htmx !== 'undefined') { if (typeof cb === 'function') cb(); }
        else { setTimeout(() => window.waitForHTMX(cb), 50); }
    };


    // Backward compatibility for event listeners
    window.reinitializeEventListeners = function(targetElement) {
        if (htmxManager) {
            htmxManager.setupDynamicEventListeners(targetElement);
        }
    };

})();
