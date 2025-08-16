# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.6.x   | :white_check_mark: |
| 0.5.x   | :x:                |
| < 0.5   | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities by emailing info@nevedomski.us or by opening a private security advisory on GitHub.

**Do not open public issues for security vulnerabilities.**

Include the following information:
- Type of issue and affected component
- Steps to reproduce the vulnerability
- Potential impact and exploitation scenarios
- Any proof-of-concept code

## Security Updates - Version 0.6.3b1 (2025-08-16)

### ✅ Fixed Critical Security Issues

All previously identified security vulnerabilities have been fixed in version 0.6.3b1:

#### 1. Path Traversal Vulnerability - FIXED ✅

- **Previous Location**: `gitbridge/file_synchronizer.py:268-289`
- **Fix**: Implemented `validate_safe_path()` function that validates all file paths
- **Protection**: Prevents "../" sequences and absolute paths from escaping the sync directory
- **Testing**: Comprehensive tests in `test_security.py`

#### 2. Proxy URL Validation - FIXED ✅

- **Previous Location**: `gitbridge/browser_sync.py:118-135`
- **Fix**: Added `validate_proxy_url()` function with comprehensive validation
- **Protection**: Validates schemes, hostnames, ports, and rejects control characters
- **Testing**: Multiple test cases for malicious URLs

#### 3. Race Condition in Certificate Cleanup - FIXED ✅

- **Previous Location**: `gitbridge/cert_support.py:19-28`
- **Fix**: Implemented thread-safe `CertificateManager` with locking
- **Protection**: Uses `threading.Lock` to prevent race conditions
- **Testing**: Thread-safety tests with concurrent operations

#### 4. Request Size Limits - IMPLEMENTED ✅

- **New Feature**: Added configurable download size limits
- **Protection**: Prevents DoS attacks via large file downloads
- **Default Limits**: 100MB per file, 500MB total, with streaming for files >10MB
- **Configuration**: Customizable via `download_limits` config section

## Security Best Practices

When using GitBridge in corporate environments:

### Authentication

- Store tokens in environment variables, never in code
- Use read-only tokens when possible
- Rotate tokens regularly
- Never commit tokens to version control

### Network Security

- Verify SSL certificates (default behavior)
- Use trusted proxy servers only
- Validate proxy URLs before configuration
- Monitor network activity for anomalies

### File System Security

- Sync to dedicated directories only
- Regularly review synced content
- Set appropriate file permissions
- Avoid syncing to system directories

### Repository Trust

- Only sync from trusted repositories
- Review repository content before syncing
- Use specific commit/tag references when possible
- Avoid syncing from public forks without review

## Security Features

GitBridge includes several security features:

- **SSL/TLS Verification**: Validates certificates by default
- **Token Management**: Supports secure token storage via environment variables
- **Corporate Certificate Support**: Integrates with Windows certificate store
- **Proxy Authentication**: Supports authenticated proxy connections
- **No Credential Storage**: Never stores credentials in configuration files

## Security Implementation Status

### Completed (v0.6.3b1)
- [x] Path traversal protection with strict validation
- [x] Input sanitization for proxy URLs and file paths
- [x] Request size limits to prevent DoS
- [x] Thread-safe certificate management

### Planned Enhancements
- [ ] Rate limiting with exponential backoff
- [ ] Audit logging for security events
- [ ] Content-type validation for API responses
- [ ] SAML/SSO authentication support

## Security Audit

Last security review: 2025-08-16 (v0.6.3b1 security fixes)

Next scheduled review: 2025-09-16

## Contact

For security concerns, please contact the maintainers through GitHub security advisories.