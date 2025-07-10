/**
 * Admin Import Requests JavaScript
 * Handles modal interactions, form validation, and enhanced user experience
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeImportRequestFeatures();
    initializeFormValidation();
    initializeTooltips();
    initializeStatusWorkflow();
    initializeTableEnhancements();
});

/**
 * Initialize import request features
 */
function initializeImportRequestFeatures() {
    // Handle HTMX events for better UX
    document.addEventListener('htmx:beforeRequest', function(event) {
        const target = event.target;
        
        // Add loading state to buttons
        if (target.tagName === 'BUTTON') {
            target.classList.add('loading');
            target.disabled = true;
            
            // Add spinner to button
            const icon = target.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-spinner fa-spin';
            }
        }
    });
    
    document.addEventListener('htmx:afterRequest', function(event) {
        const target = event.target;
        
        // Remove loading state from buttons
        if (target.tagName === 'BUTTON') {
            target.classList.remove('loading');
            target.disabled = false;
            
            // Restore original icon
            const icon = target.querySelector('i');
            if (icon && target.dataset.originalIcon) {
                icon.className = target.dataset.originalIcon;
            }
        }
        
        // Show success/error messages
        if (event.detail.xhr.status === 200) {
            showNotification('Operation completed successfully', 'success');
        } else if (event.detail.xhr.status >= 400) {
            showNotification('An error occurred. Please try again.', 'error');
        }
    });
    
    // Store original icons for restoration
    document.querySelectorAll('button[hx-get], button[hx-post], button[hx-delete]').forEach(button => {
        const icon = button.querySelector('i');
        if (icon) {
            button.dataset.originalIcon = icon.className;
        }
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    // Real-time validation for import request forms
    document.addEventListener('input', function(event) {
        const input = event.target;
        
        if (input.form && input.form.querySelector('[hx-post]')) {
            validateField(input);
        }
    });
    
    // Budget validation
    document.addEventListener('change', function(event) {
        const input = event.target;
        
        if (input.name === 'budget_min' || input.name === 'budget_max') {
            validateBudgetRange(input.form);
        }
    });
}

/**
 * Validate individual form field
 */
function validateField(field) {
    const value = field.value.trim();
    const fieldName = field.name;
    let isValid = true;
    let errorMessage = '';
    
    // Remove existing error styling
    field.classList.remove('border-red-500', 'border-green-500');
    
    // Required field validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Specific field validations
    switch (fieldName) {
        case 'year':
            const year = parseInt(value);
            const currentYear = new Date().getFullYear();
            if (value && (year < 1990 || year > currentYear + 1)) {
                isValid = false;
                errorMessage = `Year must be between 1990 and ${currentYear + 1}`;
            }
            break;
            
        case 'budget_min':
        case 'budget_max':
        case 'estimated_cost':
            if (value && parseFloat(value) < 0) {
                isValid = false;
                errorMessage = 'Amount must be positive';
            }
            break;
            
        case 'email':
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (value && !emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address';
            }
            break;
    }
    
    // Apply validation styling
    if (isValid) {
        field.classList.add('border-green-500');
        removeFieldError(field);
    } else {
        field.classList.add('border-red-500');
        showFieldError(field, errorMessage);
    }
    
    return isValid;
}

/**
 * Validate budget range
 */
function validateBudgetRange(form) {
    const minBudget = form.querySelector('[name="budget_min"]');
    const maxBudget = form.querySelector('[name="budget_max"]');
    
    if (!minBudget || !maxBudget) return;
    
    const minValue = parseFloat(minBudget.value);
    const maxValue = parseFloat(maxBudget.value);
    
    // Remove existing error styling
    minBudget.classList.remove('border-red-500');
    maxBudget.classList.remove('border-red-500');
    removeFieldError(minBudget);
    removeFieldError(maxBudget);
    
    if (minValue && maxValue && minValue >= maxValue) {
        maxBudget.classList.add('border-red-500');
        showFieldError(maxBudget, 'Maximum budget must be greater than minimum budget');
        return false;
    }
    
    return true;
}

/**
 * Show field error message
 */
function showFieldError(field, message) {
    removeFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error text-red-500 text-sm mt-1';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

/**
 * Remove field error message
 */
function removeFieldError(field) {
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

/**
 * Initialize tooltips for action buttons
 */
function initializeTooltips() {
    // Enhanced tooltip functionality
    document.addEventListener('mouseenter', function(event) {
        const element = event.target.closest('[data-tooltip]');
        if (element) {
            showTooltip(element);
        }
    }, true);
    
    document.addEventListener('mouseleave', function(event) {
        const element = event.target.closest('[data-tooltip]');
        if (element) {
            hideTooltip();
        }
    }, true);
}

/**
 * Show tooltip
 */
function showTooltip(element) {
    const tooltip = document.createElement('div');
    tooltip.className = 'admin-tooltip fixed z-50 px-2 py-1 text-xs text-white bg-gray-900 rounded shadow-lg pointer-events-none';
    tooltip.textContent = element.dataset.tooltip;
    tooltip.id = 'active-tooltip';
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
    let top = rect.top - tooltipRect.height - 8;
    
    // Adjust if tooltip goes off screen
    if (left < 0) left = 8;
    if (left + tooltipRect.width > window.innerWidth) {
        left = window.innerWidth - tooltipRect.width - 8;
    }
    if (top < 0) {
        top = rect.bottom + 8;
    }
    
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    
    // Fade in
    setTimeout(() => {
        tooltip.style.opacity = '1';
    }, 10);
}

/**
 * Hide tooltip
 */
function hideTooltip() {
    const tooltip = document.getElementById('active-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

/**
 * Initialize status workflow enhancements
 */
function initializeStatusWorkflow() {
    // Animate status changes
    document.addEventListener('htmx:afterRequest', function(event) {
        if (event.detail.xhr.responseURL && event.detail.xhr.responseURL.includes('status-update')) {
            const response = JSON.parse(event.detail.xhr.responseText);
            if (response.success) {
                animateStatusChange(response.new_status);
            }
        }
    });
}

/**
 * Animate status change
 */
function animateStatusChange(newStatus) {
    // Find status badges and animate them
    document.querySelectorAll('.status-badge').forEach(badge => {
        if (badge.textContent.toLowerCase().includes(newStatus.replace('_', ' '))) {
            badge.style.transform = 'scale(1.1)';
            badge.style.transition = 'transform 0.3s ease';
            
            setTimeout(() => {
                badge.style.transform = 'scale(1)';
            }, 300);
        }
    });
}

/**
 * Initialize table enhancements
 */
function initializeTableEnhancements() {
    // Smooth row hover effects
    document.addEventListener('mouseenter', function(event) {
        const row = event.target.closest('tbody tr');
        if (row) {
            row.style.transform = 'translateY(-1px)';
            row.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
        }
    }, true);
    
    document.addEventListener('mouseleave', function(event) {
        const row = event.target.closest('tbody tr');
        if (row) {
            row.style.transform = 'translateY(0)';
            row.style.boxShadow = 'none';
        }
    }, true);
    
    // Action button hover effects
    document.addEventListener('mouseenter', function(event) {
        const button = event.target.closest('.action-btn');
        if (button) {
            button.style.transform = 'translateY(-2px) scale(1.05)';
        }
    }, true);
    
    document.addEventListener('mouseleave', function(event) {
        const button = event.target.closest('.action-btn');
        if (button) {
            button.style.transform = 'translateY(0) scale(1)';
        }
    }, true);
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-white max-w-sm transform translate-x-full transition-transform duration-300 ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 
        type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
    }`;
    
    notification.innerHTML = `
        <div class="flex items-center justify-between">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-3 text-white hover:text-gray-200">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Slide in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(full)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

/**
 * Export functions for global use
 */
window.ImportRequestAdmin = {
    validateField: validateField,
    validateBudgetRange: validateBudgetRange,
    showNotification: showNotification,
    showTooltip: showTooltip,
    hideTooltip: hideTooltip
};
