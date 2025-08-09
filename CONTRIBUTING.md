# Contributing to GitBridge

Thank you for your interest in contributing to GitBridge! We welcome contributions from the community and are grateful for any help you can provide.

## Code of Conduct

By participating in this project, you agree to abide by our code of conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Accept feedback gracefully

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- System information (OS, Python version, GitBridge version)
- Relevant logs or error messages
- Sample configuration (with sensitive data removed)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When suggesting an enhancement:

- Use a clear and descriptive title
- Provide a detailed description of the proposed feature
- Explain why this enhancement would be useful
- List any alternative solutions you've considered

### Security Vulnerabilities

**DO NOT** open public issues for security vulnerabilities. See [SECURITY.md](./SECURITY.md) for instructions on reporting security issues.

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Commit your changes with a descriptive message
6. Push to your fork
7. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.10 or higher
- uv package manager
- Git

### Setting Up Your Development Environment

```bash
# Clone your fork
git clone https://github.com/your-username/gitbridge.git
cd gitbridge

# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=gitbridge --cov-report=html

# Run specific test file
uv run pytest tests/test_api_sync.py

# Run with verbose output
uv run pytest -v
```

### Code Quality Checks

Before submitting a PR, ensure your code passes all quality checks:

```bash
# Format code with ruff
uv run ruff format .

# Check code style
uv run ruff check . --fix

# Type checking
uv run mypy gitbridge/

# Run all pre-commit hooks
pre-commit run --all-files
```

## Coding Standards

### Python Style Guide

- Follow PEP 8 with 140-character line limit
- Use Black formatting (enforced by ruff)
- Use type hints for all function signatures
- Write Google-style docstrings for public functions and classes

### Code Organization

- Keep modules focused and cohesive
- Follow the existing component-based architecture
- Use dependency injection for testability
- Implement interfaces for abstraction

### Documentation

- Add DOCDEV comments for complex logic:
  - `DOCDEV-NOTE`: Important implementation details
  - `DOCDEV-TODO`: Planned improvements
  - `DOCDEV-QUESTION`: Design decisions needing review
- Update relevant documentation when changing functionality
- Include usage examples in docstrings

### Testing

- Write tests for all new functionality
- Maintain or improve code coverage (target: >90%)
- Use descriptive test names that explain what is being tested
- Mock external dependencies appropriately
- Test both success and failure cases

## Pull Request Process

1. **Before Starting**
   - Check if an issue exists for your change
   - Discuss major changes in an issue first
   - Ensure you're working from the latest main branch

2. **While Working**
   - Write clear, concise commit messages
   - Keep commits focused and atomic
   - Add tests for new functionality
   - Update documentation as needed

3. **Before Submitting**
   - Run all tests locally
   - Ensure code passes all quality checks
   - Update PROJECT_STATUS.md if applicable
   - Rebase on latest main if needed

4. **PR Description**
   - Reference any related issues
   - Describe what changed and why
   - Include any breaking changes
   - Add screenshots for UI changes

5. **After Submitting**
   - Respond to review feedback promptly
   - Be open to suggestions and changes
   - Keep your branch up to date with main

## Priority Areas

We especially welcome contributions in these areas:

### High Priority

- **Security fixes**: Path traversal, input validation
- **Performance**: Parallel downloads, connection pooling
- **Documentation**: Real-world examples, troubleshooting guides

### Medium Priority

- **Platform support**: GitLab, Bitbucket integration
- **User experience**: GUI application, better error messages
- **Testing**: Integration tests, performance benchmarks

### Nice to Have

- **IDE integrations**: VS Code, JetBrains plugins
- **CI/CD integrations**: Jenkins, GitHub Actions templates
- **Enterprise features**: SSO, audit logging

## Getting Help

- Check the [documentation](https://nevedomski.github.io/gitBridge/)
- Look through existing [issues](https://github.com/nevedomski/gitBridge/issues)
- Ask questions in [discussions](https://github.com/nevedomski/gitBridge/discussions)
- Reach out to maintainers for guidance

## Recognition

Contributors will be recognized in:

- The project README
- Release notes
- Documentation credits

Thank you for helping make GitBridge better for everyone!
