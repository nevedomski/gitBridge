# SSL / Certificate Errors

## Quick fixes

```bash
# Temporary (not recommended)
gitbridge sync --config config.yaml --no-verify-ssl

# Prefer supplying bundle
gitbridge sync --config config.yaml --auto-cert   # Windows
```

## Verify bundle works

```bash
openssl verify -CAfile /path/to/company-ca-bundle.pem /path/to/test-cert.pem
```

See also: [SSL Certificates](../user-guide/ssl-certificates.md).
