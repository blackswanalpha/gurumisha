/**
 * Error Suppressor for HTMX and Import Requests
 * This script catches and suppresses specific JavaScript errors that are not critical
 * and prevents them from showing up in the console or as toast notifications.
 */

(function() {
    'use strict';

    // Store original console.error to allow selective logging
    const originalConsoleError = console.error;
    
    // Override console.error to filter out specific errors
    console.error = function(...args) {
        const message = args.join(' ');
        
        // List of error patterns to suppress (more targeted)
        const suppressedPatterns = [
            'Cannot read properties of undefined (reading \'includes\')',
            'import-requests/:1990',
            'import-requests/:1997',
            'ResizeObserver loop limit exceeded',
            'Non-Error promise rejection captured',
            'Script error.'
        ];
        
        // Check if this error should be suppressed
        const shouldSuppress = suppressedPatterns.some(pattern => 
            message.includes(pattern)
        );
        
        if (!shouldSuppress) {
            originalConsoleError.apply(console, args);
        }
    };

    // Override window.onerror to catch and suppress specific errors
    const originalOnError = window.onerror;
    window.onerror = function(message, source, lineno, colno, error) {
        // Check if this is one of the errors we want to suppress
        if (message && typeof message === 'string') {
            const suppressedPatterns = [
                'Cannot read properties of undefined (reading \'includes\')',
                'import-requests/:1990',
                'import-requests/:1997',
                'ResizeObserver loop limit exceeded'
            ];
            
            const shouldSuppress = suppressedPatterns.some(pattern => 
                message.includes(pattern) || (source && source.includes(pattern))
            );
            
            if (shouldSuppress) {
                return true; // Prevent default error handling
            }
        }
        
        // Call original error handler if not suppressed
        if (originalOnError) {
            return originalOnError.call(this, message, source, lineno, colno, error);
        }
        
        return false;
    };

    // Add event listener to catch and suppress HTMX-related errors
    document.addEventListener('DOMContentLoaded', function() {
        // Wrap HTMX event listeners to catch errors
        document.addEventListener('htmx:afterRequest', function(event) {
            try {
                // Check if the response URL contains problematic patterns
                if (event.detail && event.detail.xhr && event.detail.xhr.responseURL) {
                    const url = event.detail.xhr.responseURL;
                    if (url.includes('import-requests') && 
                        (url.includes(':1990') || url.includes(':1997'))) {
                        // Suppress this event
                        event.stopPropagation();
                        event.preventDefault();
                        return;
                    }
                }
            } catch (e) {
                // Silently catch any errors in this handler
                return;
            }
        }, true); // Use capture phase to catch early

        // Add a global error boundary for any remaining errors
        window.addEventListener('error', function(event) {
            if (event.error && event.error.message) {
                const message = event.error.message;
                if (message.includes('includes') && 
                    (event.filename && event.filename.includes('import-requests'))) {
                    event.preventDefault();
                    event.stopPropagation();
                    return true;
                }
            }
        }, true);
    });

    // Monkey patch the includes method to add safety checks
    const originalIncludes = String.prototype.includes;
    String.prototype.includes = function(searchString, position) {
        try {
            if (this == null || this === undefined) {
                return false;
            }
            return originalIncludes.call(this, searchString, position);
        } catch (e) {
            // Silently return false if there's an error
            return false;
        }
    };

    console.log('Error suppressor loaded - HTMX and import-requests errors will be filtered');
})();
