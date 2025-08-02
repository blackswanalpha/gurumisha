/**
 * Hydration Test Suite for Gurumisha
 * Tests HTMX, Alpine.js, and hydration functionality
 */

// Immediate load indicator
console.log('🔄 Loading Hydration Test Suite...');

(function() {
    'use strict';

    class HydrationTester {
        constructor() {
            this.tests = [];
            this.results = [];
            this.init();
        }

        init() {
            console.log('🧪 Hydration Test Suite initialized');
            this.setupTests();
        }

        setupTests() {
            // Test 1: Alpine.js availability and version
            this.addTest('Alpine.js Availability', () => {
                return typeof Alpine !== 'undefined' && Alpine.version;
            });

            // Test 2: HTMX availability
            this.addTest('HTMX Availability', () => {
                return typeof htmx !== 'undefined' && htmx.version;
            });

            // Test 3: Hydration Manager availability
            this.addTest('Hydration Manager Availability', () => {
                return window.hydrationManager && typeof window.hydrationManager.hydrateElement === 'function';
            });

            // Test 4: Alpine Components loaded
            this.addTest('Alpine Components Loaded', () => {
                return window.alpineComponents && Object.keys(window.alpineComponents).length > 0;
            });

            // Test 5: No duplicate event listeners
            this.addTest('No Duplicate HTMX Listeners', () => {
                return window.htmxEventListenersSetup === true;
            });

            // Test 6: Script loading order
            this.addTest('Script Loading Order', () => {
                return window.alpineComponentsLoaded && 
                       typeof Alpine !== 'undefined' && 
                       typeof htmx !== 'undefined' && 
                       window.hydrationManagerLoaded;
            });

            // Test 7: Alpine component instances tracking
            this.addTest('Alpine Component Instances Tracking', () => {
                return window.alpineComponentInstances instanceof Map;
            });
        }

        addTest(name, testFunction) {
            this.tests.push({ name, testFunction });
        }

        async runTests() {
            console.log('🧪 Running hydration tests...');
            this.results = [];

            for (const test of this.tests) {
                try {
                    const result = await test.testFunction();
                    this.results.push({
                        name: test.name,
                        passed: !!result,
                        result: result,
                        error: null
                    });
                    console.log(`${result ? '✅' : '❌'} ${test.name}: ${result}`);
                } catch (error) {
                    this.results.push({
                        name: test.name,
                        passed: false,
                        result: null,
                        error: error.message
                    });
                    console.error(`❌ ${test.name}: ${error.message}`);
                }
            }

            this.displayResults();
            return this.results;
        }

        displayResults() {
            const passed = this.results.filter(r => r.passed).length;
            const total = this.results.length;
            
            console.log(`\n🧪 Test Results: ${passed}/${total} tests passed`);
            
            if (passed === total) {
                console.log('🎉 All hydration tests passed!');
            } else {
                console.warn('⚠️ Some hydration tests failed. Check the logs above.');
            }
        }

        // Test specific hydration scenarios
        async testModalHydration() {
            console.log('🧪 Testing modal hydration...');
            
            // Create a test modal
            const testModal = document.createElement('div');
            testModal.id = 'test-modal';
            testModal.setAttribute('x-data', 'editCarModal()');
            testModal.innerHTML = '<div>Test Modal Content</div>';
            document.body.appendChild(testModal);

            try {
                // Test hydration
                if (window.hydrationManager) {
                    window.hydrationManager.hydrateElement(testModal);
                }

                // Check if Alpine initialized
                const isInitialized = testModal._x_dataStack && testModal._x_dataStack.length > 0;
                console.log(`🧪 Modal hydration test: ${isInitialized ? 'PASSED' : 'FAILED'}`);

                return isInitialized;
            } finally {
                // Cleanup
                testModal.remove();
            }
        }

        async testHTMXHydration() {
            console.log('🧪 Testing HTMX hydration...');
            
            // Create a test element with HTMX attributes
            const testElement = document.createElement('div');
            testElement.setAttribute('hx-get', '/test');
            testElement.setAttribute('hx-target', '#test-target');
            testElement.innerHTML = '<button>Test Button</button>';
            document.body.appendChild(testElement);

            try {
                // Test HTMX processing
                if (typeof htmx !== 'undefined') {
                    htmx.process(testElement);
                }

                // Check if HTMX attributes are processed
                const isProcessed = testElement.querySelector('[hx-get]') !== null;
                console.log(`🧪 HTMX hydration test: ${isProcessed ? 'PASSED' : 'FAILED'}`);

                return isProcessed;
            } finally {
                // Cleanup
                testElement.remove();
            }
        }

        // Run comprehensive hydration test
        async runComprehensiveTest() {
            console.log('🧪 Running comprehensive hydration test...');
            
            const basicTests = await this.runTests();
            const modalTest = await this.testModalHydration();
            const htmxTest = await this.testHTMXHydration();

            const allPassed = basicTests.every(t => t.passed) && modalTest && htmxTest;
            
            console.log(`\n🧪 Comprehensive Test Result: ${allPassed ? 'PASSED' : 'FAILED'}`);
            
            return {
                basicTests,
                modalTest,
                htmxTest,
                allPassed
            };
        }
    }

    // Initialize tester when DOM is ready
    let hydrationTester;
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            hydrationTester = new HydrationTester();
        });
    } else {
        hydrationTester = new HydrationTester();
    }

    // Expose globally for manual testing
    window.hydrationTester = hydrationTester;
    window.testHydration = () => {
        if (hydrationTester) {
            return hydrationTester.runComprehensiveTest();
        } else {
            console.warn('⚠️ Hydration tester not ready yet');
            return Promise.resolve({ allPassed: false, error: 'Tester not ready' });
        }
    };

    // Also expose a simple status check
    window.checkHydrationStatus = () => {
        const status = {
            alpine: typeof Alpine !== 'undefined',
            htmx: typeof htmx !== 'undefined',
            hydrationManager: !!window.hydrationManager,
            alpineComponents: !!window.alpineComponents,
            errors: []
        };

        if (!status.alpine) status.errors.push('Alpine.js not loaded');
        if (!status.htmx) status.errors.push('HTMX not loaded');
        if (!status.hydrationManager) status.errors.push('Hydration Manager not loaded');
        if (!status.alpineComponents) status.errors.push('Alpine Components not loaded');

        console.log('🔍 Hydration Status:', status);
        return status;
    };

    console.log('✅ Hydration Test Suite loaded');

    // Immediate availability check
    setTimeout(() => {
        if (typeof window.checkHydrationStatus === 'function') {
            console.log('✅ window.checkHydrationStatus is available');
        } else {
            console.warn('⚠️ window.checkHydrationStatus not available, check for script errors');
        }
    }, 100);

})();
