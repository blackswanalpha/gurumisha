/**
 * Button Persistence Test Suite for Gurumisha
 * Tests button functionality after HTMX operations
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.buttonPersistenceTestLoaded) {
        console.log('Button persistence test already loaded');
        return;
    }
    window.buttonPersistenceTestLoaded = true;

    class ButtonPersistenceTest {
        constructor() {
            this.tests = [];
            this.results = [];
            this.init();
        }

        init() {
            console.log('🧪 Button Persistence Test Suite initialized');
            this.setupTests();
        }

        setupTests() {
            // Test 1: Button registry availability
            this.addTest('Button Registry Available', () => {
                return typeof window.getHTMXButtonRegistry === 'function' && 
                       window.getHTMXButtonRegistry() instanceof Map;
            });

            // Test 2: Enhanced HTMX integration
            this.addTest('Enhanced HTMX Integration Available', () => {
                return typeof window.enhancedHTMXIntegration !== 'undefined';
            });

            // Test 3: Button preservation attributes
            this.addTest('Buttons Have Preservation Attributes', () => {
                const buttons = document.querySelectorAll('button[hx-get], button[hx-post]');
                let preservedCount = 0;
                
                buttons.forEach(button => {
                    if (button.hasAttribute('data-preserve') || 
                        button.hasAttribute('data-loading-text')) {
                        preservedCount++;
                    }
                });
                
                return preservedCount > 0;
            });

            // Test 4: HTMX targeting strategy
            this.addTest('HTMX Uses Safe Targeting', () => {
                const htmxElements = document.querySelectorAll('[hx-target]');
                let safeTargets = 0;
                
                htmxElements.forEach(element => {
                    const target = element.getAttribute('hx-target');
                    const swap = element.getAttribute('hx-swap');
                    
                    // Check for safe targeting patterns
                    if (target === 'body' && swap === 'beforeend') {
                        safeTargets++; // Modal buttons - safe
                    } else if (target === '#tracking-table-content' && swap === 'innerHTML') {
                        safeTargets++; // Table updates - safe
                    } else if (!target.includes('tracking-management-table') || swap !== 'outerHTML') {
                        safeTargets++; // Other safe patterns
                    }
                });
                
                return safeTargets === htmxElements.length;
            });
        }

        addTest(name, testFunction) {
            this.tests.push({ name, testFunction });
        }

        async runTests() {
            console.log('🧪 Running button persistence tests...');
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
            
            console.log(`\n🧪 Button Persistence Test Results: ${passed}/${total} tests passed`);
            
            if (passed === total) {
                console.log('🎉 All button persistence tests passed!');
            } else {
                console.warn('⚠️ Some button persistence tests failed. Check the logs above.');
            }
        }

        // Test button functionality after HTMX operation
        async testButtonAfterHTMX() {
            console.log('🧪 Testing button functionality after HTMX operation...');
            
            try {
                // Find a button that triggers HTMX
                const testButton = document.querySelector('button[hx-get], button[hx-post]');
                if (!testButton) {
                    console.warn('⚠️ No HTMX buttons found for testing');
                    return false;
                }

                // Record initial state
                const initialId = testButton.id;
                const initialHxGet = testButton.getAttribute('hx-get');
                const initialHxPost = testButton.getAttribute('hx-post');
                
                // Check if button is registered
                const registry = window.getHTMXButtonRegistry ? window.getHTMXButtonRegistry() : new Map();
                const isRegistered = registry.has(initialId);
                
                console.log(`🧪 Button test results:`);
                console.log(`  - Button ID: ${initialId}`);
                console.log(`  - Has HTMX attributes: ${!!(initialHxGet || initialHxPost)}`);
                console.log(`  - Is registered: ${isRegistered}`);
                console.log(`  - Has preservation attributes: ${testButton.hasAttribute('data-preserve')}`);
                
                return !!(initialId && (initialHxGet || initialHxPost) && isRegistered);

            } catch (error) {
                console.error('❌ Button functionality test failed:', error);
                return false;
            }
        }

        // Test HTMX targeting safety
        async testHTMXTargetingSafety() {
            console.log('🧪 Testing HTMX targeting safety...');
            
            try {
                const unsafePatterns = [];
                const htmxElements = document.querySelectorAll('[hx-target]');
                
                htmxElements.forEach(element => {
                    const target = element.getAttribute('hx-target');
                    const swap = element.getAttribute('hx-swap');
                    const elementInfo = `${element.tagName}[${element.className}]`;
                    
                    // Check for unsafe patterns
                    if (target === '#tracking-management-table' && swap === 'outerHTML') {
                        unsafePatterns.push(`${elementInfo} replaces entire table container`);
                    }
                    
                    if (target.includes('button') && swap === 'outerHTML') {
                        unsafePatterns.push(`${elementInfo} replaces button container`);
                    }
                });
                
                if (unsafePatterns.length > 0) {
                    console.warn('⚠️ Unsafe HTMX patterns found:', unsafePatterns);
                    return false;
                }
                
                console.log('✅ All HTMX targeting patterns are safe');
                return true;

            } catch (error) {
                console.error('❌ HTMX targeting safety test failed:', error);
                return false;
            }
        }

        // Test button preservation during table updates
        async testButtonPreservationDuringTableUpdate() {
            console.log('🧪 Testing button preservation during table updates...');
            
            try {
                // Find table buttons
                const tableButtons = document.querySelectorAll('#tracking-management-table button[hx-get], #tracking-management-table button[hx-post]');
                
                if (tableButtons.length === 0) {
                    console.warn('⚠️ No table buttons found for testing');
                    return true; // Not applicable
                }

                // Check if buttons have preservation attributes
                let preservedButtons = 0;
                tableButtons.forEach(button => {
                    if (button.hasAttribute('data-preserve') || 
                        button.hasAttribute('data-loading-text') ||
                        button.getAttribute('hx-target') === 'body') {
                        preservedButtons++;
                    }
                });

                const preservationRate = preservedButtons / tableButtons.length;
                console.log(`🧪 Button preservation rate: ${preservationRate * 100}% (${preservedButtons}/${tableButtons.length})`);
                
                return preservationRate >= 0.8; // At least 80% should be preserved

            } catch (error) {
                console.error('❌ Button preservation test failed:', error);
                return false;
            }
        }

        // Run comprehensive button persistence test
        async runComprehensiveTest() {
            console.log('🧪 Running comprehensive button persistence test...');
            
            const basicTests = await this.runTests();
            const buttonFunctionality = await this.testButtonAfterHTMX();
            const targetingSafety = await this.testHTMXTargetingSafety();
            const preservationTest = await this.testButtonPreservationDuringTableUpdate();

            const allPassed = basicTests.every(t => t.passed) && 
                            buttonFunctionality && 
                            targetingSafety && 
                            preservationTest;
            
            console.log(`\n🧪 Comprehensive Button Persistence Test Result: ${allPassed ? 'PASSED' : 'FAILED'}`);
            
            return {
                basicTests,
                buttonFunctionality,
                targetingSafety,
                preservationTest,
                allPassed
            };
        }
    }

    // Initialize tester when DOM is ready
    let buttonPersistenceTest;
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            buttonPersistenceTest = new ButtonPersistenceTest();
        });
    } else {
        buttonPersistenceTest = new ButtonPersistenceTest();
    }

    // Expose globally for manual testing
    window.buttonPersistenceTest = buttonPersistenceTest;
    window.testButtonPersistence = () => {
        if (buttonPersistenceTest) {
            return buttonPersistenceTest.runComprehensiveTest();
        } else {
            console.warn('⚠️ Button persistence test suite not ready yet');
        }
    };

    console.log('✅ Button Persistence Test Suite loaded');

})();
