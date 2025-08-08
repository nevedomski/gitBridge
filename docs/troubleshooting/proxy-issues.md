# Proxy Issues

## Auto-detect (Windows)

```bash
gitbridge sync --config config.yaml --auto-proxy
```

## Manual proxy

```bash
gitbridge sync --repo https://github.com/user/repo --local ./repo --proxy http://user:pass@proxy.company.com:8080
```

## Env vars

```bash
export HTTPS_PROXY=http://proxy.company.com:8080
export HTTP_PROXY=http://proxy.company.com:8080
```

If both CLI and env are set, CLI takes precedence.
