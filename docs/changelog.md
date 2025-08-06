# Changelog

All notable changes to GitSync will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0b1] - 2025-08-06

### Changed

- **CI/CD Improvements**
  - Optimized GitHub Actions workflow for better performance
  - Simplified test matrix configuration
  - Improved caching strategy for faster builds

- **Code Quality**
  - Fixed linting issues across multiple modules
  - Improved test reliability and coverage
  - Cleaned up unused imports and variables
  - Enhanced error handling in edge cases

### Fixed

- Test failures in CI environment
- Markdown documentation formatting issues
- Minor bugs in configuration handling
- Type hints and mypy warnings

## [0.2.0] - 2025-08-06

### Added
- **Documentation**
  - Comprehensive MkDocs documentation with Material theme
  - Architecture documentation with component relationships
  - Complete user guide (configuration, authentication, proxy setup)
  - CLI reference documentation
  - API documentation for Python integration
  - Troubleshooting guide with 20+ common issues
  - GitHub Actions workflow for documentation deployment

- **CI/CD**
  - GitHub Actions workflow for automated testing
  - Multi-version testing matrix (Python 3.9-3.12)
  - Code coverage reporting with Codecov integration
  - Security scanning with safety check
  - Pre-commit hooks configuration for code quality

- **Architecture Improvements**
  - Refactored GitHubAPISync into component-based architecture
  - Abstract base classes (interfaces) for better code organization
  - SessionFactory for centralized HTTP session management
  - Specialized components: GitHubAPIClient, RepositoryManager, FileSynchronizer, ProgressTracker
  - Custom exception hierarchy with 20+ specific exception types

- **Testing**
  - 390+ comprehensive unit tests
  - 94% code coverage for core modules
  - Mock-based testing for external dependencies
  - Test fixtures and configuration setup

### Changed
- **Browser Automation**
  - Migrated from Selenium to Playwright for better performance
  - Improved browser automation reliability
  - Enhanced download handling with expect_download()
  
- **Code Quality**
  - Improved error messages with actionable solutions
  - Enhanced proxy detection algorithm
  - Better separation of concerns through component architecture
  - Comprehensive Google-style docstrings throughout

- **Dependencies**
  - Replaced Selenium with Playwright
  - Updated to use uv package manager
  - Added development dependencies for docs and testing

### Fixed
- Memory leak in browser sync method for large repositories
- Path expansion issues with home directory (~)
- Repository ref not being used from configuration
- SSL certificate validation in corporate environments
- Makefile run command argument passing

## [0.1.0] - 2025-01-15

### Added
- Initial release with full feature set
- GitHub API synchronization method
- Browser automation fallback method using Selenium
- Incremental update support with SHA-based change detection
- YAML-based configuration system
- Command-line interface with Click
- Automatic proxy detection from PAC scripts (Windows/Chrome)
- Automatic certificate extraction from Windows certificate store
- SSL verification configuration options
- Progress tracking with tqdm
- Comprehensive error handling and retry logic
- Support for branches, tags, and specific commits
- Parallel download capability for API method
- Cookie persistence for browser method
- Headless browser mode support
- Environment variable expansion in configuration
- Verbose logging and debug mode
- Dry-run capability
- JSON output format for scripting

### Features
- **Core Functionality**
  - Efficient file synchronization using GitHub REST API
  - Smart incremental updates (only downloads changed files)
  - Support for any git reference (branch/tag/commit)
  - Visual progress tracking with progress bars

- **Configuration System**
  - Flexible YAML configuration files
  - Environment variable support with expansion
  - Command-line argument overrides
  - Path expansion for home directory and variables

- **Corporate Environment Support**
  - PAC proxy auto-detection from Windows/Chrome
  - Certificate auto-detection from Windows store
  - Manual proxy configuration with authentication
  - SSL verification options
  - Custom certificate bundle support

- **User Experience**
  - Clean CLI interface using Click framework
  - Helpful error messages with solutions
  - Verbose logging for troubleshooting
  - Windows-specific helper scripts
  - Cross-platform compatibility

- **Browser Automation**
  - Selenium WebDriver-based fallback
  - Chrome/Chromium browser support
  - Custom browser binary paths
  - ZIP-based file extraction
  - Comprehensive error recovery

### Technical Details
- Python 3.9+ support
- 94% test coverage for api_sync module
- 97% test coverage for browser_sync module
- 100% test coverage for utils module
- 180+ comprehensive unit tests
- Mock-based testing strategy
- Full type hints and annotations

### Dependencies
- Core: requests, selenium, pyyaml, click, tqdm, certifi
- Optional: pypac (PAC support), wincertstore (Windows certificates)
- Development: pytest, pytest-cov, ruff, mypy

### Known Limitations
- Binary files larger than 100MB may fail with API method
- Browser method is significantly slower than API method
- Some GitHub Enterprise features not yet supported

## [0.0.1] - 2025-01-01

### Added
- Initial project structure
- Basic GitHub API integration
- Simple command-line interface
- Configuration file support

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 0.3.0b1 | 2025-08-06 | Beta release with CI/CD improvements and bug fixes |
| 0.2.0 | 2025-08-06 | Major refactoring with component architecture, Playwright migration, comprehensive testing |
| 0.1.0 | 2025-01-15 | First stable release with full feature set |
| 0.0.1 | 2025-01-01 | Initial development version |

## Upgrade Guide

### From 0.0.x to 0.1.0

1. **Configuration Changes:**
   - The configuration schema has been updated
   - Run `gitsync migrate-config` to update your configuration files
   - New fields added for proxy and certificate configuration

2. **Command Changes:**
   - `--use-browser` flag replaced with `--method browser`
   - New flags: `--auto-proxy`, `--auto-cert`

3. **Breaking Changes:**
   - None - this version maintains backward compatibility

## Support

For questions about upgrading or changelog entries:

- Open an issue: [GitHub Issues](https://github.com/nevedomski/gitsync/issues)
- Check documentation: [GitSync Documentation](https://nevedomski.github.io/gitSync/)
