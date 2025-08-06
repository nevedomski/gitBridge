# Common Issues and Solutions

This guide covers the most common issues users encounter with GitSync and their solutions.

## Quick Diagnostics

Before troubleshooting, run the diagnostic command:

```bash
gitsync diagnose --verbose
```

This will check:
- ✓ Python version and dependencies
- ✓ Network connectivity
- ✓ GitHub API access
- ✓ Proxy configuration
- ✓ SSL certificates
- ✓ Browser availability (if using browser method)

## Authentication Issues

### Error: 401 Unauthorized

!!! error "Error Message"
    ```
    Error: Authentication failed (401 Unauthorized)
    Please check your GitHub token
    ```

**Causes:**
- Invalid or expired GitHub token
- Token lacks required permissions
- Token not properly configured

**Solutions:**

1. **Verify token is valid:**
   ```bash
   # Test token directly
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
   ```

2. **Check token permissions:**
   - Go to GitHub → Settings → Developer settings → Personal access tokens
   - Ensure token has `repo` scope for private repositories
   - For public repos, `public_repo` scope is sufficient

3. **Set token correctly:**
   ```bash
   # Environment variable (recommended)
   export GITHUB_TOKEN=ghp_YourTokenHere
   gitsync sync --config config.yaml
   
   # Command line
   gitsync sync --token ghp_YourTokenHere --repo URL --local PATH
   
   # Config file
   echo "auth:
     token: ghp_YourTokenHere" >> config.yaml
   ```

### Error: 403 Forbidden

!!! error "Error Message"
    ```
    Error: API rate limit exceeded (403 Forbidden)
    ```

**Solutions:**

1. **Check rate limit status:**
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" \
        https://api.github.com/rate_limit
   ```

2. **Wait for rate limit reset:**
   ```python
   # The error message will show when limit resets
   # Typically 1 hour from when limit was hit
   ```

3. **Use authentication to increase limits:**
   - Unauthenticated: 60 requests/hour
   - Authenticated: 5,000 requests/hour

4. **Switch to browser method temporarily:**
   ```bash
   gitsync sync --method browser --config config.yaml
   ```

## Network and Connectivity Issues

### Error: Connection Timeout

!!! error "Error Message"
    ```
    ConnectTimeout: HTTPSConnectionPool(host='api.github.com', port=443): 
    Max retries exceeded with url: /repos/user/repo
    ```

**Causes:**
- Firewall blocking GitHub API
- Proxy configuration required
- Network connectivity issues

**Solutions:**

1. **Test basic connectivity:**
   ```bash
   # Test GitHub API
   curl https://api.github.com
   
   # Test with proxy
   curl --proxy http://proxy:8080 https://api.github.com
   ```

2. **Configure proxy:**
   ```bash
   # Auto-detect
   gitsync sync --auto-proxy --config config.yaml
   
   # Manual proxy
   export HTTPS_PROXY=http://proxy.company.com:8080
   gitsync sync --config config.yaml
   ```

3. **Try browser method:**
   ```bash
   gitsync sync --method browser --config config.yaml
   ```

### Error: Proxy Authentication Required

!!! error "Error Message"
    ```
    ProxyError: 407 Proxy Authentication Required
    ```

**Solutions:**

1. **Provide proxy credentials:**
   ```bash
   # Windows domain authentication
   export HTTPS_PROXY=http://DOMAIN\\username:password@proxy:8080
   
   # Regular authentication
   export HTTPS_PROXY=http://username:password@proxy:8080
   ```

2. **Use configuration file:**
   ```yaml
   network:
     proxy:
       https: http://proxy.company.com:8080
       auth:
         username: your_username
         password: your_password
   ```

## SSL/Certificate Issues

### Error: SSL Certificate Verification Failed

!!! error "Error Message"
    ```
    SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: 
    self signed certificate in certificate chain
    ```

**Causes:**
- Corporate proxy with custom certificates
- Self-signed certificates
- Missing root CA certificates

**Solutions:**

1. **Auto-detect certificates:**
   ```bash
   # Windows: Extract from certificate store
   gitsync sync --auto-cert --config config.yaml
   ```

2. **Use custom certificate bundle:**
   ```bash
   # Get company certificates from IT
   gitsync sync --ca-bundle /path/to/company-ca-bundle.crt
   
   # Or set environment variable
   export REQUESTS_CA_BUNDLE=/path/to/company-ca-bundle.crt
   ```

3. **Combine certificates:**
   ```bash
   # Combine company and default certificates
   cat /etc/ssl/company-ca.crt $(python -m certifi) > combined.crt
   export REQUESTS_CA_BUNDLE=combined.crt
   ```

4. **Last resort - disable verification:**
   ```bash
   # WARNING: Insecure! Only for testing!
   gitsync sync --no-ssl-verify --config config.yaml
   ```

## Browser Method Issues

### Error: Chrome/Chromium Not Found

!!! error "Error Message"
    ```
    WebDriverException: Message: 'chromedriver' executable needs to be in PATH
    ```

**Solutions:**

1. **Install Chrome/Chromium:**
   ```bash
   # Windows
   winget install Google.Chrome
   
   # macOS
   brew install --cask google-chrome
   
   # Linux
   sudo apt-get install chromium-browser
   ```

2. **Specify browser path:**
   ```bash
   gitsync sync --method browser \
     --browser-path "/usr/bin/chromium" \
     --config config.yaml
   ```

3. **Check ChromeDriver:**
   ```bash
   # Selenium 4+ manages ChromeDriver automatically
   # For manual installation:
   pip install webdriver-manager
   ```

### Error: Browser Timeout

!!! error "Error Message"
    ```
    TimeoutException: Message: timeout: Timed out receiving message from renderer
    ```

**Solutions:**

1. **Increase timeout:**
   ```bash
   gitsync sync --method browser \
     --browser-timeout 60 \
     --config config.yaml
   ```

2. **Run in non-headless mode for debugging:**
   ```bash
   gitsync sync --method browser --no-headless
   ```

3. **Check memory usage:**
   ```bash
   # Browser method uses more memory
   # Ensure sufficient RAM available
   free -h  # Linux
   ```

## File System Issues

### Error: Permission Denied

!!! error "Error Message"
    ```
    PermissionError: [Errno 13] Permission denied: '/path/to/file'
    ```

**Solutions:**

1. **Check directory permissions:**
   ```bash
   # Check permissions
   ls -la /path/to/directory
   
   # Fix permissions
   chmod -R u+w /path/to/directory
   ```

2. **Use different directory:**
   ```bash
   gitsync sync --local ~/writable-directory --repo URL
   ```

3. **Run as appropriate user:**
   ```bash
   # Avoid running as root
   # Use your normal user account
   ```

### Error: Disk Space

!!! error "Error Message"
    ```
    OSError: [Errno 28] No space left on device
    ```

**Solutions:**

1. **Check available space:**
   ```bash
   df -h /path/to/directory
   ```

2. **Clean up old files:**
   ```bash
   # Remove .gitsync cache
   rm -rf /path/to/repo/.gitsync
   
   # Full resync after cleanup
   gitsync sync --force --config config.yaml
   ```

## Configuration Issues

### Error: Invalid Configuration

!!! error "Error Message"
    ```
    ConfigError: Invalid configuration file: config.yaml
    ```

**Solutions:**

1. **Validate YAML syntax:**
   ```bash
   # Online validator: https://www.yamllint.com/
   
   # Or use Python
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

2. **Check required fields:**
   ```yaml
   # Minimum required configuration
   repository:
     url: https://github.com/user/repo
   
   local:
     path: /path/to/local
   ```

3. **Use example configuration:**
   ```bash
   cp config.example.yaml config.yaml
   # Edit config.yaml with your settings
   ```

### Error: Environment Variable Not Found

!!! error "Error Message"
    ```
    ConfigError: Environment variable GITHUB_TOKEN not found
    ```

**Solutions:**

1. **Set environment variable:**
   ```bash
   # Linux/macOS
   export GITHUB_TOKEN=ghp_YourToken
   
   # Windows Command Prompt
   set GITHUB_TOKEN=ghp_YourToken
   
   # Windows PowerShell
   $env:GITHUB_TOKEN="ghp_YourToken"
   ```

2. **Use .env file:**
   ```bash
   echo "GITHUB_TOKEN=ghp_YourToken" > .env
   # GitSync will load .env automatically
   ```

## Performance Issues

### Slow Synchronization

**Symptoms:**
- Initial sync takes hours
- Incremental updates are slow
- High memory usage

**Solutions:**

1. **Use API method (faster):**
   ```bash
   gitsync sync --method api --config config.yaml
   ```

2. **Enable parallel downloads:**
   ```yaml
   sync:
     parallel_downloads: 10
     chunk_size: 2097152  # 2MB chunks
   ```

3. **Skip large files:**
   ```yaml
   sync:
     skip_large_files: true
     large_file_size: 104857600  # 100MB
   ```

4. **Use incremental mode:**
   ```bash
   # Default behavior, but ensure it's enabled
   gitsync sync --incremental --config config.yaml
   ```

## Repository-Specific Issues

### Error: Repository Not Found

!!! error "Error Message"
    ```
    HTTPError: 404 Client Error: Not Found for url: https://api.github.com/repos/user/repo
    ```

**Solutions:**

1. **Check repository URL:**
   ```bash
   # Correct format
   https://github.com/owner/repository
   
   # Not
   https://github.com/owner/repository.git
   https://github.com/owner/repository/tree/main
   ```

2. **Check repository visibility:**
   - Private repos require authentication
   - Check if repo exists and you have access

3. **Check for typos:**
   ```bash
   # Test in browser first
   open https://github.com/owner/repository
   ```

### Error: Invalid Reference

!!! error "Error Message"
    ```
    GitSyncError: Reference 'feature/branch' not found in repository
    ```

**Solutions:**

1. **List available branches:**
   ```bash
   # Using API
   curl -H "Authorization: token YOUR_TOKEN" \
        https://api.github.com/repos/owner/repo/branches
   ```

2. **Use correct reference:**
   ```bash
   # Branch
   gitsync sync --ref main
   
   # Tag
   gitsync sync --ref v1.0.0
   
   # Commit SHA
   gitsync sync --ref abc123def
   ```

## Debug Mode

For persistent issues, enable debug mode:

```bash
# Maximum verbosity
gitsync sync --config config.yaml \
  --verbose \
  --log-file debug.log

# Check log file
tail -f debug.log
```

## Getting Help

If these solutions don't resolve your issue:

1. **Run diagnostics:**
   ```bash
   gitsync diagnose --verbose > diagnostic.txt
   ```

2. **Collect information:**
   - GitSync version: `gitsync --version`
   - Python version: `python --version`
   - Operating system: `uname -a` (Linux/macOS) or `ver` (Windows)
   - Full error message and stack trace
   - Configuration file (remove sensitive data)

3. **Create issue:**
   - Visit: https://github.com/nevedomski/gitsync/issues/new
   - Include diagnostic information
   - Describe steps to reproduce

## Prevention Tips

1. **Test configuration early:**
   ```bash
   gitsync status --config config.yaml
   ```

2. **Use verbose mode during setup:**
   ```bash
   gitsync sync --verbose --dry-run
   ```

3. **Keep credentials secure:**
   - Use environment variables for tokens
   - Never commit tokens to version control

4. **Monitor rate limits:**
   ```bash
   gitsync status --show-limits
   ```

5. **Regular updates:**
   ```bash
   pip install --upgrade gitsync
   ```