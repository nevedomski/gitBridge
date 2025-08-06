# User Guide

Welcome to the GitBridge User Guide. This comprehensive guide will help you understand and use all features of GitBridge effectively.

## What You'll Learn

This guide covers everything from basic usage to advanced configurations:

- Different synchronization methods and when to use them
- Configuration options and best practices
- Authentication and security setup
- Corporate environment configurations
- Performance optimization techniques
- Troubleshooting common issues

## Guide Sections

### [Sync Methods](sync-methods.md)
Learn about the two synchronization methods (API and Browser) and when to use each one.

### [Configuration](configuration.md)
Detailed guide to configuring GitBridge using YAML files, environment variables, and command-line options.

### [Authentication](authentication.md)
Set up authentication for both API and browser methods, including token management and security best practices.

### [Incremental Sync](incremental-sync.md)
Understand how incremental synchronization works and how to optimize sync performance.

### [Branch Management](branch-management.md)
Learn how to sync specific branches, tags, or commits from your repository.

### [Corporate Setup](corporate-setup.md)
Configure GitBridge for corporate environments with proxies, PAC scripts, and custom certificates.

### [Proxy Configuration](proxy-configuration.md)
Detailed guide to configuring various proxy types including HTTP, HTTPS, SOCKS, and PAC scripts.

### [SSL Certificates](ssl-certificates.md)
Handle custom SSL certificates and certificate verification in restricted environments.

## Quick Start Examples

### Basic Synchronization

Sync a public repository:

```bash
gitbridge sync --repo https://github.com/user/repo --local ~/projects/repo
```

### Authenticated Sync

Sync a private repository with authentication:

```bash
# Using environment variable
export GITHUB_TOKEN=your_token_here
gitbridge sync --repo https://github.com/user/private-repo --local ~/projects/repo

# Or directly in command
gitbridge sync --repo https://github.com/user/private-repo \
             --local ~/projects/repo \
             --token your_token_here
```

### Corporate Environment

Sync in a corporate environment with auto-detection:

```bash
# Windows with auto-detection
gitbridge sync --config config.yaml --auto-proxy --auto-cert

# Manual proxy configuration
gitbridge sync --repo https://github.com/user/repo \
             --local ~/projects/repo \
             --proxy http://proxy.company.com:8080
```

### Using Configuration File

Create a `config.yaml` file:

```yaml
repository:
  url: https://github.com/username/repo
  ref: main

local:
  path: ~/projects/repo

auth:
  token: ${GITHUB_TOKEN}

sync:
  method: api
  incremental: true

network:
  auto_proxy: true
  auto_cert: true
```

Then run:

```bash
gitbridge sync --config config.yaml
```

## Best Practices

### 1. Use Configuration Files

For repeated syncs, use a configuration file instead of command-line arguments:

- Easier to manage complex configurations
- Supports environment variable expansion
- Can be version controlled (exclude sensitive data)

### 2. Enable Incremental Sync

Always use incremental sync for better performance:

```yaml
sync:
  incremental: true
```

This only downloads changed files after the initial sync.

### 3. Set Up Authentication Properly

- Use environment variables for tokens
- Never commit tokens to version control
- Use read-only tokens when possible
- Rotate tokens regularly

### 4. Configure for Your Environment

- Use `--auto-proxy` and `--auto-cert` on Windows
- Configure specific proxy settings if auto-detection fails
- Test connectivity with `gitbridge status` before syncing

### 5. Monitor Sync Operations

- Use verbose mode (`-v`) for debugging
- Check logs for any warnings or errors
- Monitor sync statistics for performance

## Common Use Cases

### Continuous Integration

Sync repositories in CI/CD pipelines:

```bash
# In your CI script
gitbridge sync --repo $REPO_URL --local ./source --token $CI_TOKEN
```

### Backup Solution

Create regular backups of repositories:

```bash
# Cron job for daily backup
0 2 * * * gitbridge sync --config /path/to/backup-config.yaml
```

### Development Environment

Keep local copies synchronized:

```bash
# Sync multiple repositories
for repo in repo1 repo2 repo3; do
    gitbridge sync --config configs/$repo.yaml
done
```

## Performance Tips

1. **Use API method when possible** - It's faster and more efficient
2. **Enable parallel downloads** - For large repositories
3. **Configure appropriate timeouts** - Based on your network speed
4. **Use incremental sync** - Avoid re-downloading unchanged files
5. **Exclude unnecessary files** - Use ignore patterns for large binaries

## Security Considerations

1. **Token Security**
   - Use minimal required permissions
   - Store tokens securely (environment variables, secret managers)
   - Rotate tokens regularly

2. **Network Security**
   - Verify SSL certificates
   - Use secure proxy configurations
   - Monitor network traffic

3. **Local Security**
   - Secure local repository copies
   - Set appropriate file permissions
   - Clean up temporary files

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](../troubleshooting/index.md)
2. Run with verbose mode (`-v`) for detailed output
3. Check the [GitHub Issues](https://github.com/nevedomski/gitbridge/issues)
4. Contact support if needed

## Next Steps

- [Configure your first sync](configuration.md)
- [Set up authentication](authentication.md)
- [Learn about sync methods](sync-methods.md)
- [Optimize for your environment](corporate-setup.md)