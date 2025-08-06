# Troubleshooting Guide

This comprehensive troubleshooting guide helps you resolve common issues with GitBridge. Start with the diagnostic tool, then refer to specific problem categories.

## Quick Diagnostics

Run the built-in diagnostic tool to identify issues:

```bash
# Run full diagnostics
gitbridge diagnose

# Test specific components
gitbridge diagnose --network
gitbridge diagnose --auth
gitbridge diagnose --proxy
gitbridge diagnose --ssl
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
rm -rf ~/.gitbridge/cache
rm -rf ./.gitbridge

# Reinstall GitBridge
pip uninstall gitbridge -y
pip install gitbridge --upgrade

# Test with minimal configuration
gitbridge sync --repo https://github.com/github/gitignore --local ./test
```

### 2. Enable Debug Mode

```bash
# Maximum verbosity
gitbridge sync --config config.yaml -vvv

# Debug specific component
export GITSYNC_DEBUG=network,auth,proxy
gitbridge sync --config config.yaml

# Save debug output
gitbridge sync --config config.yaml \
  --log-level DEBUG \
  --log-file debug.log 2>&1
```

### 3. Validate Configuration

```bash
# Check configuration syntax
gitbridge validate --config config.yaml

# Test all components
gitbridge validate --config config.yaml \
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
# GitBridge version and environment
gitbridge info

# Output:
# GitBridge Version: 0.2.0
# Python Version: 3.11.5
# Platform: Windows-10
# Config Path: C:\Users\user\.gitbridge
# Cache Path: C:\Users\user\.gitbridge\cache
```

### Test Connectivity

```bash
# Test GitHub API access
gitbridge test-connection --url https://api.github.com

# Test repository access
gitbridge test-connection --repo https://github.com/user/repo

# Test with authentication
gitbridge test-connection --repo https://github.com/user/repo --token $TOKEN
```

### Check Rate Limits

```bash
# Show current rate limit status
gitbridge status --show-rate-limit

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
gitbridge sync --auto-cert

# 3. Proxy from Internet Explorer
gitbridge sync --auto-proxy
```

### macOS

```bash
# Common macOS issues
# 1. Keychain access
security unlock-keychain

# 2. Gatekeeper issues
xattr -d com.apple.quarantine /path/to/gitbridge

# 3. SSL certificates
export SSL_CERT_FILE=$(python -m certifi)
```

### Linux

```bash
# Common Linux issues
# 1. Missing certificates
sudo apt-get install ca-certificates

# 2. Permission issues
chmod 755 ~/.gitbridge
chown -R $USER:$USER ~/.gitbridge

# 3. DNS resolution
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

## Performance Issues

### Slow Synchronization

```bash
# Profile sync performance
gitbridge sync --config config.yaml --profile

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
gitbridge diagnose --full --output diagnostic-report.txt

# What to include when reporting issues:
# 1. GitBridge version (gitbridge --version)
# 2. Configuration file (remove sensitive data)
# 3. Error messages and stack traces
# 4. Debug log (--log-level DEBUG)
# 5. Diagnostic report
```

### Community Support

- **GitHub Issues**: [Report bugs](https://github.com/nevedomski/gitbridge/issues)
- **Discussions**: [Ask questions](https://github.com/nevedomski/gitbridge/discussions)
- **Stack Overflow**: Tag with `gitbridge`

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from gitbridge import GitHubAPISync
# Debug output will now be shown
```

## Recovery Procedures

### Corrupted Cache

```bash
# Backup current state
cp -r ~/.gitbridge ~/.gitbridge.backup

# Clear cache
rm -rf ~/.gitbridge/cache/*

# Rebuild cache
gitbridge sync --config config.yaml --rebuild-cache
```

### Interrupted Sync

```bash
# Resume from last checkpoint
gitbridge sync --config config.yaml --resume

# Or force full resync
gitbridge sync --config config.yaml --force
```

### Configuration Issues

```bash
# Reset to defaults
gitbridge init --output config.yaml --force

# Validate new configuration
gitbridge validate --config config.yaml --strict
```

## Prevention Tips

### 1. Regular Maintenance

```bash
# Weekly cache cleanup
0 0 * * 0 gitbridge cache clean --older-than 7d

# Monthly full validation
0 0 1 * * gitbridge validate --config config.yaml --full
```

### 2. Monitor Health

```bash
# Set up health checks
gitbridge health --config config.yaml --watch

# Create status dashboard
gitbridge status --format json > /var/log/gitbridge-status.json
```

### 3. Backup Configuration

```bash
# Version control your config
git init ~/.gitbridge-configs
git add config.yaml
git commit -m "Working configuration"
```

## Advanced Debugging

### Trace Execution

```bash
# Python trace
python -m trace -t $(which gitbridge) sync --config config.yaml

# System trace (Linux)
strace -f gitbridge sync --config config.yaml

# Network trace
tcpdump -i any -w gitbridge.pcap host api.github.com
```

### Memory Profiling

```python
from memory_profiler import profile
from gitbridge import GitHubAPISync

@profile
def test_sync():
    sync = GitHubAPISync(repo_url, local_path)
    sync.sync()
```

### Custom Debugging

```python
import pdb
from gitbridge import GitHubAPISync

# Set breakpoint
pdb.set_trace()
sync = GitHubAPISync(repo_url, local_path)
sync.sync()
```

## FAQ

### Q: Why is GitBridge slower than git clone?

GitBridge is designed for environments where git is blocked. It uses GitHub's REST API which has different performance characteristics than git protocol.

### Q: Can I use GitBridge with GitHub Enterprise?

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

### Q: Can GitBridge work offline?

No, GitBridge requires internet access to GitHub. For offline work, use git with a local repository.

## Next Steps

- Review specific error category guides
- Check [Common Issues](common-issues.md) for frequent problems
- Learn about [Network Errors](network-errors.md) and solutions
- Understand [Authentication](authentication-errors.md) troubleshooting
- Configure [Proxy Settings](proxy-issues.md) correctly
- Resolve [SSL/Certificate](ssl-errors.md) problems