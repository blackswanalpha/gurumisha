/**
 * Alpine.js Initialization Guard for Gurumisha
 * Prevents multiple Alpine.js initialization and provides safe utilities
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.alpineInitializationGuardLoaded) {
        console.log('Alpine initialization guard already loaded');
        return;
    }
    window.alpineInitializationGuardLoaded = true;

    class AlpineInitializationGuard {
        constructor() {
            this.isAlpineReady = false;
            this.initializationAttempts = 0;
            this.maxAttempts = 3;
            this.init();
        }

        init() {
            console.log('🛡️ Alpine.js Initialization Guard loaded');
            this.setupAlpineReadyDetection();
            this.preventMultipleStarts();
        }

        /**
         * Setup Alpine.js ready detection
         */
        setupAlpineReadyDetection() {
            // Check if Alpine.js is already available
            if (typeof Alpine !== 'undefined') {
                this.handleAlpineReady();
                return;
            }

            // Wait for Alpine.js to be available
            const checkAlpine = () => {
                if (typeof Alpine !== 'undefined') {
                    this.handleAlpineReady();
                } else if (this.initializationAttempts < this.maxAttempts) {
                    this.initializationAttempts++;
                    setTimeout(checkAlpine, 100);
                } else {
                    console.warn('⚠️ Alpine.js not detected after maximum attempts');
                }
            };

            // Start checking
            setTimeout(checkAlpine, 50);
        }

        /**
         * Handle Alpine.js ready state
         */
        handleAlpineReady() {
            console.log('🏔️ Alpine.js detected and ready');
            this.isAlpineReady = true;
            
            // Set up Alpine.js event listeners
            this.setupAlpineEventListeners();
            
            // Expose safe utilities
            this.exposeSafeUtilities();
        }

        /**
         * Prevent multiple Alpine.js starts
         */
        preventMultipleStarts() {
            // Override Alpine.start to prevent multiple calls
            const originalStart = window.Alpine?.start;
            
            if (originalStart) {
                let startCalled = false;
                
                window.Alpine.start = function() {
                    if (startCalled) {
                        console.warn('🛡️ Alpine.start() already called, ignoring duplicate call');
                        return;
                    }
                    
                    startCalled = true;
                    console.log('🏔️ Alpine.js starting (first call)');
                    return originalStart.apply(this, arguments);
                };
            }
        }

        /**
         * Setup Alpine.js event listeners
         */
        setupAlpineEventListeners() {
            if (typeof Alpine === 'undefined') return;

            // Listen for Alpine.js initialization events
            document.addEventListener('alpine:init', () => {
                console.log('🏔️ Alpine.js initialized');
            });

            document.addEventListener('alpine:initialized', () => {
                console.log('🏔️ Alpine.js fully initialized');
            });
        }

        /**
         * Expose safe utilities
         */
        exposeSafeUtilities() {
            // Safe Alpine.js initialization utility
            window.safeAlpineInit = (element) => {
                if (!this.isAlpineReady || typeof Alpine === 'undefined' || !Alpine.initTree) {
                    console.warn('⚠️ Alpine.js not ready for initialization');
                    return false;
                }

                try {
                    // Only initialize if not already initialized
                    if (!element._x_dataStack || element._x_dataStack.length === 0) {
                        Alpine.initTree(element);
                        return true;
                    } else {
                        console.log('🏔️ Alpine.js component already initialized');
                        return true;
                    }
                } catch (error) {
                    console.error('❌ Error initializing Alpine.js component:', error);
                    return false;
                }
            };

            // Safe Alpine.js batch initialization
            window.safeAlpineBatchInit = (container) => {
                if (!this.isAlpineReady || typeof Alpine === 'undefined' || !Alpine.initTree) {
                    console.warn('⚠️ Alpine.js not ready for batch initialization');
                    return 0;
                }

                const alpineElements = container.querySelectorAll('[x-data]');
                let initializedCount = 0;

                alpineElements.forEach(element => {
                    if (window.safeAlpineInit(element)) {
                        initializedCount++;
                    }
                });

                console.log(`🏔️ Batch initialized ${initializedCount}/${alpineElements.length} Alpine.js components`);
                return initializedCount;
            };

            // Alpine.js readiness checker
            window.isAlpineReady = () => {
                return this.isAlpineReady && 
                       typeof Alpine !== 'undefined' && 
                       Alpine.initTree && 
                       typeof Alpine.initTree === 'function';
            };

            // Alpine.js status reporter
            window.getAlpineStatus = () => {
                return {
                    isReady: this.isAlpineReady,
                    isAvailable: typeof Alpine !== 'undefined',
                    hasInitTree: typeof Alpine !== 'undefined' && typeof Alpine.initTree === 'function',
                    initializationAttempts: this.initializationAttempts,
                    version: typeof Alpine !== 'undefined' ? Alpine.version : null
                };
            };
        }

        /**
         * Check if Alpine.js is properly initialized
         */
        checkAlpineStatus() {
            const status = {
                available: typeof Alpine !== 'undefined',
                ready: this.isAlpineReady,
                hasInitTree: typeof Alpine !== 'undefined' && typeof Alpine.initTree === 'function',
                attempts: this.initializationAttempts
            };

            console.log('🏔️ Alpine.js Status:', status);
            return status;
        }
    }

    // Initialize the guard
    window.alpineInitializationGuard = new AlpineInitializationGuard();

    // Expose status checker
    window.checkAlpineStatus = () => {
        return window.alpineInitializationGuard.checkAlpineStatus();
    };

    console.log('✅ Alpine.js Initialization Guard loaded');

})();
