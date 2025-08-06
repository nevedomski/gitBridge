# CLI Reference

GitSync provides a comprehensive command-line interface for repository synchronization. This reference covers all available commands and options.

## Installation

After installing GitSync, the `gitsync` command becomes available:

```bash
# Check installation
gitsync --version

# Get help
gitsync --help
```

## Commands Overview

GitSync provides several commands for different operations:

| Command | Description | Usage |
|---------|-------------|--------|
| `sync` | Synchronize repository | Main synchronization command |
| `status` | Check configuration and connectivity | Validate setup |
| `validate` | Validate configuration file | Test configuration |
| `init` | Initialize configuration | Create config file |

## Global Options

These options work with all commands:

```bash
--config, -c PATH      Configuration file path
--verbose, -v          Enable verbose output
--quiet, -q            Suppress output
--log-level LEVEL      Set log level (DEBUG, INFO, WARNING, ERROR)
--log-file PATH        Log to file
--no-color             Disable colored output
--help, -h             Show help message
--version              Show version
```

## Command Details

### sync - Synchronize Repository

The main command for synchronizing repositories.

```bash
gitsync sync [OPTIONS]
```

#### Required Options

One of these option sets is required:

**Option 1: Using configuration file**
```bash
gitsync sync --config config.yaml
```

**Option 2: Using command-line arguments**
```bash
gitsync sync --repo URL --local PATH
```

#### All Options

```bash
# Repository settings
--repo, -r URL          Repository URL (required without config)
--local, -l PATH        Local directory (required without config)
--ref REF               Branch, tag, or commit (default: main)

# Authentication
--token TOKEN           GitHub personal access token
--username USER         GitHub username (browser method)
--password PASS         GitHub password (browser method)

# Sync options
--method METHOD         Sync method: api, browser, auto
--incremental           Enable incremental sync
--force                 Force full sync
--dry-run               Simulate without changes

# Network options
--proxy URL             HTTP/HTTPS proxy
--no-verify-ssl         Disable SSL verification
--auto-proxy            Auto-detect proxy settings
--auto-cert             Auto-detect certificates

# Performance options
--parallel-downloads N  Number of parallel downloads
--chunk-size SIZE       Download chunk size in bytes
--timeout SECONDS       Operation timeout
--retry-count N         Number of retries

# Browser options
--browser-type TYPE     Browser type: chromium, firefox, webkit
--headless              Run browser in headless mode
--browser-path PATH     Path to browser executable
```

#### Examples

```bash
# Basic sync
gitsync sync --repo https://github.com/user/repo --local ~/projects/repo

# With authentication
gitsync sync --repo https://github.com/user/private-repo \
             --local ~/projects/repo \
             --token ghp_xxxxxxxxxxxx

# Using configuration file
gitsync sync --config ~/configs/project.yaml

# Force full sync with verbose output
gitsync sync --config config.yaml --force -v

# Browser method with specific browser
gitsync sync --repo https://github.com/user/repo \
             --local ~/projects/repo \
             --method browser \
             --browser-type firefox

# Corporate environment with auto-detection
gitsync sync --config config.yaml --auto-proxy --auto-cert

# Dry run to see what would be synced
gitsync sync --config config.yaml --dry-run
```

### status - Check Status

Check configuration, connectivity, and sync status.

```bash
gitsync status [OPTIONS]
```

#### Options

```bash
--config, -c PATH       Configuration file
--show-config           Display resolved configuration
--show-rate-limit       Show API rate limit status
--test-connection       Test repository connectivity
--check-updates         Check for available updates
```

#### Examples

```bash
# Check basic status
gitsync status

# Check with specific configuration
gitsync status --config config.yaml

# Show detailed configuration
gitsync status --config config.yaml --show-config

# Check API rate limits
gitsync status --show-rate-limit

# Test connection to repository
gitsync status --config config.yaml --test-connection
```

#### Output Example

```
GitSync Status Report
====================

Configuration:
  ✓ Configuration file loaded: config.yaml
  ✓ Repository: https://github.com/user/repo
  ✓ Local path: /home/user/projects/repo
  ✓ Authentication: Token configured

Network:
  ✓ Proxy: Auto-detected (http://proxy:8080)
  ✓ SSL: Custom certificates loaded
  ✓ Connection: Successful

Sync Status:
  ✓ Last sync: 2025-01-20 10:30:00
  ✓ Method: API
  ✓ Files synced: 1,234
  ✓ Total size: 156.7 MB

API Rate Limit:
  ✓ Remaining: 4,892 / 5,000
  ✓ Reset: 2025-01-20 11:00:00
```

### validate - Validate Configuration

Validate configuration file syntax and values.

```bash
gitsync validate [OPTIONS]
```

#### Options

```bash
--config, -c PATH       Configuration file to validate
--check-auth            Validate authentication
--check-network         Validate network settings
--check-paths           Validate file paths
--strict                Strict validation mode
```

#### Examples

```bash
# Validate configuration file
gitsync validate --config config.yaml

# Full validation with all checks
gitsync validate --config config.yaml \
                 --check-auth \
                 --check-network \
                 --check-paths

# Strict validation (fail on warnings)
gitsync validate --config config.yaml --strict
```

#### Output Example

```
Validating configuration: config.yaml
=====================================

Syntax:
  ✓ YAML syntax valid
  ✓ Required fields present
  ✓ No unknown fields

Values:
  ✓ Repository URL valid
  ✓ Local path accessible
  ✓ Reference format valid

Authentication:
  ✓ Token format valid
  ✓ Token has required scopes
  ✓ Token not expired

Network:
  ✓ Proxy configuration valid
  ✓ SSL certificates found
  ✓ Connection test successful

Result: Configuration is valid
```

### init - Initialize Configuration

Create a new configuration file interactively.

```bash
gitsync init [OPTIONS]
```

#### Options

```bash
--output, -o PATH       Output file path (default: config.yaml)
--template TYPE         Template type: basic, full, corporate
--non-interactive       Use defaults without prompting
--force                 Overwrite existing file
```

#### Examples

```bash
# Interactive initialization
gitsync init

# Create configuration with specific template
gitsync init --template corporate --output corporate-config.yaml

# Non-interactive with defaults
gitsync init --non-interactive --output default-config.yaml

# Force overwrite existing
gitsync init --force --output config.yaml
```

#### Interactive Example

```
GitSync Configuration Wizard
============================

Repository URL: https://github.com/user/repo
Local directory [./repo]: ~/projects/repo
Branch/tag/commit [main]: develop

Authentication required? [y/N]: y
GitHub token: **********************

Sync method [api/browser/auto]: api
Enable incremental sync? [Y/n]: y

Configure proxy? [y/N]: y
Proxy URL: http://proxy.company.com:8080

Auto-detect certificates? [y/N]: y

Configuration saved to: config.yaml

Test configuration now? [Y/n]: y
✓ Configuration is valid and working!
```

## Configuration File Usage

### Loading Configuration

Configuration files are loaded in this order:

1. Specified with `--config` flag
2. `./config.yaml` in current directory
3. `~/.gitsync/config.yaml` in home directory
4. `/etc/gitsync/config.yaml` system-wide

### Environment Variable Expansion

Configuration files support environment variables:

```yaml
auth:
  token: ${GITHUB_TOKEN}

local:
  path: ${HOME}/projects/${PROJECT_NAME}
```

### Multiple Configurations

Use different configurations for different repositories:

```bash
# Personal projects
gitsync sync --config ~/.gitsync/personal.yaml

# Work projects
gitsync sync --config ~/.gitsync/work.yaml

# Open source contributions
gitsync sync --config ~/.gitsync/opensource.yaml
```

## Exit Codes

GitSync uses standard exit codes:

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Operation completed successfully |
| 1 | General error | Unspecified error occurred |
| 2 | Configuration error | Invalid configuration |
| 3 | Authentication error | Authentication failed |
| 4 | Network error | Network or connectivity issue |
| 5 | Repository error | Repository access problem |
| 6 | File system error | Local file system issue |
| 7 | Rate limit error | API rate limit exceeded |
| 8 | Browser error | Browser automation failed |

## Shell Completion

Enable shell completion for better CLI experience:

### Bash

```bash
# Add to ~/.bashrc
eval "$(_GITSYNC_COMPLETE=bash_source gitsync)"
```

### Zsh

```bash
# Add to ~/.zshrc
eval "$(_GITSYNC_COMPLETE=zsh_source gitsync)"
```

### Fish

```fish
# Add to ~/.config/fish/config.fish
eval "$(_GITSYNC_COMPLETE=fish_source gitsync)"
```

## Advanced Usage

### Scripting

Use GitSync in scripts:

```bash
#!/bin/bash

# Sync with error handling
if gitsync sync --config config.yaml --quiet; then
    echo "Sync successful"
else
    exit_code=$?
    case $exit_code in
        3) echo "Authentication failed" ;;
        4) echo "Network error" ;;
        7) echo "Rate limit exceeded" ;;
        *) echo "Sync failed with code: $exit_code" ;;
    esac
    exit $exit_code
fi
```

### Cron Jobs

Schedule regular syncs:

```bash
# Add to crontab
# Sync every hour
0 * * * * /usr/local/bin/gitsync sync --config /home/user/.gitsync/config.yaml --quiet

# Sync every day at 2 AM
0 2 * * * /usr/local/bin/gitsync sync --config /home/user/.gitsync/config.yaml --log-file /var/log/gitsync.log
```

### Docker Usage

Run GitSync in Docker:

```bash
# Using configuration file
docker run -v $(pwd)/config.yaml:/config.yaml \
           -v $(pwd)/repo:/repo \
           gitsync:latest \
           sync --config /config.yaml

# With environment variables
docker run -e GITHUB_TOKEN=$GITHUB_TOKEN \
           -v $(pwd)/repo:/repo \
           gitsync:latest \
           sync --repo https://github.com/user/repo --local /repo
```

## Troubleshooting

### Common Issues

**Command not found:**
```bash
# Check installation
pip show gitsync

# Ensure pip bin directory is in PATH
export PATH="$PATH:$(python -m site --user-base)/bin"
```

**Permission denied:**
```bash
# Check file permissions
ls -la ~/.gitsync/

# Fix permissions
chmod 600 ~/.gitsync/config.yaml
```

**SSL certificate errors:**
```bash
# Disable SSL verification (not recommended)
gitsync sync --config config.yaml --no-verify-ssl

# Or use custom certificates
gitsync sync --config config.yaml --auto-cert
```

### Debug Mode

Enable debug output for troubleshooting:

```bash
# Maximum verbosity
gitsync sync --config config.yaml -vvv --log-level DEBUG

# Save debug output to file
gitsync sync --config config.yaml --log-level DEBUG --log-file debug.log
```

## Next Steps

- [Sync Command Details](sync-command.md)
- [Configuration Guide](../user-guide/configuration.md)
- [Authentication Setup](../user-guide/authentication.md)
- [Troubleshooting Guide](../troubleshooting/index.md)