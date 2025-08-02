/**
 * Gurumisha Message System Integration
 * Integrates the messaging system with toast manager and notification badges
 * Handles popup messages, dashboard messages, and real-time notifications
 */

(function() {
    'use strict';

    if (window.messageIntegrationLoaded) {
        console.log('Message integration already loaded');
        return;
    }
    window.messageIntegrationLoaded = true;

    class MessageIntegration {
        constructor() {
            this.checkInterval = 60000; // Check for new messages every minute
            this.popupCheckInterval = 30000; // Check for popup messages every 30 seconds
            this.lastPopupCheck = 0;
            this.activePopups = new Set();
            this.init();
        }

        init() {
            this.setupEventListeners();
            this.startPeriodicChecks();
            this.checkForInitialMessages();
            this.setupNotificationBadges();
        }

        setupEventListeners() {
            // Listen for HTMX events that might trigger message updates
            document.addEventListener('htmx:afterRequest', (event) => {
                this.handleHTMXResponse(event);
            });

            // Listen for page visibility changes to check for messages when user returns
            document.addEventListener('visibilitychange', () => {
                if (!document.hidden) {
                    this.checkForMessages();
                }
            });

            // Listen for custom message events
            document.addEventListener('messageCreated', (event) => {
                this.handleNewMessage(event.detail);
            });

            document.addEventListener('messageUpdated', (event) => {
                this.handleMessageUpdate(event.detail);
            });
        }

        startPeriodicChecks() {
            // Check for new popup messages periodically
            setInterval(() => {
                this.checkForPopupMessages();
            }, this.popupCheckInterval);

            // Check for general message updates
            setInterval(() => {
                this.checkForMessages();
            }, this.checkInterval);

            // Update notification badges
            setInterval(() => {
                this.updateNotificationBadges();
            }, this.checkInterval);
        }

        checkForInitialMessages() {
            // Check for messages on page load
            setTimeout(() => {
                this.checkForPopupMessages();
                this.loadDashboardMessages();
            }, 1000); // Delay to ensure page is fully loaded
        }

        setupNotificationBadges() {
            // Initialize message-related notification badges
            this.updateNotificationBadges();
        }

        isUserAuthenticated() {
            // Check if user is authenticated by looking for common authentication indicators
            // 1. Check for CSRF token (indicates Django session)
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') ||
                             document.querySelector('meta[name="csrf-token"]') ||
                             this.getCsrfTokenFromCookie();

            // 2. Check if we're on a dashboard page (requires authentication)
            const isDashboardPage = window.location.pathname.includes('/dashboard/');

            // 3. Check for user-specific elements in the DOM
            const hasUserElements = document.querySelector('.user-menu') ||
                                   document.querySelector('[data-user-authenticated]') ||
                                   document.querySelector('.logout-btn');

            return !!(csrfToken || isDashboardPage || hasUserElements);
        }

        getCsrfTokenFromCookie() {
            // Get CSRF token from cookie
            const name = 'csrftoken';
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        async checkForPopupMessages() {
            // Only check for popup messages if user is authenticated
            if (!this.isUserAuthenticated()) {
                return;
            }

            // Prevent too frequent checks
            const now = Date.now();
            if (now - this.lastPopupCheck < this.popupCheckInterval) {
                return;
            }
            this.lastPopupCheck = now;

            try {
                const response = await fetch('/messages/popup/', {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json',
                    },
                    credentials: 'same-origin'
                });

                if (response.ok) {
                    const data = await response.text();

                    // Check if response contains a message popup
                    if (data && typeof data === 'string' && !data.includes('"no_messages": true')) {
                        this.displayPopupMessage(data);
                    }
                } else if (response.status === 302 || response.status === 401 || response.status === 403) {
                    // User is not authenticated or doesn't have permission
                    console.debug('User not authenticated for popup messages');
                }
            } catch (error) {
                console.error('Error checking for popup messages:', error);
            }
        }

        displayPopupMessage(htmlContent) {
            // Create a temporary container to parse the HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = htmlContent;
            
            const popup = tempDiv.querySelector('.message-popup');
            if (popup) {
                const messageId = popup.id.replace('user-message-popup-', '');
                
                // Check if this popup is already active
                if (this.activePopups.has(messageId)) {
                    return;
                }

                // Add to active popups
                this.activePopups.add(messageId);

                // Append to body
                document.body.appendChild(popup);

                // Show toast notification for high priority messages
                const priority = popup.dataset.priority;
                if (priority && parseInt(priority) >= 3) {
                    const title = popup.querySelector('#message-title')?.textContent || 'New Message';
                    window.showInfo(`New important message: ${title}`, {
                        duration: 8000,
                        action: {
                            text: 'View',
                            handler: () => {
                                // Focus on the popup
                                popup.scrollIntoView({ behavior: 'smooth' });
                            }
                        }
                    });
                }

                // Remove from active popups when dismissed
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        if (mutation.type === 'childList') {
                            mutation.removedNodes.forEach((node) => {
                                if (node === popup) {
                                    this.activePopups.delete(messageId);
                                    observer.disconnect();
                                }
                            });
                        }
                    });
                });

                observer.observe(document.body, { childList: true });
            }
        }

        async loadDashboardMessages() {
            const dashboardContainer = document.querySelector('#dashboard-messages-container');
            if (!dashboardContainer) {
                return; // Not on a dashboard page
            }

            // Only load dashboard messages if user is authenticated
            if (!this.isUserAuthenticated()) {
                return;
            }

            try {
                const response = await fetch('/messages/dashboard/', {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    credentials: 'same-origin'
                });

                if (response.ok) {
                    const html = await response.text();
                    dashboardContainer.innerHTML = html;
                } else if (response.status === 302 || response.status === 401 || response.status === 403) {
                    console.debug('User not authenticated for dashboard messages');
                }
            } catch (error) {
                console.error('Error loading dashboard messages:', error);
            }
        }

        async checkForMessages() {
            // General message check - can be used for various purposes
            this.updateNotificationBadges();
            
            // Refresh dashboard messages if on dashboard
            if (window.location.pathname.includes('/dashboard/')) {
                this.loadDashboardMessages();
            }
        }

        async updateNotificationBadges() {
            // Only update badges if user is authenticated and on dashboard
            if (!document.body.classList.contains('dashboard-page') &&
                !window.location.pathname.startsWith('/dashboard/')) {
                return; // Skip on non-dashboard pages
            }

            // Update message-related notification badges
            try {
                const response = await fetch('/dashboard/admin/message-management/count/', {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    credentials: 'same-origin'
                });

                if (response.ok) {
                    const count = await response.text();
                    const badge = document.querySelector('#message-count-badge');
                    if (badge && window.notificationBadgeManager) {
                        window.notificationBadgeManager.updateBadge('message-count-badge', parseInt(count));
                    }
                } else if (response.status === 401 || response.status === 403) {
                    // User not authenticated or not authorized, skip silently
                    return;
                }
            } catch (error) {
                // Only log error if it's not a network/auth issue
                if (!error.message.includes('Failed to fetch') &&
                    !error.message.includes('NetworkError')) {
                    console.error('Error updating message notification badges:', error);
                }
            }
        }

        handleHTMXResponse(event) {
            const xhr = event.detail.xhr;
            
            // Check for message-related responses
            if (event.target.closest('.message-tab') || 
                event.target.closest('[id*="message"]')) {
                
                // Update notification badges after message operations
                setTimeout(() => {
                    this.updateNotificationBadges();
                }, 500);
            }

            // Handle message creation/update success
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    // Only try to parse as JSON if the response looks like JSON
                    const responseText = xhr.responseText.trim();
                    if (responseText.startsWith('{') && responseText.endsWith('}')) {
                        const response = JSON.parse(responseText);
                        if (response.success && response.message) {
                            // Show success toast for message operations
                            if (event.target.closest('#message-create-form') ||
                                event.target.closest('#message-edit-form')) {
                                window.showSuccess(response.message);
                            }
                        }
                    }
                } catch (e) {
                    // Response might not be JSON, ignore silently
                    console.debug('Non-JSON response received, ignoring:', e.message);
                }
            }
        }

        handleNewMessage(messageData) {
            // Handle custom event for new message creation
            window.showSuccess(`Message "${messageData.title}" created successfully!`);
            
            // Update notification badges
            this.updateNotificationBadges();
            
            // Check if we should show this message as a popup
            if (messageData.show_as_popup && messageData.status === 'active') {
                setTimeout(() => {
                    this.checkForPopupMessages();
                }, 1000);
            }
        }

        handleMessageUpdate(messageData) {
            // Handle custom event for message updates
            window.showInfo(`Message "${messageData.title}" updated`);
            
            // Update notification badges
            this.updateNotificationBadges();
        }

        // Public API methods
        static checkForMessages() {
            if (window.messageIntegration) {
                window.messageIntegration.checkForMessages();
            }
        }

        static showPopupMessages() {
            if (window.messageIntegration) {
                window.messageIntegration.checkForPopupMessages();
            }
        }

        static refreshDashboardMessages() {
            if (window.messageIntegration) {
                window.messageIntegration.loadDashboardMessages();
            }
        }

        static updateBadges() {
            if (window.messageIntegration) {
                window.messageIntegration.updateNotificationBadges();
            }
        }
    }

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        // Wait for toast manager to be ready
        const initMessageIntegration = () => {
            if (window.toastManagerLoaded) {
                window.messageIntegration = new MessageIntegration();
                
                // Expose public methods
                window.MessageIntegration = MessageIntegration;
            } else {
                setTimeout(initMessageIntegration, 100);
            }
        };
        
        initMessageIntegration();
    });

    // Handle page navigation (for SPAs or HTMX navigation)
    window.addEventListener('popstate', () => {
        if (window.messageIntegration) {
            window.messageIntegration.checkForMessages();
        }
    });

})();

// Utility functions for message interactions
function dismissAllMessages() {
    const popups = document.querySelectorAll('.message-popup');
    popups.forEach(popup => {
        const messageId = popup.id.replace('user-message-popup-', '');
        if (window.dismissMessage) {
            window.dismissMessage(messageId);
        }
    });
}

function refreshMessages() {
    if (window.MessageIntegration) {
        window.MessageIntegration.checkForMessages();
        window.MessageIntegration.showPopupMessages();
        window.MessageIntegration.refreshDashboardMessages();
    }
}

// Export for use in other scripts
window.dismissAllMessages = dismissAllMessages;
window.refreshMessages = refreshMessages;
