# Configuration Guide

GitBridge provides a flexible configuration system that supports multiple sources and formats. This guide covers all configuration options and best practices.

## Configuration Sources

GitBridge resolves configuration from multiple sources in priority order:

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Configuration file** (YAML)
4. **Default values** (lowest priority)

## Configuration File

The recommended way to configure GitBridge is using a YAML configuration file.

### Basic Configuration

```yaml
# config.yaml
repository:
  url: https://github.com/username/repo
  ref: main  # branch, tag, or commit SHA

local:
  path: ~/projects/repo

auth:
  token: ${GITHUB_TOKEN}  # Environment variable expansion

sync:
  method: api  # or 'browser'
  incremental: true
```

### Complete Configuration

```yaml
# Full configuration with all options
repository:
  url: https://github.com/username/repo
  ref: main  # branch, tag, or commit SHA

local:
  path: ~/projects/repo
  create_if_missing: true
  clean_before_sync: false

auth:
  token: ${GITHUB_TOKEN}
  username: ${GITHUB_USERNAME}  # For browser method
  password: ${GITHUB_PASSWORD}  # For browser method

sync:
  method: api  # 'api', 'browser', or 'auto'
  incremental: true
  force: false
  parallel_downloads: 5
  chunk_size: 8192
  retry_count: 3
  retry_delay: 1.0
  timeout: 30
  verify_ssl: true
  ignore_patterns:
    - "*.log"
    - "*.tmp"
    - ".git/*"
  skip_large_files: false
  large_file_size: 104857600  # 100MB in bytes

network:
  proxy:
    http: http://proxy.company.com:8080
    https: https://proxy.company.com:8443
    no_proxy:
      - localhost
      - 127.0.0.1
      - .company.internal
    auth:
      username: ${PROXY_USER}
      password: ${PROXY_PASS}
  
  ssl:
    verify: true
    ca_bundle: /path/to/ca-bundle.crt
    cert_file: /path/to/client.crt
    key_file: /path/to/client.key
  
  pac:
    url: http://proxy.company.com/proxy.pac
    file: /path/to/local/proxy.pac
    cache: true
  
  auto_proxy: false  # Auto-detect proxy settings
  auto_cert: false   # Auto-detect certificates

browser:
  type: chromium  # 'chromium', 'firefox', 'webkit'
  executable_path: /path/to/browser
  headless: true
  window_size: 1920x1080
  timeout: 60
  download_timeout: 300
  user_agent: "GitBridge/1.0"
  user_data_dir: ~/.gitbridge/browser
  args:
    - "--disable-gpu"
    - "--no-sandbox"

cache:
  enabled: true
  path: ~/.gitbridge/cache
  ttl: 3600  # Cache TTL in seconds
  max_size: 1073741824  # 1GB in bytes

logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: ~/.gitbridge/gitbridge.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  console: true
  rotate: true
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

## Environment Variables

GitBridge supports environment variable expansion in configuration files and direct environment variable configuration.

### Environment Variable Expansion

Use `${VAR_NAME}` syntax in configuration files:

```yaml
auth:
  token: ${GITHUB_TOKEN}
  username: ${GITHUB_USER:-default_user}  # With default value
```

### Direct Environment Variables

Set configuration directly via environment variables:

```bash
# Repository configuration
export GITSYNC_REPO_URL="https://github.com/user/repo"
export GITSYNC_REPO_REF="main"

# Local path
export GITSYNC_LOCAL_PATH="~/projects/repo"

# Authentication
export GITSYNC_AUTH_TOKEN="your_token_here"

# Sync settings
export GITSYNC_SYNC_METHOD="api"
export GITSYNC_SYNC_INCREMENTAL="true"

# Network settings
export GITSYNC_PROXY_HTTP="http://proxy:8080"
export GITSYNC_AUTO_PROXY="true"
export GITSYNC_AUTO_CERT="true"

# Logging
export GITSYNC_LOG_LEVEL="DEBUG"
export GITSYNC_LOG_FILE="/var/log/gitbridge.log"
```

## Command-Line Arguments

Command-line arguments override all other configuration sources.

### Basic Arguments

```bash
gitbridge sync \
  --repo https://github.com/user/repo \
  --local ~/projects/repo \
  --ref main \
  --token YOUR_TOKEN
```

### Advanced Arguments

```bash
gitbridge sync \
  --repo https://github.com/user/repo \
  --local ~/projects/repo \
  --ref develop \
  --method browser \
  --proxy http://proxy:8080 \
  --no-verify-ssl \
  --parallel-downloads 10 \
  --retry-count 5 \
  --verbose
```

### All Available Arguments

```bash
# Repository settings
--repo, -r              Repository URL (required)
--local, -l             Local directory path (required)
--ref                   Branch, tag, or commit (default: main)

# Authentication
--token, -t             GitHub personal access token
--username              GitHub username (browser method)
--password              GitHub password (browser method)

# Sync options
--method, -m            Sync method: api, browser, auto
--incremental           Enable incremental sync
--force                 Force full sync
--parallel-downloads    Number of parallel downloads
--retry-count           Number of retries for failed operations
--timeout               Operation timeout in seconds

# Network options
--proxy                 HTTP/HTTPS proxy URL
--no-proxy              Comma-separated list of hosts to bypass
--no-verify-ssl         Disable SSL verification
--ca-bundle             Path to CA bundle file
--auto-proxy            Auto-detect proxy settings
--auto-cert             Auto-detect certificates

# Browser options
--browser-type          Browser type: chromium, firefox, webkit
--headless              Run browser in headless mode
--browser-path          Path to browser executable

# Logging options
--verbose, -v           Enable verbose output
--quiet, -q             Suppress output
--log-file              Log file path
--log-level             Log level: DEBUG, INFO, WARNING, ERROR

# Other options
--config, -c            Configuration file path
--dry-run               Simulate sync without changes
--help, -h              Show help message
--version               Show version
```

## Configuration Precedence

When the same setting is specified in multiple places, GitBridge uses this precedence order:

1. **Command-line arguments** - Always take precedence
2. **Environment variables** - Override config file
3. **Configuration file** - Override defaults
4. **Default values** - Used when nothing else specified

### Example

```yaml
# config.yaml
sync:
  method: api
```

```bash
export GITSYNC_SYNC_METHOD="browser"
```

```bash
gitbridge sync --config config.yaml --method api
# Result: method = "api" (command-line wins)
```

## Path Expansion

GitBridge automatically expands paths:

- `~` expands to user home directory
- Environment variables are expanded
- Relative paths are resolved

```yaml
local:
  path: ~/projects/${PROJECT_NAME}/repo
  # Expands to: /home/user/projects/myproject/repo
```

## Validation

GitBridge validates configuration on startup:

- Required fields are present
- URLs are valid
- Paths are accessible
- Authentication is valid
- Network settings work

Use the `validate` command to test configuration:

```bash
gitbridge validate --config config.yaml
```

## Best Practices

### 1. Use Configuration Files

Store common settings in configuration files:

```yaml
# base.yaml - Shared settings
sync:
  incremental: true
  parallel_downloads: 5

network:
  auto_proxy: true
  auto_cert: true

logging:
  level: INFO
```

### 2. Environment-Specific Configs

Create different configs for different environments:

```yaml
# dev.yaml
repository:
  ref: develop

logging:
  level: DEBUG

# prod.yaml
repository:
  ref: main

logging:
  level: WARNING
```

### 3. Secure Sensitive Data

Never commit sensitive data to version control:

```yaml
# config.yaml (safe to commit)
auth:
  token: ${GITHUB_TOKEN}  # From environment

# .env (add to .gitignore)
GITHUB_TOKEN=your_actual_token_here
```

### 4. Use Defaults Wisely

Let GitBridge use sensible defaults:

```yaml
# Minimal config - uses many defaults
repository:
  url: https://github.com/user/repo

local:
  path: ./repo

# GitBridge will use default:
# - method: api
# - incremental: true
# - parallel_downloads: 5
# - retry_count: 3
# etc.
```

### 5. Validate Before Production

Always validate configuration changes:

```bash
# Test configuration
gitbridge validate --config new-config.yaml

# Dry run to see what would happen
gitbridge sync --config new-config.yaml --dry-run
```

## Configuration Examples

### Public Repository

```yaml
# public-repo.yaml
repository:
  url: https://github.com/torvalds/linux
  ref: master

local:
  path: ~/projects/linux

sync:
  method: api
  incremental: true
```

### Private Repository

```yaml
# private-repo.yaml
repository:
  url: https://github.com/company/private-repo
  ref: main

local:
  path: ~/work/private-repo

auth:
  token: ${GITHUB_TOKEN}

sync:
  method: api
  incremental: true
```

### Corporate Environment

```yaml
# corporate.yaml
repository:
  url: https://github.com/company/repo
  ref: main

local:
  path: ~/projects/repo

auth:
  token: ${GITHUB_TOKEN}

network:
  auto_proxy: true
  auto_cert: true
  proxy:
    http: ${HTTP_PROXY}
    https: ${HTTPS_PROXY}
    no_proxy:
      - localhost
      - .company.com

sync:
  method: api
  verify_ssl: true
```

### Browser Fallback

```yaml
# browser-fallback.yaml
repository:
  url: https://github.com/user/repo
  ref: main

local:
  path: ~/projects/repo

sync:
  method: browser

browser:
  type: chromium
  headless: false  # Show browser for debugging
  timeout: 120
```

## Troubleshooting Configuration

### Common Issues

1. **Configuration not loading**
   ```bash
   gitbridge validate --config config.yaml -v
   ```

2. **Environment variables not expanding**
   ```bash
   # Check if variable is set
   echo $GITHUB_TOKEN
   
   # Export if needed
   export GITHUB_TOKEN=your_token
   ```

3. **Path not found**
   ```bash
   # Use absolute paths for debugging
   gitbridge sync --local /absolute/path/to/repo
   ```

4. **Proxy not working**
   ```bash
   # Test with explicit proxy
   gitbridge sync --proxy http://proxy:8080 -v
   ```

### Debug Configuration

Enable debug logging to see configuration resolution:

```bash
gitbridge sync --config config.yaml --log-level DEBUG
```

This shows:
- Which configuration sources were loaded
- How values were resolved
- What the final configuration looks like

## Next Steps

- [Set up authentication](authentication.md)
- [Configure for corporate environment](corporate-setup.md)
- [Learn about sync methods](sync-methods.md)
- [Optimize performance](incremental-sync.md)