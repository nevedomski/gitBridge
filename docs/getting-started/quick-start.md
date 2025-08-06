# Quick Start Guide

Get up and running with GitSync in under 5 minutes! This guide will walk you through syncing your first repository.

## Prerequisites

Before starting, ensure you have:

- [x] GitSync installed ([Installation Guide](installation.md))
- [x] Network access to GitHub.com
- [x] A target directory for the synced repository

## Step 1: Basic Repository Sync

Let's start by syncing a public repository:

```bash
gitsync sync --repo https://github.com/python/cpython --local ~/projects/cpython
```

What happens:

1. GitSync connects to the GitHub repository
2. Downloads the entire repository structure
3. Saves files to `~/projects/cpython`
4. Creates `.gitsync/metadata.json` for tracking

!!! success "Success!"
    You've synced your first repository! The output will show:
    ```
    ✓ Repository synced successfully
    Files: 4,521 downloaded, 0 skipped
    Time: 2m 34s
    ```

## Step 2: Incremental Updates

Run the same command again:

```bash
gitsync sync --repo https://github.com/python/cpython --local ~/projects/cpython
```

Notice how it's much faster! GitSync only downloads changed files:

```
✓ Repository synced successfully  
Files: 3 updated, 4,518 unchanged
Time: 5s
```

## Step 3: Using Configuration Files

Instead of typing long commands, create a configuration file:

=== "config.yaml"

    ```yaml
    repository:
      url: https://github.com/python/cpython
      branch: main
    
    local:
      path: ~/projects/cpython
    
    sync:
      incremental: true
      method: api
    ```

=== "Command"

    ```bash
    # Now just run:
    gitsync sync --config config.yaml
    ```

## Step 4: Syncing Private Repositories

For private repositories, you need authentication:

### Generate a GitHub Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (full control of private repositories)
4. Copy the generated token

### Use the Token

=== "Command Line"

    ```bash
    gitsync sync \
      --repo https://github.com/yourusername/private-repo \
      --local ~/projects/private-repo \
      --token ghp_YourGitHubTokenHere
    ```

=== "Environment Variable"

    ```bash
    export GITHUB_TOKEN=ghp_YourGitHubTokenHere
    gitsync sync \
      --repo https://github.com/yourusername/private-repo \
      --local ~/projects/private-repo
    ```

=== "Configuration File"

    ```yaml
    repository:
      url: https://github.com/yourusername/private-repo
    
    local:
      path: ~/projects/private-repo
    
    auth:
      token: ${GITHUB_TOKEN}  # Read from environment
    ```

## Step 5: Specific Branch or Tag

Sync a specific branch, tag, or commit:

```bash
# Sync a branch
gitsync sync --repo https://github.com/user/repo --local ~/repo --ref develop

# Sync a tag
gitsync sync --repo https://github.com/user/repo --local ~/repo --ref v1.0.0

# Sync a specific commit
gitsync sync --repo https://github.com/user/repo --local ~/repo --ref abc123def
```

## Common Use Cases

### Corporate Environment with Proxy

If you're behind a corporate proxy:

```bash
# Auto-detect proxy from system
gitsync sync --config config.yaml --auto-proxy

# Or specify manually
gitsync sync --config config.yaml --proxy http://proxy.company.com:8080
```

### When API Access is Blocked

Use browser automation as fallback:

```bash
gitsync sync --repo https://github.com/user/repo --local ~/repo --method browser
```

!!! warning "Browser Mode"
    Browser mode is slower but works when API access is blocked. It requires Chrome/Chromium installed.

### Check Repository Status

Before syncing, check the repository status:

```bash
gitsync status --config config.yaml
```

Output:
```
Repository: https://github.com/python/cpython
Branch: main
Latest commit: abc123def (2 hours ago)
Local path: ~/projects/cpython
Last sync: 2025-01-15 10:30:00
Status: 42 files outdated
```

## Quick Reference

### Essential Commands

| Command | Description |
|---------|-------------|
| `gitsync sync` | Synchronize repository |
| `gitsync status` | Check repository status |
| `gitsync --help` | Show help message |
| `gitsync --version` | Show version |

### Key Options

| Option | Description | Example |
|--------|-------------|---------|
| `--repo` | Repository URL | `--repo https://github.com/user/repo` |
| `--local` | Local directory | `--local ~/projects/repo` |
| `--token` | GitHub token | `--token ghp_abc123` |
| `--ref` | Branch/tag/commit | `--ref develop` |
| `--method` | Sync method | `--method browser` |
| `--config` | Config file | `--config config.yaml` |
| `--verbose` | Detailed output | `--verbose` |

## Tips and Tricks

!!! tip "Speed Up Syncs"
    Use incremental mode (default) to only download changed files:
    ```yaml
    sync:
      incremental: true
    ```

!!! tip "Multiple Repositories"
    Create multiple config files:
    ```bash
    gitsync sync --config work-repo.yaml
    gitsync sync --config personal-repo.yaml
    ```

!!! tip "Automation"
    Add to cron for automatic syncing:
    ```bash
    # Sync every hour
    0 * * * * /usr/bin/gitsync sync --config /home/user/config.yaml
    ```

!!! tip "Debugging"
    Use verbose mode for troubleshooting:
    ```bash
    gitsync sync --config config.yaml --verbose
    ```

## What's Next?

Now that you've mastered the basics:

- 📖 Read the [User Guide](../user-guide/index.md) for advanced features
- 🔧 Learn about [Configuration](configuration-basics.md) options
- 🔐 Set up [Authentication](../user-guide/authentication.md) properly
- 🏢 Configure for [Corporate Environments](../user-guide/corporate-setup.md)
- 🤖 Explore [CLI Commands](../cli/index.md) in detail

## Need Help?

If something doesn't work:

1. Check the [Troubleshooting Guide](../troubleshooting/common-issues.md)
2. Run with `--verbose` for detailed error messages
3. Check your network access to GitHub
4. [Create an issue](https://github.com/nevedomski/gitsync/issues/new) for support