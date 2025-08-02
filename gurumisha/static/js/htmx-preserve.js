/**
 * HTMX Preserve Extension for Gurumisha
 * Provides hx-preserve functionality to keep specific elements during swaps
 */

(function() {
    'use strict';

    // Extension configuration
    const PRESERVE_ATTRIBUTE = 'hx-preserve';
    const PRESERVE_ID_ATTRIBUTE = 'hx-preserve-id';
    
    // Storage for preserved elements
    let preservedElements = new Map();
    
    /**
     * HTMX Preserve Extension
     */
    htmx.defineExtension('preserve', {
        onEvent: function(name, evt) {
            if (name === 'htmx:beforeSwap') {
                preserveElements(evt.detail.target);
            } else if (name === 'htmx:afterSwap') {
                restorePreservedElements(evt.detail.target);
            }
        }
    });

    /**
     * Preserve elements marked with hx-preserve before swap
     */
    function preserveElements(targetElement) {
        // Find all elements with preserve attributes
        const elementsToPreserve = targetElement.querySelectorAll(`[${PRESERVE_ATTRIBUTE}]`);
        
        elementsToPreserve.forEach(element => {
            const preserveId = element.getAttribute(PRESERVE_ID_ATTRIBUTE) || element.id || generatePreserveId();
            
            if (preserveId) {
                // Clone the element and store it
                const clonedElement = element.cloneNode(true);
                preservedElements.set(preserveId, {
                    element: clonedElement,
                    parent: element.parentNode,
                    nextSibling: element.nextSibling,
                    originalElement: element
                });
                
                console.log(`🔒 Preserved element: ${preserveId}`);
            }
        });
    }

    /**
     * Restore preserved elements after swap
     */
    function restorePreservedElements(targetElement) {
        // Find placeholders for preserved elements
        const preservePlaceholders = targetElement.querySelectorAll(`[${PRESERVE_ATTRIBUTE}]`);
        
        preservePlaceholders.forEach(placeholder => {
            const preserveId = placeholder.getAttribute(PRESERVE_ID_ATTRIBUTE) || placeholder.id;
            
            if (preserveId && preservedElements.has(preserveId)) {
                const preserved = preservedElements.get(preserveId);
                
                // Replace placeholder with preserved element
                placeholder.parentNode.replaceChild(preserved.element, placeholder);
                
                // Re-hydrate the preserved element if needed
                hydratePreservedElement(preserved.element);
                
                console.log(`🔓 Restored preserved element: ${preserveId}`);
                
                // Clean up
                preservedElements.delete(preserveId);
            }
        });
    }

    /**
     * Re-hydrate preserved elements (Alpine.js, event listeners, etc.)
     */
    function hydratePreservedElement(element) {
        // Re-initialize Alpine.js if present
        if (typeof Alpine !== 'undefined' && element.hasAttribute('x-data')) {
            try {
                Alpine.initTree(element);
            } catch (error) {
                console.warn('⚠️ Failed to re-hydrate Alpine component:', error);
            }
        }

        // Re-initialize any custom components
        if (window.initializeCustomComponents) {
            window.initializeCustomComponents(element);
        }

        // Trigger custom hydration event
        element.dispatchEvent(new CustomEvent('htmx:preserved-hydrated', {
            detail: { element: element }
        }));
    }

    /**
     * Generate a unique preserve ID
     */
    function generatePreserveId() {
        return 'preserve-' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Utility function to mark elements for preservation
     */
    window.htmxPreserve = {
        /**
         * Mark an element for preservation
         */
        mark: function(element, preserveId) {
            if (typeof element === 'string') {
                element = document.querySelector(element);
            }
            
            if (element) {
                element.setAttribute(PRESERVE_ATTRIBUTE, 'true');
                if (preserveId) {
                    element.setAttribute(PRESERVE_ID_ATTRIBUTE, preserveId);
                }
            }
        },

        /**
         * Unmark an element from preservation
         */
        unmark: function(element) {
            if (typeof element === 'string') {
                element = document.querySelector(element);
            }
            
            if (element) {
                element.removeAttribute(PRESERVE_ATTRIBUTE);
                element.removeAttribute(PRESERVE_ID_ATTRIBUTE);
            }
        },

        /**
         * Check if an element is marked for preservation
         */
        isMarked: function(element) {
            if (typeof element === 'string') {
                element = document.querySelector(element);
            }
            
            return element ? element.hasAttribute(PRESERVE_ATTRIBUTE) : false;
        }
    };

    console.log('✅ HTMX Preserve Extension loaded');
})();
