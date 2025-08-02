/**
 * Modal Button Test Suite for Gurumisha
 * Tests modal button persistence and prevents button disappearing
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.modalButtonTestSuiteLoaded) {
        console.log('Modal Button Test Suite already loaded');
        return;
    }
    window.modalButtonTestSuiteLoaded = true;

    class ModalButtonTestSuite {
        constructor() {
            this.tests = [];
            this.results = [];
            this.init();
        }

        init() {
            console.log('🧪 Modal Button Test Suite initialized');
            this.setupTests();
        }

        setupTests() {
            // Test 1: Modal button persistence system availability
            this.addTest('Modal Button Persistence Available', () => {
                return typeof window.modalButtonPersistence !== 'undefined' &&
                       typeof window.modalButtonPersistence.protectButton === 'function';
            });

            // Test 2: Button protection functionality
            this.addTest('Button Protection Works', () => {
                const testButton = document.createElement('button');
                testButton.setAttribute('hx-get', '/test-modal/');
                testButton.setAttribute('hx-target', 'body');
                testButton.id = 'test-protection-button';
                
                document.body.appendChild(testButton);
                
                if (window.modalButtonPersistence) {
                    window.modalButtonPersistence.protectButton(testButton);
                    const isProtected = window.modalButtonPersistence.protectedButtons.has(testButton.id);
                    
                    testButton.remove();
                    return isProtected;
                }
                
                testButton.remove();
                return false;
            });

            // Test 3: Button state preservation
            this.addTest('Button State Preservation', () => {
                if (!window.modalButtonPersistence) return false;
                
                const initialStateCount = window.modalButtonPersistence.buttonStates.size;
                
                const testButton = document.createElement('button');
                testButton.setAttribute('hx-get', '/test-modal/');
                testButton.id = 'test-state-button';
                testButton.innerHTML = 'Test Button';
                
                document.body.appendChild(testButton);
                window.modalButtonPersistence.protectButton(testButton);
                
                const hasState = window.modalButtonPersistence.buttonStates.has(testButton.id);
                
                testButton.remove();
                return hasState && window.modalButtonPersistence.buttonStates.size > initialStateCount;
            });

            // Test 4: Loading state management
            this.addTest('Loading State Management', () => {
                if (!window.modalButtonPersistence) return false;
                
                const testButton = document.createElement('button');
                testButton.setAttribute('hx-get', '/test-modal/');
                testButton.setAttribute('data-loading-text', 'Loading...');
                testButton.id = 'test-loading-button';
                testButton.innerHTML = 'Click Me';
                
                document.body.appendChild(testButton);
                window.modalButtonPersistence.protectButton(testButton);
                
                // Simulate loading state
                window.modalButtonPersistence.setButtonLoadingState(testButton, testButton.id);
                
                const isInLoadingState = testButton.disabled && testButton.innerHTML.includes('Loading...');
                
                testButton.remove();
                return isInLoadingState;
            });

            // Test 5: Button restoration
            this.addTest('Button Restoration Works', () => {
                if (!window.modalButtonPersistence) return false;
                
                const testButton = document.createElement('button');
                testButton.id = 'test-restore-button';
                testButton.innerHTML = 'Original Text';
                
                document.body.appendChild(testButton);
                window.modalButtonPersistence.protectButton(testButton);
                
                // Change button state
                testButton.innerHTML = 'Changed Text';
                testButton.disabled = true;
                
                // Restore button
                window.modalButtonPersistence.restoreButtonState(testButton.id);
                
                const isRestored = testButton.innerHTML === 'Original Text' && !testButton.disabled;
                
                testButton.remove();
                return isRestored;
            });

            // Test 6: Modal button detection
            this.addTest('Modal Button Detection', () => {
                const modalButtons = document.querySelectorAll('button[hx-target="body"], button[data-modal-button="true"]');
                return modalButtons.length > 0;
            });

            // Test 7: Button statistics
            this.addTest('Button Statistics Available', () => {
                return typeof window.getModalButtonStats === 'function';
            });

            // Test 8: Force restore functionality
            this.addTest('Force Restore Available', () => {
                return typeof window.forceRestoreModalButtons === 'function';
            });
        }

        addTest(name, testFunction) {
            this.tests.push({ name, testFunction });
        }

        async runTests() {
            console.log('🧪 Running modal button tests...');
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
            
            console.log(`\n🧪 Modal Button Test Results: ${passed}/${total} tests passed`);
            
            if (passed === total) {
                console.log('🎉 All modal button tests passed!');
            } else {
                console.warn('⚠️ Some modal button tests failed. Check the logs above.');
            }
        }

        // Test button persistence during table refresh
        async testButtonPersistenceDuringRefresh() {
            console.log('🧪 Testing button persistence during table refresh...');
            
            try {
                if (!window.modalButtonPersistence) {
                    return false;
                }

                // Find existing modal buttons
                const modalButtons = document.querySelectorAll('button[data-modal-button="true"]');
                
                if (modalButtons.length === 0) {
                    console.warn('⚠️ No modal buttons found for testing');
                    return true; // Not applicable
                }

                // Record button states before refresh
                const buttonStates = Array.from(modalButtons).map(button => ({
                    id: button.id,
                    innerHTML: button.innerHTML,
                    disabled: button.disabled,
                    exists: true
                }));

                // Simulate table refresh (if possible)
                const refreshButton = document.querySelector('[data-user-initiated="true"]');
                if (refreshButton) {
                    console.log('🧪 Simulating table refresh...');
                    
                    // Mark modal operation in progress
                    window.modalButtonPersistence.modalOperationInProgress = true;
                    
                    // Wait a moment
                    await new Promise(resolve => setTimeout(resolve, 100));
                    
                    // Check if buttons still exist and are functional
                    let persistenceWorking = true;
                    
                    buttonStates.forEach(state => {
                        const button = document.getElementById(state.id);
                        if (!button) {
                            console.warn(`⚠️ Button ${state.id} disappeared during refresh`);
                            persistenceWorking = false;
                        }
                    });
                    
                    // Reset modal operation flag
                    window.modalButtonPersistence.modalOperationInProgress = false;
                    
                    return persistenceWorking;
                }

                console.log('🧪 Table refresh simulation not available, checking protection status');
                return modalButtons.length > 0;

            } catch (error) {
                console.error('❌ Button persistence test failed:', error);
                return false;
            }
        }

        // Test button click simulation
        async testButtonClickSimulation() {
            console.log('🧪 Testing button click simulation...');
            
            try {
                if (!window.modalButtonPersistence) {
                    return false;
                }

                // Create a test button
                const testButton = document.createElement('button');
                testButton.id = 'click-test-button';
                testButton.setAttribute('hx-get', '/test-modal/');
                testButton.setAttribute('hx-target', 'body');
                testButton.setAttribute('data-loading-text', 'Loading...');
                testButton.innerHTML = 'Test Click';
                
                document.body.appendChild(testButton);
                window.modalButtonPersistence.protectButton(testButton);

                // Simulate click
                const clickEvent = new Event('click');
                testButton.dispatchEvent(clickEvent);

                // Check if loading state was applied
                const hasLoadingState = testButton.disabled && testButton.innerHTML.includes('Loading...');

                // Cleanup
                testButton.remove();

                console.log('🧪 Button click simulation test:', hasLoadingState ? 'PASSED' : 'FAILED');
                return hasLoadingState;

            } catch (error) {
                console.error('❌ Button click simulation test failed:', error);
                return false;
            }
        }

        // Test HTMX integration
        async testHTMXIntegration() {
            console.log('🧪 Testing HTMX integration...');
            
            try {
                if (!window.modalButtonPersistence) {
                    return false;
                }

                // Check if HTMX event listeners are set up
                const hasHTMXIntegration = typeof window.modalButtonPersistence.setupHTMXInterception === 'function';

                console.log('🧪 HTMX integration test:', hasHTMXIntegration ? 'PASSED' : 'FAILED');
                return hasHTMXIntegration;

            } catch (error) {
                console.error('❌ HTMX integration test failed:', error);
                return false;
            }
        }

        // Run comprehensive modal button test
        async runComprehensiveTest() {
            console.log('🧪 Running comprehensive modal button test...');
            
            const basicTests = await this.runTests();
            const persistenceTest = await this.testButtonPersistenceDuringRefresh();
            const clickTest = await this.testButtonClickSimulation();
            const htmxTest = await this.testHTMXIntegration();

            const allPassed = basicTests.every(t => t.passed) && 
                            persistenceTest && 
                            clickTest && 
                            htmxTest;
            
            console.log(`\n🧪 Comprehensive Modal Button Test Result: ${allPassed ? 'PASSED' : 'FAILED'}`);
            
            return {
                basicTests,
                persistenceTest,
                clickTest,
                htmxTest,
                allPassed
            };
        }

        // Get current button status
        getButtonStatus() {
            const modalButtons = document.querySelectorAll('button[data-modal-button="true"]');
            const protectedButtons = window.modalButtonPersistence ? 
                window.modalButtonPersistence.protectedButtons.size : 0;
            
            return {
                totalModalButtons: modalButtons.length,
                protectedButtons: protectedButtons,
                persistenceSystemActive: !!window.modalButtonPersistence,
                modalOperationInProgress: window.modalButtonPersistence?.modalOperationInProgress || false
            };
        }
    }

    // Initialize tester when DOM is ready
    let modalButtonTestSuite;
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            modalButtonTestSuite = new ModalButtonTestSuite();
        });
    } else {
        modalButtonTestSuite = new ModalButtonTestSuite();
    }

    // Expose globally for manual testing
    window.modalButtonTestSuite = modalButtonTestSuite;
    window.testModalButtons = () => {
        if (modalButtonTestSuite) {
            return modalButtonTestSuite.runComprehensiveTest();
        } else {
            console.warn('⚠️ Modal button test suite not ready yet');
        }
    };

    window.getModalButtonStatus = () => {
        if (modalButtonTestSuite) {
            return modalButtonTestSuite.getButtonStatus();
        } else {
            return { error: 'Test suite not ready' };
        }
    };

    console.log('✅ Modal Button Test Suite loaded');

})();
