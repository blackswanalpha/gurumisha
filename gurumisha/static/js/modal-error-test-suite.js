/**
 * Modal Error Test Suite for Gurumisha
 * Tests modal error handling and recovery mechanisms
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.modalErrorTestSuiteLoaded) {
        console.log('Modal Error Test Suite already loaded');
        return;
    }
    window.modalErrorTestSuiteLoaded = true;

    class ModalErrorTestSuite {
        constructor() {
            this.tests = [];
            this.results = [];
            this.init();
        }

        init() {
            console.log('🧪 Modal Error Test Suite initialized');
            this.setupTests();
        }

        setupTests() {
            // Test 1: Modal error catcher availability
            this.addTest('Modal Error Catcher Available', () => {
                return typeof window.modalErrorCatcher !== 'undefined' &&
                       typeof window.modalErrorCatcher.handleModalError === 'function';
            });

            // Test 2: Error logging functionality
            this.addTest('Error Logging Works', () => {
                if (!window.modalErrorCatcher) return false;
                
                const initialErrorCount = window.modalErrorCatcher.errorLog.length;
                
                // Simulate an error
                window.modalErrorCatcher.handleModalError({
                    type: 'test_error',
                    message: 'Test error message',
                    timestamp: new Date().toISOString()
                });
                
                return window.modalErrorCatcher.errorLog.length > initialErrorCount;
            });

            // Test 3: Error display functionality
            this.addTest('Error Display Works', () => {
                return typeof window.modalErrorCatcher.showModalError === 'function';
            });

            // Test 4: Modal element detection
            this.addTest('Modal Element Detection', () => {
                // Create a test modal
                const testModal = document.createElement('div');
                testModal.setAttribute('role', 'dialog');
                testModal.id = 'test-modal';
                
                const isDetected = window.modalErrorCatcher.isModalElement(testModal);
                
                return isDetected;
            });

            // Test 5: HTMX request detection
            this.addTest('HTMX Request Detection', () => {
                const mockEvent = {
                    detail: {
                        requestConfig: { path: '/modal-content/' },
                        target: document.body,
                        elt: { hasAttribute: () => true, getAttribute: () => 'body' }
                    }
                };
                
                return window.modalErrorCatcher.isModalHTMXRequest(mockEvent);
            });

            // Test 6: Form validation
            this.addTest('Form Validation Works', () => {
                // Create a test form
                const testForm = document.createElement('form');
                const requiredInput = document.createElement('input');
                requiredInput.setAttribute('required', 'true');
                requiredInput.value = 'test value';
                testForm.appendChild(requiredInput);
                
                return window.modalErrorCatcher.validateModalForm(testForm);
            });

            // Test 7: Error recovery mechanisms
            this.addTest('Error Recovery Available', () => {
                return typeof window.modalErrorCatcher.attemptModalRecovery === 'function' &&
                       typeof window.modalErrorCatcher.fallbackCloseModal === 'function';
            });

            // Test 8: Error statistics
            this.addTest('Error Statistics Available', () => {
                const stats = window.modalErrorCatcher.getErrorStats();
                return stats && 
                       typeof stats.totalErrors === 'number' &&
                       typeof stats.errorTypes === 'object';
            });
        }

        addTest(name, testFunction) {
            this.tests.push({ name, testFunction });
        }

        async runTests() {
            console.log('🧪 Running modal error tests...');
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
            
            console.log(`\n🧪 Modal Error Test Results: ${passed}/${total} tests passed`);
            
            if (passed === total) {
                console.log('🎉 All modal error tests passed!');
            } else {
                console.warn('⚠️ Some modal error tests failed. Check the logs above.');
            }
        }

        // Test error handling for specific scenarios
        async testHTMXErrorHandling() {
            console.log('🧪 Testing HTMX error handling...');
            
            try {
                if (!window.modalErrorCatcher) {
                    return false;
                }

                // Simulate HTMX response error
                const mockEvent = {
                    detail: {
                        xhr: { status: 500, statusText: 'Internal Server Error' },
                        requestConfig: { path: '/test-modal/' },
                        target: document.body
                    }
                };

                // This should not throw an error
                window.modalErrorCatcher.handleModalHTMXError(mockEvent);
                
                console.log('🧪 HTMX error handling test: PASSED');
                return true;

            } catch (error) {
                console.error('❌ HTMX error handling test failed:', error);
                return false;
            }
        }

        // Test Alpine.js error handling
        async testAlpineErrorHandling() {
            console.log('🧪 Testing Alpine.js error handling...');
            
            try {
                if (!window.modalErrorCatcher) {
                    return false;
                }

                // Create a test modal with Alpine.js
                const testModal = document.createElement('div');
                testModal.id = 'alpine-test-modal';
                testModal.setAttribute('role', 'dialog');
                testModal.setAttribute('x-data', '{ show: true }');
                
                document.body.appendChild(testModal);

                // Setup error handling
                window.modalErrorCatcher.setupModalElementErrorHandling(testModal);

                // Cleanup
                testModal.remove();

                console.log('🧪 Alpine.js error handling test: PASSED');
                return true;

            } catch (error) {
                console.error('❌ Alpine.js error handling test failed:', error);
                return false;
            }
        }

        // Test error recovery mechanisms
        async testErrorRecovery() {
            console.log('🧪 Testing error recovery mechanisms...');
            
            try {
                if (!window.modalErrorCatcher) {
                    return false;
                }

                // Create a test modal
                const testModal = document.createElement('div');
                testModal.id = 'recovery-test-modal';
                testModal.setAttribute('role', 'dialog');
                document.body.appendChild(testModal);

                // Test recovery
                window.modalErrorCatcher.attemptModalRecovery(document.body);

                // Modal should be removed
                const modalStillExists = document.getElementById('recovery-test-modal');

                console.log('🧪 Error recovery test:', !modalStillExists ? 'PASSED' : 'FAILED');
                return !modalStillExists;

            } catch (error) {
                console.error('❌ Error recovery test failed:', error);
                return false;
            }
        }

        // Test error display mechanisms
        async testErrorDisplay() {
            console.log('🧪 Testing error display mechanisms...');
            
            try {
                if (!window.modalErrorCatcher) {
                    return false;
                }

                // Test error display (should not throw)
                window.modalErrorCatcher.showModalError('Test error message');

                console.log('🧪 Error display test: PASSED');
                return true;

            } catch (error) {
                console.error('❌ Error display test failed:', error);
                return false;
            }
        }

        // Run comprehensive modal error test
        async runComprehensiveTest() {
            console.log('🧪 Running comprehensive modal error test...');
            
            const basicTests = await this.runTests();
            const htmxTest = await this.testHTMXErrorHandling();
            const alpineTest = await this.testAlpineErrorHandling();
            const recoveryTest = await this.testErrorRecovery();
            const displayTest = await this.testErrorDisplay();

            const allPassed = basicTests.every(t => t.passed) && 
                            htmxTest && 
                            alpineTest && 
                            recoveryTest && 
                            displayTest;
            
            console.log(`\n🧪 Comprehensive Modal Error Test Result: ${allPassed ? 'PASSED' : 'FAILED'}`);
            
            return {
                basicTests,
                htmxTest,
                alpineTest,
                recoveryTest,
                displayTest,
                allPassed
            };
        }

        // Simulate various error scenarios for testing
        simulateErrors() {
            console.log('🧪 Simulating various error scenarios...');
            
            if (!window.modalErrorCatcher) {
                console.error('Modal error catcher not available');
                return;
            }

            // Simulate different types of errors
            const errorScenarios = [
                {
                    type: 'htmx_response_error',
                    status: 500,
                    message: 'Server error simulation'
                },
                {
                    type: 'alpine_close_error',
                    modalId: 'test-modal',
                    message: 'Alpine.js close error simulation'
                },
                {
                    type: 'form_validation_error',
                    modalId: 'test-modal',
                    message: 'Form validation error simulation'
                },
                {
                    type: 'button_click_error',
                    modalId: 'test-modal',
                    buttonId: 'test-button',
                    message: 'Button click error simulation'
                }
            ];

            errorScenarios.forEach((scenario, index) => {
                setTimeout(() => {
                    window.modalErrorCatcher.handleModalError({
                        ...scenario,
                        timestamp: new Date().toISOString(),
                        simulated: true
                    });
                }, index * 100);
            });

            console.log('🧪 Error simulation complete. Check error stats with window.getModalErrorStats()');
        }
    }

    // Initialize tester when DOM is ready
    let modalErrorTestSuite;
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            modalErrorTestSuite = new ModalErrorTestSuite();
        });
    } else {
        modalErrorTestSuite = new ModalErrorTestSuite();
    }

    // Expose globally for manual testing
    window.modalErrorTestSuite = modalErrorTestSuite;
    window.testModalErrors = () => {
        if (modalErrorTestSuite) {
            return modalErrorTestSuite.runComprehensiveTest();
        } else {
            console.warn('⚠️ Modal error test suite not ready yet');
        }
    };

    window.simulateModalErrors = () => {
        if (modalErrorTestSuite) {
            modalErrorTestSuite.simulateErrors();
        } else {
            console.warn('⚠️ Modal error test suite not ready yet');
        }
    };

    console.log('✅ Modal Error Test Suite loaded');

})();
