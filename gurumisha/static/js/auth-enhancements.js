/**
 * Authentication Pages Enhancement JavaScript
 * Provides interactive features for login and register pages
 */

// Prevent multiple script executions
(function() {
    'use strict';

    if (window.authEnhancementsLoaded) {
        console.log('Auth enhancements already loaded');
        return;
    }
    window.authEnhancementsLoaded = true;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize authentication page enhancements
    initPasswordVisibilityToggle();
    initEnhancedFormValidation();
    initPasswordStrengthIndicator();
    initFormAnimations();
    initAccessibilityFeatures();
    initializeRememberMeEnhancements();
    initRealTimeValidation();
    initToastIntegration();
});

/**
 * Enhanced Password Visibility Toggle
 */
function initPasswordVisibilityToggle() {
    const passwordFields = document.querySelectorAll('input[type="password"]');

    passwordFields.forEach(field => {
        // Check if toggle button already exists (from HTML)
        const existingToggle = field.parentElement.querySelector('.password-toggle-btn');

        if (existingToggle) {
            // Use existing toggle button
            setupPasswordToggle(field, existingToggle);
        } else {
            // Create new toggle button (fallback)
            createPasswordToggle(field);
        }
    });
}

/**
 * Setup existing password toggle button
 */
function setupPasswordToggle(field, toggleButton) {
    // Add click event listener
    toggleButton.addEventListener('click', function() {
        togglePasswordVisibility(field, toggleButton);
    });

    // Add keyboard support
    toggleButton.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            togglePasswordVisibility(field, toggleButton);
        }
    });

    // Add touch support for mobile
    toggleButton.addEventListener('touchstart', function(e) {
        e.preventDefault();
        togglePasswordVisibility(field, toggleButton);
    });
}

/**
 * Create new password toggle button (fallback)
 */
function createPasswordToggle(field) {
    const wrapper = field.parentElement;

    // Create toggle button
    const toggleButton = document.createElement('button');
    toggleButton.type = 'button';
    toggleButton.className = 'password-toggle-btn';
    toggleButton.innerHTML = '<i class="fas fa-eye"></i>';
    toggleButton.setAttribute('aria-label', 'Show password');

    // Add to wrapper
    wrapper.appendChild(toggleButton);

    // Setup toggle functionality
    setupPasswordToggle(field, toggleButton);
}

/**
 * Toggle password visibility
 */
function togglePasswordVisibility(field, button) {
    const isPassword = field.type === 'password';
    const icon = button.querySelector('i');

    if (isPassword) {
        field.type = 'text';
        icon.className = 'fas fa-eye-slash';
        button.setAttribute('aria-label', 'Hide password');
        button.classList.add('active');
    } else {
        field.type = 'password';
        icon.className = 'fas fa-eye';
        button.setAttribute('aria-label', 'Show password');
        button.classList.remove('active');
    }

    // Add animation class
    button.classList.add('toggle-animation');
    setTimeout(() => {
        button.classList.remove('toggle-animation');
    }, 200);
}

/**
 * Enhanced Form Validation System
 */
function initEnhancedFormValidation() {
    const forms = document.querySelectorAll('#login-form, #register-form');

    forms.forEach(form => {
        const inputs = form.querySelectorAll('.auth-form-input');

        inputs.forEach(input => {
            // Enhanced focus effects
            input.addEventListener('focus', function() {
                const formGroup = this.closest('.auth-form-group');
                if (formGroup) {
                    formGroup.classList.add('focused');
                }
                this.classList.remove('invalid', 'valid');
            });

            input.addEventListener('blur', function() {
                const formGroup = this.closest('.auth-form-group');
                if (formGroup) {
                    formGroup.classList.remove('focused');
                }
                // Validate on blur for better UX
                validateFieldEnhanced(this);
            });
        });

        // Enhanced form submission
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            handleFormSubmission(this);
        });
    });
}

/**
 * Real-time Validation System
 */
function initRealTimeValidation() {
    const inputs = document.querySelectorAll('.auth-form-input[data-validation]');

    inputs.forEach(input => {
        let validationTimeout;

        input.addEventListener('input', function() {
            // Clear previous timeout
            clearTimeout(validationTimeout);

            // Add validating state
            this.classList.remove('valid', 'invalid');
            this.classList.add('validating');

            // Debounce validation
            validationTimeout = setTimeout(() => {
                validateFieldRealTime(this);
            }, 300);
        });

        // Immediate validation on paste
        input.addEventListener('paste', function() {
            setTimeout(() => {
                validateFieldRealTime(this);
            }, 100);
        });
    });
}

/**
 * Toast Integration for Form Feedback
 */
function initToastIntegration() {
    // Listen for form validation events
    document.addEventListener('fieldValidated', function(e) {
        const { field, isValid, message } = e.detail;

        if (!isValid && message && field.dataset.showToastErrors === 'true') {
            if (window.showError) {
                window.showError(message, { duration: 3000 });
            }
        }
    });

    // Listen for form submission events
    document.addEventListener('formSubmissionError', function(e) {
        const { message } = e.detail;

        if (window.showError) {
            window.showError(message, { duration: 5000 });
        }
    });

    // Listen for form submission success
    document.addEventListener('formSubmissionSuccess', function(e) {
        const { message } = e.detail;

        if (window.showSuccess) {
            window.showSuccess(message, { duration: 3000 });
        }
    });
}

/**
 * Enhanced Field Validation with Real-time Feedback
 */
function validateFieldEnhanced(field) {
    const value = field.value.trim();
    const validationType = field.dataset.validation;
    const fieldName = field.name;

    // Clear previous validation states
    clearFieldValidation(field);

    let isValid = true;
    let errorMessage = '';

    // Validation rules based on field type and requirements
    if (field.required && !value) {
        isValid = false;
        errorMessage = getRequiredFieldMessage(fieldName);
    } else if (value) {
        const validationResult = performFieldValidation(value, validationType, fieldName);
        isValid = validationResult.isValid;
        errorMessage = validationResult.message;
    }

    // Apply validation state
    applyValidationState(field, isValid, errorMessage);

    // Dispatch custom event for toast integration
    const event = new CustomEvent('fieldValidated', {
        detail: { field, isValid, message: errorMessage }
    });
    document.dispatchEvent(event);

    return isValid;
}

/**
 * Real-time Field Validation (with debouncing)
 */
function validateFieldRealTime(field) {
    field.classList.remove('validating');
    return validateFieldEnhanced(field);
}

/**
 * Perform specific validation based on field type
 */
function performFieldValidation(value, validationType, fieldName) {
    switch (validationType) {
        case 'email':
            return validateEmailField(value);
        case 'password':
            return validatePasswordField(value, fieldName);
        default:
            return validateGenericField(value, fieldName);
    }
}

/**
 * Email field validation
 */
function validateEmailField(email) {
    if (!isValidEmail(email)) {
        return { isValid: false, message: 'Please enter a valid email address' };
    }

    // Additional email validation rules
    if (email.length > 254) {
        return { isValid: false, message: 'Email address is too long' };
    }

    const localPart = email.split('@')[0];
    if (localPart.length > 64) {
        return { isValid: false, message: 'Email address format is invalid' };
    }

    return { isValid: true, message: 'Valid email address' };
}

/**
 * Password field validation for login
 */
function validatePasswordField(password, fieldName) {
    if (fieldName === 'password') {
        // For login, just check if password is provided
        if (password.length === 0) {
            return { isValid: false, message: 'Password is required' };
        }
        return { isValid: true, message: 'Password entered' };
    }

    // For registration passwords, use comprehensive validation
    return validatePassword(password);
}

/**
 * Generic field validation
 */
function validateGenericField(value, fieldName) {
    // Add specific validation rules for other fields as needed
    if (fieldName === 'username' && value) {
        if (value.length < 3) {
            return { isValid: false, message: 'Username must be at least 3 characters long' };
        }
        if (value.length > 30) {
            return { isValid: false, message: 'Username must be less than 30 characters' };
        }
        if (!/^[a-zA-Z0-9_.-]+$/.test(value)) {
            return { isValid: false, message: 'Username can only contain letters, numbers, dots, hyphens, and underscores' };
        }
    }

    return { isValid: true, message: 'Valid input' };
}

/**
 * Get appropriate required field message
 */
function getRequiredFieldMessage(fieldName) {
    const messages = {
        'username': 'Email address is required',
        'password': 'Password is required',
        'email': 'Email address is required',
        'first_name': 'First name is required',
        'last_name': 'Last name is required'
    };

    return messages[fieldName] || 'This field is required';
}

/**
 * Clear field validation states and messages
 */
function clearFieldValidation(field) {
    // Remove validation classes
    field.classList.remove('valid', 'invalid', 'error', 'success', 'validating');

    // Hide validation messages
    const formGroup = field.closest('.auth-form-group');
    if (formGroup) {
        const validationError = formGroup.querySelector('.auth-validation-error');
        const successIndicator = formGroup.querySelector('.auth-success-indicator');

        if (validationError) {
            validationError.style.display = 'none';
        }
        if (successIndicator) {
            successIndicator.style.display = 'none';
        }
    }
}

/**
 * Apply validation state to field
 */
function applyValidationState(field, isValid, message) {
    const formGroup = field.closest('.auth-form-group');
    if (!formGroup) return;

    const validationError = formGroup.querySelector('.auth-validation-error');
    const successIndicator = formGroup.querySelector('.auth-success-indicator');
    const errorText = validationError?.querySelector('.error-text');

    if (isValid && field.value.trim()) {
        // Show success state
        field.classList.add('valid');
        if (successIndicator) {
            successIndicator.style.display = 'flex';
        }
        if (validationError) {
            validationError.style.display = 'none';
        }
    } else if (!isValid) {
        // Show error state
        field.classList.add('invalid');
        if (validationError && errorText) {
            errorText.textContent = message;
            validationError.style.display = 'flex';
        }
        if (successIndicator) {
            successIndicator.style.display = 'none';
        }
    }
}

/**
 * Enhanced Password Validation
 */
function validatePassword(password) {
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    if (password.length < minLength) {
        return { isValid: false, message: `Password must be at least ${minLength} characters long` };
    }

    if (!hasLowerCase) {
        return { isValid: false, message: 'Password must contain at least one lowercase letter' };
    }

    if (!hasUpperCase) {
        return { isValid: false, message: 'Password must contain at least one uppercase letter' };
    }

    if (!hasNumbers) {
        return { isValid: false, message: 'Password must contain at least one number' };
    }

    if (!hasSpecialChar) {
        return { isValid: false, message: 'Password must contain at least one special character' };
    }

    return { isValid: true, message: 'Password is strong' };
}

/**
 * Enhanced Form Submission Handler
 */
function handleFormSubmission(form) {
    const submitBtn = form.querySelector('.auth-submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');

    // Validate all fields before submission
    const inputs = form.querySelectorAll('.auth-form-input[data-validation]');
    let isFormValid = true;

    inputs.forEach(input => {
        const fieldValid = validateFieldEnhanced(input);
        if (!fieldValid) {
            isFormValid = false;
        }
    });

    if (!isFormValid) {
        // Show form-level error
        const event = new CustomEvent('formSubmissionError', {
            detail: { message: 'Please correct the errors above and try again.' }
        });
        document.dispatchEvent(event);
        return;
    }

    // Show loading state
    if (submitBtn && btnText && btnLoading) {
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoading.style.display = 'flex';
        submitBtn.classList.add('loading');
    }

    // Add a small delay for better UX
    setTimeout(() => {
        form.submit();
    }, 500);
}

/**
 * Legacy support functions (kept for compatibility)
 */
function showFieldSuccess(field) {
    // This function is kept for backward compatibility
    // The new validation system handles success states differently
    console.log('Legacy showFieldSuccess called for:', field.name);
}

function showFieldError(field, message) {
    // This function is kept for backward compatibility
    // The new validation system handles errors differently
    console.log('Legacy showFieldError called for:', field.name, 'with message:', message);
}

/**
 * Email validation
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Enhanced Password Strength Indicator
 */
function initPasswordStrengthIndicator() {
    // Handle registration form
    const passwordField = document.getElementById('id_password1');
    const confirmPasswordField = document.getElementById('id_password2');

    // Handle password reset form
    const newPasswordField = document.getElementById('id_new_password1');
    const confirmNewPasswordField = document.getElementById('id_new_password2');

    // Initialize for registration form
    if (passwordField) {
        initPasswordStrengthForField(passwordField);

        if (confirmPasswordField) {
            initPasswordMatching(passwordField, confirmPasswordField);
        }
    }

    // Initialize for password reset form
    if (newPasswordField) {
        initPasswordStrengthForField(newPasswordField);

        if (confirmNewPasswordField) {
            initPasswordMatching(newPasswordField, confirmNewPasswordField);
        }
    }
}

function initPasswordStrengthForField(passwordField) {
    const strengthContainer = document.getElementById(`password-strength-${passwordField.id}`);
    if (!strengthContainer) return;

    const strengthFill = strengthContainer.querySelector('.password-strength-fill');
    const strengthValue = strengthContainer.querySelector('.strength-value');
    const requirements = strengthContainer.querySelectorAll('.requirement');

    passwordField.addEventListener('input', function() {
        const password = this.value;
        const strength = calculatePasswordStrength(password);
        updatePasswordStrengthDisplay(strength, strengthFill, strengthValue, requirements);
    });
}

function initPasswordMatching(passwordField, confirmPasswordField) {
    const matchContainer = document.getElementById(`password-match-${confirmPasswordField.id}`);
    if (!matchContainer) return;

    const matchIcon = matchContainer.querySelector('.match-icon');
    const matchText = matchContainer.querySelector('.match-text');

    function checkPasswordMatch() {
        const password = passwordField.value;
        const confirmPassword = confirmPasswordField.value;

        if (confirmPassword.length === 0) {
            matchContainer.style.display = 'none';
            return;
        }

        matchContainer.style.display = 'block';

        if (password === confirmPassword && password.length > 0) {
            matchContainer.className = 'password-match-container match';
            matchIcon.className = 'fas fa-check-circle match-icon';
            matchText.textContent = 'Passwords match';
        } else {
            matchContainer.className = 'password-match-container no-match';
            matchIcon.className = 'fas fa-times-circle match-icon';
            matchText.textContent = 'Passwords do not match';
        }
    }

    passwordField.addEventListener('input', checkPasswordMatch);
    confirmPasswordField.addEventListener('input', checkPasswordMatch);
}

function updatePasswordStrengthDisplay(strength, strengthFill, strengthValue, requirements) {
    // Update strength bar
    strengthFill.style.width = `${strength.percentage}%`;

    // Update strength text
    strengthValue.textContent = strength.text;
    strengthValue.className = `strength-value ${strength.level}`;

    // Get the current password field (could be registration or reset form)
    const passwordField = document.getElementById('id_password1') || document.getElementById('id_new_password1');
    if (!passwordField) return;

    const password = passwordField.value;

    requirements.forEach(requirement => {
        const type = requirement.getAttribute('data-requirement');
        let isMet = false;

        switch(type) {
            case 'length':
                isMet = password.length >= 8;
                break;
            case 'uppercase':
                isMet = /[A-Z]/.test(password);
                break;
            case 'lowercase':
                isMet = /[a-z]/.test(password);
                break;
            case 'number':
                isMet = /\d/.test(password);
                break;
            case 'special':
                isMet = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
                break;
        }

        if (isMet) {
            requirement.classList.remove('unmet');
            requirement.classList.add('met');
            requirement.querySelector('.requirement-icon').className = 'fas fa-check-circle requirement-icon';
        } else {
            requirement.classList.remove('met');
            requirement.classList.add('unmet');
            requirement.querySelector('.requirement-icon').className = 'fas fa-times-circle requirement-icon';
        }
    });
}

/**
 * Calculate password strength
 */
function calculatePasswordStrength(password) {
    let score = 0;
    
    if (password.length >= 8) score += 25;
    if (password.length >= 12) score += 25;
    if (/[a-z]/.test(password)) score += 10;
    if (/[A-Z]/.test(password)) score += 10;
    if (/[0-9]/.test(password)) score += 10;
    if (/[^A-Za-z0-9]/.test(password)) score += 20;
    
    let level, text;
    if (score < 30) {
        level = 'weak';
        text = 'Weak';
    } else if (score < 60) {
        level = 'fair';
        text = 'Fair';
    } else if (score < 90) {
        level = 'good';
        text = 'Good';
    } else {
        level = 'strong';
        text = 'Strong';
    }
    
    return { level, text, percentage: Math.min(score, 100) };
}

/**
 * Form Animations
 */
function initFormAnimations() {
    // Stagger form field animations
    const formGroups = document.querySelectorAll('.auth-form-group');
    formGroups.forEach((group, index) => {
        group.style.animationDelay = `${index * 100}ms`;
        group.classList.add('animate-fade-in-up');
    });
    
    // Button hover effects
    const buttons = document.querySelectorAll('.auth-submit-btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

/**
 * Accessibility Features
 */
function initAccessibilityFeatures() {
    // Keyboard navigation for custom checkboxes
    const checkboxes = document.querySelectorAll('.auth-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.checked = !this.checked;
            }
        });
    });
    
    // Focus management
    const firstInput = document.querySelector('.auth-form-input');
    if (firstInput) {
        firstInput.focus();
    }
    
    // High contrast mode detection
    if (window.matchMedia('(prefers-contrast: high)').matches) {
        document.body.classList.add('high-contrast');
    }
    
    // Reduced motion detection
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.body.classList.add('reduced-motion');
    }
}

/**
 * Add CSS for password strength indicator
 */
const style = document.createElement('style');
style.textContent = `
    .password-strength {
        margin-top: 0.5rem;
    }
    
    .strength-container {
        background-color: #e5e7eb;
        border-radius: 9999px;
        height: 0.5rem;
        margin-bottom: 0.25rem;
        overflow: hidden;
    }
    
    .strength-bar {
        height: 100%;
        transition: all 0.3s ease;
        border-radius: 9999px;
    }
    
    .strength-weak {
        background-color: #ef4444;
    }
    
    .strength-fair {
        background-color: #f59e0b;
    }
    
    .strength-good {
        background-color: #3b82f6;
    }
    
    .strength-strong {
        background-color: #10b981;
    }
    
    .strength-text {
        font-size: 0.875rem;
        color: #6b7280;
    }
    
    .animate-fade-in-up {
        animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .auth-form-group.focused .auth-form-input {
        border-color: #dc2626;
        box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
    }
    
    .high-contrast .auth-form-input {
        border-width: 2px;
    }
    
    .reduced-motion * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
`;
document.head.appendChild(style);

/**
 * Enhanced Remember Me Functionality
 */
function initializeRememberMeEnhancements() {
    const rememberMeGroup = document.getElementById('remember-me-group');
    const rememberMeCheckbox = document.querySelector('input[name*="remember_me"]');

    if (!rememberMeGroup || !rememberMeCheckbox) return;

    // Add visual feedback for checkbox state
    function updateRememberMeState() {
        if (rememberMeCheckbox.checked) {
            rememberMeGroup.classList.add('active');

            // Add success animation
            rememberMeGroup.style.transform = 'scale(1.02)';
            setTimeout(() => {
                rememberMeGroup.style.transform = '';
            }, 200);

            // Show session duration info
            showSessionInfo();
        } else {
            rememberMeGroup.classList.remove('active');
            hideSessionInfo();
        }
    }

    // Show session duration information
    function showSessionInfo() {
        let sessionInfo = rememberMeGroup.querySelector('.session-duration-info');
        if (!sessionInfo) {
            sessionInfo = document.createElement('div');
            sessionInfo.className = 'session-duration-info';
            sessionInfo.innerHTML = `
                <div style="
                    font-size: 0.75rem;
                    color: #059669;
                    margin-top: 0.5rem;
                    padding: 0.5rem;
                    background: rgba(16, 185, 129, 0.1);
                    border-radius: 0.375rem;
                    border: 1px solid rgba(16, 185, 129, 0.2);
                    animation: slideDown 0.3s ease-out;
                ">
                    <i class="fas fa-shield-alt mr-1"></i>
                    Your session will remain active for 30 days on this device
                </div>
            `;
            rememberMeGroup.appendChild(sessionInfo);
        }
        sessionInfo.style.display = 'block';
    }

    // Hide session duration information
    function hideSessionInfo() {
        const sessionInfo = rememberMeGroup.querySelector('.session-duration-info');
        if (sessionInfo) {
            sessionInfo.style.display = 'none';
        }
    }

    // Event listeners
    rememberMeCheckbox.addEventListener('change', updateRememberMeState);

    // Initialize state
    updateRememberMeState();

    // Enhanced keyboard interaction
    rememberMeGroup.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            rememberMeCheckbox.checked = !rememberMeCheckbox.checked;
            updateRememberMeState();
        }
    });

    // Add hover effects
    rememberMeGroup.addEventListener('mouseenter', function() {
        if (!rememberMeCheckbox.checked) {
            this.style.transform = 'translateY(-1px)';
        }
    });

    rememberMeGroup.addEventListener('mouseleave', function() {
        if (!rememberMeCheckbox.checked) {
            this.style.transform = '';
        }
    });
}

// Add slide down animation for session info
const slideDownStyle = document.createElement('style');
slideDownStyle.textContent = `
    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-10px);
            max-height: 0;
        }
        to {
            opacity: 1;
            transform: translateY(0);
            max-height: 100px;
        }
    }
`;
document.head.appendChild(slideDownStyle);

})(); // End of IIFE
