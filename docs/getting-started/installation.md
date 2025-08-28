# Installation

This guide covers all installation methods for GitBridge, including optional components for corporate environments.

## System Requirements

### Minimum Requirements

- **Python**: 3.10 or higher
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Memory**: 512 MB RAM
- **Disk Space**: 100 MB for GitBridge + space for repositories
- **Network**: HTTPS access to github.com

### Recommended Requirements

- **Python**: 3.11 or higher
- **Memory**: 2 GB RAM
- **For Browser Mode**: Chrome/Chromium browser

## Installation Methods

### Method 1: From PyPI (Recommended)

GitBridge is available on PyPI as `gitbridge`:

```bash
# Basic installation
pip install gitbridge

# With browser automation support (Playwright)
pip install gitbridge[browser]

# For development
pip install gitbridge[dev]

# All extras
pip install gitbridge[all]
```

**Note for Windows users**: Windows-specific dependencies (pypac, wincertstore, pywin32) are **automatically installed** when you install GitBridge on Windows.

### Method 2: Using uv

[uv](https://github.com/astral-sh/uv) is a fast Python package manager that handles virtual environments automatically:

=== "Linux/macOS"

    ```bash
    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Install gitbridge from PyPI
    uv pip install gitbridge
    
    # With browser automation
    uv pip install "gitbridge[browser]"
    ```

=== "Windows"

    ```powershell
    # Install uv
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    # Install gitbridge (Windows deps auto-install)
    uv pip install gitbridge
    
    # With browser automation
    uv pip install "gitbridge[browser]"
    ```

### Method 3: From Source

Install directly from the GitHub repository:

```bash
# Clone the repository
git clone https://github.com/nevedomski/gitbridge
cd gitbridge

# Install with uv
uv pip install -e .

# Or with pip
pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"
```

## Optional Dependencies

GitBridge has several optional dependency groups for specific features:

### Browser Automation

For browser-based synchronization fallback:

```bash
pip install "gitbridge[browser]"
```

This installs:
- `playwright`: Browser automation framework

### Windows Platform Support

**Note**: Windows dependencies are **automatically installed** on Windows systems. You don't need to specify them manually.

The following are included automatically on Windows:
- `pypac`: PAC file parsing and proxy detection
- `wincertstore`: Windows certificate store access
- `pywin32`: Windows API access

### Development Dependencies

For contributing to GitBridge:

```bash
pip install "gitbridge[dev]"
```

This installs:
- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting
- `ruff`: Linting and formatting
- `mypy`: Type checking
- Type stubs for better IDE support

### All Extras

Install all optional dependencies:

```bash
pip install "gitbridge[all]"
# or
pip install "gitbridge[browser,dev]"
```

## Browser Mode Setup

If you plan to use the browser automation fallback method, you need:

### 1. Install Chrome or Chromium

=== "Windows"

    Download from [Google Chrome](https://www.google.com/chrome/) or use:
    ```powershell
    winget install Google.Chrome
    ```

=== "macOS"

    ```bash
    brew install --cask google-chrome
    # or
    brew install chromium
    ```

=== "Linux"

    ```bash
    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install chromium-browser
    
    # Fedora
    sudo dnf install chromium
    
    # Arch
    sudo pacman -S chromium
    ```

### 2. Install Playwright Browsers

Playwright manages browser binaries automatically:

=== "Automatic Installation"

    ```bash
    # Install browser binaries
    playwright install chromium
    
    # Or install all browsers
    playwright install
    ```

=== "System Requirements"

    Playwright will automatically download the appropriate browser binaries for your system.
    No additional driver installation is required.

## Verification

After installation, verify GitBridge is working:

```bash
# Check version
gitbridge --version

# Show help
gitbridge --help

# Test configuration
gitbridge status
```

Expected output:
```
GitBridge version 1.0.0
Python 3.11.5
System: Linux-6.15.8-200.fc42.x86_64
```

## Corporate Environment Setup

For corporate environments with special requirements:

### 1. Behind a Proxy

```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Install with proxy
pip install --proxy http://proxy.company.com:8080 gitbridge
```

### 2. Custom Certificate Bundle

```bash
# Set certificate bundle path
export REQUESTS_CA_BUNDLE=/path/to/company/ca-bundle.crt
export SSL_CERT_FILE=/path/to/company/ca-bundle.crt

# Or use GitBridge's auto-detection
gitbridge sync --auto-cert
```

### 3. Offline Installation

For air-gapped environments:

```bash
# On a machine with internet access
pip download gitbridge -d ./offline_packages
pip download -r requirements.txt -d ./offline_packages

# Transfer offline_packages directory to target machine

# On the target machine
pip install --no-index --find-links ./offline_packages gitbridge
```

## Updating GitBridge

### Update to Latest Version

```bash
# Using pip
pip install --upgrade gitbridge

# Using uv
uv pip install --upgrade gitbridge

# From source
cd gitbridge
git pull
pip install -e .
```

### Check for Updates

```bash
# Check current version
gitbridge --version

# Check latest version on PyPI
pip index versions gitbridge
```

## Uninstallation

To completely remove GitBridge:

```bash
# Using pip
pip uninstall gitbridge

# Remove configuration files (optional)
rm -rf ~/.gitbridge
rm ~/.gitbridgerc  # If exists

# Remove cached data (optional)
rm -rf ~/.cache/gitbridge
```

## Troubleshooting Installation

### Common Issues

!!! warning "Permission Denied"
    If you get permission errors, use `--user` flag:
    ```bash
    pip install --user gitbridge
    ```

!!! warning "Python Version Error"
    GitBridge requires Python 3.10+. Check your version:
    ```bash
    python --version
    ```
    
    Use `python3` if needed:
    ```bash
    python3 -m pip install gitbridge
    ```

!!! warning "SSL Certificate Error"
    For SSL errors in corporate environments:
    ```bash
    pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org gitbridge
    ```

### Getting Help

If you encounter issues:

1. Check [Troubleshooting Guide](../troubleshooting/index.md)
2. Search [GitHub Issues](https://github.com/nevedomski/gitbridge/issues)
3. Create a [new issue](https://github.com/nevedomski/gitbridge/issues/new) with:
   - Python version (`python --version`)
   - GitBridge version (`gitbridge --version`)
   - Full error message
   - Operating system details

## Next Steps

Now that GitBridge is installed:

- [Quick Start Guide](quick-start.md) - Start syncing repositories
- [Configuration](configuration-basics.md) - Set up your preferences
- [Authentication](../user-guide/authentication.md) - Access private repositories