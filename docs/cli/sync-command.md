# sync Command

The `sync` command is the primary command for synchronizing GitHub repositories to local directories.

## Synopsis

```bash
gitsync sync [OPTIONS]
```

## Description

Synchronizes a GitHub repository to a local directory, downloading new and updated files while preserving unchanged files. Supports both API and browser-based synchronization methods.

## Options

### Required Options (one of)

Either provide a configuration file OR specify repository and local path:

| Option | Description |
|--------|-------------|
| `--config FILE` | Path to configuration file |
| `--repo URL` + `--local PATH` | Repository URL and local directory |

### Repository Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--repo URL` | `-r` | GitHub repository URL | - |
| `--local PATH` | `-l` | Local directory path | - |
| `--ref REF` | | Branch, tag, or commit SHA | `main` |
| `--token TOKEN` | `-t` | GitHub personal access token | `$GITHUB_TOKEN` |

### Sync Options

| Option | Description | Default |
|--------|-------------|---------|
| `--method METHOD` | Sync method: `api`, `browser`, or `auto` | `api` |
| `--incremental/--full` | Incremental or full sync | `incremental` |
| `--force` | Force sync even if up-to-date | `false` |
| `--dry-run` | Show what would be synced without downloading | `false` |

### Network Options

| Option | Description | Default |
|--------|-------------|---------|
| `--proxy URL` | HTTP/HTTPS proxy URL | - |
| `--proxy-auth USER:PASS` | Proxy authentication | - |
| `--auto-proxy` | Auto-detect proxy from PAC/system | `false` |
| `--no-proxy HOSTS` | Comma-separated list of hosts to bypass proxy | - |

### SSL/Certificate Options

| Option | Description | Default |
|--------|-------------|---------|
| `--ca-bundle PATH` | Path to CA certificate bundle | System default |
| `--auto-cert` | Auto-detect certificates from system | `false` |
| `--no-ssl-verify` | Disable SSL verification (insecure!) | `false` |

### Browser Options (for browser method)

| Option | Description | Default |
|--------|-------------|---------|
| `--browser TYPE` | Browser type: `chrome`, `chromium`, `edge` | `chrome` |
| `--browser-path PATH` | Path to browser executable | Auto-detect |
| `--headless/--no-headless` | Run browser in headless mode | `true` |
| `--browser-timeout SECONDS` | Browser operation timeout | `30` |

### Output Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--verbose` | `-v` | Verbose output | `false` |
| `--quiet` | `-q` | Suppress output except errors | `false` |
| `--json` | | Output in JSON format | `false` |
| `--log-file PATH` | | Save log to file | - |

## Examples

### Basic Usage

```bash
# Sync a public repository
gitsync sync --repo https://github.com/python/cpython --local ~/cpython

# Sync a private repository with token
gitsync sync \
  --repo https://github.com/company/private-repo \
  --local ~/projects/private-repo \
  --token ghp_YourGitHubToken
```

### Using Configuration File

```bash
# With configuration file
gitsync sync --config ~/.gitsync/config.yaml

# Override config file settings
gitsync sync --config config.yaml --ref develop --force
```

### Specific Branch or Tag

```bash
# Sync specific branch
gitsync sync \
  --repo https://github.com/user/repo \
  --local ~/repo \
  --ref feature/new-feature

# Sync specific tag
gitsync sync \
  --repo https://github.com/user/repo \
  --local ~/repo \
  --ref v2.0.0

# Sync specific commit
gitsync sync \
  --repo https://github.com/user/repo \
  --local ~/repo \
  --ref abc123def456
```

### Corporate Environment

```bash
# Auto-detect proxy and certificates
gitsync sync \
  --config config.yaml \
  --auto-proxy \
  --auto-cert

# Manual proxy configuration
gitsync sync \
  --repo https://github.com/user/repo \
  --local ~/repo \
  --proxy http://proxy.company.com:8080 \
  --proxy-auth domain\\username:password

# Custom certificate bundle
gitsync sync \
  --config config.yaml \
  --ca-bundle /path/to/company-ca-bundle.crt
```

### Browser Method

```bash
# Use browser method
gitsync sync \
  --repo https://github.com/user/repo \
  --local ~/repo \
  --method browser

# Browser with custom path
gitsync sync \
  --repo https://github.com/user/repo \
  --local ~/repo \
  --method browser \
  --browser-path /usr/bin/chromium

# Browser in visible mode (for debugging)
gitsync sync \
  --repo https://github.com/user/repo \
  --local ~/repo \
  --method browser \
  --no-headless
```

### Advanced Usage

```bash
# Dry run to see what would be synced
gitsync sync \
  --config config.yaml \
  --dry-run \
  --verbose

# Force full sync (ignore cache)
gitsync sync \
  --config config.yaml \
  --force \
  --full

# JSON output for scripting
gitsync sync \
  --config config.yaml \
  --json > sync-result.json

# Quiet mode with log file
gitsync sync \
  --config config.yaml \
  --quiet \
  --log-file ~/.gitsync/sync.log
```

## Configuration File

Instead of command-line options, you can use a YAML configuration file:

```yaml
# config.yaml
repository:
  url: https://github.com/user/repo
  ref: main  # branch, tag, or commit

local:
  path: ~/projects/repo

auth:
  token: ${GITHUB_TOKEN}  # From environment variable

sync:
  method: api  # or 'browser'
  incremental: true
  parallel_downloads: 5

network:
  proxy:
    https: http://proxy.company.com:8080
  ssl:
    verify: true
    ca_bundle: /path/to/ca-bundle.crt
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Authentication error |
| 4 | Network error |
| 5 | Repository not found |
| 6 | Permission denied |
| 7 | Rate limit exceeded |

## Environment Variables

The sync command respects these environment variables:

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub personal access token |
| `GITSYNC_CONFIG` | Default configuration file path |
| `HTTP_PROXY` | HTTP proxy URL |
| `HTTPS_PROXY` | HTTPS proxy URL |
| `NO_PROXY` | Hosts to bypass proxy |
| `REQUESTS_CA_BUNDLE` | CA certificate bundle path |
| `SSL_CERT_FILE` | SSL certificate file |

## Output Format

### Standard Output

```
GitSync v0.1.0
Repository: https://github.com/user/repo (branch: main)
Local path: /home/user/projects/repo

Fetching repository information... done
Comparing with local files... done

Changes detected:
  New files: 5
  Updated files: 12
  Deleted files: 0

Downloading files... 100% [==================] 17/17
  
✓ Sync completed successfully
  Files downloaded: 17
  Files skipped: 483
  Total size: 2.4 MB
  Time elapsed: 12.3s
```

### JSON Output

With `--json` flag:

```json
{
  "status": "success",
  "repository": {
    "url": "https://github.com/user/repo",
    "ref": "main",
    "commit": "abc123def456"
  },
  "local": {
    "path": "/home/user/projects/repo"
  },
  "changes": {
    "new": 5,
    "updated": 12,
    "deleted": 0,
    "unchanged": 483
  },
  "performance": {
    "duration": 12.3,
    "bytes_downloaded": 2516582,
    "files_processed": 500
  }
}
```

### Verbose Output

With `--verbose` flag, additional information is shown:

```
[DEBUG] Loading configuration from config.yaml
[DEBUG] Proxy detected: http://proxy.company.com:8080
[DEBUG] Using CA bundle: /etc/ssl/certs/ca-certificates.crt
[INFO] Connecting to GitHub API...
[DEBUG] GET https://api.github.com/repos/user/repo
[DEBUG] Response: 200 OK
[INFO] Repository: user/repo (main branch)
[DEBUG] Fetching tree for commit abc123def456
[DEBUG] Tree contains 500 items
[INFO] Comparing with local files...
[DEBUG] File: README.md (SHA mismatch: local=old123, remote=new456)
[INFO] Downloading: README.md (1234 bytes)
[DEBUG] GET https://api.github.com/repos/user/repo/contents/README.md
[DEBUG] Saved to: /home/user/projects/repo/README.md
```

## Performance Tips

1. **Use incremental mode** (default) for faster syncs
2. **Enable parallel downloads** for large repositories
3. **Use API method** when possible (much faster than browser)
4. **Cache authentication tokens** in environment variables
5. **Configure proxy once** in config file rather than command line

## Common Issues

### Authentication Failed

```bash
# Check token is valid
gitsync sync --repo https://github.com/user/private-repo --token YOUR_TOKEN

# Token from environment
export GITHUB_TOKEN=ghp_YourToken
gitsync sync --repo https://github.com/user/private-repo
```

### Proxy Issues

```bash
# Test with auto-detection
gitsync sync --auto-proxy --verbose

# Manual proxy with authentication
export HTTPS_PROXY=http://user:pass@proxy:8080
gitsync sync --config config.yaml
```

### SSL Certificate Errors

```bash
# Try auto-detection first
gitsync sync --auto-cert

# Custom certificate bundle
gitsync sync --ca-bundle /path/to/certs.pem

# Last resort (insecure!)
gitsync sync --no-ssl-verify
```

## See Also

- [status command](status-command.md) - Check repository status
- [Configuration Guide](../user-guide/configuration.md) - Detailed configuration options
- [Troubleshooting](../troubleshooting/index.md) - Common problems and solutions