/**
 * Gurumisha Toast Manager
 * Comprehensive toast notification system with harrier design patterns
 * Handles all system messages, errors, and user feedback
 */

// Prevent multiple script executions
if (window.toastManagerLoaded) {
    return;
}
window.toastManagerLoaded = true;

class ToastManager {
    constructor() {
        this.toasts = new Map();
        this.container = null;
        this.maxToasts = 5;
        this.defaultDuration = 5000;
        this.init();
    }

    init() {
        // Create toast container
        this.createContainer();
        
        // Listen for Django messages
        this.handleDjangoMessages();
        
        // Listen for HTMX events
        this.handleHTMXEvents();
        
        // Listen for global errors
        this.handleGlobalErrors();
        
        // Expose global methods
        window.showToast = this.show.bind(this);
        window.showSuccess = (message, options) => this.show(message, 'success', options);
        window.showError = (message, options) => this.show(message, 'error', options);
        window.showWarning = (message, options) => this.show(message, 'warning', options);
        window.showInfo = (message, options) => this.show(message, 'info', options);
        window.clearToasts = this.clearAll.bind(this);

        // Featured car specific methods
        window.showFeaturedSuccess = this.showFeaturedSuccess.bind(this);
        window.showFeaturedError = this.showFeaturedError.bind(this);
        window.showFeaturedLimitReached = this.showFeaturedLimitReached.bind(this);
    }

    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.className = 'fixed top-4 right-4 z-[9999] space-y-3 pointer-events-none';
        this.container.style.maxWidth = '400px';
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', options = {}) {
        const config = {
            duration: options.duration || this.defaultDuration,
            persistent: options.persistent || false,
            dismissible: options.dismissible !== false,
            action: options.action || null,
            id: options.id || this.generateId(),
            ...options
        };

        // Remove existing toast with same ID
        if (this.toasts.has(config.id)) {
            this.remove(config.id);
        }

        // Limit number of toasts
        if (this.toasts.size >= this.maxToasts) {
            const oldestId = this.toasts.keys().next().value;
            this.remove(oldestId);
        }

        const toast = this.createToast(message, type, config);
        this.toasts.set(config.id, toast);
        this.container.appendChild(toast.element);

        // Animate in
        requestAnimationFrame(() => {
            toast.element.classList.add('toast-show');
        });

        // Auto-remove if not persistent
        if (!config.persistent && config.duration > 0) {
            toast.timeout = setTimeout(() => {
                this.remove(config.id);
            }, config.duration);
        }

        return config.id;
    }

    createToast(message, type, config) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} pointer-events-auto transform transition-all duration-300 ease-out translate-x-full opacity-0`;
        
        const colors = this.getColors(type);
        const icon = this.getIcon(type);
        
        toast.innerHTML = `
            <div class="flex items-start p-4 rounded-xl shadow-xl ${colors.bg} ${colors.border} border backdrop-blur-sm">
                <div class="flex-shrink-0">
                    <div class="w-6 h-6 flex items-center justify-center rounded-full ${colors.iconBg}">
                        <i class="${icon} ${colors.iconColor} text-sm"></i>
                    </div>
                </div>
                <div class="ml-3 flex-1 min-w-0">
                    <div class="${colors.text} font-medium text-sm leading-5 font-montserrat">
                        ${this.escapeHtml(message)}
                    </div>
                    ${config.action ? `
                        <div class="mt-2">
                            <button class="toast-action text-xs font-semibold ${colors.actionColor} hover:${colors.actionHover} transition-colors duration-200">
                                ${config.action.text}
                            </button>
                        </div>
                    ` : ''}
                </div>
                ${config.dismissible ? `
                    <div class="ml-4 flex-shrink-0">
                        <button class="toast-close inline-flex ${colors.closeColor} hover:${colors.closeHover} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white focus:ring-gray-400 transition-colors duration-200 rounded-md p-1">
                            <i class="fas fa-times text-xs"></i>
                        </button>
                    </div>
                ` : ''}
            </div>
        `;

        // Add event listeners
        if (config.dismissible) {
            const closeBtn = toast.querySelector('.toast-close');
            closeBtn.addEventListener('click', () => this.remove(config.id));
        }

        if (config.action) {
            const actionBtn = toast.querySelector('.toast-action');
            actionBtn.addEventListener('click', (e) => {
                e.preventDefault();
                config.action.handler();
                if (config.action.dismissOnClick !== false) {
                    this.remove(config.id);
                }
            });
        }

        // Add click to dismiss (except on action buttons)
        toast.addEventListener('click', (e) => {
            if (!e.target.closest('.toast-action') && !e.target.closest('.toast-close') && config.dismissible) {
                this.remove(config.id);
            }
        });

        return {
            element: toast,
            config: config,
            timeout: null
        };
    }

    getColors(type) {
        const colors = {
            success: {
                bg: 'bg-white',
                border: 'border-green-200',
                text: 'text-gray-900',
                iconBg: 'bg-green-100',
                iconColor: 'text-green-600',
                actionColor: 'text-green-600',
                actionHover: 'text-green-800',
                closeColor: 'text-gray-400',
                closeHover: 'text-gray-600'
            },
            error: {
                bg: 'bg-white',
                border: 'border-red-200',
                text: 'text-gray-900',
                iconBg: 'bg-red-100',
                iconColor: 'text-red-600',
                actionColor: 'text-red-600',
                actionHover: 'text-red-800',
                closeColor: 'text-gray-400',
                closeHover: 'text-gray-600'
            },
            warning: {
                bg: 'bg-white',
                border: 'border-yellow-200',
                text: 'text-gray-900',
                iconBg: 'bg-yellow-100',
                iconColor: 'text-yellow-600',
                actionColor: 'text-yellow-600',
                actionHover: 'text-yellow-800',
                closeColor: 'text-gray-400',
                closeHover: 'text-gray-600'
            },
            info: {
                bg: 'bg-white',
                border: 'border-blue-200',
                text: 'text-gray-900',
                iconBg: 'bg-blue-100',
                iconColor: 'text-blue-600',
                actionColor: 'text-blue-600',
                actionHover: 'text-blue-800',
                closeColor: 'text-gray-400',
                closeHover: 'text-gray-600'
            }
        };

        return colors[type] || colors.info;
    }

    getIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        return icons[type] || icons.info;
    }

    remove(id) {
        const toast = this.toasts.get(id);
        if (!toast) return;

        // Clear timeout
        if (toast.timeout) {
            clearTimeout(toast.timeout);
        }

        // Animate out
        toast.element.classList.remove('toast-show');
        toast.element.classList.add('translate-x-full', 'opacity-0');

        // Remove from DOM after animation
        setTimeout(() => {
            if (toast.element.parentNode) {
                toast.element.parentNode.removeChild(toast.element);
            }
            this.toasts.delete(id);
        }, 300);
    }

    clearAll() {
        this.toasts.forEach((_, id) => this.remove(id));
    }

    handleDjangoMessages() {
        // Handle Django messages on page load
        document.addEventListener('DOMContentLoaded', () => {
            const messages = document.querySelectorAll('.django-message');
            messages.forEach(msg => {
                const type = msg.dataset.type || 'info';
                const message = msg.textContent.trim();
                if (message) {
                    this.show(message, type);
                }
                msg.remove();
            });
        });
    }

    handleHTMXEvents() {
        // Handle HTMX responses
        document.addEventListener('htmx:afterRequest', (event) => {
            const xhr = event.detail.xhr;
            
            if (xhr.status >= 200 && xhr.status < 300) {
                // Check for success messages in response headers
                const successMessage = xhr.getResponseHeader('X-Toast-Success');
                if (successMessage) {
                    this.show(successMessage, 'success');
                }
            } else if (xhr.status >= 400) {
                // Handle error responses
                const errorMessage = xhr.getResponseHeader('X-Toast-Error') || 
                                   this.getDefaultErrorMessage(xhr.status);
                this.show(errorMessage, 'error');
            }
        });

        // Handle HTMX errors
        document.addEventListener('htmx:responseError', (event) => {
            const xhr = event.detail.xhr;
            const errorMessage = xhr.getResponseHeader('X-Toast-Error') || 
                               'An error occurred. Please try again.';
            this.show(errorMessage, 'error');
        });

        document.addEventListener('htmx:sendError', () => {
            this.show('Network error. Please check your connection.', 'error');
        });

        document.addEventListener('htmx:timeout', () => {
            this.show('Request timed out. Please try again.', 'warning');
        });
    }

    handleGlobalErrors() {
        // Handle JavaScript errors
        window.addEventListener('error', (event) => {
            // Filter out common non-critical errors
            const ignoredErrors = [
                'isSubmitting is not defined',
                'Script error.',
                'ResizeObserver loop limit exceeded',
                'Non-Error promise rejection captured',
                'Loading chunk'
            ];

            // Check if error should be ignored
            if (!event.error ||
                event.error === null ||
                event.filename.includes('cdn.min.js') ||
                event.filename.includes('alpine') ||
                ignoredErrors.some(ignored => event.message && event.message.includes(ignored))) {
                return;
            }

            // Only log actual meaningful errors
            if (event.error && event.error.stack && !event.error.stack.includes('isSubmitting')) {
                console.error('Global error:', event.error);
                this.show('An unexpected error occurred.', 'error', {
                    action: {
                        text: 'Reload Page',
                        handler: () => window.location.reload()
                    }
                });
            }
        });

        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            // Filter out null rejections and common non-critical rejections
            if (!event.reason ||
                event.reason === null ||
                (typeof event.reason === 'string' && event.reason.includes('isSubmitting'))) {
                return;
            }

            console.error('Unhandled promise rejection:', event.reason);
            this.show('An unexpected error occurred.', 'error');
        });
    }

    getDefaultErrorMessage(status) {
        const messages = {
            400: 'Bad request. Please check your input.',
            401: 'You are not authorized. Please log in.',
            403: 'Access denied.',
            404: 'Resource not found.',
            422: 'Invalid data provided.',
            429: 'Too many requests. Please wait.',
            500: 'Server error. Please try again later.',
            502: 'Service temporarily unavailable.',
            503: 'Service temporarily unavailable.',
            504: 'Request timed out.'
        };

        return messages[status] || 'An error occurred. Please try again.';
    }

    generateId() {
        return 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Featured car specific notification methods
    showFeaturedSuccess(carTitle, tier, remainingSlots) {
        const tierDisplay = tier.charAt(0).toUpperCase() + tier.slice(1);
        return this.show(
            `Car "${carTitle}" featured as ${tierDisplay}`,
            'success',
            {
                action: {
                    text: `${remainingSlots} slots remaining`,
                    handler: () => {
                        // Optional: Navigate to featured cars view
                        window.location.href = '/dashboard/admin/listings/?status=featured';
                    },
                    dismissOnClick: false
                },
                duration: 6000
            }
        );
    }

    showFeaturedError(message, remainingSlots = null) {
        const options = {
            duration: 7000
        };

        if (remainingSlots !== null) {
            options.action = {
                text: `${remainingSlots} slots available`,
                handler: () => {
                    window.location.href = '/dashboard/admin/listings/?status=featured';
                },
                dismissOnClick: false
            };
        }

        return this.show(message, 'error', options);
    }

    showFeaturedLimitReached() {
        return this.show(
            'Featured cars limit reached (9/9)',
            'warning',
            {
                action: {
                    text: 'View Featured Cars',
                    handler: () => {
                        window.location.href = '/dashboard/admin/listings/?status=featured';
                    }
                },
                duration: 8000
            }
        );
    }

    showCarUnfeatured(carTitle, availableSlots) {
        return this.show(
            `Featured status removed from "${carTitle}"`,
            'info',
            {
                action: {
                    text: `${availableSlots} slots now available`,
                    handler: () => {
                        // Optional action
                    },
                    dismissOnClick: false
                },
                duration: 5000
            }
        );
    }

    showCarApproved(carTitle) {
        return this.show(
            `Car "${carTitle}" approved successfully`,
            'success',
            {
                action: {
                    text: 'Feature this car?',
                    handler: () => {
                        // This would need to be implemented based on context
                        console.log('Feature car action triggered');
                    }
                },
                duration: 6000
            }
        );
    }
}

// CSS for animations
const toastStyles = `
    .toast-show {
        transform: translateX(0) !important;
        opacity: 1 !important;
    }
    
    .toast {
        transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
    }
    
    @media (max-width: 640px) {
        #toast-container {
            left: 1rem;
            right: 1rem;
            top: 1rem;
            max-width: none;
        }
    }
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = toastStyles;
document.head.appendChild(styleSheet);

// Initialize toast manager only if not already initialized
if (!window.toastManager) {
    window.toastManager = new ToastManager();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastManager;
}
