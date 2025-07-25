/**
 * Enhanced Price Formatting Utilities for Gurumisha
 * Provides consistent currency formatting across the application
 */

class PriceFormatter {
    constructor() {
        this.currency = 'KSh';
        this.locale = 'en-KE';
        this.defaultOptions = {
            style: 'decimal',
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        };
    }

    /**
     * Format price with consistent KSh currency format
     * @param {number|string} value - The price value to format
     * @param {object} options - Formatting options
     * @returns {string} Formatted price string
     */
    formatPrice(value, options = {}) {
        try {
            // Handle null, undefined, or empty values
            if (value === null || value === undefined || value === '') {
                return `${this.currency} 0`;
            }

            // Clean and convert to number
            let numValue = this.cleanPriceValue(value);
            
            // Validate the number
            if (isNaN(numValue) || numValue < 0) {
                return `${this.currency} 0`;
            }

            // Merge options with defaults
            const formatOptions = { ...this.defaultOptions, ...options };
            
            // Format the number
            const formatter = new Intl.NumberFormat(this.locale, formatOptions);
            const formattedNumber = formatter.format(numValue);
            
            return `${this.currency} ${formattedNumber}`;
        } catch (error) {
            console.warn('Price formatting error:', error);
            return `${this.currency} 0`;
        }
    }

    /**
     * Format price without decimals
     * @param {number|string} value - The price value to format
     * @returns {string} Formatted price string without decimals
     */
    formatPriceNoDecimals(value) {
        return this.formatPrice(value, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }

    /**
     * Format price with exact 2 decimal places
     * @param {number|string} value - The price value to format
     * @returns {string} Formatted price string with 2 decimals
     */
    formatPriceWithDecimals(value) {
        return this.formatPrice(value, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    /**
     * Format price range
     * @param {number|string} minPrice - Minimum price
     * @param {number|string} maxPrice - Maximum price
     * @returns {string} Formatted price range string
     */
    formatPriceRange(minPrice, maxPrice) {
        try {
            const hasMin = minPrice !== null && minPrice !== undefined && minPrice !== '';
            const hasMax = maxPrice !== null && maxPrice !== undefined && maxPrice !== '';

            if (hasMin && hasMax) {
                const minFormatted = this.formatPriceNoDecimals(minPrice);
                const maxFormatted = this.formatPriceNoDecimals(maxPrice);
                return `${minFormatted} - ${maxFormatted}`;
            } else if (hasMin) {
                const minFormatted = this.formatPriceNoDecimals(minPrice);
                return `From ${minFormatted}`;
            } else if (hasMax) {
                const maxFormatted = this.formatPriceNoDecimals(maxPrice);
                return `Up to ${maxFormatted}`;
            } else {
                return 'Any Price';
            }
        } catch (error) {
            console.warn('Price range formatting error:', error);
            return 'Any Price';
        }
    }

    /**
     * Clean price value by removing currency symbols and formatting
     * @param {number|string} value - The value to clean
     * @returns {number} Cleaned numeric value
     */
    cleanPriceValue(value) {
        if (typeof value === 'number') {
            return value;
        }

        if (typeof value === 'string') {
            // Remove currency symbols, commas, and whitespace
            return parseFloat(
                value
                    .replace(/KSh|KES|Ksh|ksh/gi, '')
                    .replace(/,/g, '')
                    .trim()
            );
        }

        return 0;
    }

    /**
     * Format number with commas (no currency symbol)
     * @param {number|string} value - The value to format
     * @returns {string} Formatted number string
     */
    formatNumber(value) {
        try {
            const numValue = this.cleanPriceValue(value);
            
            if (isNaN(numValue)) {
                return '0';
            }

            const formatter = new Intl.NumberFormat(this.locale, {
                style: 'decimal',
                minimumFractionDigits: 0,
                maximumFractionDigits: numValue % 1 === 0 ? 0 : 2
            });
            
            return formatter.format(numValue);
        } catch (error) {
            console.warn('Number formatting error:', error);
            return '0';
        }
    }

    /**
     * Parse price from formatted string
     * @param {string} formattedPrice - Formatted price string
     * @returns {number} Numeric price value
     */
    parsePrice(formattedPrice) {
        return this.cleanPriceValue(formattedPrice);
    }

    /**
     * Validate price input
     * @param {string|number} value - Price value to validate
     * @returns {object} Validation result with isValid and message
     */
    validatePrice(value) {
        try {
            const numValue = this.cleanPriceValue(value);
            
            if (isNaN(numValue)) {
                return {
                    isValid: false,
                    message: 'Please enter a valid price'
                };
            }

            if (numValue < 0) {
                return {
                    isValid: false,
                    message: 'Price cannot be negative'
                };
            }

            if (numValue > 1000000000) { // 1 billion limit
                return {
                    isValid: false,
                    message: 'Price is too high'
                };
            }

            return {
                isValid: true,
                message: 'Valid price',
                value: numValue
            };
        } catch (error) {
            return {
                isValid: false,
                message: 'Invalid price format'
            };
        }
    }

    /**
     * Format price for display in forms (without currency symbol)
     * @param {number|string} value - The price value
     * @returns {string} Formatted value for form inputs
     */
    formatForInput(value) {
        const numValue = this.cleanPriceValue(value);
        return isNaN(numValue) ? '' : this.formatNumber(numValue);
    }

    /**
     * Calculate and format discount
     * @param {number|string} originalPrice - Original price
     * @param {number|string} discountedPrice - Discounted price
     * @returns {object} Discount information
     */
    calculateDiscount(originalPrice, discountedPrice) {
        try {
            const original = this.cleanPriceValue(originalPrice);
            const discounted = this.cleanPriceValue(discountedPrice);
            
            if (isNaN(original) || isNaN(discounted) || original <= 0) {
                return {
                    amount: 0,
                    percentage: 0,
                    formattedAmount: this.formatPriceNoDecimals(0),
                    formattedPercentage: '0%'
                };
            }

            const discountAmount = original - discounted;
            const discountPercentage = (discountAmount / original) * 100;

            return {
                amount: discountAmount,
                percentage: discountPercentage,
                formattedAmount: this.formatPriceNoDecimals(discountAmount),
                formattedPercentage: `${Math.round(discountPercentage)}%`
            };
        } catch (error) {
            console.warn('Discount calculation error:', error);
            return {
                amount: 0,
                percentage: 0,
                formattedAmount: this.formatPriceNoDecimals(0),
                formattedPercentage: '0%'
            };
        }
    }
}

// Create global instance
window.priceFormatter = new PriceFormatter();

// Utility functions for backward compatibility
window.formatPrice = (value) => window.priceFormatter.formatPriceNoDecimals(value);
window.formatPriceWithDecimals = (value) => window.priceFormatter.formatPriceWithDecimals(value);
window.formatPriceRange = (min, max) => window.priceFormatter.formatPriceRange(min, max);
window.parsePrice = (value) => window.priceFormatter.parsePrice(value);

// Auto-format price inputs on page load
document.addEventListener('DOMContentLoaded', function() {
    // Format all elements with price-format class
    document.querySelectorAll('.price-format').forEach(element => {
        const value = element.textContent || element.value;
        if (value) {
            const formatted = window.priceFormatter.formatPriceNoDecimals(value);
            if (element.tagName === 'INPUT') {
                element.value = window.priceFormatter.formatForInput(value);
            } else {
                element.textContent = formatted;
            }
        }
    });

    // Add real-time formatting to price inputs
    document.querySelectorAll('input[type="number"][data-price], input[data-price-format]').forEach(input => {
        input.addEventListener('blur', function() {
            const validation = window.priceFormatter.validatePrice(this.value);
            if (validation.isValid) {
                this.value = window.priceFormatter.formatForInput(validation.value);
            }
        });
    });
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PriceFormatter;
}
