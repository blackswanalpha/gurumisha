/**
 * Hot Deals JavaScript functionality
 * Handles countdown timers, deal interactions, and HTMX integration
 */

class HotDealsManager {
    constructor() {
        this.countdownTimers = new Map();
        this.init();
    }

    init() {
        this.initCountdownTimers();
        this.initDealInteractions();
        this.initHotDealForm();
        
        // Update timers every second
        setInterval(() => {
            this.updateAllCountdowns();
        }, 1000);
    }

    initCountdownTimers() {
        const countdownElements = document.querySelectorAll('[data-countdown-end]');
        
        countdownElements.forEach(element => {
            const endTime = new Date(element.dataset.countdownEnd);
            const dealId = element.dataset.dealId;
            
            this.countdownTimers.set(dealId, {
                element: element,
                endTime: endTime,
                isActive: true
            });
        });
    }

    updateAllCountdowns() {
        this.countdownTimers.forEach((timer, dealId) => {
            if (timer.isActive) {
                this.updateCountdown(dealId, timer);
            }
        });
    }

    updateCountdown(dealId, timer) {
        const now = new Date();
        const timeLeft = timer.endTime - now;

        if (timeLeft <= 0) {
            // Deal expired
            timer.element.innerHTML = `
                <div class="bg-gray-500 text-white px-3 py-1 rounded-full text-xs font-bold">
                    <i class="fas fa-clock mr-1"></i>
                    EXPIRED
                </div>
            `;
            timer.isActive = false;
            this.handleDealExpired(dealId);
            return;
        }

        const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

        let timeString = '';
        if (days > 0) {
            timeString = `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            timeString = `${hours}h ${minutes}m ${seconds}s`;
        } else if (minutes > 0) {
            timeString = `${minutes}m ${seconds}s`;
        } else {
            timeString = `${seconds}s`;
        }

        // Add urgency styling for last hour
        const urgencyClass = timeLeft < 3600000 ? 'animate-pulse bg-red-600' : 'bg-red-500';
        
        timer.element.innerHTML = `
            <div class="${urgencyClass} text-white px-3 py-1 rounded-full text-xs font-bold">
                <i class="fas fa-fire mr-1"></i>
                ${timeString} left
            </div>
        `;
    }

    handleDealExpired(dealId) {
        // Show expired message
        const dealCard = document.querySelector(`[data-deal-id="${dealId}"]`);
        if (dealCard) {
            dealCard.classList.add('opacity-50');
            
            // Add expired overlay
            const overlay = document.createElement('div');
            overlay.className = 'absolute inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center rounded-lg';
            overlay.innerHTML = `
                <div class="text-white text-center">
                    <i class="fas fa-clock text-4xl mb-2"></i>
                    <p class="font-bold">Deal Expired</p>
                </div>
            `;
            dealCard.style.position = 'relative';
            dealCard.appendChild(overlay);
        }
    }

    initDealInteractions() {
        // Track deal views
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-deal-view]')) {
                const dealId = e.target.closest('[data-deal-view]').dataset.dealView;
                this.trackDealInteraction(dealId, 'view');
            }
        });

        // Track deal clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-deal-click]')) {
                const dealId = e.target.closest('[data-deal-click]').dataset.dealClick;
                this.trackDealInteraction(dealId, 'click');
            }
        });
    }

    trackDealInteraction(dealId, type) {
        // Send analytics data
        fetch('/hot-deals/track/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
            body: JSON.stringify({
                deal_id: dealId,
                interaction_type: type
            })
        }).catch(error => {
            console.log('Analytics tracking failed:', error);
        });
    }

    initHotDealForm() {
        const form = document.getElementById('hot-deal-form');
        if (!form) return;

        // Real-time discount calculation
        const discountTypeSelect = form.querySelector('[name="discount_type"]');
        const discountValueInput = form.querySelector('[name="discount_value"]');
        const originalPriceInput = form.querySelector('[name="original_price"]');
        const discountedPriceDisplay = form.querySelector('#discounted-price');

        const calculateDiscount = () => {
            const discountType = discountTypeSelect?.value;
            const discountValue = parseFloat(discountValueInput?.value) || 0;
            const originalPrice = parseFloat(originalPriceInput?.value) || 0;

            if (!originalPrice || !discountValue) {
                discountedPriceDisplay.textContent = 'KSh 0';
                return;
            }

            let discountedPrice;
            if (discountType === 'percentage') {
                discountedPrice = originalPrice - (originalPrice * discountValue / 100);
            } else {
                discountedPrice = originalPrice - discountValue;
            }

            discountedPrice = Math.max(0, discountedPrice);
            discountedPriceDisplay.textContent = `KSh ${discountedPrice.toLocaleString()}`;
        };

        discountTypeSelect?.addEventListener('change', calculateDiscount);
        discountValueInput?.addEventListener('input', calculateDiscount);
        originalPriceInput?.addEventListener('input', calculateDiscount);

        // Form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitHotDealForm(form);
        });
    }

    submitHotDealForm(form) {
        const formData = new FormData(form);
        const submitButton = form.querySelector('[type="submit"]');
        const originalText = submitButton.textContent;

        // Show loading state
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Creating...';

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success message
                this.showToast('Hot deal created successfully!', 'success');
                form.reset();
                
                // Redirect or update UI
                if (data.deal_id) {
                    setTimeout(() => {
                        window.location.href = `/hot-deals/${data.deal_id}/`;
                    }, 1500);
                }
            } else {
                this.showToast(data.message || 'Error creating hot deal', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showToast('An error occurred while creating the hot deal', 'error');
        })
        .finally(() => {
            // Reset button
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        });
    }

    showToast(message, type = 'info') {
        // Use existing toast system if available
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            // Fallback alert
            alert(message);
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    // Public methods for external use
    addCountdownTimer(dealId, endTime) {
        const element = document.querySelector(`[data-deal-id="${dealId}"] .countdown-timer`);
        if (element) {
            this.countdownTimers.set(dealId, {
                element: element,
                endTime: new Date(endTime),
                isActive: true
            });
        }
    }

    removeCountdownTimer(dealId) {
        this.countdownTimers.delete(dealId);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.hotDealsManager = new HotDealsManager();
});

// HTMX integration
document.addEventListener('htmx:afterSwap', () => {
    // Reinitialize countdown timers after HTMX swaps
    if (window.hotDealsManager) {
        window.hotDealsManager.initCountdownTimers();
    }
});
