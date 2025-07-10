# Contributing to Gurumisha

Thank you for your interest in contributing to Gurumisha! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

1. **Search existing issues** first to avoid duplicates
2. **Use the issue template** when creating new issues
3. **Provide detailed information** including:
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - Environment details (OS, Python version, etc.)

### Submitting Pull Requests

1. **Fork the repository**
2. **Create a feature branch** from `master`
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following our coding standards
4. **Write or update tests** for your changes
5. **Update documentation** if necessary
6. **Commit your changes** with clear, descriptive messages
7. **Push to your fork** and submit a pull request

### Pull Request Guidelines

- **One feature per PR** - Keep changes focused and atomic
- **Clear description** - Explain what your PR does and why
- **Link related issues** - Reference any related issue numbers
- **Update CHANGELOG** - Add your changes to the unreleased section
- **Ensure tests pass** - All existing and new tests must pass
- **Follow code style** - Use our linting and formatting tools

## 🛠 Development Setup

### Prerequisites

- Python 3.10+
- Node.js 16+
- Git

### Local Development

1. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/gurumisha.git
   cd gurumisha
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   npm install
   ```

4. **Set up database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Run development server**
   ```bash
   python manage.py runserver
   ```

6. **Run Tailwind CSS watcher** (in another terminal)
   ```bash
   npm run dev
   ```

## 📝 Coding Standards

### Python/Django

- **Follow PEP 8** style guidelines
- **Use Black** for code formatting
- **Use isort** for import sorting
- **Write docstrings** for all functions and classes
- **Follow Django best practices**
- **Use type hints** where appropriate

### Frontend

- **Use semantic HTML5** markup
- **Follow Tailwind CSS** utility-first approach
- **Implement mobile-first** responsive design
- **Use HTMX** for dynamic interactions
- **Follow accessibility** guidelines (WCAG 2.1)

### Code Formatting

Run these commands before committing:

```bash
# Format Python code
black .
isort .

# Format JavaScript/CSS
npm run format

# Lint code
flake8 .
npm run lint
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Writing Tests

- **Write tests** for all new functionality
- **Use Django's TestCase** for database-related tests
- **Use factory_boy** for test data generation
- **Mock external services** in tests
- **Aim for high test coverage** (>90%)

### Test Structure

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import YourModel

User = get_user_model()

class YourModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_model_creation(self):
        """Test that model can be created successfully."""
        # Your test code here
        pass
```

## 📚 Documentation

### Code Documentation

- **Write clear docstrings** for all functions and classes
- **Use Google-style docstrings**
- **Document complex logic** with inline comments
- **Keep README.md updated** with new features

### API Documentation

- **Document all API endpoints**
- **Include request/response examples**
- **Use DRF's built-in documentation**

## 🎨 Design Guidelines

### UI/UX Principles

- **Follow Harrier design system**
- **Use consistent color palette** (Red, Black, Dark Blue, White)
- **Implement smooth transitions** and micro-interactions
- **Ensure mobile responsiveness**
- **Maintain accessibility standards**

### Component Development

- **Create reusable components**
- **Follow atomic design principles**
- **Document component usage**
- **Test across different screen sizes**

## 🚀 Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version number bumped
- [ ] Migration files created if needed
- [ ] Security review completed

## 🔒 Security

### Reporting Security Issues

- **Do not** create public issues for security vulnerabilities
- **Email** security concerns to: kamandembugua18@gmail.com
- **Include** detailed information about the vulnerability
- **Allow time** for us to address the issue before disclosure

### Security Best Practices

- **Validate all inputs**
- **Use Django's built-in security features**
- **Keep dependencies updated**
- **Follow OWASP guidelines**
- **Implement proper authentication and authorization**

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: For bug reports and feature requests
- **Email**: kamandembugua18@gmail.com for direct communication
- **Documentation**: Check README.md and inline documentation

### Before Asking for Help

1. **Search existing issues** and documentation
2. **Check the FAQ** section in README.md
3. **Provide context** when asking questions
4. **Include relevant code** and error messages

## 🏆 Recognition

Contributors will be recognized in:
- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **GitHub contributors** section

## 📋 Code of Conduct

### Our Standards

- **Be respectful** and inclusive
- **Welcome newcomers** and help them learn
- **Focus on constructive feedback**
- **Respect different viewpoints** and experiences
- **Show empathy** towards other community members

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal attacks
- Publishing private information
- Other unprofessional conduct

### Enforcement

Instances of unacceptable behavior may be reported to kamandembugua18@gmail.com. All complaints will be reviewed and investigated promptly and fairly.

---

Thank you for contributing to Gurumisha! Your efforts help make this project better for everyone. 🚀
