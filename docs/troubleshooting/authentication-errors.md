# Authentication Errors

Common: 401 Unauthorized, 403 Requires authentication, or token scope issues.

## Verify token

```bash
echo "$GITHUB_TOKEN" | wc -c   # length (should be ~40+)
```

Token needs repo read access for private repos. Generate at: <https://github.com/settings/tokens>

## Use env var

```bash
export GITHUB_TOKEN=ghp_xxx
gitbridge sync --repo https://github.com/org/private --local ./repo
```

## Rate limits

```bash
gitbridge status --show-rate-limit
```

If near zero, wait for reset or use a different token.
