/**
 * Enhanced Notification Badge Manager
 * Handles real-time updates, animations, and accessibility for notification badges
 */

class NotificationBadgeManager {
    constructor() {
        this.badges = new Map();
        this.updateInterval = 30000; // 30 seconds
        this.animationDuration = 600; // 0.6 seconds
        this.init();
    }

    init() {
        this.collectBadges();
        this.setupEventListeners();
        this.startPeriodicUpdates();
        this.setupAccessibility();
    }

    /**
     * Collect all notification badges on the page
     */
    collectBadges() {
        const badgeElements = document.querySelectorAll('.notification-badge');
        badgeElements.forEach(badge => {
            const count = parseInt(badge.dataset.count) || 0;
            const type = this.getBadgeType(badge);
            const id = this.generateBadgeId(badge);
            
            this.badges.set(id, {
                element: badge,
                count: count,
                type: type,
                lastUpdate: Date.now()
            });
        });
    }

    /**
     * Generate unique ID for badge tracking
     */
    generateBadgeId(badge) {
        const parent = badge.closest('a, button, .nav-link');
        const href = parent?.getAttribute('href') || '';
        const text = parent?.textContent?.trim() || '';
        return `badge-${href.replace(/[^a-zA-Z0-9]/g, '')}-${text.replace(/[^a-zA-Z0-9]/g, '')}`;
    }

    /**
     * Get badge type from CSS classes
     */
    getBadgeType(badge) {
        const classes = badge.className;
        if (classes.includes('notification-badge-primary')) return 'primary';
        if (classes.includes('notification-badge-secondary')) return 'secondary';
        if (classes.includes('notification-badge-blue')) return 'blue';
        if (classes.includes('notification-badge-success')) return 'success';
        if (classes.includes('notification-badge-warning')) return 'warning';
        if (classes.includes('notification-badge-danger')) return 'danger';
        if (classes.includes('notification-badge-info')) return 'info';
        return 'primary';
    }

    /**
     * Update badge count with animation
     */
    updateBadge(badgeId, newCount, options = {}) {
        const badge = this.badges.get(badgeId);
        if (!badge) return;

        const oldCount = badge.count;
        const element = badge.element;

        // Update count
        badge.count = newCount;
        badge.lastUpdate = Date.now();

        // Handle visibility
        if (newCount <= 0) {
            this.hideBadge(element);
            return;
        }

        // Show badge if hidden
        if (element.style.display === 'none' || !element.offsetParent) {
            this.showBadge(element);
        }

        // Update text content
        const displayCount = newCount > 99 ? '99+' : newCount.toString();
        element.textContent = displayCount;
        element.dataset.count = newCount;

        // Add animation based on count change
        if (newCount > oldCount) {
            this.animateIncrease(element, options);
        } else if (newCount < oldCount) {
            this.animateDecrease(element, options);
        }

        // Update ARIA label
        this.updateAriaLabel(element, newCount);

        // Trigger custom event
        this.dispatchBadgeEvent('badgeUpdated', {
            badgeId,
            oldCount,
            newCount,
            element
        });
    }

    /**
     * Show badge with fade-in animation
     */
    showBadge(element) {
        element.style.display = 'inline-flex';
        element.classList.remove('hidden');
        element.style.opacity = '0';
        element.style.transform = 'scale(0.3)';
        
        // Trigger reflow
        element.offsetHeight;
        
        element.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        element.style.opacity = '1';
        element.style.transform = 'scale(1)';
    }

    /**
     * Hide badge with fade-out animation
     */
    hideBadge(element) {
        element.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        element.style.opacity = '0';
        element.style.transform = 'scale(0.3)';
        
        setTimeout(() => {
            element.style.display = 'none';
            element.classList.add('hidden');
        }, 300);
    }

    /**
     * Animate badge increase
     */
    animateIncrease(element, options = {}) {
        element.classList.remove('count-decreased');
        element.classList.add('count-increased');
        
        if (options.urgent) {
            element.classList.add('notification-badge-urgent');
            setTimeout(() => {
                element.classList.remove('notification-badge-urgent');
            }, 3000);
        } else if (options.pulse) {
            element.classList.add('notification-badge-pulse');
            setTimeout(() => {
                element.classList.remove('notification-badge-pulse');
            }, 4000);
        }

        setTimeout(() => {
            element.classList.remove('count-increased');
        }, this.animationDuration);
    }

    /**
     * Animate badge decrease
     */
    animateDecrease(element, options = {}) {
        element.classList.remove('count-increased');
        element.classList.add('count-decreased');
        
        setTimeout(() => {
            element.classList.remove('count-decreased');
        }, this.animationDuration);
    }

    /**
     * Update ARIA label for accessibility
     */
    updateAriaLabel(element, count) {
        const baseLabel = element.getAttribute('aria-label') || 'notifications';
        const newLabel = `${count} ${baseLabel}`;
        element.setAttribute('aria-label', newLabel);
        
        // Update screen reader announcement
        if (count > 0) {
            this.announceToScreenReader(`${count} ${baseLabel}`);
        }
    }

    /**
     * Announce to screen readers
     */
    announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for HTMX events
        document.addEventListener('htmx:afterRequest', (event) => {
            if (event.detail.xhr.getResponseHeader('X-Badge-Updates')) {
                const updates = JSON.parse(event.detail.xhr.getResponseHeader('X-Badge-Updates'));
                this.processBadgeUpdates(updates);
            }
        });

        // Listen for custom badge events
        document.addEventListener('updateBadge', (event) => {
            const { badgeId, count, options } = event.detail;
            this.updateBadge(badgeId, count, options);
        });

        // Handle visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.refreshAllBadges();
            }
        });
    }

    /**
     * Process badge updates from server
     */
    processBadgeUpdates(updates) {
        updates.forEach(update => {
            this.updateBadge(update.badgeId, update.count, update.options || {});
        });
    }

    /**
     * Setup accessibility features
     */
    setupAccessibility() {
        // Add keyboard navigation for badges
        document.querySelectorAll('.notification-badge').forEach(badge => {
            const parent = badge.closest('a, button');
            if (parent) {
                parent.addEventListener('focus', () => {
                    badge.style.outline = '2px solid rgba(59, 130, 246, 0.5)';
                    badge.style.outlineOffset = '2px';
                });
                
                parent.addEventListener('blur', () => {
                    badge.style.outline = 'none';
                });
            }
        });
    }

    /**
     * Start periodic updates
     */
    startPeriodicUpdates() {
        setInterval(() => {
            this.refreshAllBadges();
        }, this.updateInterval);
    }

    /**
     * Refresh all badges from server
     */
    async refreshAllBadges() {
        try {
            const response = await fetch('/api/notification-badges/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.processBadgeUpdates(data.badges || []);
            }
        } catch (error) {
            console.warn('Failed to refresh notification badges:', error);
        }
    }

    /**
     * Dispatch custom badge event
     */
    dispatchBadgeEvent(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }

    /**
     * Public API methods
     */
    static updateBadge(selector, count, options = {}) {
        const element = document.querySelector(selector);
        if (element) {
            const manager = window.notificationBadgeManager;
            const badgeId = manager.generateBadgeId(element);
            manager.updateBadge(badgeId, count, options);
        }
    }

    static pulseBadge(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.classList.add('notification-badge-pulse');
            setTimeout(() => {
                element.classList.remove('notification-badge-pulse');
            }, 4000);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.notificationBadgeManager = new NotificationBadgeManager();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationBadgeManager;
}
