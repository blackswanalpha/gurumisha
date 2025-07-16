/**
 * Gurumisha Welcome Popup Manager
 * Handles the welcome popup display logic, session storage, and user interactions
 * Follows harrier design patterns and integrates with existing toast system
 */

// Prevent multiple script executions
(function() {
    'use strict';

    if (window.welcomePopupLoaded) {
        console.log('Welcome popup manager already loaded');
        return;
    }
    window.welcomePopupLoaded = true;

/**
 * Welcome Popup Configuration
 */
const WELCOME_CONFIG = {
    // Storage keys
    SESSION_KEY: 'gurumisha_welcome_seen',
    PERSISTENT_KEY: 'gurumisha_welcome_dont_show',
    ANALYTICS_KEY: 'gurumisha_welcome_analytics',
    
    // Timing configuration
    INITIAL_DELAY: 1000,        // Delay before showing popup (ms)
    CLOSE_ANIMATION_DELAY: 300, // Time to wait for close animation (ms)
    SCROLL_DELAY: 400,          // Delay before scrolling to search (ms)
    
    // Display rules
    MAX_DISPLAYS_PER_SESSION: 1,
    COOLDOWN_HOURS: 24,         // Hours before showing again if not opted out
    
    // Analytics tracking
    TRACK_EVENTS: true
};

/**
 * Welcome Popup Analytics
 */
class WelcomeAnalytics {
    constructor() {
        this.events = this.loadAnalytics();
    }
    
    loadAnalytics() {
        try {
            const stored = localStorage.getItem(WELCOME_CONFIG.ANALYTICS_KEY);
            return stored ? JSON.parse(stored) : {
                totalShows: 0,
                totalCloses: 0,
                getStartedClicks: 0,
                browseCarsClicks: 0,
                dontShowAgainSelections: 0,
                lastShown: null,
                firstShown: null
            };
        } catch (e) {
            console.warn('Failed to load welcome popup analytics:', e);
            return {};
        }
    }
    
    saveAnalytics() {
        try {
            localStorage.setItem(WELCOME_CONFIG.ANALYTICS_KEY, JSON.stringify(this.events));
        } catch (e) {
            console.warn('Failed to save welcome popup analytics:', e);
        }
    }
    
    trackEvent(eventType, data = {}) {
        if (!WELCOME_CONFIG.TRACK_EVENTS) return;
        
        const timestamp = new Date().toISOString();
        
        switch (eventType) {
            case 'popup_shown':
                this.events.totalShows = (this.events.totalShows || 0) + 1;
                this.events.lastShown = timestamp;
                if (!this.events.firstShown) {
                    this.events.firstShown = timestamp;
                }
                break;
                
            case 'popup_closed':
                this.events.totalCloses = (this.events.totalCloses || 0) + 1;
                break;
                
            case 'get_started_clicked':
                this.events.getStartedClicks = (this.events.getStartedClicks || 0) + 1;
                break;
                
            case 'browse_cars_clicked':
                this.events.browseCarsClicks = (this.events.browseCarsClicks || 0) + 1;
                break;
                
            case 'dont_show_again_selected':
                this.events.dontShowAgainSelections = (this.events.dontShowAgainSelections || 0) + 1;
                break;
        }
        
        this.saveAnalytics();
        
        // Log for debugging (remove in production)
        console.log(`Welcome Popup Analytics: ${eventType}`, data);
    }
}

/**
 * Welcome Popup Display Rules
 */
class WelcomeDisplayRules {
    static shouldShowPopup() {
        // Check if user has permanently opted out
        const dontShowAgain = localStorage.getItem(WELCOME_CONFIG.PERSISTENT_KEY);
        if (dontShowAgain === 'true') {
            return false;
        }
        
        // Check session storage for current session
        const seenThisSession = sessionStorage.getItem(WELCOME_CONFIG.SESSION_KEY);
        if (seenThisSession === 'true') {
            return false;
        }
        
        // Check cooldown period
        const analytics = new WelcomeAnalytics();
        if (analytics.events.lastShown) {
            const lastShown = new Date(analytics.events.lastShown);
            const now = new Date();
            const hoursSinceLastShown = (now - lastShown) / (1000 * 60 * 60);
            
            if (hoursSinceLastShown < WELCOME_CONFIG.COOLDOWN_HOURS) {
                return false;
            }
        }
        
        // Check if we're on the homepage
        const isHomepage = window.location.pathname === '/' || 
                          window.location.pathname === '/homepage/' ||
                          window.location.pathname.endsWith('/');
        
        if (!isHomepage) {
            return false;
        }
        
        return true;
    }
    
    static markAsShown() {
        sessionStorage.setItem(WELCOME_CONFIG.SESSION_KEY, 'true');
    }
    
    static markDontShowAgain() {
        localStorage.setItem(WELCOME_CONFIG.PERSISTENT_KEY, 'true');
    }
}

/**
 * Enhanced Welcome Popup Component
 */
function welcomePopup() {
    return {
        show: false,
        dontShowAgain: false,
        analytics: new WelcomeAnalytics(),
        isClosing: false,
        
        init() {
            // Check display rules
            if (!WelcomeDisplayRules.shouldShowPopup()) {
                return;
            }
            
            // Wait for page to be fully loaded
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    this.showPopupWithDelay();
                });
            } else {
                this.showPopupWithDelay();
            }
        },
        
        showPopupWithDelay() {
            // Additional check for page elements
            const heroSection = document.querySelector('.main-banner, .hero-content');
            if (!heroSection) {
                // If hero section not found, wait a bit more
                setTimeout(() => this.showPopupWithDelay(), 500);
                return;
            }
            
            // Show popup with configured delay
            setTimeout(() => {
                this.showPopup();
            }, WELCOME_CONFIG.INITIAL_DELAY);
        },
        
        showPopup() {
            this.show = true;
            document.body.style.overflow = 'hidden';
            
            // Track analytics
            this.analytics.trackEvent('popup_shown');
            WelcomeDisplayRules.markAsShown();
            
            // Add keyboard event listener for ESC key
            document.addEventListener('keydown', this.handleKeydown.bind(this));
            
            // Show success toast if toast manager is available
            if (window.showInfo) {
                setTimeout(() => {
                    window.showInfo('Welcome to Gurumisha! Explore our features below.', {
                        duration: 3000,
                        id: 'welcome-info'
                    });
                }, 2000);
            }
        },
        
        closePopup(reason = 'manual') {
            if (this.isClosing) return;
            
            this.isClosing = true;
            this.show = false;
            document.body.style.overflow = '';
            
            // Track analytics
            this.analytics.trackEvent('popup_closed', { reason });
            
            // Handle "don't show again" preference
            if (this.dontShowAgain) {
                WelcomeDisplayRules.markDontShowAgain();
                this.analytics.trackEvent('dont_show_again_selected');
                
                // Show confirmation toast
                if (window.showSuccess) {
                    window.showSuccess('Got it! We won\'t show this welcome message again.', {
                        duration: 4000
                    });
                }
            }
            
            // Remove keyboard event listener
            document.removeEventListener('keydown', this.handleKeydown.bind(this));
            
            // Hide popup element after animation
            setTimeout(() => {
                const popup = document.getElementById('welcome-popup');
                if (popup) {
                    popup.classList.add('hidden');
                }
                this.isClosing = false;
            }, WELCOME_CONFIG.CLOSE_ANIMATION_DELAY);
        },
        
        getStarted() {
            // Track analytics
            this.analytics.trackEvent('get_started_clicked');
            
            // Close popup
            this.closePopup('get_started');
            
            // Navigate to search section with smooth scrolling
            setTimeout(() => {
                this.scrollToSearch();
            }, WELCOME_CONFIG.SCROLL_DELAY);
        },
        
        browseCars() {
            // Track analytics
            this.analytics.trackEvent('browse_cars_clicked');
            
            // Close popup
            this.closePopup('browse_cars');
            
            // Navigate to car listings
            setTimeout(() => {
                window.location.href = '/cars/';
            }, WELCOME_CONFIG.SCROLL_DELAY);
        },
        
        scrollToSearch() {
            const searchSection = document.querySelector('.car-search-form, .hero-content form, [data-search-form]');
            if (searchSection) {
                searchSection.scrollIntoView({ 
                    behavior: 'smooth',
                    block: 'center'
                });
                
                // Focus on the first input field
                setTimeout(() => {
                    const firstInput = searchSection.querySelector('input:not([type="hidden"]), select');
                    if (firstInput) {
                        firstInput.focus();
                        
                        // Add visual highlight
                        firstInput.style.boxShadow = '0 0 0 3px rgba(220, 38, 38, 0.3)';
                        setTimeout(() => {
                            firstInput.style.boxShadow = '';
                        }, 2000);
                    }
                }, 500);
            } else {
                // Fallback: scroll to top of page
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        },
        
        handleKeydown(event) {
            // Close popup on ESC key
            if (event.key === 'Escape') {
                this.closePopup('keyboard');
            }
        }
    }
}

/**
 * Global Welcome Popup Utilities
 */
window.WelcomePopup = {
    // Force show popup (for testing)
    forceShow() {
        sessionStorage.removeItem(WELCOME_CONFIG.SESSION_KEY);
        localStorage.removeItem(WELCOME_CONFIG.PERSISTENT_KEY);
        location.reload();
    },
    
    // Reset all welcome popup data
    reset() {
        sessionStorage.removeItem(WELCOME_CONFIG.SESSION_KEY);
        localStorage.removeItem(WELCOME_CONFIG.PERSISTENT_KEY);
        localStorage.removeItem(WELCOME_CONFIG.ANALYTICS_KEY);
        console.log('Welcome popup data reset');
    },
    
    // Get analytics data
    getAnalytics() {
        const analytics = new WelcomeAnalytics();
        return analytics.events;
    },
    
    // Configuration
    config: WELCOME_CONFIG
};

// Make welcomePopup function globally available
window.welcomePopup = welcomePopup;

// Auto-initialize if Alpine.js is not available
document.addEventListener('DOMContentLoaded', function() {
    // Check if Alpine.js is handling the component
    const popupElement = document.getElementById('welcome-popup');
    if (popupElement && !window.Alpine) {
        console.warn('Alpine.js not found. Welcome popup requires Alpine.js for proper functionality.');
    }
});

})(); // End IIFE
