# Getting Started

Welcome to GitSync! This section will help you get up and running quickly.

## Quick Navigation

<div class="grid cards" markdown>

- :material-download: **[Installation](installation.md)**  
  Install GitSync on your system

- :material-rocket: **[Quick Start](quick-start.md)**  
  5-minute guide to your first sync

- :material-sync: **[First Sync](first-sync.md)**  
  Detailed walkthrough of syncing a repository

- :material-cog: **[Configuration Basics](configuration-basics.md)**  
  Understanding configuration options

</div>

## Prerequisites

Before you begin, ensure you have:

- [x] Python 3.9 or higher installed
- [x] Network access to GitHub.com (via browser)
- [x] A GitHub repository you want to sync
- [x] (Optional) GitHub Personal Access Token for private repositories

## Installation Options

=== "Quick Install (pip)"

    ```bash
    pip install gitsync
    ```

=== "Recommended (uv)"

    ```bash
    # Install uv first
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Install gitsync
    uv pip install gitsync
    ```

=== "From Source"

    ```bash
    git clone https://github.com/nevedomski/gitsync
    cd gitsync
    pip install -e .
    ```

## Your First Sync

The simplest way to sync a repository:

```bash
gitsync sync --repo https://github.com/python/cpython --local ~/cpython
```

This will:

1. Connect to the GitHub repository
2. Download all files to your local directory
3. Create a `.gitsync` metadata file for tracking
4. Show progress with a nice progress bar

!!! success "That's it!"
    You've successfully synced your first repository! The next sync will only download changed files.

## What's Next?

After your first successful sync, explore these topics:

- **[Authentication](../user-guide/authentication.md)** - Access private repositories
- **[Configuration Files](configuration-basics.md)** - Save your settings
- **[Corporate Setup](../user-guide/corporate-setup.md)** - Work behind proxies
- **[Browser Mode](../user-guide/sync-methods.md#browser-automation-method)** - When API access is blocked

## Getting Help

If you run into issues:

1. Check the [Troubleshooting Guide](../troubleshooting/index.md)
2. Search [existing issues](https://github.com/nevedomski/gitsync/issues)
3. Ask for help by [creating an issue](https://github.com/nevedomski/gitsync/issues/new)

!!! tip "Pro Tip"
    Use `gitsync --help` to see all available commands and options at any time.