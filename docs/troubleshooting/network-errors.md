# Network Errors

Common networking issues and solutions.
Symptoms: timeouts, connection refused, DNS failures.

## Quick checks

```bash
# GitHub API reachable?
curl -I https://api.github.com

# Corporate proxy set?
printenv | grep -i -E 'http_proxy|https_proxy'

# PAC in effect? (Windows)
# use --auto-proxy in CLI if needed
```

## Try with auto-proxy

```bash
gitbridge sync --config config.yaml --auto-proxy
```

## Validate outside GitBridge

```bash
curl -I https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore
```

If curl fails, fix network/proxy first.
