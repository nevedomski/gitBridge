# GitBridge - GitHub Repository Synchronization Tool

[![CI](https://github.com/nevedomski/gitBridge/workflows/CI/badge.svg)](https://github.com/nevedomski/gitBridge/actions)
[![GitHub Release](https://img.shields.io/github/v/release/nevedomski/gitbridge?include_prereleases&label=version)](https://github.com/nevedomski/gitbridge/releases)
[![PyPI Version](https://img.shields.io/pypi/v/gitbridge?label=pypi)](https://pypi.org/project/gitbridge/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/gitbridge?label=downloads)](https://pypi.org/project/gitbridge/)
[![Python Versions](https://img.shields.io/pypi/pyversions/gitbridge)](https://pypi.org/project/gitbridge/)
[![codecov](https://codecov.io/gh/nevedomski/gitBridge/branch/main/graph/badge.svg)](https://codecov.io/gh/nevedomski/gitBridge)
[![Tests](https://img.shields.io/github/actions/workflow/status/nevedomski/gitbridge/ci.yml?branch=main&label=tests)](https://github.com/nevedomski/gitbridge/actions)
[![Known Vulnerabilities](https://snyk.io/test/github/nevedomski/gitbridge/badge.svg)](https://snyk.io/test/github/nevedomski/gitbridge)
[![Ruff Format](https://img.shields.io/github/actions/workflow/status/nevedomski/gitbridge/ruff-format.yml?branch=main&label=ruff%20format)](https://github.com/nevedomski/gitbridge/actions)
[![Ruff Lint](https://img.shields.io/github/actions/workflow/status/nevedomski/gitbridge/ruff-lint.yml?branch=main&label=ruff%20lint)](https://github.com/nevedomski/gitbridge/actions)
[![MyPy](https://img.shields.io/github/actions/workflow/status/nevedomski/gitbridge/mypy.yml?branch=main&label=mypy)](https://github.com/nevedomski/gitbridge/actions)
[![License](https://img.shields.io/github/license/nevedomski/gitbridge)](./LICENSE)
[![Docs](https://img.shields.io/badge/docs-github%20pages-blue)](https://nevedomski.github.io/gitBridge/)

**Production-ready tool to synchronize GitHub repositories when direct git access is blocked.**

🎉 **v1.0.0 Released!** - First stable release now available on PyPI

## Features

- **GitHub API Sync**: Uses GitHub's REST API for efficient repository synchronization
- **Browser Automation Fallback**: Falls back to Playwright-based browser automation if API access is blocked
- **Incremental Updates**: Only downloads changed files after initial sync
- **Configuration Support**: Flexible configuration via YAML files
- **Command-Line Interface**: Easy-to-use CLI for various sync operations
- **Progress Tracking**: Visual progress bars and detailed logging
- **Automatic Proxy Detection**: Auto-detects proxy settings from Windows/Chrome PAC scripts
- **Corporate Environment Support**: Works with SSL certificates and proxy configurations
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Comprehensive Testing**: 502+ tests with 83% code coverage

## Installation

### From PyPI (Recommended)

```bash
# Basic installation
pip install gitbridge

# With browser automation support
pip install gitbridge[browser]

# For development
pip install gitbridge[dev]
```

### Windows Users

Windows dependencies (pypac, wincertstore, pywin32) are **automatically installed** when you install GitBridge on Windows.

### From Source

Using [uv](https://github.com/astral-sh/uv):

```bash
# Clone the repository
git clone https://github.com/nevedomski/gitbridge.git
cd gitbridge

# Install with uv
uv pip install -e .

# Or with all extras
uv pip install -e ".[all]"
```

## Quick Start

1. Create a configuration file (`config.yaml`):

```yaml
repository:
  url: https://github.com/username/repo
  branch: main

local:
  path: /path/to/local/folder

auth:
  token: your_github_personal_access_token

sync:
  method: api  # or 'browser'
  incremental: true
```

2. Run the sync:

```bash
gitbridge sync --config config.yaml
```

## Usage

### Basic Sync
```bash
gitbridge sync --repo https://github.com/username/repo --local /path/to/local
```

### With Personal Access Token
```bash
gitbridge sync --repo https://github.com/username/repo --local /path/to/local --token YOUR_TOKEN
```

### Force Browser Mode
```bash
gitbridge sync --repo https://github.com/username/repo --local /path/to/local --method browser
```

### Check Repository Status
```bash
gitbridge status --config config.yaml
```

### Corporate Environment Support

For Windows users in corporate environments:

```bash
# Auto-detect proxy from Chrome/Windows settings
gitbridge sync --repo https://github.com/username/repo --local /path/to/local --auto-proxy

# Auto-detect certificates from Windows certificate store
gitbridge sync --repo https://github.com/username/repo --local /path/to/local --auto-cert

# Use both auto-detection features together
gitbridge sync --config config.yaml --auto-proxy --auto-cert

# Last resort: disable SSL verification
gitbridge sync --config config.yaml --auto-proxy --no-ssl-verify
```

Or add to your configuration file:

```yaml
sync:
  auto_proxy: true   # Auto-detect proxy from PAC
  auto_cert: true    # Auto-detect certificates from Windows
  # verify_ssl: false  # Only if absolutely necessary
```

The tool will automatically:
- Extract proxy settings from Windows/Chrome PAC scripts
- Export trusted certificates from Windows certificate store
- Combine them with certifi's default bundle
- Configure requests to use both proxy and certificates

## Configuration

### Environment Variables
- `GITHUB_TOKEN`: GitHub Personal Access Token
- `GITSYNC_CONFIG`: Default configuration file path

### Configuration File Format
See `config.example.yaml` for a complete example.

## Requirements

- Python 3.10+ (recommended: 3.11+)
- [uv](https://github.com/astral-sh/uv) for dependency management
- For browser mode: Chrome/Chromium and ChromeDriver

## Development

```bash
# Install development dependencies
make install-dev

# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Run tests
make test
```

## Limitations

- Binary files larger than 100MB may fail with API method
- Browser method is significantly slower than API method
- Some GitHub Enterprise features may not be supported

## License

MIT License