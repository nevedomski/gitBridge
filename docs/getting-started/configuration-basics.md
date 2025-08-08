# Configuration Basics

A quick guide to the minimum config you need, common options, and how env variables expand.

## Minimal config.yaml

```yaml
repository:
  url: https://github.com/user/repo
  ref: main

local:
  path: ./repo

auth:
  token: ${GITHUB_TOKEN}   # optional for public repos

sync:
  method: api              # api | browser
  incremental: true        # faster subsequent syncs
```

Run it:

```bash
gitbridge sync --config config.yaml
```

## Environment variables

Values like `${HOME}` and `${GITHUB_TOKEN}` expand at runtime.

```yaml
local:
  path: ${HOME}/projects/repo

auth:
  token: ${GITHUB_TOKEN}
```

Set them in your shell:

```bash
export GITHUB_TOKEN=ghp_xxx
```

## Common options

```yaml
sync:
  method: api        # prefer api; fallback to browser
  incremental: true  # only changed files
  # auto_proxy: true # detect proxy from PAC (Windows)
  # auto_cert: true  # detect certificates (Windows)
```

## CLI vs file

Anything in the file can be provided via CLI:

```bash
gitbridge sync --repo https://github.com/user/repo --local ./repo --ref main
```

Next: full [Configuration guide](../user-guide/configuration.md) and [Authentication](../user-guide/authentication.md).
