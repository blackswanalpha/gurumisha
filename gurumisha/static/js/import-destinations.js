/**
 * Enhanced Import Destinations Interactive Features
 * Provides smooth animations, hover effects, and enhanced user interactions
 */

class ImportDestinationsManager {
    constructor() {
        this.destinationCards = document.querySelectorAll('.destination-card');
        this.trustIndicators = document.querySelectorAll('.trust-indicator');
        this.ctaButton = document.querySelector('.cta-explore-destinations');
        this.isInitialized = false;
        
        this.init();
    }

    init() {
        if (this.isInitialized) return;
        
        this.setupDestinationCards();
        this.setupTrustIndicators();
        this.setupCTAButton();
        this.setupScrollAnimations();
        this.setupAccessibility();
        
        this.isInitialized = true;
        console.log('Import Destinations Manager initialized successfully');
    }

    setupDestinationCards() {
        this.destinationCards.forEach((card, index) => {
            // Add staggered entrance animation
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('animate-slide-up');

            // Enhanced hover effects with throttling
            let hoverThrottle = false;

            card.addEventListener('mouseenter', (e) => {
                if (!hoverThrottle) {
                    hoverThrottle = true;
                    this.handleCardHover(e, true);
                    setTimeout(() => { hoverThrottle = false; }, 100);
                }
            });

            card.addEventListener('mouseleave', (e) => {
                if (!hoverThrottle) {
                    hoverThrottle = true;
                    this.handleCardHover(e, false);
                    setTimeout(() => { hoverThrottle = false; }, 100);
                }
            });

            // Click analytics tracking
            card.addEventListener('click', (e) => this.handleCardClick(e));

            // Touch support for mobile
            card.addEventListener('touchstart', (e) => this.handleCardTouch(e));
        });
    }

    handleCardHover(event, isEntering) {
        const card = event.currentTarget;
        const countryName = card.dataset.country;

        // Prevent rapid hover state changes
        clearTimeout(card.hoverTimeout);

        if (isEntering) {
            // Add enhanced hover state with delay to prevent flickering
            card.hoverTimeout = setTimeout(() => {
                card.classList.add('destination-card-hovered');

                // Trigger subtle animation on other cards with requestAnimationFrame
                requestAnimationFrame(() => {
                    this.destinationCards.forEach(otherCard => {
                        if (otherCard !== card) {
                            otherCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                            otherCard.style.opacity = '0.8';
                            otherCard.style.transform = 'scale(0.99)';
                        }
                    });
                });

                // Show additional info tooltip (if needed)
                this.showCountryTooltip(card, countryName);
            }, 50);

        } else {
            // Remove hover state with delay
            card.hoverTimeout = setTimeout(() => {
                card.classList.remove('destination-card-hovered');

                // Reset other cards with requestAnimationFrame
                requestAnimationFrame(() => {
                    this.destinationCards.forEach(otherCard => {
                        otherCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                        otherCard.style.opacity = '1';
                        otherCard.style.transform = 'scale(1)';
                    });
                });

                // Hide tooltip
                this.hideCountryTooltip();
            }, 50);
        }
    }

    handleCardClick(event) {
        const card = event.currentTarget;
        const countryName = card.dataset.country;
        
        // Add click animation
        card.style.transform = 'scale(0.95)';
        setTimeout(() => {
            card.style.transform = '';
        }, 150);
        
        // Track analytics (if analytics system is available)
        if (typeof gtag !== 'undefined') {
            gtag('event', 'destination_card_click', {
                'country': countryName,
                'section': 'import_destinations'
            });
        }
        
        console.log(`Destination card clicked: ${countryName}`);
    }

    handleCardTouch(event) {
        const card = event.currentTarget;
        
        // Add touch feedback
        card.classList.add('destination-card-touched');
        setTimeout(() => {
            card.classList.remove('destination-card-touched');
        }, 200);
    }

    setupTrustIndicators() {
        this.trustIndicators.forEach((indicator, index) => {
            // Staggered animation
            indicator.style.animationDelay = `${0.5 + (index * 0.1)}s`;
            indicator.classList.add('animate-fade-in');
            
            // Hover effects
            indicator.addEventListener('mouseenter', () => {
                indicator.style.transform = 'translateY(-2px) scale(1.05)';
            });
            
            indicator.addEventListener('mouseleave', () => {
                indicator.style.transform = 'translateY(0) scale(1)';
            });
        });
    }

    setupCTAButton() {
        if (!this.ctaButton) return;
        
        this.ctaButton.addEventListener('mouseenter', () => {
            this.ctaButton.style.transform = 'translateY(-3px) scale(1.05)';
        });
        
        this.ctaButton.addEventListener('mouseleave', () => {
            this.ctaButton.style.transform = 'translateY(0) scale(1)';
        });
        
        this.ctaButton.addEventListener('click', (e) => {
            // Add click animation
            this.ctaButton.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.ctaButton.style.transform = '';
            }, 150);
            
            // Track analytics
            if (typeof gtag !== 'undefined') {
                gtag('event', 'cta_click', {
                    'button_text': 'explore_all_destinations',
                    'section': 'import_destinations'
                });
            }
        });
    }

    setupScrollAnimations() {
        // Intersection Observer for scroll-triggered animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                    
                    // Trigger staggered animations for child elements
                    const childElements = entry.target.querySelectorAll('.destination-card, .trust-indicator');
                    childElements.forEach((child, index) => {
                        setTimeout(() => {
                            child.classList.add('animate-entrance');
                        }, index * 100);
                    });
                }
            });
        }, observerOptions);

        // Observe the main section
        const destinationsSection = document.querySelector('#popular-destinations, .destination-cards-container');
        if (destinationsSection) {
            observer.observe(destinationsSection);
        }
    }

    setupAccessibility() {
        // Enhanced keyboard navigation
        this.destinationCards.forEach(card => {
            card.setAttribute('tabindex', '0');
            card.setAttribute('role', 'button');
            card.setAttribute('aria-label', `Explore import options from ${card.dataset.country}`);
            
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    card.click();
                }
            });
            
            card.addEventListener('focus', () => {
                card.style.outline = '2px solid #DC2626';
                card.style.outlineOffset = '2px';
            });
            
            card.addEventListener('blur', () => {
                card.style.outline = 'none';
            });
        });
    }

    showCountryTooltip(card, countryName) {
        // Create or update tooltip (optional feature)
        let tooltip = document.getElementById('country-tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'country-tooltip';
            tooltip.className = 'fixed z-50 bg-black bg-opacity-80 text-white px-3 py-2 rounded-lg text-sm pointer-events-none transition-opacity duration-200';
            document.body.appendChild(tooltip);
        }
        
        tooltip.textContent = `Click to explore ${countryName} import options`;
        tooltip.style.opacity = '1';
        
        // Position tooltip near cursor
        document.addEventListener('mousemove', this.updateTooltipPosition);
    }

    hideCountryTooltip() {
        const tooltip = document.getElementById('country-tooltip');
        if (tooltip) {
            tooltip.style.opacity = '0';
            document.removeEventListener('mousemove', this.updateTooltipPosition);
        }
    }

    updateTooltipPosition(e) {
        const tooltip = document.getElementById('country-tooltip');
        if (tooltip) {
            tooltip.style.left = `${e.clientX + 10}px`;
            tooltip.style.top = `${e.clientY - 40}px`;
        }
    }

    // Performance optimization: Debounced resize handler
    handleResize() {
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
            this.recalculateAnimations();
        }, 250);
    }

    recalculateAnimations() {
        // Recalculate animations for responsive design
        const isMobile = window.innerWidth < 768;
        
        this.destinationCards.forEach(card => {
            if (isMobile) {
                card.style.transition = 'all 0.3s ease';
            } else {
                card.style.transition = 'all 0.5s cubic-bezier(0.25, 1, 0.5, 1)';
            }
        });
    }

    // Public method to refresh the component
    refresh() {
        this.isInitialized = false;
        this.init();
    }

    // Public method to destroy the component
    destroy() {
        this.destinationCards.forEach(card => {
            card.removeEventListener('mouseenter', this.handleCardHover);
            card.removeEventListener('mouseleave', this.handleCardHover);
            card.removeEventListener('click', this.handleCardClick);
            card.removeEventListener('touchstart', this.handleCardTouch);
        });
        
        if (this.ctaButton) {
            this.ctaButton.removeEventListener('mouseenter', () => {});
            this.ctaButton.removeEventListener('mouseleave', () => {});
            this.ctaButton.removeEventListener('click', () => {});
        }
        
        this.isInitialized = false;
        console.log('Import Destinations Manager destroyed');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on a page with import destinations
    if (document.querySelector('.destination-card')) {
        window.importDestinationsManager = new ImportDestinationsManager();
    }
});

// Handle page navigation (for SPA-like behavior)
document.addEventListener('htmx:afterSwap', () => {
    if (document.querySelector('.destination-card')) {
        if (window.importDestinationsManager) {
            window.importDestinationsManager.refresh();
        } else {
            window.importDestinationsManager = new ImportDestinationsManager();
        }
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImportDestinationsManager;
}
