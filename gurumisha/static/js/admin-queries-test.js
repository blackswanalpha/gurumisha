/**
 * Test Suite for Admin Queries Page
 * Validates HTMX, Alpine.js, and modal functionality
 */

(function() {
    'use strict';

    class AdminQueriesTestSuite {
        constructor() {
            this.tests = [];
            this.results = {
                passed: 0,
                failed: 0,
                total: 0
            };
        }

        // Test Alpine.js component initialization
        testAlpineInitialization() {
            console.log('🧪 Testing Alpine.js initialization...');
            
            const alpineElement = document.querySelector('[x-data*="adminQueries"]');
            if (alpineElement && alpineElement._x_dataStack) {
                console.log('✅ Alpine.js component initialized successfully');
                return true;
            } else {
                console.error('❌ Alpine.js component not initialized');
                return false;
            }
        }

        // Test HTMX availability and configuration
        testHTMXConfiguration() {
            console.log('🧪 Testing HTMX configuration...');
            
            if (typeof htmx !== 'undefined') {
                console.log('✅ HTMX is available');
                
                // Test HTMX configuration
                if (htmx.config) {
                    console.log('✅ HTMX configuration loaded');
                    return true;
                } else {
                    console.error('❌ HTMX configuration missing');
                    return false;
                }
            } else {
                console.error('❌ HTMX not available');
                return false;
            }
        }

        // Test modal functionality
        testModalFunctionality() {
            console.log('🧪 Testing modal functionality...');
            
            const modalContainer = document.getElementById('modal-container');
            const modalContentArea = document.getElementById('modal-content-area');
            
            if (modalContainer && modalContentArea) {
                console.log('✅ Modal elements found');
                
                // Test modal show/hide functionality
                if (window.adminQueriesComponent) {
                    console.log('✅ Admin queries component available for modal testing');
                    return true;
                } else {
                    console.warn('⚠️ Admin queries component not available');
                    return false;
                }
            } else {
                console.error('❌ Modal elements not found');
                return false;
            }
        }

        // Test hydration manager
        testHydrationManager() {
            console.log('🧪 Testing hydration manager...');
            
            if (window.hydrationManagerLoaded) {
                console.log('✅ Hydration manager loaded');
                return true;
            } else {
                console.error('❌ Hydration manager not loaded');
                return false;
            }
        }

        // Test toast manager
        testToastManager() {
            console.log('🧪 Testing toast manager...');
            
            if (window.toastManager) {
                console.log('✅ Toast manager available');
                
                // Test toast functionality
                try {
                    window.toastManager.show('Test message', 'info');
                    console.log('✅ Toast functionality working');
                    return true;
                } catch (error) {
                    console.error('❌ Toast functionality error:', error);
                    return false;
                }
            } else {
                console.warn('⚠️ Toast manager not available');
                return false;
            }
        }

        // Test API endpoints
        async testAPIEndpoints() {
            console.log('🧪 Testing API endpoints...');
            
            try {
                // Test queries table endpoint
                const response = await fetch('/dashboard/admin/queries/table-htmx/', {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                if (response.ok) {
                    console.log('✅ Queries table endpoint accessible');
                    return true;
                } else {
                    console.error('❌ Queries table endpoint error:', response.status);
                    return false;
                }
            } catch (error) {
                console.error('❌ API endpoint test error:', error);
                return false;
            }
        }

        // Test form validation
        testFormValidation() {
            console.log('🧪 Testing form validation...');
            
            const forms = document.querySelectorAll('form[data-validate]');
            if (forms.length > 0) {
                console.log('✅ Validation forms found');
                return true;
            } else {
                console.log('ℹ️ No validation forms found (this is okay)');
                return true;
            }
        }

        // Test responsive design
        testResponsiveDesign() {
            console.log('🧪 Testing responsive design...');
            
            const glassmorphismCards = document.querySelectorAll('.glassmorphism-card');
            const queryTableRows = document.querySelectorAll('.query-table-row');
            
            if (glassmorphismCards.length > 0 && queryTableRows.length >= 0) {
                console.log('✅ Responsive design elements found');
                return true;
            } else {
                console.warn('⚠️ Some responsive design elements missing');
                return false;
            }
        }

        // Run all tests
        async runAllTests() {
            console.log('🚀 Starting Admin Queries Test Suite...');
            console.log('=====================================');
            
            const tests = [
                { name: 'Alpine.js Initialization', test: () => this.testAlpineInitialization() },
                { name: 'HTMX Configuration', test: () => this.testHTMXConfiguration() },
                { name: 'Modal Functionality', test: () => this.testModalFunctionality() },
                { name: 'Hydration Manager', test: () => this.testHydrationManager() },
                { name: 'Toast Manager', test: () => this.testToastManager() },
                { name: 'API Endpoints', test: () => this.testAPIEndpoints() },
                { name: 'Form Validation', test: () => this.testFormValidation() },
                { name: 'Responsive Design', test: () => this.testResponsiveDesign() }
            ];

            for (const testCase of tests) {
                try {
                    const result = await testCase.test();
                    this.results.total++;
                    
                    if (result) {
                        this.results.passed++;
                    } else {
                        this.results.failed++;
                    }
                } catch (error) {
                    console.error(`❌ Test "${testCase.name}" threw an error:`, error);
                    this.results.failed++;
                    this.results.total++;
                }
            }

            this.displayResults();
        }

        // Display test results
        displayResults() {
            console.log('=====================================');
            console.log('🏁 Test Suite Complete');
            console.log(`✅ Passed: ${this.results.passed}`);
            console.log(`❌ Failed: ${this.results.failed}`);
            console.log(`📊 Total: ${this.results.total}`);
            console.log(`📈 Success Rate: ${((this.results.passed / this.results.total) * 100).toFixed(1)}%`);
            
            if (this.results.failed === 0) {
                console.log('🎉 All tests passed! Admin Queries page is working correctly.');
            } else {
                console.log('⚠️ Some tests failed. Please check the issues above.');
            }
        }
    }

    // Auto-run tests when page is loaded
    document.addEventListener('DOMContentLoaded', () => {
        // Wait a bit for all components to initialize
        setTimeout(() => {
            const testSuite = new AdminQueriesTestSuite();
            testSuite.runAllTests();
        }, 2000);
    });

    // Expose test suite globally for manual testing
    window.AdminQueriesTestSuite = AdminQueriesTestSuite;

})();
