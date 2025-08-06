# Troubleshooting Guide

This comprehensive troubleshooting guide helps you resolve common issues with GitSync. Start with the diagnostic tool, then refer to specific problem categories.

## Quick Diagnostics

Run the built-in diagnostic tool to identify issues:

```bash
# Run full diagnostics
gitsync diagnose

# Test specific components
gitsync diagnose --network
gitsync diagnose --auth
gitsync diagnose --proxy
gitsync diagnose --ssl
```

## Common Issues by Category

### 🔌 [Network Errors](network-errors.md)
- Connection timeouts
- DNS resolution failures
- Firewall blocking
- Rate limiting

### 🔐 [Authentication Errors](authentication-errors.md)
- Invalid tokens
- Expired credentials
- Permission denied
- Two-factor authentication

### 🌐 [Proxy Issues](proxy-issues.md)
- Proxy configuration errors
- PAC script problems
- Proxy authentication failures
- Bypass rules not working

### 🔒 [SSL/Certificate Errors](ssl-errors.md)
- Certificate verification failures
- Self-signed certificates
- Corporate CA certificates
- Certificate chain issues

### 🌏 [Browser Automation](browser-automation.md)
- Browser not found
- Playwright installation issues
- Headless mode problems
- Download failures

### 📁 [Common Issues](common-issues.md)
- Configuration problems
- File permission errors
- Path resolution issues
- Cache corruption

## Quick Fixes

### 1. Reset and Start Fresh

```bash
# Clear all cache and metadata
rm -rf ~/.gitsync/cache
rm -rf ./.gitsync

# Reinstall GitSync
pip uninstall gitsync -y
pip install gitsync --upgrade

# Test with minimal configuration
gitsync sync --repo https://github.com/github/gitignore --local ./test
```

### 2. Enable Debug Mode

```bash
# Maximum verbosity
gitsync sync --config config.yaml -vvv

# Debug specific component
export GITSYNC_DEBUG=network,auth,proxy
gitsync sync --config config.yaml

# Save debug output
gitsync sync --config config.yaml \
  --log-level DEBUG \
  --log-file debug.log 2>&1
```

### 3. Validate Configuration

```bash
# Check configuration syntax
gitsync validate --config config.yaml

# Test all components
gitsync validate --config config.yaml \
  --check-auth \
  --check-network \
  --check-paths
```

## Error Messages Quick Reference

| Error Message | Likely Cause | Quick Fix |
|--------------|--------------|-----------|
| `401 Unauthorized` | Invalid token | Check token, regenerate if needed |
| `403 Forbidden` | Insufficient permissions | Verify token scopes |
| `404 Not Found` | Wrong repository URL | Check repository exists and URL |
| `Connection refused` | Proxy/firewall blocking | Check proxy settings |
| `SSL certificate problem` | Certificate verification | Use `--auto-cert` or add CA bundle |
| `Rate limit exceeded` | Too many API requests | Add authentication or wait |
| `Permission denied` | File system permissions | Check directory permissions |
| `Browser not found` | Playwright not installed | Run `playwright install` |

## Diagnostic Commands

### Check System Information

```bash
# GitSync version and environment
gitsync info

# Output:
# GitSync Version: 0.2.0
# Python Version: 3.11.5
# Platform: Windows-10
# Config Path: C:\Users\user\.gitsync
# Cache Path: C:\Users\user\.gitsync\cache
```

### Test Connectivity

```bash
# Test GitHub API access
gitsync test-connection --url https://api.github.com

# Test repository access
gitsync test-connection --repo https://github.com/user/repo

# Test with authentication
gitsync test-connection --repo https://github.com/user/repo --token $TOKEN
```

### Check Rate Limits

```bash
# Show current rate limit status
gitsync status --show-rate-limit

# Output:
# Rate Limit Status:
#   Limit: 5000 requests/hour
#   Remaining: 4892
#   Reset: 2025-01-20 14:00:00 (in 23 minutes)
```

## Environment-Specific Issues

### Windows

```powershell
# Common Windows issues
# 1. Long path support
git config --system core.longpaths true

# 2. Certificate store access
gitsync sync --auto-cert

# 3. Proxy from Internet Explorer
gitsync sync --auto-proxy
```

### macOS

```bash
# Common macOS issues
# 1. Keychain access
security unlock-keychain

# 2. Gatekeeper issues
xattr -d com.apple.quarantine /path/to/gitsync

# 3. SSL certificates
export SSL_CERT_FILE=$(python -m certifi)
```

### Linux

```bash
# Common Linux issues
# 1. Missing certificates
sudo apt-get install ca-certificates

# 2. Permission issues
chmod 755 ~/.gitsync
chown -R $USER:$USER ~/.gitsync

# 3. DNS resolution
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

## Performance Issues

### Slow Synchronization

```bash
# Profile sync performance
gitsync sync --config config.yaml --profile

# Optimize configuration
cat > optimized.yaml << EOF
sync:
  parallel_downloads: 10
  chunk_size: 2097152  # 2MB chunks
  incremental: true
  
cache:
  enabled: true
  ttl: 3600
EOF
```

### High Memory Usage

```yaml
# Limit memory usage
sync:
  max_file_size: 52428800  # 50MB max in memory
  stream_large_files: true
  batch_size: 100  # Process files in batches
```

### Network Bottlenecks

```yaml
# Optimize for slow networks
sync:
  parallel_downloads: 2  # Reduce parallel connections
  retry_count: 5
  retry_delay: 10
  timeout: 120
  compression: true  # Enable compression if supported
```

## Getting Help

### Collect Diagnostic Information

```bash
# Generate diagnostic report
gitsync diagnose --full --output diagnostic-report.txt

# What to include when reporting issues:
# 1. GitSync version (gitsync --version)
# 2. Configuration file (remove sensitive data)
# 3. Error messages and stack traces
# 4. Debug log (--log-level DEBUG)
# 5. Diagnostic report
```

### Community Support

- **GitHub Issues**: [Report bugs](https://github.com/nevedomski/gitsync/issues)
- **Discussions**: [Ask questions](https://github.com/nevedomski/gitsync/discussions)
- **Stack Overflow**: Tag with `gitsync`

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from gitsync import GitHubAPISync
# Debug output will now be shown
```

## Recovery Procedures

### Corrupted Cache

```bash
# Backup current state
cp -r ~/.gitsync ~/.gitsync.backup

# Clear cache
rm -rf ~/.gitsync/cache/*

# Rebuild cache
gitsync sync --config config.yaml --rebuild-cache
```

### Interrupted Sync

```bash
# Resume from last checkpoint
gitsync sync --config config.yaml --resume

# Or force full resync
gitsync sync --config config.yaml --force
```

### Configuration Issues

```bash
# Reset to defaults
gitsync init --output config.yaml --force

# Validate new configuration
gitsync validate --config config.yaml --strict
```

## Prevention Tips

### 1. Regular Maintenance

```bash
# Weekly cache cleanup
0 0 * * 0 gitsync cache clean --older-than 7d

# Monthly full validation
0 0 1 * * gitsync validate --config config.yaml --full
```

### 2. Monitor Health

```bash
# Set up health checks
gitsync health --config config.yaml --watch

# Create status dashboard
gitsync status --format json > /var/log/gitsync-status.json
```

### 3. Backup Configuration

```bash
# Version control your config
git init ~/.gitsync-configs
git add config.yaml
git commit -m "Working configuration"
```

## Advanced Debugging

### Trace Execution

```bash
# Python trace
python -m trace -t $(which gitsync) sync --config config.yaml

# System trace (Linux)
strace -f gitsync sync --config config.yaml

# Network trace
tcpdump -i any -w gitsync.pcap host api.github.com
```

### Memory Profiling

```python
from memory_profiler import profile
from gitsync import GitHubAPISync

@profile
def test_sync():
    sync = GitHubAPISync(repo_url, local_path)
    sync.sync()
```

### Custom Debugging

```python
import pdb
from gitsync import GitHubAPISync

# Set breakpoint
pdb.set_trace()
sync = GitHubAPISync(repo_url, local_path)
sync.sync()
```

## FAQ

### Q: Why is GitSync slower than git clone?

GitSync is designed for environments where git is blocked. It uses GitHub's REST API which has different performance characteristics than git protocol.

### Q: Can I use GitSync with GitHub Enterprise?

Yes! Configure the API endpoint:

```yaml
repository:
  url: https://github.enterprise.com/user/repo
  api_url: https://github.enterprise.com/api/v3
```

### Q: How do I sync large repositories?

Use these optimizations:

```yaml
sync:
  shallow: true  # Don't download full history
  sparse:
    - /src  # Only sync specific directories
    - /docs
  skip_large_files: true
  large_file_threshold: 104857600  # 100MB
```

### Q: Can GitSync work offline?

No, GitSync requires internet access to GitHub. For offline work, use git with a local repository.

## Next Steps

- Review specific error category guides
- Check [Common Issues](common-issues.md) for frequent problems
- Learn about [Network Errors](network-errors.md) and solutions
- Understand [Authentication](authentication-errors.md) troubleshooting
- Configure [Proxy Settings](proxy-issues.md) correctly
- Resolve [SSL/Certificate](ssl-errors.md) problems