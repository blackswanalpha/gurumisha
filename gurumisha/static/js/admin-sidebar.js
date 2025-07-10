/**
 * Enhanced Admin Sidebar JavaScript
 * Handles mobile navigation, real-time updates, and interactive features
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeSidebar();
    initializeActiveStateManagement();
    initializeIconAnimations();
    initializeRealTimeUpdates();
    initializeTooltips();
    initializeKeyboardShortcuts();
    initializeMobileGestures();
    initializeAccessibility();
});

/**
 * Initialize sidebar functionality
 */
function initializeSidebar() {
    const mobileToggle = document.getElementById('mobile-sidebar-toggle');
    const sidebar = document.querySelector('.admin-sidebar');
    const overlay = document.querySelector('.admin-sidebar-overlay');
    
    // Mobile sidebar toggle
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', function() {
            toggleMobileSidebar();
        });
    }
    
    // Close sidebar when clicking overlay
    if (overlay) {
        overlay.addEventListener('click', function() {
            closeMobileSidebar();
        });
    }
    
    // Close sidebar on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeMobileSidebar();
        }
    });
    
    // Add loading states to navigation links
    const navLinks = document.querySelectorAll('.admin-nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!this.href.includes('#')) {
                addLoadingState(this);
            }
        });
    });
    
    // Initialize collapsible sections
    initializeCollapsibleSections();
}

/**
 * Toggle mobile sidebar
 */
function toggleMobileSidebar() {
    const sidebar = document.querySelector('.admin-sidebar');
    const overlay = document.querySelector('.admin-sidebar-overlay');
    
    if (sidebar && overlay) {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
        document.body.classList.toggle('sidebar-open');
    }
}

/**
 * Close mobile sidebar
 */
function closeMobileSidebar() {
    const sidebar = document.querySelector('.admin-sidebar');
    const overlay = document.querySelector('.admin-sidebar-overlay');
    
    if (sidebar && overlay) {
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
        document.body.classList.remove('sidebar-open');
    }
}

/**
 * Add loading state to navigation link
 */
function addLoadingState(link) {
    link.classList.add('loading');
    
    // Remove loading state after navigation
    setTimeout(() => {
        link.classList.remove('loading');
    }, 2000);
}

/**
 * Initialize collapsible sections
 */
function initializeCollapsibleSections() {
    const collapsibleHeaders = document.querySelectorAll('[data-collapsible]');
    
    collapsibleHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const target = document.querySelector(this.dataset.collapsible);
            if (target) {
                target.classList.toggle('collapsed');
                target.classList.toggle('expanded');
                
                // Update icon
                const icon = this.querySelector('i');
                if (icon) {
                    icon.classList.toggle('fa-chevron-down');
                    icon.classList.toggle('fa-chevron-up');
                }
            }
        });
    });
}

/**
 * Initialize real-time updates for sidebar stats
 */
function initializeRealTimeUpdates() {
    // Update sidebar stats every 30 seconds
    setInterval(updateSidebarStats, 30000);

    // Update immediately on page load
    updateSidebarStats();

    // Initialize HTMX-powered real-time updates
    initializeHTMXUpdates();
}

/**
 * Initialize HTMX real-time updates
 */
function initializeHTMXUpdates() {
    // Listen for HTMX events
    document.addEventListener('htmx:afterRequest', function(event) {
        if (event.detail.xhr.status === 200) {
            const target = event.target;
            if (target.hasAttribute('data-stat')) {
                animateBadge(target);
            }
        }
    });

    // Handle HTMX errors gracefully
    document.addEventListener('htmx:responseError', function(event) {
        console.warn('HTMX request failed:', event.detail);
        // Fallback to manual updates
        setTimeout(updateSidebarStats, 5000);
    });
}

/**
 * Enhanced sidebar statistics update
 */
function updateSidebarStats() {
    // Update tracking stats
    fetch('/dashboard/htmx/tracking-stats/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'HX-Request': 'true'
        }
    })
    .then(response => response.json())
    .then(data => {
        updateTrackingBadges(data);
    })
    .catch(error => {
        console.log('Tracking stats update failed:', error);
    });

    // Update inquiry stats
    fetch('/dashboard/htmx/inquiry-stats/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'HX-Request': 'true'
        }
    })
    .then(response => response.json())
    .then(data => {
        updateInquiryBadges(data);
    })
    .catch(error => {
        console.log('Inquiry stats update failed:', error);
    });

    // Update general admin stats
    fetch('/dashboard/htmx/admin-quick-actions/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'HX-Request': 'true'
        }
    })
    .then(response => response.json())
    .then(data => {
        updateGeneralBadges(data);
    })
    .catch(error => {
        console.log('General stats update failed:', error);
    });
}

/**
 * Update tracking-related badges
 */
function updateTrackingBadges(data) {
    const badges = {
        'total-orders': data.total_orders,
        'pending-orders': data.pending_orders,
        'in-transit': data.in_transit,
        'arrived': data.arrived,
        'under-clearance': data.under_clearance,
        'ready-for-dispatch': data.ready_for_dispatch
    };

    Object.entries(badges).forEach(([stat, value]) => {
        const badge = document.querySelector(`[data-stat="${stat}"]`);
        if (badge && value !== undefined) {
            updateBadgeValue(badge, value);
        }
    });
}

/**
 * Update inquiry-related badges
 */
function updateInquiryBadges(data) {
    const badges = {
        'new-inquiries': data.new_inquiries,
        'total-inquiries': data.total_inquiries,
        'pending-inquiries': data.pending_inquiries
    };

    Object.entries(badges).forEach(([stat, value]) => {
        const badge = document.querySelector(`[data-stat="${stat}"]`);
        if (badge && value !== undefined) {
            updateBadgeValue(badge, value);
        }
    });
}

/**
 * Update general admin badges
 */
function updateGeneralBadges(data) {
    const badges = {
        'total-users': data.total_users,
        'active-vendors': data.active_vendors,
        'total-cars': data.total_cars,
        'pending-approvals': data.pending_approvals,
        'low-stock': data.low_stock || 0
    };

    Object.entries(badges).forEach(([stat, value]) => {
        const badge = document.querySelector(`[data-stat="${stat}"]`);
        if (badge && value !== undefined) {
            updateBadgeValue(badge, value);
        }
    });
}

/**
 * Update badge value with animation and styling
 */
function updateBadgeValue(badge, value) {
    const oldValue = parseInt(badge.textContent) || 0;
    const newValue = parseInt(value) || 0;

    // Update the value
    badge.textContent = newValue;

    // Apply appropriate styling based on value
    if (newValue === 0) {
        badge.classList.add('zero');
        badge.style.display = 'none';
    } else {
        badge.classList.remove('zero');
        badge.style.display = 'flex';

        // Animate if value changed
        if (oldValue !== newValue) {
            animateBadge(badge);

            // Add pulse animation for increases
            if (newValue > oldValue) {
                badge.classList.add('increased');
                setTimeout(() => badge.classList.remove('increased'), 2000);
            }
        }
    }
}

/**
 * Animate badge update
 */
function animateBadge(badge) {
    badge.style.transform = 'scale(1.2)';
    badge.style.transition = 'transform 0.2s ease';
    
    setTimeout(() => {
        badge.style.transform = 'scale(1)';
    }, 200);
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

/**
 * Show tooltip
 */
function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'admin-tooltip';
    tooltip.textContent = e.target.dataset.tooltip;
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
    
    setTimeout(() => {
        tooltip.classList.add('show');
    }, 10);
}

/**
 * Hide tooltip
 */
function hideTooltip() {
    const tooltip = document.querySelector('.admin-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

/**
 * Enhanced Active State Management for Modern Navigation Links
 */
function initializeActiveStateManagement() {
    const navLinks = document.querySelectorAll('.modern-nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));

            // Add active class to clicked link
            this.classList.add('active');

            // Store active state in sessionStorage for persistence
            sessionStorage.setItem('activeNavLink', this.getAttribute('href'));

            // Add visual feedback
            this.style.transform = 'translateX(10px) scale(1.02)';
            setTimeout(() => {
                this.style.transform = '';
            }, 200);
        });

        // Add hover sound effect (optional)
        link.addEventListener('mouseenter', function() {
            // You can add a subtle sound effect here if desired
            this.style.transition = 'all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        });
    });

    // Restore active state on page load
    const activeHref = sessionStorage.getItem('activeNavLink');
    if (activeHref) {
        const activeLink = document.querySelector(`a[href="${activeHref}"]`);
        if (activeLink && activeLink.classList.contains('modern-nav-link')) {
            navLinks.forEach(l => l.classList.remove('active'));
            activeLink.classList.add('active');
        }
    }
}

/**
 * Enhanced Icon Animation System
 */
function initializeIconAnimations() {
    const navIcons = document.querySelectorAll('.nav-icon i');

    navIcons.forEach(icon => {
        const link = icon.closest('.modern-nav-link');

        if (link) {
            link.addEventListener('mouseenter', function() {
                icon.style.transform = 'scale(1.1) rotate(5deg)';
            });

            link.addEventListener('mouseleave', function() {
                if (!this.classList.contains('active')) {
                    icon.style.transform = 'scale(1) rotate(0deg)';
                }
            });

            link.addEventListener('click', function() {
                // Trigger activation animation
                icon.style.animation = 'iconActivate 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55) both';

                setTimeout(() => {
                    icon.style.animation = '';
                }, 600);
            });
        }
    });
}

/**
 * Initialize keyboard shortcuts
 */
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Alt + D for Dashboard
        if (e.altKey && e.key === 'd') {
            e.preventDefault();
            const dashboardLink = document.querySelector('a[href*="dashboard"]');
            if (dashboardLink) dashboardLink.click();
        }
        
        // Alt + I for Import Tracking
        if (e.altKey && e.key === 'i') {
            e.preventDefault();
            const importLink = document.querySelector('a[href*="importorder"]');
            if (importLink) importLink.click();
        }
        
        // Alt + U for Users
        if (e.altKey && e.key === 'u') {
            e.preventDefault();
            const usersLink = document.querySelector('a[href*="admin/users"]');
            if (usersLink) usersLink.click();
        }
        
        // Alt + S for Sidebar toggle (mobile)
        if (e.altKey && e.key === 's') {
            e.preventDefault();
            toggleMobileSidebar();
        }
    });
}

/**
 * Notification system for sidebar
 */
function showSidebarNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `sidebar-notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
            <span>${message}</span>
        </div>
    `;
    
    const sidebar = document.querySelector('.admin-sidebar');
    if (sidebar) {
        sidebar.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
}

/**
 * Handle sidebar search functionality
 */
function initializeSidebarSearch() {
    const searchInput = document.querySelector('.sidebar-search');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            const navLinks = document.querySelectorAll('.admin-nav-link');
            
            navLinks.forEach(link => {
                const text = link.textContent.toLowerCase();
                const parent = link.closest('li');
                
                if (text.includes(query) || query === '') {
                    parent.style.display = 'block';
                } else {
                    parent.style.display = 'none';
                }
            });
        });
    }
}

/**
 * Initialize mobile gesture support
 */
function initializeMobileGestures() {
    const sidebar = document.querySelector('.admin-sidebar');
    const overlay = document.querySelector('.admin-sidebar-overlay');

    if (!sidebar || window.innerWidth > 1024) return;

    let startX = 0;
    let currentX = 0;
    let isDragging = false;

    // Touch start
    sidebar.addEventListener('touchstart', function(e) {
        startX = e.touches[0].clientX;
        isDragging = true;
        sidebar.classList.add('swiping');
    }, { passive: true });

    // Touch move
    sidebar.addEventListener('touchmove', function(e) {
        if (!isDragging) return;

        currentX = e.touches[0].clientX;
        const deltaX = currentX - startX;

        // Only allow swiping left (closing)
        if (deltaX < 0) {
            const translateX = Math.max(deltaX, -sidebar.offsetWidth);
            sidebar.style.transform = `translateX(${translateX}px)`;

            // Update overlay opacity
            const opacity = Math.max(0, 1 + (deltaX / sidebar.offsetWidth));
            if (overlay) {
                overlay.style.opacity = opacity;
            }
        }
    }, { passive: true });

    // Touch end
    sidebar.addEventListener('touchend', function(e) {
        if (!isDragging) return;

        isDragging = false;
        sidebar.classList.remove('swiping');

        const deltaX = currentX - startX;
        const threshold = sidebar.offsetWidth * 0.3;

        if (deltaX < -threshold) {
            // Close sidebar
            closeMobileSidebar();
        } else {
            // Snap back to open position
            sidebar.style.transform = '';
            if (overlay) {
                overlay.style.opacity = '';
            }
        }
    }, { passive: true });

    // Prevent scrolling when swiping
    sidebar.addEventListener('touchmove', function(e) {
        if (isDragging) {
            e.preventDefault();
        }
    });
}

/**
 * Initialize accessibility features
 */
function initializeAccessibility() {
    // Add ARIA labels and roles
    const sidebar = document.querySelector('.admin-sidebar');
    if (sidebar) {
        sidebar.setAttribute('role', 'navigation');
        sidebar.setAttribute('aria-label', 'Admin navigation menu');
    }

    // Add keyboard navigation for mobile toggle
    const mobileToggle = document.getElementById('mobile-sidebar-toggle');
    if (mobileToggle) {
        mobileToggle.setAttribute('aria-label', 'Toggle navigation menu');
        mobileToggle.setAttribute('aria-expanded', 'false');

        // Update aria-expanded when sidebar opens/closes
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    const isOpen = sidebar.classList.contains('open');
                    mobileToggle.setAttribute('aria-expanded', isOpen.toString());
                }
            });
        });

        observer.observe(sidebar, { attributes: true });
    }

    // Add focus management
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab' && sidebar.classList.contains('open')) {
            trapFocusInSidebar(e);
        }
    });
}

/**
 * Trap focus within sidebar when open on mobile
 */
function trapFocusInSidebar(e) {
    const sidebar = document.querySelector('.admin-sidebar');
    const focusableElements = sidebar.querySelectorAll(
        'a[href], button, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
    }
}

/**
 * Enhanced notification system with better mobile support
 */
function showSidebarNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `sidebar-notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
            <span>${message}</span>
            <button class="notification-close" aria-label="Close notification">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    const sidebar = document.querySelector('.admin-sidebar');
    if (sidebar) {
        sidebar.appendChild(notification);

        // Add close button functionality
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            hideNotification(notification);
        });

        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Auto-hide after duration
        setTimeout(() => {
            hideNotification(notification);
        }, duration);
    }
}

/**
 * Hide notification with animation
 */
function hideNotification(notification) {
    notification.classList.remove('show');
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 300);
}

/**
 * Export functions for global use
 */
window.AdminSidebar = {
    toggle: toggleMobileSidebar,
    close: closeMobileSidebar,
    showNotification: showSidebarNotification,
    updateStats: updateSidebarStats,
    updateTrackingBadges: updateTrackingBadges,
    updateInquiryBadges: updateInquiryBadges,
    updateGeneralBadges: updateGeneralBadges
};
