# GitSync - GitHub Repository Synchronization Tool

<div align="center">

![GitSync Logo](assets/banner.png)

**Synchronize GitHub repositories when direct git access is blocked**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](license.md)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-brightgreen)](index.md)
[![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)](troubleshooting/index.md)

[Get Started](getting-started/quick-start.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/nevedomski/gitsync){ .md-button }

</div>

## Overview

GitSync is a powerful Python tool designed to synchronize GitHub repositories to local folders when direct git access is blocked. It provides two synchronization methods - GitHub API and browser automation - ensuring you can always access your code, even in restricted network environments.

## Key Features

<div class="grid cards" markdown>

- :material-api: **GitHub API Sync**  
  Fast and efficient synchronization using GitHub's REST API with incremental updates

- :material-web: **Browser Automation**  
  Selenium-based fallback method that works when API access is restricted

- :material-shield-check: **Corporate Ready**  
  Built-in support for proxies, PAC scripts, and SSL certificates

- :material-sync: **Incremental Updates**  
  Only downloads changed files after initial sync, saving bandwidth and time

- :material-cog: **Flexible Configuration**  
  YAML-based configuration with environment variable support

- :material-console: **Intuitive CLI**  
  Easy-to-use command-line interface with progress tracking

</div>

## Quick Example

=== "Command Line"

    ```bash
    # Basic sync
    gitsync sync --repo https://github.com/user/repo --local ~/projects/repo

    # With authentication
    gitsync sync --repo https://github.com/user/repo \
                 --local ~/projects/repo \
                 --token YOUR_GITHUB_TOKEN

    # Corporate environment with auto-detection
    gitsync sync --config config.yaml --auto-proxy --auto-cert
    ```

=== "Configuration File"

    ```yaml title="config.yaml"
    repository:
      url: https://github.com/username/repo
      branch: main

    local:
      path: ~/projects/repo

    auth:
      token: ${GITHUB_TOKEN}  # From environment variable

    sync:
      method: api
      incremental: true
    ```

=== "Python API"

    ```python
    from gitsync import GitHubAPISync

    sync = GitHubAPISync(
        repo_url="https://github.com/user/repo",
        local_path="/path/to/local",
        token="YOUR_GITHUB_TOKEN"
    )

    # Perform sync
    changes = sync.sync()
    print(f"Synced {changes['updated']} files")
    ```

## Why GitSync?

### The Problem

Many corporate and institutional networks block direct git access (SSH and HTTPS) for security reasons, making it impossible to use standard git commands like `git clone` or `git pull`. However, browser access to GitHub often remains available.

### The Solution

GitSync provides two robust methods to synchronize repositories:

1. **API Method**: Uses GitHub's REST API over HTTPS (same as browser traffic)
2. **Browser Method**: Automates a real browser to download files when API is blocked

Both methods support:

- :material-check: Incremental updates (only changed files)
- :material-check: Branch and tag selection
- :material-check: Progress tracking
- :material-check: Corporate proxy support
- :material-check: SSL certificate handling

## Installation

```bash
# Using pip
pip install gitsync

# Using uv (recommended)
uv pip install gitsync

# From source
git clone https://github.com/nevedomski/gitsync
cd gitsync
uv pip install -e .
```

[Full Installation Guide](getting-started/installation.md){ .md-button }

## Documentation Structure

<div class="grid cards" markdown>

- :material-rocket-launch: **[Getting Started](getting-started/index.md)**  
  Installation, quick start guide, and your first sync

- :material-book-open: **[User Guide](user-guide/index.md)**  
  Detailed guides for all features and use cases

- :material-console-line: **[CLI Reference](cli/index.md)**  
  Complete command-line interface documentation

- :material-architecture: **[Architecture](architecture/index.md)**  
  Technical details about how GitSync works

- :material-api: **[API Reference](api/index.md)**  
  Python API documentation for developers

- :material-help-circle: **[Troubleshooting](troubleshooting/index.md)**  
  Solutions to common problems and issues

</div>

## System Requirements

- **Python**: 3.9 or higher (3.11+ recommended)
- **Operating System**: Windows, macOS, or Linux
- **For Browser Mode**: Chrome/Chromium and ChromeDriver
- **Network**: HTTPS access to GitHub (browser access)

## Support

- :material-github: [GitHub Issues](https://github.com/nevedomski/gitsync/issues)
- :material-book: [Documentation](index.md)
- :material-email: [Email Support](mailto:info@nevedomski.us)

## License

GitSync is open source software licensed under the [MIT License](license.md).

---

!!! tip "Ready to get started?"
    Check out our [Quick Start Guide](getting-started/quick-start.md) to sync your first repository in under 5 minutes!