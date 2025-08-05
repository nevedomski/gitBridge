# GitSync - GitHub Repository Synchronization Tool

A Python tool to synchronize GitHub repositories to local folders when direct git access is blocked.

## Features

- **GitHub API Sync**: Uses GitHub's REST API for efficient repository synchronization
- **Browser Automation Fallback**: Falls back to Selenium-based browser automation if API access is blocked
- **Incremental Updates**: Only downloads changed files after initial sync
- **Configuration Support**: Flexible configuration via YAML files
- **Command-Line Interface**: Easy-to-use CLI for various sync operations
- **Progress Tracking**: Visual progress bars and detailed logging
- **Automatic Proxy Detection**: Auto-detects proxy settings from Windows/Chrome PAC scripts
- **Corporate Environment Support**: Works with SSL certificates and proxy configurations

## Installation

Using [uv](https://github.com/astral-sh/uv):

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the project
uv pip install -e .

# Or install with development dependencies
uv pip install -e ".[dev]"

# Install with PAC proxy support (Windows)
uv pip install -e ".[pac]"
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
gitsync sync --config config.yaml
```

## Usage

### Basic Sync
```bash
gitsync sync --repo https://github.com/username/repo --local /path/to/local
```

### With Personal Access Token
```bash
gitsync sync --repo https://github.com/username/repo --local /path/to/local --token YOUR_TOKEN
```

### Force Browser Mode
```bash
gitsync sync --repo https://github.com/username/repo --local /path/to/local --method browser
```

### Check Repository Status
```bash
gitsync status --config config.yaml
```

### Corporate Environment Support

For Windows users in corporate environments:

```bash
# Auto-detect proxy from Chrome/Windows settings
gitsync sync --repo https://github.com/username/repo --local /path/to/local --auto-proxy

# Auto-detect certificates from Windows certificate store
gitsync sync --repo https://github.com/username/repo --local /path/to/local --auto-cert

# Use both auto-detection features together
gitsync sync --config config.yaml --auto-proxy --auto-cert

# Last resort: disable SSL verification
gitsync sync --config config.yaml --auto-proxy --no-ssl-verify
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

- Python 3.9+ (recommended: 3.11+)
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