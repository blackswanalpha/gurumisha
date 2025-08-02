/**
 * HTMX Utilities for Gurumisha
 * Enhanced targeting, swapping, and preservation utilities
 */

(function() {
    'use strict';

    /**
     * HTMX Utilities Namespace
     */
    window.htmxUtils = {
        
        /**
         * Smart target selector that avoids replacing button containers
         */
        smartTarget: function(element, fallbackTarget) {
            const target = element.getAttribute('hx-target');
            if (!target) return fallbackTarget;
            
            const targetElement = document.querySelector(target);
            if (!targetElement) return fallbackTarget;
            
            // Check if target contains interactive elements that should be preserved
            const hasInteractiveElements = targetElement.querySelector('button, input, select, textarea, [x-data]');
            
            if (hasInteractiveElements) {
                // Look for a content wrapper inside the target
                const contentWrapper = targetElement.querySelector('[data-content], .content-wrapper, .inner-content');
                if (contentWrapper) {
                    return '#' + (contentWrapper.id || this.generateId(contentWrapper, 'content-'));
                }
                
                // Create a content wrapper if none exists
                const wrapper = document.createElement('div');
                wrapper.className = 'htmx-content-wrapper';
                wrapper.id = this.generateId(wrapper, 'htmx-content-');
                
                // Move all children to wrapper
                while (targetElement.firstChild) {
                    wrapper.appendChild(targetElement.firstChild);
                }
                targetElement.appendChild(wrapper);
                
                return '#' + wrapper.id;
            }
            
            return target;
        },

        /**
         * Enhanced swap strategy that preserves interactive elements
         */
        enhancedSwap: function(element, content, swapStyle = 'innerHTML') {
            const target = document.querySelector(element.getAttribute('hx-target'));
            if (!target) return;

            // Store interactive elements before swap
            const interactiveElements = this.preserveInteractiveElements(target);
            
            // Perform the swap
            switch (swapStyle) {
                case 'innerHTML':
                    target.innerHTML = content;
                    break;
                case 'outerHTML':
                    target.outerHTML = content;
                    break;
                case 'afterend':
                    target.insertAdjacentHTML('afterend', content);
                    break;
                case 'beforeend':
                    target.insertAdjacentHTML('beforeend', content);
                    break;
                default:
                    target.innerHTML = content;
            }
            
            // Restore preserved elements
            this.restoreInteractiveElements(target, interactiveElements);
        },

        /**
         * Preserve interactive elements before swap
         */
        preserveInteractiveElements: function(container) {
            const preserved = new Map();
            const interactiveSelectors = [
                'button[data-preserve="true"]',
                'input[data-preserve="true"]',
                '[x-data][data-preserve="true"]',
                '[hx-preserve="true"]'
            ];
            
            interactiveSelectors.forEach(selector => {
                const elements = container.querySelectorAll(selector);
                elements.forEach(element => {
                    const id = element.id || this.generateId(element, 'preserved-');
                    preserved.set(id, {
                        element: element.cloneNode(true),
                        parent: element.parentNode,
                        nextSibling: element.nextSibling
                    });
                });
            });
            
            return preserved;
        },

        /**
         * Restore preserved interactive elements after swap
         */
        restoreInteractiveElements: function(container, preserved) {
            preserved.forEach((data, id) => {
                const placeholder = container.querySelector(`[id="${id}"]`);
                if (placeholder && data.element) {
                    placeholder.parentNode.replaceChild(data.element, placeholder);
                    
                    // Re-hydrate the restored element
                    this.hydrateElement(data.element);
                }
            });
        },

        /**
         * Generate unique ID for elements
         */
        generateId: function(element, prefix = 'htmx-') {
            const timestamp = Date.now();
            const random = Math.random().toString(36).substr(2, 5);
            const id = prefix + timestamp + '-' + random;
            element.id = id;
            return id;
        },

        /**
         * Enhanced element hydration
         */
        hydrateElement: function(element) {
            // Alpine.js hydration
            if (typeof Alpine !== 'undefined' && element.hasAttribute('x-data')) {
                try {
                    Alpine.initTree(element);
                    console.log('🎯 Alpine component hydrated:', element);
                } catch (error) {
                    console.warn('⚠️ Alpine hydration failed:', error);
                }
            }

            // Re-initialize HTMX for new elements
            if (typeof htmx !== 'undefined') {
                htmx.process(element);
            }

            // Custom component initialization
            if (window.initializeCustomComponents) {
                window.initializeCustomComponents(element);
            }

            // Trigger hydration event
            element.dispatchEvent(new CustomEvent('htmx:element-hydrated', {
                detail: { element: element }
            }));
        },

        /**
         * Safe button replacement that preserves functionality
         */
        replaceButton: function(oldButton, newButtonHTML) {
            const container = oldButton.parentNode;
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = newButtonHTML;
            const newButton = tempDiv.firstElementChild;
            
            // Preserve event listeners and data
            this.preserveButtonState(oldButton, newButton);
            
            // Replace the button
            container.replaceChild(newButton, oldButton);
            
            // Re-hydrate
            this.hydrateElement(newButton);
            
            return newButton;
        },

        /**
         * Preserve button state during replacement
         */
        preserveButtonState: function(oldButton, newButton) {
            // Copy data attributes
            Array.from(oldButton.attributes).forEach(attr => {
                if (attr.name.startsWith('data-') && !newButton.hasAttribute(attr.name)) {
                    newButton.setAttribute(attr.name, attr.value);
                }
            });

            // Preserve Alpine.js state if present
            if (oldButton._x_dataStack && typeof Alpine !== 'undefined') {
                newButton._x_dataStack = oldButton._x_dataStack;
            }
        },

        /**
         * Enhanced HTMX request with better error handling
         */
        request: function(method, url, options = {}) {
            const defaultOptions = {
                target: options.target || 'body',
                swap: options.swap || 'innerHTML',
                indicator: options.indicator,
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    ...options.headers
                }
            };

            // Use smart targeting
            if (options.smartTarget && options.triggerElement) {
                defaultOptions.target = this.smartTarget(options.triggerElement, defaultOptions.target);
            }

            return htmx.ajax(method, url, defaultOptions);
        },

        /**
         * Get CSRF token from meta tag or cookie
         */
        getCSRFToken: function() {
            const metaToken = document.querySelector('meta[name="csrf-token"]');
            if (metaToken) return metaToken.getAttribute('content');
            
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrftoken') return value;
            }
            
            return '';
        },

        /**
         * Batch update multiple elements safely
         */
        batchUpdate: function(updates) {
            const preservedStates = new Map();
            
            // Preserve states
            updates.forEach(update => {
                const element = document.querySelector(update.target);
                if (element) {
                    preservedStates.set(update.target, this.preserveInteractiveElements(element));
                }
            });
            
            // Apply updates
            updates.forEach(update => {
                const element = document.querySelector(update.target);
                if (element) {
                    element.innerHTML = update.content;
                    
                    // Restore preserved elements
                    const preserved = preservedStates.get(update.target);
                    if (preserved) {
                        this.restoreInteractiveElements(element, preserved);
                    }
                    
                    // Re-hydrate
                    this.hydrateElement(element);
                }
            });
        }
    };

    /**
     * Initialize utilities when DOM is ready
     */
    document.addEventListener('DOMContentLoaded', function() {
        console.log('✅ HTMX Utilities loaded');
        
        // Enhance existing HTMX elements
        document.querySelectorAll('[hx-get], [hx-post], [hx-put], [hx-delete]').forEach(element => {
            // Add smart targeting if not already specified
            if (!element.hasAttribute('hx-target')) {
                const smartTarget = window.htmxUtils.smartTarget(element, 'body');
                if (smartTarget !== 'body') {
                    element.setAttribute('hx-target', smartTarget);
                }
            }
        });
    });

})();
