/**
 * Frontend Validator for Gurumisha
 * Comprehensive testing and validation system for Alpine.js, HTMX, and hydration
 * Provides real-time monitoring and debugging capabilities
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.frontendValidatorLoaded) {
        console.log('Frontend validator already loaded');
        return;
    }
    window.frontendValidatorLoaded = true;

    class FrontendValidator {
        constructor() {
            this.tests = new Map();
            this.results = new Map();
            this.monitoring = false;
            this.init();
        }

        init() {
            console.log('🧪 Frontend Validator initialized (v2.2 - DOM-aware initialization)');
            this.registerTests();
            this.setupMonitoring();
            this.createDebugPanel();
        }

        /**
         * Register all validation tests
         */
        registerTests() {
            // Alpine.js tests
            this.registerTest('alpine-loaded', 'Alpine.js Loaded', () => {
                return typeof Alpine !== 'undefined';
            });

            this.registerTest('alpine-components', 'Alpine.js Components', () => {
                return window.alpineComponents && Object.keys(window.alpineComponents).length > 0;
            });

            this.registerTest('alpine-hydration', 'Alpine.js Hydration', () => {
                const alpineElements = document.querySelectorAll('[x-data]');
                if (alpineElements.length === 0) {
                    return true; // No Alpine elements to test
                }

                let hydratedCount = 0;
                alpineElements.forEach(el => {
                    if (el._x_dataStack && el._x_dataStack.length > 0) {
                        hydratedCount++;
                    }
                });

                // Return true if all elements are hydrated, or if no elements exist
                return hydratedCount === alpineElements.length;
            });

            // HTMX tests
            this.registerTest('htmx-loaded', 'HTMX Loaded', () => {
                return typeof htmx !== 'undefined';
            });

            this.registerTest('htmx-config', 'HTMX Configuration', () => {
                return window.htmxConfigLoaded === true;
            });

            this.registerTest('htmx-elements', 'HTMX Elements', () => {
                const htmxElements = document.querySelectorAll('[hx-get], [hx-post], [hx-put], [hx-delete]');
                return htmxElements.length;
            });

            // Hydration tests
            this.registerTest('hydration-manager', 'Hydration Manager', () => {
                return window.hydrationManager && typeof window.hydrationManager.hydrateElement === 'function';
            });

            this.registerTest('modal-manager', 'Modal Manager', () => {
                return window.modalManager && typeof window.modalManager.showModal === 'function';
            });

            // Toast system tests
            this.registerTest('toast-manager', 'Toast Manager', () => {
                // Check for any available toast function
                return typeof window.showToast === 'function' ||
                       typeof window.simpleShowToast === 'function' ||
                       window.toastManager;
            });

            // Error handling tests
            this.registerTest('error-suppressor', 'Error Suppressor', () => {
                // Only test if error suppressor script is loaded
                return !document.querySelector('script[src*="error-suppressor"]') ||
                       window.console.error !== console.error;
            });

            // Component-specific tests (only run on relevant pages)
            this.registerTest('compare-widget', 'Compare Widget', () => {
                // Only test on car listing/detail pages
                if (!document.body.classList.contains('car-listing-page') &&
                    !document.body.classList.contains('car-detail-page')) {
                    return true; // Skip test on irrelevant pages
                }
                const widget = document.getElementById('floating-compare-widget');
                return widget !== null;
            });

            this.registerTest('wishlist-buttons', 'Wishlist Buttons', () => {
                // Only test on pages that should have wishlist buttons
                if (!document.body.classList.contains('car-listing-page') &&
                    !document.body.classList.contains('car-detail-page')) {
                    return true; // Skip test on irrelevant pages
                }
                const buttons = document.querySelectorAll('[id^="wishlist-btn-"]');
                return buttons.length > 0;
            });
        }

        /**
         * Register a new test
         */
        registerTest(id, name, testFunction) {
            this.tests.set(id, { name, testFunction });
        }

        /**
         * Run all tests
         */
        runAllTests() {
            console.log('🧪 Running all frontend validation tests...');
            const results = new Map();

            this.tests.forEach((test, id) => {
                try {
                    const result = test.testFunction();
                    results.set(id, {
                        name: test.name,
                        passed: this.evaluateResult(result),
                        result: result,
                        timestamp: new Date()
                    });
                } catch (error) {
                    results.set(id, {
                        name: test.name,
                        passed: false,
                        result: error.message,
                        error: error,
                        timestamp: new Date()
                    });
                }
            });

            this.results = results;
            this.displayResults();
            return results;
        }

        /**
         * Evaluate test result
         */
        evaluateResult(result) {
            if (typeof result === 'boolean') {
                return result;
            }
            if (typeof result === 'number') {
                return result > 0;
            }
            if (typeof result === 'object' && result !== null) {
                if (result.total !== undefined && result.hydrated !== undefined) {
                    return result.hydrated === result.total && result.total > 0;
                }
                return true; // Assume object results are positive
            }
            return !!result;
        }

        /**
         * Display test results
         */
        displayResults() {
            console.group('🧪 Frontend Validation Results');
            
            let passedCount = 0;
            let totalCount = 0;

            this.results.forEach((result, id) => {
                totalCount++;
                if (result.passed) {
                    passedCount++;
                    console.log(`✅ ${result.name}: PASSED`, result.result);
                } else {
                    console.error(`❌ ${result.name}: FAILED`, result.result);
                }
            });

            console.log(`\n📊 Summary: ${passedCount}/${totalCount} tests passed`);
            console.groupEnd();

            // Update debug panel if it exists
            this.updateDebugPanel();
        }

        /**
         * Setup continuous monitoring
         */
        setupMonitoring() {
            // Check if document.body is available
            if (!document.body) {
                // Silently wait for DOM to be ready instead of warning
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', () => {
                        this.setupMonitoring();
                    });
                } else {
                    // Try again after a short delay
                    setTimeout(() => {
                        this.setupMonitoring();
                    }, 50);
                }
                return;
            }

            // Monitor for new Alpine.js components
            const observer = new MutationObserver((mutations) => {
                if (!this.monitoring) return;

                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                this.validateNewElement(node);
                            }
                        });
                    }
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });

            // Monitor HTMX events
            document.addEventListener('htmx:afterSwap', () => {
                if (this.monitoring) {
                    setTimeout(() => this.runSpecificTests(['alpine-hydration', 'htmx-elements']), 100);
                }
            });
        }

        /**
         * Validate a new element
         */
        validateNewElement(element) {
            // Check if it's an Alpine.js component
            if (element.hasAttribute && element.hasAttribute('x-data')) {
                setTimeout(() => {
                    if (!element._x_dataStack || element._x_dataStack.length === 0) {
                        console.warn('⚠️ Alpine.js component not hydrated:', element);
                    }
                }, 200);
            }

            // Check if it has HTMX attributes
            const htmxAttributes = ['hx-get', 'hx-post', 'hx-put', 'hx-delete', 'hx-patch'];
            const hasHTMX = htmxAttributes.some(attr => element.hasAttribute && element.hasAttribute(attr));
            
            if (hasHTMX) {
                setTimeout(() => {
                    if (!element.hasAttribute('hx-processed')) {
                        console.warn('⚠️ HTMX element not processed:', element);
                    }
                }, 100);
            }
        }

        /**
         * Run specific tests
         */
        runSpecificTests(testIds) {
            const results = new Map();

            testIds.forEach(id => {
                if (this.tests.has(id)) {
                    const test = this.tests.get(id);
                    try {
                        const result = test.testFunction();
                        results.set(id, {
                            name: test.name,
                            passed: this.evaluateResult(result),
                            result: result,
                            timestamp: new Date()
                        });
                    } catch (error) {
                        results.set(id, {
                            name: test.name,
                            passed: false,
                            result: error.message,
                            error: error,
                            timestamp: new Date()
                        });
                    }
                }
            });

            return results;
        }

        /**
         * Create debug panel
         */
        createDebugPanel() {
            // Only create in development or when explicitly enabled
            if (!window.location.hostname.includes('localhost') && !localStorage.getItem('gurumisha-debug')) {
                return;
            }

            const panel = document.createElement('div');
            panel.id = 'frontend-debug-panel';
            panel.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 300px;
                max-height: 400px;
                background: white;
                border: 1px solid #ccc;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 10000;
                font-family: monospace;
                font-size: 12px;
                overflow: hidden;
                display: none;
            `;

            panel.innerHTML = `
                <div style="background: #f5f5f5; padding: 8px; border-bottom: 1px solid #ccc; display: flex; justify-content: between; align-items: center;">
                    <strong>Frontend Debug</strong>
                    <button id="debug-close" style="background: none; border: none; cursor: pointer; font-size: 16px;">×</button>
                </div>
                <div id="debug-content" style="padding: 8px; max-height: 350px; overflow-y: auto;">
                    <button id="run-tests" style="width: 100%; padding: 4px; margin-bottom: 8px; background: #007cba; color: white; border: none; border-radius: 4px; cursor: pointer;">Run Tests</button>
                    <div id="test-results"></div>
                </div>
            `;

            document.body.appendChild(panel);

            // Event listeners
            document.getElementById('debug-close').addEventListener('click', () => {
                panel.style.display = 'none';
            });

            document.getElementById('run-tests').addEventListener('click', () => {
                this.runAllTests();
            });

            // Show panel with Ctrl+Shift+D
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
                }
            });
        }

        /**
         * Update debug panel with results
         */
        updateDebugPanel() {
            const resultsDiv = document.getElementById('test-results');
            if (!resultsDiv) return;

            let html = '';
            this.results.forEach((result, id) => {
                const status = result.passed ? '✅' : '❌';
                const color = result.passed ? 'green' : 'red';
                html += `<div style="margin: 2px 0; color: ${color};">${status} ${result.name}</div>`;
            });

            resultsDiv.innerHTML = html;
        }

        /**
         * Start monitoring
         */
        startMonitoring() {
            this.monitoring = true;
            console.log('🔍 Frontend monitoring started');
        }

        /**
         * Stop monitoring
         */
        stopMonitoring() {
            this.monitoring = false;
            console.log('🔍 Frontend monitoring stopped');
        }

        /**
         * Get validation report
         */
        getReport() {
            const report = {
                timestamp: new Date(),
                tests: {},
                summary: {
                    total: this.results.size,
                    passed: 0,
                    failed: 0
                }
            };

            this.results.forEach((result, id) => {
                report.tests[id] = result;
                if (result.passed) {
                    report.summary.passed++;
                } else {
                    report.summary.failed++;
                }
            });

            return report;
        }
    }

    // Initialize validator
    const validator = new FrontendValidator();

    // Expose globally
    window.frontendValidator = validator;
    window.runFrontendTests = () => validator.runAllTests();
    window.startFrontendMonitoring = () => validator.startMonitoring();
    window.stopFrontendMonitoring = () => validator.stopMonitoring();

    // Auto-run tests after page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => validator.runAllTests(), 2000);
        });
    } else {
        setTimeout(() => validator.runAllTests(), 2000);
    }

    console.log('✅ Frontend Validator loaded and active');
    console.log('💡 Use Ctrl+Shift+D to toggle debug panel or call runFrontendTests() in console');

})();
