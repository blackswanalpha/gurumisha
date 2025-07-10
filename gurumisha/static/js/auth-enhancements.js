/**
 * Authentication Pages Enhancement JavaScript
 * Provides interactive features for login and register pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize authentication page enhancements
    initPasswordVisibilityToggle();
    initFormValidation();
    initPasswordStrengthIndicator();
    initFormAnimations();
    initAccessibilityFeatures();
    initializeRememberMeEnhancements();
});

/**
 * Password Visibility Toggle
 */
function initPasswordVisibilityToggle() {
    const passwordFields = document.querySelectorAll('input[type="password"]');

    passwordFields.forEach(field => {
        // Create toggle button container
        const toggleContainer = document.createElement('div');
        toggleContainer.className = 'password-toggle-container';

        // Create toggle button
        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'password-toggle-btn';
        toggleButton.innerHTML = '<i class="fas fa-eye"></i>';
        toggleButton.setAttribute('aria-label', 'Show password');

        // Wrap the input field
        const wrapper = document.createElement('div');
        wrapper.className = 'password-input-wrapper';

        // Insert wrapper before the input
        field.parentNode.insertBefore(wrapper, field);

        // Move input into wrapper and add toggle button
        wrapper.appendChild(field);
        wrapper.appendChild(toggleButton);

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
    });
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
 * Form Validation Enhancement
 */
function initFormValidation() {
    const forms = document.querySelectorAll('#login-form, #register-form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('.auth-form-input');
        
        inputs.forEach(input => {
            // Real-time validation
            input.addEventListener('input', function() {
                validateField(this);
            });
            
            // Focus effects
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
                validateField(this);
            });
        });
        
        // Form submission
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('.auth-submit-btn');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
            }
        });
    });
}

/**
 * Enhanced Field Validation
 */
function validateField(field) {
    const value = field.value.trim();
    const fieldType = field.type === 'text' && field.getAttribute('data-original-type') === 'password' ? 'password' : field.type;
    const fieldName = field.name;

    // Remove existing validation classes
    field.classList.remove('error', 'success');

    // Remove existing error messages
    const existingError = field.parentElement.querySelector('.auth-error-message');
    if (existingError && !existingError.textContent.includes('exclamation-circle')) {
        existingError.remove();
    }

    let isValid = true;
    let errorMessage = '';

    // Enhanced validation rules
    if (field.required && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    } else if (fieldType === 'email' && value && !isValidEmail(value)) {
        isValid = false;
        errorMessage = 'Please enter a valid email address';
    } else if (fieldName === 'username' && value) {
        if (value.length < 3) {
            isValid = false;
            errorMessage = 'Username must be at least 3 characters long';
        } else if (value.length > 30) {
            isValid = false;
            errorMessage = 'Username must be less than 30 characters';
        } else if (!/^[a-zA-Z0-9_]+$/.test(value)) {
            isValid = false;
            errorMessage = 'Username can only contain letters, numbers, and underscores';
        }
    } else if (fieldType === 'password' && value) {
        const passwordValidation = validatePassword(value);
        if (!passwordValidation.isValid) {
            isValid = false;
            errorMessage = passwordValidation.message;
        }
    } else if (fieldName === 'password2' && value) {
        const password1 = document.querySelector('input[name="password1"]');
        if (password1 && value !== password1.value) {
            isValid = false;
            errorMessage = 'Passwords do not match';
        }
    } else if (fieldName === 'first_name' || fieldName === 'last_name') {
        if (value && (value.length < 2 || value.length > 50)) {
            isValid = false;
            errorMessage = 'Name must be between 2 and 50 characters';
        } else if (value && !/^[a-zA-Z\s'-]+$/.test(value)) {
            isValid = false;
            errorMessage = 'Name can only contain letters, spaces, hyphens, and apostrophes';
        }
    } else if (fieldName === 'phone' && value) {
        if (!/^[\+]?[0-9\s\-\(\)]{10,15}$/.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid phone number';
        }
    }

    // Apply validation state
    if (value) {
        if (isValid) {
            field.classList.add('success');
            showFieldSuccess(field);
        } else {
            field.classList.add('error');
            showFieldError(field, errorMessage);
        }
    }

    return isValid;
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
 * Show field success state
 */
function showFieldSuccess(field) {
    // Remove existing success message
    const existingSuccess = field.parentElement.querySelector('.auth-success-message');
    if (existingSuccess) {
        existingSuccess.remove();
    }

    // Add success icon to field
    field.style.backgroundImage = 'url("data:image/svg+xml,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 16 16\' fill=\'%2310b981\'%3e%3cpath d=\'M12.736 3.97a.733.733 0 0 1 1.047 0c.286.289.29.756.01 1.05L7.88 12.01a.733.733 0 0 1-1.065.02L3.217 8.384a.757.757 0 0 1 0-1.06.733.733 0 0 1 1.047 0l3.052 3.093 5.4-6.425a.247.247 0 0 1 .02-.022Z\'/%3e%3c/svg%3e")';
    field.style.backgroundRepeat = 'no-repeat';
    field.style.backgroundPosition = 'right 1rem center';
    field.style.backgroundSize = '1rem';
}

/**
 * Show field error message
 */
function showFieldError(field, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'auth-error-message';
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle mr-1"></i>${message}`;
    field.parentElement.appendChild(errorDiv);
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
