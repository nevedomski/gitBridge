# SSL Certificates

How to handle TLS verification in corporate environments.

## Windows auto-detection

On Windows, GitBridge can export trusted certificates from the Windows store and merge them with certifi.

```bash
gitbridge sync --config config.yaml --auto-cert
```

This sets up `requests` to trust both system and custom authorities.

## Custom CA bundle

Provide a path to a PEM bundle via config:

```yaml
sync:
	verify_ssl: /path/to/company-ca-bundle.pem
```

Or disable verification as a last resort (not recommended):

```bash
gitbridge sync --config config.yaml --no-verify-ssl
```

## Troubleshooting

- Verify the bundle has the full chain (root + intermediates)
- Check file permissions and path
- Try `--no-verify-ssl` to isolate certificate vs network issues (then revert)

See also: [Proxy Configuration](proxy-configuration.md) and [SSL errors](../troubleshooting/ssl-errors.md).
