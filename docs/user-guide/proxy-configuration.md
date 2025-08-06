# Proxy Configuration Guide

GitSync provides comprehensive proxy support for corporate and restricted network environments. This guide covers all aspects of configuring and using proxies.

## Overview

GitSync supports multiple proxy configurations:

- **HTTP/HTTPS proxies** - Standard web proxies
- **SOCKS proxies** - SOCKS4/SOCKS5 proxies
- **PAC scripts** - Proxy Auto-Configuration
- **System proxy** - Use OS proxy settings
- **Auto-detection** - Automatic proxy discovery

## Basic Proxy Configuration

### Command Line

```bash
# Simple HTTP proxy
gitsync sync --repo https://github.com/user/repo \
             --local ~/projects/repo \
             --proxy http://proxy.company.com:8080

# Proxy with authentication
gitsync sync --repo https://github.com/user/repo \
             --local ~/projects/repo \
             --proxy http://username:password@proxy.company.com:8080
```

### Configuration File

```yaml
network:
  proxy:
    http: http://proxy.company.com:8080
    https: https://proxy.company.com:8443
    no_proxy:
      - localhost
      - 127.0.0.1
      - .internal.company.com
```

### Environment Variables

```bash
# Standard proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8443
export NO_PROXY=localhost,127.0.0.1,.internal.company.com

# GitSync-specific variables
export GITSYNC_PROXY_HTTP=http://proxy.company.com:8080
export GITSYNC_PROXY_HTTPS=https://proxy.company.com:8443
```

## Proxy Authentication

### Basic Authentication

```yaml
network:
  proxy:
    http: http://proxy.company.com:8080
    auth:
      username: ${PROXY_USER}
      password: ${PROXY_PASS}
```

### URL-Encoded Authentication

```bash
# Special characters must be URL-encoded
# @ becomes %40, : becomes %3A, etc.
gitsync sync --proxy http://user%40domain:pass%3Aword@proxy:8080
```

### Secure Credential Storage

Never store credentials in plain text. Use:

```bash
# Environment variables
export PROXY_USER=john.doe
export PROXY_PASS=secret_password

# System keyring (Python keyring)
python -c "import keyring; keyring.set_password('gitsync', 'proxy_user', 'john.doe')"
python -c "import keyring; keyring.set_password('gitsync', 'proxy_pass', 'secret')"
```

## PAC Script Configuration

### What is PAC?

Proxy Auto-Configuration (PAC) scripts dynamically determine proxy settings based on the URL being accessed.

### PAC Configuration

```yaml
network:
  pac:
    # Option 1: PAC file URL
    url: http://proxy.company.com/proxy.pac
    
    # Option 2: Local PAC file
    file: /path/to/proxy.pac
    
    # Cache PAC results
    cache: true
    cache_ttl: 3600  # seconds
```

### Auto-Detect PAC (Windows)

```bash
# Enable PAC auto-detection
gitsync sync --config config.yaml --auto-proxy

# This will check:
# 1. Windows Registry for PAC URL
# 2. Internet Explorer settings
# 3. Chrome settings
# 4. WPAD (Web Proxy Auto-Discovery)
```

### Manual PAC Testing

```bash
# Test PAC script
gitsync test-pac --pac-url http://proxy.company.com/proxy.pac \
                  --test-url https://github.com

# Output:
# PAC script returned: PROXY proxy1.company.com:8080; PROXY proxy2.company.com:8080
```

## SOCKS Proxy Configuration

### SOCKS5 Proxy

```yaml
network:
  proxy:
    # SOCKS5 proxy
    http: socks5://proxy.company.com:1080
    https: socks5://proxy.company.com:1080
    
    # SOCKS5 with authentication
    socks_auth:
      username: ${SOCKS_USER}
      password: ${SOCKS_PASS}
```

### SOCKS4 Proxy

```bash
# SOCKS4 doesn't support authentication
gitsync sync --proxy socks4://proxy.company.com:1080
```

## Proxy Bypass Rules

### No-Proxy Configuration

```yaml
network:
  proxy:
    http: http://proxy.company.com:8080
    no_proxy:
      # Exact hostnames
      - localhost
      - github.internal.com
      
      # IP addresses
      - 127.0.0.1
      - 192.168.0.0/16
      - 10.0.0.0/8
      
      # Domain wildcards
      - .internal.company.com
      - "*.local"
      
      # Ports
      - ":8080"
      - "localhost:3000"
```

### Complex Bypass Rules

```python
# Custom proxy resolver
from gitsync.pac_support import ProxyResolver

resolver = ProxyResolver()
resolver.add_rule("*.github.com", "PROXY proxy1:8080")
resolver.add_rule("*.internal.com", "DIRECT")
resolver.add_rule("10.*", "DIRECT")
```

## Auto-Detection

### Windows Auto-Detection

```bash
# Auto-detect all proxy settings
gitsync sync --config config.yaml --auto-proxy

# What it does:
# 1. Checks Windows Registry
# 2. Reads Internet Explorer settings
# 3. Checks Chrome preferences
# 4. Looks for PAC scripts
# 5. Tests WPAD
```

### macOS Auto-Detection

```bash
# Uses macOS network settings
gitsync sync --config config.yaml --auto-proxy

# Checks:
# 1. System Preferences → Network → Advanced → Proxies
# 2. scutil --proxy command output
```

### Linux Auto-Detection

```bash
# Checks multiple sources
gitsync sync --config config.yaml --auto-proxy

# Sources:
# 1. Environment variables (HTTP_PROXY, etc.)
# 2. GNOME settings (gsettings)
# 3. KDE settings
# 4. /etc/environment
```

## Browser Method with Proxy

### Playwright Proxy Configuration

```yaml
sync:
  method: browser

browser:
  type: chromium
  proxy:
    server: http://proxy.company.com:8080
    username: ${PROXY_USER}
    password: ${PROXY_PASS}
    bypass: localhost,127.0.0.1
```

### Browser-Specific Settings

```yaml
browser:
  # Use system proxy
  use_system_proxy: true
  
  # Or specify browser args
  args:
    - "--proxy-server=http://proxy:8080"
    - "--proxy-bypass-list=localhost,127.0.0.1"
```

## Proxy Chains

### Multiple Proxy Hops

```yaml
network:
  proxy_chain:
    - http://proxy1.company.com:8080
    - http://proxy2.company.com:8080
    - socks5://final-proxy.com:1080
```

### Failover Configuration

```yaml
network:
  proxy:
    primary: http://proxy1.company.com:8080
    fallback:
      - http://proxy2.company.com:8080
      - http://proxy3.company.com:8080
    
    failover:
      enabled: true
      timeout: 5  # seconds to wait before failover
      retry_count: 2
```

## SSL/TLS with Proxies

### Proxy with Custom CA

```yaml
network:
  proxy:
    http: https://secure-proxy.company.com:8443
    
  ssl:
    verify: true
    ca_bundle: /path/to/company-ca-bundle.crt
    
    # For proxy certificate
    proxy_ca: /path/to/proxy-ca.crt
```

### Client Certificates

```yaml
network:
  proxy:
    http: https://secure-proxy.company.com:8443
    
    # Client certificate for proxy authentication
    client_cert:
      cert_file: /path/to/client.crt
      key_file: /path/to/client.key
      password: ${CERT_PASSWORD}
```

## Testing and Debugging

### Test Proxy Connection

```bash
# Test proxy connectivity
gitsync test-proxy --proxy http://proxy:8080 \
                   --test-url https://api.github.com

# Verbose output
gitsync test-proxy --proxy http://proxy:8080 -v

# Output:
# Testing proxy: http://proxy:8080
# Connecting to proxy... ✓
# Authenticating... ✓
# Testing target URL... ✓
# Proxy is working correctly
```

### Debug Proxy Issues

```bash
# Enable proxy debugging
export GITSYNC_DEBUG_PROXY=1
gitsync sync --config config.yaml -v

# Log all proxy decisions
gitsync sync --config config.yaml \
             --log-level DEBUG \
             --log-file proxy-debug.log
```

### Proxy Diagnostic Tool

```bash
# Run comprehensive proxy diagnostics
gitsync diagnose-proxy

# Output:
# Proxy Diagnostics
# =================
# 
# Environment Variables:
#   HTTP_PROXY: http://proxy:8080 ✓
#   HTTPS_PROXY: https://proxy:8443 ✓
#   NO_PROXY: localhost,127.0.0.1 ✓
# 
# System Proxy:
#   Windows Registry: http://proxy:8080 ✓
#   PAC URL: http://proxy.company.com/proxy.pac ✓
# 
# Connectivity Tests:
#   Direct connection: ✗ (blocked)
#   Via HTTP proxy: ✓
#   Via HTTPS proxy: ✓
#   PAC resolution: ✓
# 
# Recommended configuration:
#   Use HTTP proxy: http://proxy:8080
```

## Common Proxy Scenarios

### Corporate Firewall

```yaml
# Typical corporate setup
network:
  auto_proxy: true  # Auto-detect first
  
  proxy:
    # Fallback if auto-detect fails
    http: http://proxy.company.com:8080
    https: http://proxy.company.com:8080
    
    no_proxy:
      - localhost
      - .company.internal
      - 10.0.0.0/8
      - 172.16.0.0/12
      - 192.168.0.0/16
    
    auth:
      username: ${DOMAIN}\\${USERNAME}  # Domain authentication
      password: ${PASSWORD}
```

### Split Tunneling

```yaml
# Different proxies for different destinations
network:
  proxy_rules:
    - pattern: "*.github.com"
      proxy: http://external-proxy:8080
    
    - pattern: "*.internal.com"
      proxy: DIRECT
    
    - pattern: "*"
      proxy: http://default-proxy:8080
```

### Proxy with VPN

```yaml
# When using VPN
network:
  detect_vpn: true
  
  vpn_proxy:
    # Use this proxy when VPN is connected
    http: http://vpn-proxy.company.com:8080
  
  normal_proxy:
    # Use this proxy when VPN is disconnected
    http: http://regular-proxy.company.com:8080
```

## Performance Optimization

### Connection Pooling

```yaml
network:
  proxy:
    http: http://proxy:8080
    
    # Connection pool settings
    pool:
      max_connections: 10
      max_connections_per_host: 5
      keepalive: true
      keepalive_timeout: 300  # seconds
```

### Caching Proxy Responses

```yaml
network:
  proxy:
    http: http://proxy:8080
    
    cache:
      enabled: true
      cache_dir: ~/.gitsync/proxy-cache
      max_size: 100MB
      ttl: 3600  # seconds
```

## Troubleshooting

### Common Issues

#### 1. Proxy Authentication Failed

```bash
# Check credentials
echo $PROXY_USER
echo $PROXY_PASS | sed 's/./*/g'  # Mask password

# Test with curl
curl -x http://user:pass@proxy:8080 https://api.github.com

# Try different authentication methods
gitsync sync --proxy http://DOMAIN\\user:pass@proxy:8080  # NTLM
gitsync sync --proxy http://user@domain:pass@proxy:8080   # Alternative
```

#### 2. SSL Certificate Errors with Proxy

```bash
# Temporarily disable SSL verification (not recommended)
gitsync sync --config config.yaml --no-verify-ssl

# Better: Add proxy CA certificate
gitsync sync --config config.yaml --proxy-ca /path/to/proxy-ca.crt
```

#### 3. PAC Script Not Working

```bash
# Download and test PAC script manually
curl http://proxy.company.com/proxy.pac -o proxy.pac
gitsync test-pac --pac-file proxy.pac --test-url https://github.com

# Use PAC script directly
gitsync sync --pac-file ./proxy.pac
```

#### 4. Proxy Timeout

```yaml
network:
  proxy:
    http: http://proxy:8080
    
    timeouts:
      connect: 30     # Connection timeout
      read: 60        # Read timeout
      total: 300      # Total request timeout
```

## Best Practices

### 1. Use Environment Variables for Credentials

```bash
# .env file (don't commit!)
export PROXY_USER=john.doe
export PROXY_PASS=secret123

# config.yaml (safe to commit)
network:
  proxy:
    auth:
      username: ${PROXY_USER}
      password: ${PROXY_PASS}
```

### 2. Test Proxy Configuration

```bash
# Always test before production use
gitsync validate --config config.yaml --check-network
```

### 3. Document Proxy Requirements

```yaml
# Add comments to configuration
network:
  proxy:
    # Company proxy (required for external access)
    # Contact: it-support@company.com
    http: http://proxy.company.com:8080
    
    # Bypass internal resources
    no_proxy:
      - .company.internal  # Internal domains
      - 10.0.0.0/8         # Corporate network
```

### 4. Monitor Proxy Performance

```bash
# Enable metrics
gitsync sync --config config.yaml --metrics

# Check proxy latency
gitsync benchmark-proxy --proxy http://proxy:8080
```

## Next Steps

- [Configure SSL certificates](ssl-certificates.md)
- [Set up for corporate environment](corporate-setup.md)
- [Troubleshoot proxy issues](../troubleshooting/proxy-issues.md)
- [Learn about authentication](authentication.md)