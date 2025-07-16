/**
 * Logo Manager - Dynamic Logo Sizing and Management
 * Handles responsive logo sizing, loading states, and adaptive display
 */

// Prevent multiple script executions
(function() {
    'use strict';

    if (window.logoManagerLoaded) {
        console.log('Logo manager already loaded');
        return;
    }
    window.logoManagerLoaded = true;

class LogoManager {
    constructor() {
        this.logos = document.querySelectorAll('.logo-primary, .logo-compact, .logo-full, .logo-footer');
        this.breakpoints = {
            xs: 0,
            sm: 640,
            md: 768,
            lg: 1024,
            xl: 1280,
            '2xl': 1536
        };
        this.logoSizes = {
            xs: '1.5rem',
            sm: '2rem',
            md: '2.5rem',
            lg: '3rem',
            xl: '3.5rem',
            '2xl': '4rem',
            '3xl': '5rem'
        };
        
        this.init();
    }

    init() {
        this.handleResponsiveLoading();
        this.setupErrorHandling();
        this.setupAccessibility();
        this.setupPerformanceOptimizations();
        
        // Listen for window resize
        window.addEventListener('resize', this.debounce(this.handleResize.bind(this), 250));
        
        // Listen for orientation change
        window.addEventListener('orientationchange', () => {
            setTimeout(() => this.handleResize(), 100);
        });
    }

    /**
     * Handle responsive logo loading
     */
    handleResponsiveLoading() {
        this.logos.forEach(logo => {
            // Add loading state
            logo.classList.add('logo-loading');
            
            // Handle load event
            logo.addEventListener('load', () => {
                logo.classList.remove('logo-loading');
                this.optimizeLogoSize(logo);
            });
            
            // Handle error event
            logo.addEventListener('error', () => {
                this.handleLogoError(logo);
            });
        });
    }

    /**
     * Setup error handling for logos
     */
    setupErrorHandling() {
        this.logos.forEach(logo => {
            logo.addEventListener('error', (e) => {
                console.warn('Logo failed to load:', e.target.src);
                this.showFallbackLogo(e.target);
            });
        });
    }

    /**
     * Show fallback logo or text
     */
    showFallbackLogo(logoElement) {
        const fallback = document.createElement('div');
        fallback.className = 'logo-error flex items-center justify-center';
        fallback.style.height = logoElement.style.height || '2.5rem';
        fallback.style.width = 'auto';
        fallback.innerHTML = '<span class="font-bold text-red-600">GURUMISHA</span>';
        
        logoElement.parentNode.replaceChild(fallback, logoElement);
    }

    /**
     * Setup accessibility features
     */
    setupAccessibility() {
        this.logos.forEach(logo => {
            // Ensure proper alt text
            if (!logo.alt || logo.alt.trim() === '') {
                logo.alt = 'Gurumisha Motors - Premium Automotive Marketplace';
            }
            
            // Add role for screen readers
            logo.setAttribute('role', 'img');
            
            // Add keyboard navigation
            const logoLink = logo.closest('a');
            if (logoLink) {
                logoLink.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        logoLink.click();
                    }
                });
            }
        });
    }

    /**
     * Setup performance optimizations
     */
    setupPerformanceOptimizations() {
        // Use Intersection Observer for lazy loading if needed
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.optimizeLogoSize(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            });

            this.logos.forEach(logo => {
                observer.observe(logo);
            });
        }
    }

    /**
     * Optimize logo size based on viewport and container
     */
    optimizeLogoSize(logo) {
        const container = logo.parentElement;
        const containerWidth = container.offsetWidth;
        const viewportWidth = window.innerWidth;
        
        // Calculate optimal size based on container and viewport
        let optimalSize = this.calculateOptimalSize(containerWidth, viewportWidth);
        
        // Apply size with smooth transition
        logo.style.transition = 'height 0.3s ease, width 0.3s ease';
        logo.style.height = optimalSize;
        logo.style.width = 'auto';
    }

    /**
     * Calculate optimal logo size
     */
    calculateOptimalSize(containerWidth, viewportWidth) {
        // Base size calculation
        let baseSize = Math.min(containerWidth * 0.8, viewportWidth * 0.15);
        
        // Apply breakpoint-based sizing
        if (viewportWidth >= this.breakpoints['2xl']) {
            return Math.max(baseSize, 80) + 'px'; // 5rem
        } else if (viewportWidth >= this.breakpoints.xl) {
            return Math.max(baseSize, 64) + 'px'; // 4rem
        } else if (viewportWidth >= this.breakpoints.lg) {
            return Math.max(baseSize, 56) + 'px'; // 3.5rem
        } else if (viewportWidth >= this.breakpoints.md) {
            return Math.max(baseSize, 48) + 'px'; // 3rem
        } else if (viewportWidth >= this.breakpoints.sm) {
            return Math.max(baseSize, 40) + 'px'; // 2.5rem
        } else {
            return Math.max(baseSize, 32) + 'px'; // 2rem
        }
    }

    /**
     * Handle window resize
     */
    handleResize() {
        this.logos.forEach(logo => {
            if (!logo.classList.contains('logo-loading')) {
                this.optimizeLogoSize(logo);
            }
        });
    }

    /**
     * Debounce utility function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Public method to manually set logo size
     */
    setLogoSize(size) {
        if (this.logoSizes[size]) {
            this.logos.forEach(logo => {
                logo.style.height = this.logoSizes[size];
                logo.style.width = 'auto';
            });
        }
    }

    /**
     * Public method to reset logo sizes to default
     */
    resetLogoSizes() {
        this.logos.forEach(logo => {
            logo.style.height = '';
            logo.style.width = '';
            this.optimizeLogoSize(logo);
        });
    }

    /**
     * Public method to get current logo dimensions
     */
    getLogoDimensions() {
        const dimensions = {};
        this.logos.forEach((logo, index) => {
            dimensions[`logo_${index}`] = {
                width: logo.offsetWidth,
                height: logo.offsetHeight,
                naturalWidth: logo.naturalWidth,
                naturalHeight: logo.naturalHeight
            };
        });
        return dimensions;
    }

    /**
     * Public method to preload logo variants
     */
    preloadLogoVariants() {
        const logoUrls = [
            '/static/images/logo.png',
            '/static/images/logo-compact.png'
        ];

        logoUrls.forEach(url => {
            const img = new Image();
            img.src = url;
        });
    }
}

// Initialize Logo Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (!window.logoManager) {
        window.logoManager = new LogoManager();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LogoManager;
}

})(); // End of IIFE
