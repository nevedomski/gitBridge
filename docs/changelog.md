# Changelog

All notable changes to GitBridge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-08-28

### 🎉 First Stable Release

This is the first stable production release of GitBridge, a tool to synchronize GitHub repositories when direct git access is blocked.

### Added
- **PyPI Distribution**
  - Published to PyPI as `gitbridge` package
  - Universal wheel with automatic platform-specific dependency installation
  - Windows dependencies (pypac, wincertstore, pywin32) auto-install on Windows only
  - Optional extras: `[browser]` for Playwright, `[dev]` for development tools

### Changed
- **Packaging Improvements**
  - Moved Windows dependencies to main dependencies with platform markers
  - Simplified installation process - Windows users get everything automatically
  - Enhanced CI/CD with wheel testing across all platforms
  - Automatic TestPyPI deployment from main branch

### Infrastructure
- **GitHub Actions Workflows**
  - CI workflow now tests wheel installation on every push/PR
  - Automatic deployment to TestPyPI for main branch commits
  - Simplified publish workflow for PyPI releases
  - Cross-platform testing matrix (Windows, Linux, macOS × Python 3.10-3.12)

## [0.8.0b1] - 2025-08-28

### Changed
- **Complete Playwright Migration**
  - Removed all remaining Selenium references from codebase
  - Updated all documentation to reflect Playwright usage
  - Updated exception messages and docstrings
  - Updated installation and troubleshooting guides
  - Marked migration as complete in ROADMAP and PROJECT_STATUS

### Documentation
- Updated AGENTS.md to reflect completed Playwright implementation
- Updated architecture diagrams to show Playwright instead of Selenium
- Updated all historical changelog entries for consistency
- Removed ChromeDriver installation instructions

## [0.7.0b1] - 2025-08-16

### Fixed
- Fixed Codecov badge showing "unknown" by correcting repository URL from `gh/user/gitBridge` to `gh/nevedomski/gitBridge`
- Replaced all hardcoded badge values with dynamic badges in README and documentation
- Fixed 11 failing tests due to GitHubAPIClient constructor signature changes (added `config` parameter)
- Fixed test mocks to use `get_with_limits` instead of `get` method
- Fixed Codecov configuration paths from `gitbridge/` to `src/gitbridge/` after project restructure
- Fixed pytest coverage command to use `--cov=src/gitbridge` instead of `--cov=gitbridge`
- Fixed browser sync failing with ERR_ABORTED error when downloading ZIP files
- Fixed browser sync tests to match new implementation using `context.request.get()`

### Added
- Created separate CI workflows for individual tool badges (ruff-format.yml, ruff-lint.yml, mypy.yml)
- Added CI job to auto-generate requirements.txt from pyproject.toml for Snyk compatibility
- Created .snyk configuration file to ignore false positive MPL-2.0 license warnings
- Added CODECOV_TOKEN to CI workflow for more reliable uploads

### Changed
- Browser sync now uses `context.request.get()` instead of `page.goto()` for downloading ZIP files
- Updated all tests to match new browser sync implementation
- All 528 tests now passing with 84% code coverage

## [0.6.3b1] - 2025-08-16

### Security
- **CRITICAL**: Fixed path traversal vulnerability in FileSynchronizer that could allow files to be written outside the sync directory
- **CRITICAL**: Added comprehensive proxy URL validation to prevent injection attacks
- **CRITICAL**: Fixed race condition in certificate cleanup that could cause crashes in multi-threaded operations
- **CRITICAL**: Implemented request size limits to prevent DoS attacks (default: 100MB per file)

### Added
- `validate_safe_path()` utility function for secure path validation
- `validate_proxy_url()` utility function for comprehensive proxy URL validation
- Thread-safe `CertificateManager` class with proper locking mechanisms
- Configurable download limits in configuration:
  - `max_file_size`: Maximum size for individual files (default: 100MB)
  - `max_total_size`: Maximum total download size (default: 500MB)
  - `stream_threshold`: File size threshold for streaming (default: 10MB)
  - `chunk_size`: Download chunk size (default: 8192 bytes)
  - `timeout`: Request timeout in seconds (default: 30)
- `SecurityError` exception type for security-related violations
- Streaming support for large files to prevent memory exhaustion
- Comprehensive security test suite with 18 test cases

### Changed
- FileSynchronizer now validates all file paths before writing
- BrowserSync now validates proxy URLs before configuration
- GitHubAPIClient now enforces size limits on all downloads
- Large files (>10MB) are now streamed to prevent memory issues

### Fixed
- Path traversal vulnerability allowing directory escape
- Missing validation for malicious proxy URLs
- Race condition in temporary certificate file cleanup
- Potential DoS via unlimited file downloads

## [0.6.2b1] - 2025-08-16

### Fixed
- Minor version update for release preparation

## [0.6.1b1] - 2025-08-16

### Fixed
- MyPy type-check paths in CI configuration

## [0.5.1b1] - 2025-01-11

### Added
- **Documentation Comments (DOCDEV)**
  - Added DOCDEV-NOTE comments to critical CI/CD workflow steps for better maintainability
  - Added DOCDEV-TODO for Codecov test analytics monitoring
  - Documented GitHub Actions GITHUB_REF normalization behavior in config.py
  - Enhanced codecov.yml with documentation about test analytics features

### Changed
- **CI/CD Improvements**
  - Fixed dependency installation command from `uv sync --dev` to `uv sync --extra dev` for proper development dependencies
  - Improved CI workflow documentation with inline explanations
  
- **Documentation**
  - Updated AGENTS.md with current version (0.5.0b1) and test coverage metrics
  - Fixed MkDocs social links to use relative paths instead of external URLs
  - Changelog link now points to local changelog.md instead of GitHub
  - License link now points to local license.md instead of PyPI

### Fixed
- Development dependency installation in GitHub Actions workflow

## [0.5.0b1] - 2025-08-09

### Changed
- **Breaking**: Minimum Python version requirement changed from 3.9 to 3.10
- Fixed GITHUB_REF environment variable normalization for GitHub Actions compatibility
- Added project version display in MkDocs documentation footer (displays as "Copyright © 2025 Nevedomski Sergei • Version X.X.X")

### Fixed
- CI workflow: Removed incorrect `--site-url` option from mkdocs build command
- Test suite: Fixed branch name assertion to handle GitHub Actions ref format (refs/heads/main → main)

## [0.4.2b1] - 2025-08-06

### Added
- **Project Documentation**
  - SECURITY.md with vulnerability disclosure policy
  - ROADMAP.md with detailed development timeline
  - CONTRIBUTING.md with contribution guidelines
  - Comprehensive review documentation in PROJECT_STATUS.md

### Changed
- **Documentation**
  - Updated README with production status and security monitoring
  - Added comprehensive review results and action items
  - Completed full migration from Selenium to Playwright
  - Enhanced project status with prioritized action items

### Security
- Documented critical security issues pending fixes:
  - Path traversal vulnerability in FileSynchronizer
  - Proxy URL validation in BrowserSync
  - Race condition in certificate cleanup

## [0.4.1b1] - 2025-08-06

### Added
- **Comprehensive Review Process**
  - Product management review completed
  - Architecture review completed
  - Documentation review completed
  - Code quality review completed
  - Security audit performed

### Fixed
- All ruff linting issues resolved
- All mypy type checking errors fixed
- Test isolation issues addressed
- Documentation formatting issues corrected

## [0.4.0b1] - 2025-08-06

### Changed
- **Version Numbering**
  - Updated to semantic versioning 0.4.x series
  - Marked as beta (b1) pending security fixes

### Fixed
- **Type Hints and Code Quality**
  - Fixed all remaining type hints across 15 source files
  - Resolved 110+ mypy type annotation issues
  - Fixed RateLimitError and ProxyError exception classes
  - Updated test expectations for correct exception structure
  - All 502 tests now passing (7 skipped)
  - Achieved 83% overall test coverage

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
  - Fully migrated from Selenium to Playwright for better performance
  - Improved browser automation reliability
  - Enhanced download handling with expect_download()
  
- **Code Quality**
  - Improved error messages with actionable solutions
  - Enhanced proxy detection algorithm
  - Better separation of concerns through component architecture
  - Comprehensive Google-style docstrings throughout

- **Dependencies**
  - Completed replacement of Selenium with Playwright
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
- Browser automation fallback method using Playwright
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
  - Playwright-based fallback
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
- Core: requests, playwright, pyyaml, click, tqdm, certifi
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
| 1.0.0 | 2025-08-28 | **STABLE RELEASE** - PyPI distribution, automatic Windows dependency installation, universal wheel |
| 0.8.0b1 | 2025-08-28 | Complete Playwright migration, removed all Selenium references |
| 0.7.0b1 | 2025-08-16 | Fixed badges, test failures, Codecov/Snyk integration, browser sync ERR_ABORTED error |
| 0.6.3b1 | 2025-08-16 | **SECURITY RELEASE** - Fixed all critical vulnerabilities (path traversal, proxy validation, race conditions, DoS) |
| 0.6.2b1 | 2025-08-16 | Minor version update for release preparation |
| 0.6.1b1 | 2025-08-16 | MyPy type-check paths fix in CI configuration |
| 0.5.1b1 | 2025-01-11 | CI/CD fixes, documentation improvements, DOCDEV comments added |
| 0.5.0b1 | 2025-08-09 | Python 3.10+ requirement, GitHub Actions fixes, MkDocs version display |
| 0.4.2b1 | 2025-08-06 | Added security documentation, roadmap, and contribution guidelines |
| 0.4.1b1 | 2025-08-06 | Comprehensive review completed, all quality checks passing |
| 0.4.0b1 | 2025-08-06 | Fixed all type hints, 502 tests passing, 83% coverage |
| 0.3.0b1 | 2025-08-06 | Beta release with CI/CD improvements and bug fixes |
| 0.2.0 | 2025-08-06 | Major refactoring with component architecture, Playwright migration, comprehensive testing |
| 0.1.0 | 2025-01-15 | First stable release with full feature set |
| 0.0.1 | 2025-01-01 | Initial development version |

## Upgrade Guide

### From 0.3.x to 0.4.x

1. **Security Considerations:**
   - Review SECURITY.md for known vulnerabilities
   - Avoid syncing untrusted repositories until 1.0.0 release
   - Validate proxy URLs before use

2. **Browser Automation:**
   - Migration to Playwright is complete
   - Update any custom scripts that referenced Selenium

3. **Type Hints:**
   - All code now has complete type annotations
   - Update any custom integrations to match new type signatures

### From 0.2.x to 0.3.x

1. **No Breaking Changes:**
   - This version maintains full backward compatibility
   - All existing configurations continue to work

### From 0.1.x to 0.2.x

1. **Component Architecture:**
   - Internal refactoring doesn't affect external API
   - All CLI commands remain the same

### From 0.0.x to 0.1.0

1. **Configuration Changes:**
   - The configuration schema has been updated
   - Run `gitbridge migrate-config` to update your configuration files
   - New fields added for proxy and certificate configuration

2. **Command Changes:**
   - `--use-browser` flag replaced with `--method browser`
   - New flags: `--auto-proxy`, `--auto-cert`

3. **Breaking Changes:**
   - None - this version maintains backward compatibility

## Support

For questions about upgrading or changelog entries:

- Open an issue: [GitHub Issues](https://github.com/nevedomski/gitbridge/issues)
- Check documentation: [GitBridge Documentation](https://nevedomski.github.io/gitBridge/)
