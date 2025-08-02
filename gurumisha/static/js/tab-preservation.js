/**
 * Tab and Button Preservation System for HTMX + Hydration Frameworks
 * Fixes common issues with tabs and buttons losing functionality after HTMX swaps
 */

(function() {
    'use strict';

    /**
     * Tab Preservation Manager
     */
    window.TabPreservationManager = {
        // Store active tab states
        activeTabStates: new Map(),
        
        // Store tab event listeners
        tabEventListeners: new Map(),
        
        // Store button states
        buttonStates: new Map(),

        /**
         * Initialize tab preservation system
         */
        init: function() {
            this.setupHTMXEventListeners();
            this.preserveInitialTabStates();
            this.setupGlobalTabHandlers();
            console.log('✅ Tab Preservation Manager initialized');
        },

        /**
         * Setup HTMX event listeners for tab preservation
         */
        setupHTMXEventListeners: function() {
            // Before HTMX swap - preserve tab states
            document.addEventListener('htmx:beforeSwap', (event) => {
                this.preserveTabStates(event.detail.target);
                this.preserveButtonStates(event.detail.target);
            });

            // After HTMX swap - restore tab functionality
            document.addEventListener('htmx:afterSwap', (event) => {
                this.restoreTabFunctionality(event.detail.target);
                this.restoreButtonFunctionality(event.detail.target);
                this.rehydrateComponents(event.detail.target);
            });

            // After HTMX settle - final cleanup
            document.addEventListener('htmx:afterSettle', (event) => {
                this.finalizeTabRestoration(event.detail.target);
            });
        },

        /**
         * Preserve current tab states before swap
         */
        preserveTabStates: function(targetElement) {
            const tabContainers = targetElement.querySelectorAll('[data-tab-container], .tab-navigation, .content-tab-container');
            
            tabContainers.forEach(container => {
                const containerId = container.id || this.generateId(container, 'tab-container-');
                const activeTab = container.querySelector('.nav-tab.active, .content-tab.active, .tab-button.active');
                const activeContent = container.querySelector('.tab-content-panel.active, .tab-content.active');
                
                if (activeTab) {
                    this.activeTabStates.set(containerId, {
                        activeTabId: activeTab.id || activeTab.getAttribute('data-tab'),
                        activeTabData: activeTab.getAttribute('data-tab'),
                        activeContentId: activeContent ? activeContent.id : null,
                        scrollPosition: this.getScrollPosition(container)
                    });
                    
                    console.log(`🔒 Preserved tab state for container: ${containerId}`);
                }
            });
        },

        /**
         * Preserve button states before swap
         */
        preserveButtonStates: function(targetElement) {
            const buttons = targetElement.querySelectorAll('button[data-preserve-state], .preserve-button-state');
            
            buttons.forEach(button => {
                const buttonId = button.id || this.generateId(button, 'btn-');
                this.buttonStates.set(buttonId, {
                    innerHTML: button.innerHTML,
                    className: button.className,
                    disabled: button.disabled,
                    ariaSelected: button.getAttribute('aria-selected'),
                    dataAttributes: this.getDataAttributes(button)
                });
            });
        },

        /**
         * Restore tab functionality after swap
         */
        restoreTabFunctionality: function(targetElement) {
            // Find all tab containers in the swapped content
            const tabContainers = targetElement.querySelectorAll('[data-tab-container], .tab-navigation, .content-tab-container');
            
            tabContainers.forEach(container => {
                const containerId = container.id || this.generateId(container, 'tab-container-');
                const preservedState = this.activeTabStates.get(containerId);
                
                if (preservedState) {
                    this.restoreActiveTab(container, preservedState);
                }
                
                // Re-initialize tab event listeners
                this.initializeTabContainer(container);
            });

            // Initialize any new tab containers
            this.initializeNewTabs(targetElement);
        },

        /**
         * Restore active tab state
         */
        restoreActiveTab: function(container, state) {
            // Remove active classes from all tabs and content
            const allTabs = container.querySelectorAll('.nav-tab, .content-tab, .tab-button');
            const allContent = container.querySelectorAll('.tab-content-panel, .tab-content');
            
            allTabs.forEach(tab => tab.classList.remove('active'));
            allContent.forEach(content => content.classList.remove('active'));
            
            // Restore active tab
            let activeTab = null;
            if (state.activeTabId) {
                activeTab = container.querySelector(`#${state.activeTabId}`);
            }
            if (!activeTab && state.activeTabData) {
                activeTab = container.querySelector(`[data-tab="${state.activeTabData}"]`);
            }
            
            if (activeTab) {
                activeTab.classList.add('active');
                activeTab.setAttribute('aria-selected', 'true');
                
                // Restore active content
                const targetTab = activeTab.getAttribute('data-tab');
                const activeContent = container.querySelector(`#${targetTab}-tab, [data-tab-content="${targetTab}"]`);
                if (activeContent) {
                    activeContent.classList.add('active');
                    activeContent.style.display = 'block';
                }
                
                console.log(`🔓 Restored active tab: ${targetTab}`);
            }
            
            // Restore scroll position
            if (state.scrollPosition) {
                this.restoreScrollPosition(container, state.scrollPosition);
            }
        },

        /**
         * Initialize tab container with event listeners
         */
        initializeTabContainer: function(container) {
            const tabs = container.querySelectorAll('.nav-tab, .content-tab, .tab-button');
            
            tabs.forEach(tab => {
                // Remove existing listeners to prevent duplicates
                const newTab = tab.cloneNode(true);
                tab.parentNode.replaceChild(newTab, tab);
                
                // Add click listener
                newTab.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.handleTabClick(newTab, container);
                });
                
                // Add keyboard support
                newTab.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.handleTabClick(newTab, container);
                    }
                });
                
                // Add HTMX support
                if (newTab.hasAttribute('hx-get')) {
                    newTab.addEventListener('htmx:afterRequest', (e) => {
                        if (e.detail.successful) {
                            this.handleTabClick(newTab, container);
                        }
                    });
                }
            });
        },

        /**
         * Handle tab click with proper state management
         */
        handleTabClick: function(clickedTab, container) {
            const targetTab = clickedTab.getAttribute('data-tab');
            
            if (!targetTab) return;
            
            // Update tab states
            const allTabs = container.querySelectorAll('.nav-tab, .content-tab, .tab-button');
            const allContent = container.querySelectorAll('.tab-content-panel, .tab-content');
            
            // Remove active states
            allTabs.forEach(tab => {
                tab.classList.remove('active');
                tab.setAttribute('aria-selected', 'false');
            });
            allContent.forEach(content => {
                content.classList.remove('active');
                content.style.display = 'none';
            });
            
            // Set active states
            clickedTab.classList.add('active');
            clickedTab.setAttribute('aria-selected', 'true');
            
            // Show target content
            const targetContent = container.querySelector(`#${targetTab}-tab, [data-tab-content="${targetTab}"]`);
            if (targetContent) {
                targetContent.classList.add('active');
                targetContent.style.display = 'block';
            }
            
            // Update mobile selector if present
            const mobileSelect = container.querySelector('.mobile-tab-select, select[data-tab-select]');
            if (mobileSelect) {
                mobileSelect.value = targetTab;
            }
            
            // Trigger custom event
            container.dispatchEvent(new CustomEvent('tab:changed', {
                detail: { activeTab: targetTab, clickedElement: clickedTab }
            }));
            
            console.log(`🎯 Tab switched to: ${targetTab}`);
        },

        /**
         * Initialize new tabs that weren't present before
         */
        initializeNewTabs: function(targetElement) {
            const newTabContainers = targetElement.querySelectorAll('[data-tab-container]:not([data-initialized]), .tab-navigation:not([data-initialized])');
            
            newTabContainers.forEach(container => {
                this.initializeTabContainer(container);
                container.setAttribute('data-initialized', 'true');
            });
        },

        /**
         * Restore button functionality after swap
         */
        restoreButtonFunctionality: function(targetElement) {
            const buttons = targetElement.querySelectorAll('button');
            
            buttons.forEach(button => {
                const buttonId = button.id;
                const preservedState = this.buttonStates.get(buttonId);
                
                if (preservedState) {
                    // Restore button state if needed
                    if (button.getAttribute('data-preserve-state') === 'true') {
                        button.className = preservedState.className;
                        button.disabled = preservedState.disabled;
                        if (preservedState.ariaSelected) {
                            button.setAttribute('aria-selected', preservedState.ariaSelected);
                        }
                    }
                }
                
                // Re-initialize button if it has special functionality
                this.initializeButton(button);
            });
        },

        /**
         * Initialize button with enhanced functionality
         */
        initializeButton: function(button) {
            // Add loading state management for HTMX buttons
            if (button.hasAttribute('hx-get') || button.hasAttribute('hx-post')) {
                button.addEventListener('htmx:beforeRequest', function() {
                    this.setAttribute('aria-busy', 'true');
                    this.style.opacity = '0.7';
                });
                
                button.addEventListener('htmx:afterRequest', function() {
                    this.removeAttribute('aria-busy');
                    this.style.opacity = '1';
                });
            }
        },

        /**
         * Re-hydrate components after swap
         */
        rehydrateComponents: function(targetElement) {
            // Alpine.js hydration
            if (typeof Alpine !== 'undefined') {
                const alpineElements = targetElement.querySelectorAll('[x-data]');
                alpineElements.forEach(element => {
                    if (!element._x_dataStack) {
                        try {
                            Alpine.initTree(element);
                            console.log('🎯 Alpine component hydrated:', element);
                        } catch (error) {
                            console.warn('⚠️ Alpine hydration failed:', error);
                        }
                    }
                });
            }
            
            // Bootstrap tabs hydration
            if (typeof bootstrap !== 'undefined' && bootstrap.Tab) {
                const bootstrapTabs = targetElement.querySelectorAll('[data-bs-toggle="tab"]');
                bootstrapTabs.forEach(tab => {
                    new bootstrap.Tab(tab);
                });
            }
            
            // Custom component hydration
            if (window.initializeCustomComponents) {
                window.initializeCustomComponents(targetElement);
            }
        },

        /**
         * Finalize tab restoration after settle
         */
        finalizeTabRestoration: function(targetElement) {
            // Clean up old states
            this.cleanupOldStates();
            
            // Trigger final initialization events
            targetElement.dispatchEvent(new CustomEvent('tabs:restored'));
        },

        /**
         * Utility functions
         */
        generateId: function(element, prefix) {
            const id = prefix + Date.now() + '-' + Math.random().toString(36).substr(2, 5);
            element.id = id;
            return id;
        },

        getDataAttributes: function(element) {
            const data = {};
            Array.from(element.attributes).forEach(attr => {
                if (attr.name.startsWith('data-')) {
                    data[attr.name] = attr.value;
                }
            });
            return data;
        },

        getScrollPosition: function(element) {
            return {
                scrollTop: element.scrollTop,
                scrollLeft: element.scrollLeft
            };
        },

        restoreScrollPosition: function(element, position) {
            element.scrollTop = position.scrollTop;
            element.scrollLeft = position.scrollLeft;
        },

        preserveInitialTabStates: function() {
            const tabContainers = document.querySelectorAll('[data-tab-container], .tab-navigation, .content-tab-container');
            tabContainers.forEach(container => {
                this.preserveTabStates(container);
                this.initializeTabContainer(container);
                container.setAttribute('data-initialized', 'true');
            });
        },

        setupGlobalTabHandlers: function() {
            // Global tab switching function
            window.switchToTab = (tabName, containerId) => {
                const container = containerId ? document.getElementById(containerId) : document.querySelector('[data-tab-container], .tab-navigation');
                if (container) {
                    const tab = container.querySelector(`[data-tab="${tabName}"]`);
                    if (tab) {
                        this.handleTabClick(tab, container);
                    }
                }
            };
        },

        cleanupOldStates: function() {
            // Remove states for elements that no longer exist
            const currentTime = Date.now();
            const maxAge = 5 * 60 * 1000; // 5 minutes
            
            this.activeTabStates.forEach((state, id) => {
                if (!document.getElementById(id) && (currentTime - state.timestamp > maxAge)) {
                    this.activeTabStates.delete(id);
                }
            });
        }
    };

    /**
     * Initialize on DOM ready
     */
    document.addEventListener('DOMContentLoaded', function() {
        TabPreservationManager.init();
    });

    console.log('✅ Tab Preservation System loaded');
})();
