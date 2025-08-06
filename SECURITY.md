# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.4.x   | :white_check_mark: |
| < 0.4   | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities by opening a private security advisory on GitHub or by emailing the maintainers directly. 

**Do not open public issues for security vulnerabilities.**

## Known Security Issues

The following security issues have been identified and are being addressed:

### Critical Issues (Fix in Progress)

#### 1. Path Traversal Vulnerability

- **Location**: `gitbridge/file_synchronizer.py:268-289`
- **Impact**: High - Malicious repository content could write files outside the intended sync directory
- **Status**: Fix in development
- **Mitigation**: Avoid syncing untrusted repositories until patched

#### 2. Insufficient Proxy URL Validation

- **Location**: `gitbridge/browser_sync.py:118-135`
- **Impact**: Medium - Malformed proxy URLs could cause credential leakage
- **Status**: Fix in development
- **Mitigation**: Validate proxy URLs before use

#### 3. Race Condition in Certificate Cleanup

- **Location**: `gitbridge/cert_support.py:19-28`
- **Impact**: Low - Could lead to incomplete cleanup in concurrent scenarios
- **Status**: Fix in development
- **Mitigation**: Single-threaded operation recommended

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

## Upcoming Security Enhancements

- [ ] Path traversal protection with strict validation
- [ ] Input sanitization for all user inputs
- [ ] Request size limits to prevent DoS
- [ ] Rate limiting with exponential backoff
- [ ] Audit logging for security events
- [ ] Content-type validation for API responses

## Security Audit

Last security review: 2025-08-06

Next scheduled review: 2025-09-06

## Contact

For security concerns, please contact the maintainers through GitHub security advisories.