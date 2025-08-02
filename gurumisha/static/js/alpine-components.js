/**
 * Alpine.js Components for Gurumisha
 * Centralized Alpine.js component definitions and initialization
 * Version 2.0 - Optimized for unified hydration system
 */

(function() {
    'use strict';

    // Prevent multiple script executions
    if (window.alpineComponentsLoaded) {
        console.log('Alpine components already loaded');
        return;
    }
    window.alpineComponentsLoaded = true;

    // Global Alpine.js component registry with initialization tracking
    window.alpineComponents = {};
    window.alpineComponentInstances = new Map(); // Track component instances

    /**
     * Edit Car Modal Component
     */
    window.alpineComponents.editCarModal = function() {
        return {
            show: false,
            activeTab: 'basic',
            isSubmitting: false,
            initialized: false,

            // Initialize the modal (with double-init protection)
            initModal() {
                if (this.initialized) {
                    console.log('🎯 Modal already initialized, skipping');
                    return;
                }

                console.log('🎯 Alpine.js modal component initialized');
                this.initialized = true;
                this.show = true;

                // Register this instance
                const modalId = this.$el.id || 'edit-car-modal';
                window.alpineComponentInstances.set(modalId, this);

                // Focus management
                this.$nextTick(() => {
                    const firstInput = this.$el.querySelector('input, select, textarea');
                    if (firstInput) {
                        firstInput.focus();
                        console.log('🎯 Focus set to first input');
                    }
                });

                // Initialize additional components
                this.initializeComponents();
            },

            // Close modal function
            closeModal() {
                console.log('🚪 Closing modal');
                this.show = false;

                // Call global restoreScroll() function
                if (typeof window.restoreScroll === 'function') {
                    window.restoreScroll();
                }

                setTimeout(() => {
                    if (this.$el && this.$el.remove) {
                        this.$el.remove();
                        console.log('🗑️ Modal removed from DOM');
                    }

                    // Ensure restoreScroll() is called again after DOM removal
                    if (typeof window.restoreScroll === 'function') {
                        window.restoreScroll();
                    }
                }, 200);
            },

            // Switch tabs
            switchTab(tab) {
                console.log('📑 Switching to tab:', tab);
                this.activeTab = tab;
            },

            // Initialize additional components
            initializeComponents() {
                this.initHotDealToggles();
                this.initFormValidation();
                this.initPriceFormatting();
            },

            // Initialize hot deal toggles
            initHotDealToggles() {
                const hotDealCheckbox = this.$el.querySelector('#id_is_hot_deal');
                if (hotDealCheckbox) {
                    hotDealCheckbox.addEventListener('change', (e) => {
                        if (typeof toggleHotDealFields === 'function') {
                            toggleHotDealFields(e.target.checked);
                        }
                    });

                    if (hotDealCheckbox.checked && typeof toggleHotDealFields === 'function') {
                        toggleHotDealFields(true);
                    }
                }

                const featuredCheckbox = this.$el.querySelector('#id_is_featured');
                if (featuredCheckbox) {
                    featuredCheckbox.addEventListener('change', (e) => {
                        if (typeof toggleFeaturedFields === 'function') {
                            toggleFeaturedFields(e.target.checked);
                        }
                    });

                    if (featuredCheckbox.checked && typeof toggleFeaturedFields === 'function') {
                        toggleFeaturedFields(true);
                    }
                }
            },

            // Initialize form validation
            initFormValidation() {
                const form = this.$el.querySelector('#edit-car-form');
                if (form) {
                    form.addEventListener('submit', (e) => {
                        if (!this.validateForm()) {
                            e.preventDefault();
                            return false;
                        }
                        this.isSubmitting = true;
                    });
                }
            },

            // Initialize price formatting
            initPriceFormatting() {
                const priceInputs = this.$el.querySelectorAll('.price-format');
                priceInputs.forEach(input => {
                    if (typeof formatPrice === 'function') {
                        input.addEventListener('input', (e) => {
                            formatPrice(e.target);
                        });
                    }
                });
            },

            // Form validation
            validateForm() {
                // Basic validation - can be extended
                const requiredFields = this.$el.querySelectorAll('[required]');
                let isValid = true;

                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        field.classList.add('border-red-500');
                        isValid = false;
                    } else {
                        field.classList.remove('border-red-500');
                    }
                });

                return isValid;
            }
        };
    };

    /**
     * Image Gallery Component
     */
    window.alpineComponents.imageGallery = function() {
        return {
            images: [],
            currentIndex: 0,
            currentImage: null,
            loading: true,
            fullscreenOpen: false,

            init() {
                console.log('🖼️ Image gallery component initialized');
                // Initialize with images passed from parent template
                if (window.galleryImages) {
                    this.images = window.galleryImages;
                    this.setCurrentImage(0);
                }
            },

            setCurrentImage(index) {
                if (index >= 0 && index < this.images.length) {
                    this.currentIndex = index;
                    this.currentImage = this.images[index];
                    this.loading = true;
                }
            },

            nextImage() {
                if (this.currentIndex < this.images.length - 1) {
                    this.setCurrentImage(this.currentIndex + 1);
                }
            },

            previousImage() {
                if (this.currentIndex > 0) {
                    this.setCurrentImage(this.currentIndex - 1);
                }
            },

            openFullscreen() {
                this.fullscreenOpen = true;
                // Use global scroll management if available
                if (typeof window.setGlobalBodyScrollLock === 'function') {
                    window.setGlobalBodyScrollLock();
                } else {
                    document.body.style.overflow = 'hidden';
                }
            },

            closeFullscreen() {
                this.fullscreenOpen = false;

                // Call global restoreScroll() function first
                if (typeof window.restoreScroll === 'function') {
                    window.restoreScroll();
                } else if (typeof window.restoreGlobalBodyScroll === 'function') {
                    // Fallback to legacy function
                    window.restoreGlobalBodyScroll();
                    // Also run final check
                    if (typeof window.finalGlobalScrollCheck === 'function') {
                        window.finalGlobalScrollCheck();
                    }
                } else {
                    document.body.style.overflow = 'auto';
                }
            },

            handleImageError() {
                this.loading = false;
                console.error('Failed to load image:', this.currentImage?.url);
            }
        };
    };

    /**
     * Live Tracking Map Component
     */
    window.alpineComponents.liveTrackingMap = function() {
        return {
            map: null,
            marker: null,
            orderNumber: '',
            currentLat: 0,
            currentLng: 0,

            initializeMap() {
                console.log('🗺️ Live tracking map component initialized');
                this.orderNumber = this.$el.dataset.orderNumber;
                this.currentLat = parseFloat(this.$el.dataset.currentLat) || 0;
                this.currentLng = parseFloat(this.$el.dataset.currentLng) || 0;

                // Initialize map if coordinates are available
                if (this.currentLat && this.currentLng) {
                    this.createMap();
                }
            },

            createMap() {
                // Map creation logic would go here
                // This is a placeholder for the actual map implementation
                console.log('Creating map for order:', this.orderNumber);
            },

            updateMapFromResponse(event) {
                // Update map from HTMX response
                console.log('Updating map from HTMX response');
                // Implementation would depend on the specific map library used
            }
        };
    };

    /**
     * Live Dashboard Component
     */
    window.alpineComponents.liveDashboard = function() {
        return {
            initialized: false,

            initializeDashboard() {
                console.log('📊 Live dashboard component initialized');
                this.initialized = true;
            }
        };
    };

    /**
     * Live Notifications Component
     */
    window.alpineComponents.liveNotifications = function() {
        return {
            notifications: [],

            initializeNotifications() {
                console.log('🔔 Live notifications component initialized');
            },

            updateNotifications(event) {
                console.log('Updating notifications from HTMX response');
                // Implementation for updating notifications
            }
        };
    };

    // Global function to get Alpine component
    window.getAlpineComponent = function(componentName) {
        return window.alpineComponents[componentName] || function() {
            console.warn(`Alpine component '${componentName}' not found`);
            return {};
        };
    };

    // Helper function to safely initialize Alpine components
    window.initAlpineComponent = function(element, componentName) {
        if (!element || !componentName) return false;

        const elementId = element.id || `alpine_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        // Check if already initialized
        if (window.alpineComponentInstances.has(elementId)) {
            console.log(`🏔️ Alpine component '${componentName}' already initialized for element:`, elementId);
            return true;
        }

        try {
            // Set the component data
            const componentFunction = window.alpineComponents[componentName];
            if (componentFunction) {
                element.setAttribute('x-data', `${componentName}()`);

                // Initialize with Alpine if available
                if (typeof Alpine !== 'undefined' && Alpine.initTree) {
                    Alpine.initTree(element);
                    console.log(`🏔️ Successfully initialized Alpine component '${componentName}' for element:`, elementId);
                    return true;
                }
            }
        } catch (error) {
            console.error(`❌ Failed to initialize Alpine component '${componentName}':`, error);
        }

        return false;
    };

    // Helper function to safely set Alpine data
    window.safeAlpineSet = function(property, value, context) {
        try {
            if (context && typeof context[property] !== 'undefined') {
                context[property] = value;
                return true;
            } else if (typeof window[property] !== 'undefined') {
                window[property] = value;
                return true;
            }
        } catch (error) {
            console.warn(`⚠️ Could not set Alpine property '${property}':`, error);
        }
        return false;
    };

    // Expose individual components globally for backward compatibility
    window.editCarModal = window.alpineComponents.editCarModal;
    window.imageGallery = window.alpineComponents.imageGallery;
    window.liveTrackingMap = window.alpineComponents.liveTrackingMap;
    window.liveDashboard = window.alpineComponents.liveDashboard;
    window.liveNotifications = window.alpineComponents.liveNotifications;

    console.log('✅ Alpine.js components v2.0 loaded and registered');

})();
