/**
 * HTMX Configuration and Error Handling for Gurumisha
 * Provides enhanced HTMX functionality with proper error handling,
 * loading states, and integration with the hydration system
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.htmxConfigLoaded) {
        console.log('HTMX config already loaded');
        return;
    }
    window.htmxConfigLoaded = true;

    // Wait for HTMX to be available
    const waitForHTMX = () => {
        if (typeof htmx !== 'undefined') {
            console.log('🔧 HTMX detected - Setting up configuration');
            initializeHTMXConfig();
        } else {
            setTimeout(waitForHTMX, 100);
        }
    };

    function initializeHTMXConfig() {
        // Configure HTMX defaults
        htmx.config.defaultSwapStyle = 'innerHTML';
        htmx.config.defaultSwapDelay = 0;
        htmx.config.defaultSettleDelay = 20;
        htmx.config.includeIndicatorStyles = false; // We'll handle our own loading styles
        htmx.config.requestClass = 'htmx-request';
        htmx.config.addedClass = 'htmx-added';
        htmx.config.settlingClass = 'htmx-settling';
        htmx.config.swappingClass = 'htmx-swapping';

        // Setup global HTMX event listeners
        setupHTMXEventListeners();

        // Setup CSRF token handling
        setupCSRFHandling();

        // Setup loading indicators
        setupLoadingIndicators();

        // Setup error handling
        setupErrorHandling();

        // Setup OOB swap handling
        setupOOBSwapHandling();

        console.log('✅ HTMX configuration complete');
    }

    // Enhanced Button Preservation System
    let preservedButtonStates = new Map();

    function preserveButtonStates(triggerElement) {
        // Find all buttons in the target area that might be affected
        const targetSelector = triggerElement.getAttribute('hx-target');
        if (!targetSelector) return;

        const targetElement = document.querySelector(targetSelector);
        if (!targetElement) return;

        // Store button states before swap
        const buttons = targetElement.querySelectorAll('button[id], [data-preserve="true"]');
        buttons.forEach(button => {
            if (button.id) {
                preservedButtonStates.set(button.id, {
                    innerHTML: button.innerHTML,
                    className: button.className,
                    disabled: button.disabled,
                    attributes: Array.from(button.attributes).reduce((acc, attr) => {
                        acc[attr.name] = attr.value;
                        return acc;
                    }, {})
                });
            }
        });
    }

    function restoreButtonStates(targetElement) {
        // Restore preserved button states after swap
        const buttons = targetElement.querySelectorAll('button[id]');
        buttons.forEach(button => {
            if (preservedButtonStates.has(button.id)) {
                const preserved = preservedButtonStates.get(button.id);

                // Only restore if the button structure hasn't intentionally changed
                if (!button.hasAttribute('data-updated')) {
                    button.innerHTML = preserved.innerHTML;
                    button.className = preserved.className;
                    button.disabled = preserved.disabled;
                }

                // Clean up preserved state
                preservedButtonStates.delete(button.id);
            }
        });
    }

    // Alpine.js hydration is now handled by the unified Hydration Manager
    // This function is kept for backward compatibility but delegates to the manager
    function hydrateAlpineComponents(targetElement) {
        if (window.hydrationManager) {
            window.hydrationManager.hydrateAlpineComponents(targetElement);
        } else {
            console.warn('⚠️ Hydration Manager not available, skipping Alpine hydration');
        }
    }

    // Re-initialize Event Listeners for Dynamic Content
    function reinitializeEventListeners(targetElement) {
        // Re-initialize hover effects
        const hoverElements = targetElement.querySelectorAll('.hover-lift, .hover-scale, .card-animate');
        hoverElements.forEach(element => {
            element.addEventListener('mouseenter', function() {
                this.style.transform = this.classList.contains('hover-lift') ? 'translateY(-8px)' :
                                     this.classList.contains('hover-scale') ? 'scale(1.05)' :
                                     'translateY(-8px)';
            });

            element.addEventListener('mouseleave', function() {
                this.style.transform = '';
            });
        });

        // Re-initialize any custom components
        if (window.initializeCustomComponents) {
            window.initializeCustomComponents(targetElement);
        }
    }

    // Enhanced Out-of-Band (OOB) Swap Handling
    function setupOOBSwapHandling() {
        // Listen for OOB swaps specifically for modals
        document.addEventListener('htmx:oobAfterSwap', function(event) {
            const target = event.detail.target;

            // Handle modal OOB swaps
            if (target.classList.contains('modal') || target.id.includes('modal')) {
                console.log('🎭 Modal OOB swap detected:', target.id);

                // Re-hydrate modal content
                hydrateAlpineComponents(target);

                // Initialize modal-specific functionality
                initializeModalFeatures(target);

                // Show modal if it has auto-show attribute
                if (target.hasAttribute('data-auto-show')) {
                    showModal(target.id);
                }
            }
        });

        // Enhanced modal management
        document.addEventListener('htmx:afterRequest', function(event) {
            // Check if response contains OOB modal content
            const response = event.detail.xhr.responseText;
            if (response && response.includes('hx-swap-oob') && response.includes('modal')) {
                console.log('🎭 OOB modal content detected in response');
            }
        });

        // Global HTMX afterSwap handler to ensure restoreScroll() is always called
        document.addEventListener('htmx:afterSwap', function(event) {
            const target = event.detail.target;

            // Call global restoreScroll() after any swap operation
            setTimeout(() => {
                if (typeof window.restoreScroll === 'function') {
                    window.restoreScroll();
                    console.log('🔄 Global restoreScroll() called after HTMX swap:', target.id || target.tagName);
                }
            }, 50);
        });
    }

    // Initialize modal-specific features
    function initializeModalFeatures(modalElement) {
        // Setup close button handlers
        const closeButtons = modalElement.querySelectorAll('[data-modal-close]');
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                hideModal(modalElement.id);
            });
        });

        // Setup backdrop click to close
        if (modalElement.hasAttribute('data-backdrop-close')) {
            modalElement.addEventListener('click', function(e) {
                if (e.target === modalElement) {
                    hideModal(modalElement.id);
                }
            });
        }

        // Setup escape key to close
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modalElement.style.display !== 'none') {
                hideModal(modalElement.id);
            }
        });
    }

    // Modal utility functions
    window.showModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.add('modal-show');
            modal.classList.remove('modal-hide');

            // Comprehensive body scroll lock
            setGlobalBodyScrollLock();

            // Focus management
            const firstFocusable = modal.querySelector('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }

            // Trigger custom event
            modal.dispatchEvent(new CustomEvent('modal:shown', { detail: { modalId } }));
        }
    };

    window.hideModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('modal-hide');
            modal.classList.remove('modal-show');

            // Call global restoreScroll() function
            if (typeof window.restoreScroll === 'function') {
                window.restoreScroll();
            } else {
                // Fallback to legacy function
                restoreGlobalBodyScroll();
            }

            // Hide after animation
            setTimeout(() => {
                modal.style.display = 'none';
                // Final scroll state check
                finalGlobalScrollCheck();

                // Ensure restoreScroll() is called again after modal removal
                if (typeof window.restoreScroll === 'function') {
                    window.restoreScroll();
                }
            }, 300);

            // Trigger custom event
            modal.dispatchEvent(new CustomEvent('modal:hidden', { detail: { modalId } }));
        }
    };

    // Enhanced HTMX request function with OOB support
    window.htmxModalRequest = function(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            target: 'this',
            swap: 'none', // Don't swap the trigger
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest',
                ...options.headers
            }
        };

        return htmx.ajax(defaultOptions.method, url, {
            ...defaultOptions,
            ...options
        });
    };

    function getCSRFToken() {
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) return metaToken.getAttribute('content');

        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') return value;
        }
        return '';
    }

    function setupHTMXEventListeners() {
        // Prevent duplicate listener setup
        if (window.htmxEventListenersSetup) return;
        window.htmxEventListenersSetup = true;

        // Before request - setup loading states
        document.addEventListener('htmx:beforeRequest', function(event) {
            const element = event.detail.elt;

            // Add loading state to the triggering element
            if (element.tagName === 'BUTTON') {
                element.setAttribute('aria-busy', 'true');
                element.style.cursor = 'wait';

                // Store original text and show loading
                if (!element.dataset.originalText) {
                    element.dataset.originalText = element.textContent;
                }

                // Add loading spinner if it's a button
                const spinner = '<i class="fas fa-spinner fa-spin mr-2"></i>';
                if (!element.innerHTML.includes('fa-spinner')) {
                    element.innerHTML = spinner + (element.dataset.loadingText || 'Loading...');
                }
            }

            // Enhanced button preservation check
            preserveButtonStates(element);
        });

        // Simplified afterSwap - let hydration manager handle Alpine.js
        document.addEventListener('htmx:afterSwap', function(event) {
            const target = event.detail.target;

            // Restore button states after swap
            restoreButtonStates(target);

            // Re-initialize event listeners for new content
            reinitializeEventListeners(target);

            // Trigger custom hydration event (hydration manager will handle Alpine.js)
            target.dispatchEvent(new CustomEvent('htmx:hydrated', {
                detail: { target: target }
            }));
        });

        // After request - cleanup loading states
        document.addEventListener('htmx:afterRequest', function(event) {
            const element = event.detail.elt;

            // Remove loading state from buttons
            if (element.tagName === 'BUTTON') {
                element.setAttribute('aria-busy', 'false');
                element.style.cursor = '';

                // Restore original text
                if (element.dataset.originalText) {
                    element.textContent = element.dataset.originalText;
                }
            }

            // Hide global loading indicator
            hideGlobalLoadingIndicator();

            // Handle response status
            const xhr = event.detail.xhr;
            if (xhr.status >= 200 && xhr.status < 300) {
                handleSuccessResponse(xhr, element);
            } else {
                handleErrorResponse(xhr, element);
            }

            // Global scroll restoration after any HTMX request
            setTimeout(() => {
                if (typeof window.restoreScroll === 'function') {
                    window.restoreScroll();
                }
            }, 100);
        });

        // Note: afterSwap hydration is handled above, no duplicate needed

        // After settle - final cleanup
        document.addEventListener('htmx:afterSettle', function(event) {
            const target = event.detail.target;
            
            // Final hydration check
            if (window.hydrationManager) {
                window.hydrationManager.finalizeHydration(target);
            }

            // Scroll to target if needed
            handleScrollToTarget(target, event.detail);
        });

        // Handle configuration requests
        document.addEventListener('htmx:configRequest', function(event) {
            // Add CSRF token to all requests
            const csrfToken = getCSRFToken();
            if (csrfToken) {
                event.detail.headers['X-CSRFToken'] = csrfToken;
            }

            // Add custom headers
            event.detail.headers['X-Requested-With'] = 'XMLHttpRequest';
            event.detail.headers['X-HTMX-Request'] = 'true';
        });
    }

    function setupCSRFHandling() {
        // Get CSRF token from various sources
        window.getCSRFToken = function() {
            // Try meta tag first
            const metaToken = document.querySelector('meta[name="csrf-token"]');
            if (metaToken) {
                return metaToken.getAttribute('content');
            }

            // Try cookie
            const cookieToken = getCookie('csrftoken');
            if (cookieToken) {
                return cookieToken;
            }

            // Try hidden input
            const inputToken = document.querySelector('input[name="csrfmiddlewaretoken"]');
            if (inputToken) {
                return inputToken.value;
            }

            return null;
        };

        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    }

    function setupLoadingIndicators() {
        // Create global loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'htmx-global-loading';
        loadingIndicator.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 z-[9999] bg-white rounded-lg shadow-lg px-4 py-2 flex items-center space-x-2 opacity-0 transition-opacity duration-300 pointer-events-none';
        loadingIndicator.innerHTML = `
            <div class="w-4 h-4 border-2 border-harrier-red border-t-transparent rounded-full animate-spin"></div>
            <span class="text-sm font-medium text-gray-700">Loading...</span>
        `;
        document.body.appendChild(loadingIndicator);

        window.showGlobalLoadingIndicator = function() {
            const indicator = document.getElementById('htmx-global-loading');
            if (indicator) {
                indicator.style.opacity = '1';
                indicator.style.pointerEvents = 'auto';
            }
        };

        window.hideGlobalLoadingIndicator = function() {
            const indicator = document.getElementById('htmx-global-loading');
            if (indicator) {
                indicator.style.opacity = '0';
                indicator.style.pointerEvents = 'none';
            }
        };
    }

    function setupErrorHandling() {
        // Response error handling
        document.addEventListener('htmx:responseError', function(event) {
            const xhr = event.detail.xhr;
            const element = event.detail.elt;
            
            console.error('HTMX Response Error:', {
                status: xhr.status,
                statusText: xhr.statusText,
                url: xhr.responseURL,
                element: element
            });

            // Show user-friendly error message
            if (window.showToast) {
                const errorMessage = getErrorMessage(xhr.status);
                window.showToast(errorMessage, 'error');
            }

            // Handle specific error types
            handleSpecificErrors(xhr, element);
        });

        // Send error handling
        document.addEventListener('htmx:sendError', function(event) {
            console.error('HTMX Send Error:', event.detail);
            
            if (window.showToast) {
                window.showToast('Network error. Please check your connection.', 'error');
            }
        });

        // Timeout handling
        document.addEventListener('htmx:timeout', function(event) {
            console.warn('HTMX Timeout:', event.detail);
            
            if (window.showToast) {
                window.showToast('Request timed out. Please try again.', 'warning');
            }
        });
    }

    function handleSuccessResponse(xhr, element) {
        // Check for success messages in response headers
        const successMessage = xhr.getResponseHeader('X-Toast-Success');
        if (successMessage && window.showToast) {
            window.showToast(successMessage, 'success');
        }

        // Handle redirect responses
        const redirectUrl = xhr.getResponseHeader('X-Redirect');
        if (redirectUrl) {
            window.location.href = redirectUrl;
        }
    }

    function handleErrorResponse(xhr, element) {
        // Check for error messages in response headers
        const errorMessage = xhr.getResponseHeader('X-Toast-Error');
        if (errorMessage && window.showToast) {
            window.showToast(errorMessage, 'error');
        }
    }

    function handlePostSwapProcessing(target, detail) {
        // Handle modal-specific processing
        if (target.id && target.id.includes('modal')) {
            // Focus management for modals
            const firstFocusable = target.querySelector('input, select, textarea, button');
            if (firstFocusable) {
                setTimeout(() => firstFocusable.focus(), 100);
            }
        }

        // Handle form-specific processing
        const forms = target.querySelectorAll('form');
        forms.forEach(form => {
            // Re-initialize form validation
            if (window.hydrationManager) {
                window.hydrationManager.registerComponent('form[data-validate]', (element) => {
                    element.addEventListener('submit', (e) => {
                        if (!validateForm(element)) {
                            e.preventDefault();
                        }
                    });
                });
            }
        });
    }

    function handleScrollToTarget(target, detail) {
        // Auto-scroll to target if it has scroll attribute
        if (target.hasAttribute('data-scroll-to')) {
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    function handleSpecificErrors(xhr, element) {
        switch (xhr.status) {
            case 401:
                // Unauthorized - redirect to login
                window.location.href = '/login/';
                break;
            case 403:
                // Forbidden - show access denied message
                if (window.showToast) {
                    window.showToast('Access denied. You do not have permission to perform this action.', 'error');
                }
                break;
            case 404:
                // Not found - show not found message
                if (window.showToast) {
                    window.showToast('The requested resource was not found.', 'error');
                }
                break;
            case 422:
                // Validation error - try to show form errors
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.errors) {
                        showFormErrors(response.errors, element);
                    }
                } catch (e) {
                    console.warn('Could not parse validation errors:', e);
                }
                break;
            case 500:
                // Server error - show generic error
                if (window.showToast) {
                    window.showToast('A server error occurred. Please try again later.', 'error');
                }
                break;
        }
    }

    function getErrorMessage(status) {
        const messages = {
            400: 'Bad request. Please check your input.',
            401: 'You are not authorized. Please log in.',
            403: 'Access denied.',
            404: 'Resource not found.',
            422: 'Invalid data provided.',
            429: 'Too many requests. Please wait.',
            500: 'Server error. Please try again later.',
            502: 'Service temporarily unavailable.',
            503: 'Service temporarily unavailable.',
            504: 'Request timed out.'
        };

        return messages[status] || 'An error occurred. Please try again.';
    }

    function showFormErrors(errors, formElement) {
        // Clear existing errors
        const existingErrors = formElement.querySelectorAll('.error-message');
        existingErrors.forEach(error => error.remove());

        // Show new errors
        Object.keys(errors).forEach(fieldName => {
            const field = formElement.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.classList.add('border-red-500');
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message text-red-500 text-sm mt-1';
                errorDiv.textContent = errors[fieldName][0]; // Show first error
                
                field.parentNode.appendChild(errorDiv);
            }
        });
    }

    function validateForm(form) {
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

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', waitForHTMX);
    } else {
        waitForHTMX();
    }

    // Global scroll management functions
    window.setGlobalBodyScrollLock = function() {
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

        console.log('🔒 Global: Body scroll locked');
    };

    window.restoreGlobalBodyScroll = function() {
        // Check if there are any active modals
        const activeModals = document.querySelectorAll('.modal.modal-show');
        if (activeModals.length <= 1) { // 1 or less (the one being closed)
            // Comprehensive scroll restoration
            document.body.style.overflow = '';
            document.body.style.overflowY = '';
            document.body.classList.remove('modal-open');
            document.documentElement.style.overflow = '';

            console.log('✅ Global: Body scroll restored');
        } else {
            console.log('⏸️ Global: Keeping scroll locked - active modals:', activeModals.length - 1);
        }
    };

    window.finalGlobalScrollCheck = function() {
        setTimeout(() => {
            const remainingModals = document.querySelectorAll('.modal.modal-show');
            if (remainingModals.length === 0) {
                // Ensure no scroll restrictions remain
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

                console.log('✅ Global: Final scroll state verified');
            }
        }, 50);
    };

    console.log('✅ HTMX configuration script loaded');

})();
