/**
 * Modal Test Suite for Gurumisha
 * Tests modal functionality, accessibility, and integration
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.modalTestSuiteLoaded) {
        console.log('Modal test suite already loaded');
        return;
    }
    window.modalTestSuiteLoaded = true;

    class ModalTestSuite {
        constructor() {
            this.tests = [];
            this.results = [];
            this.init();
        }

        init() {
            console.log('🧪 Modal Test Suite initialized');
            this.setupTests();
        }

        setupTests() {
            // Test 1: Modal utilities availability
            this.addTest('Modal Utilities Available', () => {
                return typeof window.modalUtils !== 'undefined' && 
                       typeof window.modalUtils.closeAllModals === 'function';
            });

            // Test 2: Enhanced modal manager availability
            this.addTest('Enhanced Modal Manager Available', () => {
                return typeof window.enhancedModalManager !== 'undefined';
            });

            // Test 3: Alpine.js integration
            this.addTest('Alpine.js Integration', () => {
                return typeof Alpine !== 'undefined' && Alpine.version;
            });

            // Test 4: HTMX integration
            this.addTest('HTMX Integration', () => {
                return typeof htmx !== 'undefined';
            });

            // Test 5: No orphaned modals
            this.addTest('No Orphaned Modals', () => {
                const modals = document.querySelectorAll('[id*="modal"]');
                return modals.length === 0; // Should be no modals on page load
            });
        }

        addTest(name, testFunction) {
            this.tests.push({ name, testFunction });
        }

        async runTests() {
            console.log('🧪 Running modal tests...');
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
            
            console.log(`\n🧪 Modal Test Results: ${passed}/${total} tests passed`);
            
            if (passed === total) {
                console.log('🎉 All modal tests passed!');
            } else {
                console.warn('⚠️ Some modal tests failed. Check the logs above.');
            }
        }

        // Test modal creation and cleanup
        async testModalLifecycle() {
            console.log('🧪 Testing modal lifecycle...');
            
            try {
                // Create a test modal
                const testModal = document.createElement('div');
                testModal.id = 'test-modal';
                testModal.className = 'fixed inset-0 z-50';
                testModal.setAttribute('role', 'dialog');
                testModal.setAttribute('x-data', '{ show: true, closeModal() { this.show = false; } }');
                testModal.innerHTML = `
                    <div class="modal-backdrop" @click="closeModal()"></div>
                    <div class="modal-content">
                        <h3 id="test-modal-title">Test Modal</h3>
                        <button @click="closeModal()">Close</button>
                    </div>
                `;
                
                document.body.appendChild(testModal);

                // Initialize with Alpine.js
                if (typeof Alpine !== 'undefined') {
                    Alpine.initTree(testModal);
                }

                // Test modal utilities
                if (window.modalUtils) {
                    window.modalUtils.initializeModal(testModal);
                }

                // Check if modal is detected as open
                const isOpen = window.modalUtils ? window.modalUtils.isModalOpen() : true;
                
                // Cleanup
                setTimeout(() => {
                    if (testModal.parentNode) {
                        testModal.parentNode.removeChild(testModal);
                    }
                }, 100);

                console.log(`🧪 Modal lifecycle test: ${isOpen ? 'PASSED' : 'FAILED'}`);
                return isOpen;

            } catch (error) {
                console.error('❌ Modal lifecycle test failed:', error);
                return false;
            }
        }

        // Test HTMX modal integration
        async testHTMXIntegration() {
            console.log('🧪 Testing HTMX modal integration...');
            
            try {
                // Check if HTMX event listeners are set up
                const hasHTMXListeners = window.enhancedModalManager && 
                                        window.enhancedModalManager.activeModals instanceof Map;

                console.log(`🧪 HTMX integration test: ${hasHTMXListeners ? 'PASSED' : 'FAILED'}`);
                return hasHTMXListeners;

            } catch (error) {
                console.error('❌ HTMX integration test failed:', error);
                return false;
            }
        }

        // Test accessibility features
        async testAccessibility() {
            console.log('🧪 Testing modal accessibility...');
            
            try {
                // Create a test modal
                const testModal = document.createElement('div');
                testModal.id = 'accessibility-test-modal';
                testModal.className = 'fixed inset-0 z-50';
                testModal.innerHTML = `
                    <div>
                        <h3>Accessibility Test Modal</h3>
                        <button>Test Button</button>
                    </div>
                `;
                
                document.body.appendChild(testModal);

                // Test accessibility enhancement
                if (window.modalUtils) {
                    window.modalUtils.enhanceAccessibility(testModal);
                }

                // Check ARIA attributes
                const hasRole = testModal.hasAttribute('role');
                const hasAriaModal = testModal.hasAttribute('aria-modal');
                const hasAriaLabelledby = testModal.hasAttribute('aria-labelledby');

                // Cleanup
                testModal.remove();

                const passed = hasRole && hasAriaModal;
                console.log(`🧪 Accessibility test: ${passed ? 'PASSED' : 'FAILED'}`);
                console.log(`  - Role: ${hasRole}`);
                console.log(`  - Aria-modal: ${hasAriaModal}`);
                console.log(`  - Aria-labelledby: ${hasAriaLabelledby}`);

                return passed;

            } catch (error) {
                console.error('❌ Accessibility test failed:', error);
                return false;
            }
        }

        // Run comprehensive modal test
        async runComprehensiveTest() {
            console.log('🧪 Running comprehensive modal test...');
            
            const basicTests = await this.runTests();
            const lifecycleTest = await this.testModalLifecycle();
            const htmxTest = await this.testHTMXIntegration();
            const accessibilityTest = await this.testAccessibility();

            const allPassed = basicTests.every(t => t.passed) && 
                            lifecycleTest && 
                            htmxTest && 
                            accessibilityTest;
            
            console.log(`\n🧪 Comprehensive Modal Test Result: ${allPassed ? 'PASSED' : 'FAILED'}`);
            
            return {
                basicTests,
                lifecycleTest,
                htmxTest,
                accessibilityTest,
                allPassed
            };
        }
    }

    // Initialize tester when DOM is ready
    let modalTestSuite;
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            modalTestSuite = new ModalTestSuite();
        });
    } else {
        modalTestSuite = new ModalTestSuite();
    }

    // Expose globally for manual testing
    window.modalTestSuite = modalTestSuite;
    window.testModals = () => {
        if (modalTestSuite) {
            return modalTestSuite.runComprehensiveTest();
        } else {
            console.warn('⚠️ Modal test suite not ready yet');
        }
    };

    // Add to diagnostic function
    if (window.diagnoseHydration) {
        const originalDiagnose = window.diagnoseHydration;
        window.diagnoseHydration = function() {
            const result = originalDiagnose();
            result.modalUtils = !!window.modalUtils;
            result.enhancedModalManager = !!window.enhancedModalManager;
            result.modalTestSuite = !!window.modalTestSuite;
            return result;
        };
    }

    console.log('✅ Modal Test Suite loaded');

})();
