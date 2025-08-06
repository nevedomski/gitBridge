# Changelog

All notable changes to GitSync will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive MkDocs documentation with Material theme
- GitHub Actions workflow for automated testing
- Support for GitHub Enterprise

### Changed
- Improved error messages for better debugging
- Enhanced proxy detection algorithm

### Fixed
- Memory leak in browser sync method for large repositories

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
- Open an issue: https://github.com/nevedomski/gitsync/issues
- Check documentation: https://gitsync.readthedocs.io