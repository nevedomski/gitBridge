# Corporate Environment Setup

This guide helps you configure GitSync to work in restricted corporate networks with proxies, certificates, and other security measures.

## Overview

Corporate networks often have:

- 🔒 **Proxy servers** for internet access
- 🔐 **Custom SSL certificates** for security
- 🚫 **Blocked ports** (SSH, Git protocols)
- 📋 **PAC scripts** for proxy configuration
- 🛡️ **Deep packet inspection** firewalls

GitSync is designed to handle all these scenarios.

## Quick Setup

For most corporate Windows environments:

```bash
# Auto-detect everything
gitsync sync --config config.yaml --auto-proxy --auto-cert

# If that doesn't work, disable SSL verification (last resort)
gitsync sync --config config.yaml --auto-proxy --no-ssl-verify
```

## Proxy Configuration

### Automatic Proxy Detection

GitSync can automatically detect proxy settings from:

1. **PAC Scripts** (Windows/Chrome)
2. **System Proxy Settings** (Windows)
3. **Environment Variables** (All platforms)

#### Enable Auto-Detection

=== "Command Line"

    ```bash
    gitsync sync --auto-proxy --repo https://github.com/user/repo --local ~/repo
    ```

=== "Configuration File"

    ```yaml
    sync:
      auto_proxy: true
      
    # GitSync will check in order:
    # 1. PAC script from Chrome
    # 2. Windows system proxy
    # 3. HTTP_PROXY environment variable
    ```

#### How PAC Detection Works

```mermaid
flowchart TD
    A[Start] --> B{Check Chrome<br/>Preferences}
    B -->|Found| C[Extract PAC URL]
    B -->|Not Found| D{Check Windows<br/>Registry}
    C --> E[Download PAC Script]
    D -->|Found| E
    D -->|Not Found| F[Check Env Variables]
    E --> G[Parse JavaScript]
    G --> H[Determine Proxy<br/>for github.com]
    H --> I[Configure Requests]
    F --> I
```

### Manual Proxy Configuration

If auto-detection doesn't work, configure manually:

#### Environment Variables

```bash
# Basic proxy
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# With authentication
export HTTPS_PROXY=http://username:password@proxy.company.com:8080

# Bypass proxy for internal sites
export NO_PROXY=localhost,127.0.0.1,.company.internal
```

#### Configuration File

```yaml
network:
  proxy:
    http: http://proxy.company.com:8080
    https: http://proxy.company.com:8080
    no_proxy: 
      - localhost
      - 127.0.0.1
      - .company.internal
    
    # With authentication
    auth:
      username: ${PROXY_USER}      # From environment
      password: ${PROXY_PASSWORD}  # From environment
```

#### Command Line

```bash
gitsync sync \
  --proxy http://proxy.company.com:8080 \
  --proxy-auth username:password \
  --repo https://github.com/user/repo \
  --local ~/repo
```

### PAC Script Support

For networks using PAC (Proxy Auto-Configuration) scripts:

```yaml
network:
  pac:
    url: http://proxy.company.com/proxy.pac
    # or
    file: /path/to/local/proxy.pac
    
    # Cache PAC script locally
    cache: true
    cache_dir: ~/.gitsync/pac_cache
```

## SSL Certificate Configuration

### Automatic Certificate Detection

GitSync can extract certificates from:

1. **Windows Certificate Store**
2. **System Certificate Bundle**
3. **Chrome Certificate Store**

#### Enable Auto-Detection

=== "Command Line"

    ```bash
    gitsync sync --auto-cert --repo https://github.com/user/repo --local ~/repo
    ```

=== "Configuration File"

    ```yaml
    sync:
      auto_cert: true
      
    # GitSync will:
    # 1. Extract from Windows store (if on Windows)
    # 2. Combine with certifi bundle
    # 3. Create temporary combined bundle
    ```

### Manual Certificate Configuration

#### Custom Certificate Bundle

```yaml
network:
  ssl:
    ca_bundle: /path/to/company/ca-bundle.crt
    verify: true
    
    # For self-signed certificates
    cert_file: /path/to/client.crt
    key_file: /path/to/client.key
```

#### Adding Company Root Certificate

1. **Get your company's root certificate:**
   ```bash
   # From your browser (Chrome example):
   # 1. Visit https://github.com
   # 2. Click padlock → Certificate → Details
   # 3. Export root certificate
   ```

2. **Add to GitSync:**
   ```bash
   # Option 1: Append to certifi bundle
   cat company-root.crt >> $(python -m certifi)
   
   # Option 2: Use custom bundle
   export REQUESTS_CA_BUNDLE=/path/to/company-bundle.crt
   gitsync sync --config config.yaml
   ```

### Disable SSL Verification (Last Resort)

!!! danger "Security Warning"
    Disabling SSL verification makes you vulnerable to man-in-the-middle attacks. Only use in trusted, isolated networks as a last resort.

```bash
# Command line
gitsync sync --no-ssl-verify --repo https://github.com/user/repo --local ~/repo

# Configuration file
network:
  ssl:
    verify: false
```

## Windows-Specific Setup

### PowerShell Script for Windows Users

Create `setup-gitsync.ps1`:

```powershell
# GitSync Windows Setup Script

# Set up environment variables
$env:GITHUB_TOKEN = Read-Host "Enter GitHub Token" -AsSecureString
$env:GITSYNC_CONFIG = "$HOME\.gitsync\config.yaml"

# Create config directory
New-Item -ItemType Directory -Force -Path "$HOME\.gitsync"

# Auto-detect proxy from IE/Edge
$proxy = (Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings').ProxyServer
if ($proxy) {
    $env:HTTPS_PROXY = "http://$proxy"
    Write-Host "Proxy detected: $proxy"
}

# Install GitSync with Windows support
pip install "gitsync[win,pac]"

# Test configuration
gitsync status --auto-proxy --auto-cert

Write-Host "Setup complete! Run 'gitsync sync --config $env:GITSYNC_CONFIG' to start"
```

### Windows Certificate Store Integration

GitSync automatically uses Windows certificates when `--auto-cert` is enabled:

```python
# What happens internally:
import wincertstore

# Open Windows certificate stores
for storename in ('CA', 'ROOT'):
    with wincertstore.CertSystemStore(storename) as store:
        for cert in store:
            # Export and add to bundle
            pem_cert = cert.get_pem()
            # Added to temporary certificate bundle
```

## Common Corporate Scenarios

### Scenario 1: Behind Authenticating Proxy

```yaml
# config-corporate.yaml
repository:
  url: https://github.com/company/internal-repo
  branch: main

local:
  path: C:\Projects\internal-repo

auth:
  token: ${GITHUB_TOKEN}

network:
  proxy:
    https: http://${DOMAIN_USER}:${DOMAIN_PASS}@proxy.company.com:8080
  ssl:
    ca_bundle: C:\Company\Certificates\ca-bundle.crt

sync:
  method: api
  auto_proxy: false  # Using manual config
  auto_cert: false   # Using manual config
```

### Scenario 2: PAC Script with Custom Certificates

```yaml
# config-pac.yaml
repository:
  url: https://github.com/company/project

local:
  path: ~/projects/company-project

sync:
  auto_proxy: true   # Detect from PAC
  auto_cert: true    # Detect from Windows
  method: api
  
  # Fallback if detection fails
  fallback:
    proxy: http://proxy.company.com:8080
    no_ssl_verify: true  # Last resort
```

### Scenario 3: Air-Gapped Network (No Internet)

For networks with no direct internet access:

1. **On machine with internet access:**
   ```bash
   # Download repository as ZIP
   gitsync export --repo https://github.com/user/repo --output repo.zip
   ```

2. **Transfer `repo.zip` to air-gapped network**

3. **On air-gapped machine:**
   ```bash
   # Import from ZIP
   gitsync import --input repo.zip --local /path/to/local
   ```

## Troubleshooting Corporate Issues

### Diagnosing Connection Problems

Use the diagnostic command:

```bash
gitsync diagnose --verbose

# Output will show:
# ✓ Python version: 3.11.0
# ✓ GitSync version: 0.1.0
# ✓ Proxy detected: http://proxy.company.com:8080
# ✓ Certificates: Using custom bundle (42 certificates)
# ✓ GitHub API accessible: Yes
# ✓ GitHub website accessible: Yes
```

### Common Error Messages

!!! error "SSL: CERTIFICATE_VERIFY_FAILED"
    **Solution**: Use `--auto-cert` or provide company certificate bundle:
    ```bash
    gitsync sync --auto-cert --config config.yaml
    ```

!!! error "ProxyError: 407 Proxy Authentication Required"
    **Solution**: Provide proxy credentials:
    ```bash
    export HTTPS_PROXY=http://domain\\username:password@proxy:8080
    gitsync sync --config config.yaml
    ```

!!! error "ConnectTimeout: Unable to connect to api.github.com"
    **Solution**: Check if API is blocked, try browser method:
    ```bash
    gitsync sync --method browser --config config.yaml
    ```

### Network Testing Script

Test your network configuration:

```python
#!/usr/bin/env python3
"""Test corporate network configuration for GitSync."""

import requests
import os
from urllib.parse import urlparse

def test_connection():
    """Test various connection methods."""
    
    # Test direct connection
    print("Testing direct connection...")
    try:
        r = requests.get("https://api.github.com", timeout=10)
        print(f"✓ Direct connection: {r.status_code}")
    except Exception as e:
        print(f"✗ Direct connection failed: {e}")
    
    # Test with proxy
    proxy = os.environ.get('HTTPS_PROXY')
    if proxy:
        print(f"\nTesting with proxy: {proxy}")
        try:
            r = requests.get("https://api.github.com", 
                           proxies={'https': proxy}, 
                           timeout=10)
            print(f"✓ Proxy connection: {r.status_code}")
        except Exception as e:
            print(f"✗ Proxy connection failed: {e}")
    
    # Test with custom certificates
    ca_bundle = os.environ.get('REQUESTS_CA_BUNDLE')
    if ca_bundle:
        print(f"\nTesting with certificates: {ca_bundle}")
        try:
            r = requests.get("https://api.github.com", 
                           verify=ca_bundle, 
                           timeout=10)
            print(f"✓ Certificate validation: {r.status_code}")
        except Exception as e:
            print(f"✗ Certificate validation failed: {e}")

if __name__ == "__main__":
    test_connection()
```

## Best Practices

1. **Security First**: Always use proper certificates rather than disabling SSL
2. **Cache Credentials**: Use secure credential managers for tokens and passwords
3. **Test Incrementally**: Test each component (proxy, certs) separately
4. **Document Settings**: Keep a record of working configuration for your team
5. **Use Auto-Detection**: Let GitSync detect settings when possible
6. **Have Fallbacks**: Configure both API and browser methods

## Quick Reference Card

```bash
# Windows corporate setup (most common)
gitsync sync --auto-proxy --auto-cert --config config.yaml

# Manual proxy with auth
export HTTPS_PROXY=http://DOMAIN\\username:password@proxy:8080
gitsync sync --config config.yaml

# Custom certificate bundle
export REQUESTS_CA_BUNDLE=/path/to/company-certs.pem
gitsync sync --config config.yaml

# Browser method when API is blocked
gitsync sync --method browser --config config.yaml

# Debug mode for troubleshooting
gitsync sync --verbose --debug --config config.yaml

# Last resort (insecure!)
gitsync sync --no-ssl-verify --config config.yaml
```

## Next Steps

- Configure [Proxy Settings](proxy-configuration.md) in detail
- Set up [SSL Certificates](ssl-certificates.md) properly
- Learn about [Authentication](authentication.md) methods
- Troubleshoot [Network Errors](../troubleshooting/network-errors.md)