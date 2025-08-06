# Authentication Guide

GitBridge supports multiple authentication methods for accessing GitHub repositories. This guide covers how to set up and manage authentication securely.

## Authentication Methods

### 1. Personal Access Token (Recommended)

Personal Access Tokens (PATs) are the recommended authentication method for GitBridge.

#### Creating a Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Click "Generate new token" (classic or fine-grained)
3. Set expiration and select scopes:
   - For public repos: `public_repo`
   - For private repos: `repo` (full control)
   - For organizations: `read:org` (if needed)
4. Generate and copy the token

#### Using the Token

**Environment Variable (Recommended):**

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
gitbridge sync --repo https://github.com/user/repo --local ~/projects/repo
```

**Configuration File:**

```yaml
auth:
  token: ${GITHUB_TOKEN}  # References environment variable
```

**Command Line (Not Recommended):**

```bash
gitbridge sync --token ghp_xxxxxxxxxxxxxxxxxxxx ...
```

### 2. GitHub App Installation Token

For organization-wide access, use GitHub App installation tokens.

```yaml
auth:
  app_id: 123456
  installation_id: 789012
  private_key_path: /path/to/private-key.pem
```

### 3. Anonymous Access

Public repositories can be accessed without authentication:

```bash
gitbridge sync --repo https://github.com/torvalds/linux --local ~/linux
```

**Note:** Anonymous access has lower rate limits (60 requests/hour vs 5000 for authenticated).

### 4. Browser Authentication

The browser sync method can use session-based authentication:

```yaml
sync:
  method: browser

browser:
  # Browser will prompt for login if needed
  headless: false  # Show browser for manual login
```

## Security Best Practices

### 1. Token Storage

**DO:**
- Use environment variables
- Use secret management tools
- Use GitHub's built-in secrets (for Actions)
- Rotate tokens regularly

**DON'T:**
- Commit tokens to version control
- Share tokens between users
- Use tokens in URLs
- Log tokens

### 2. Token Permissions

Use minimal required permissions:

| Repository Type | Required Scope | Permissions |
|----------------|---------------|-------------|
| Public | `public_repo` | Read public repositories |
| Private | `repo` | Full control of private repositories |
| Organization | `read:org` | Read organization data |
| Workflow | `workflow` | Update GitHub Actions |

### 3. Token Rotation

Implement regular token rotation:

```bash
# Script for token rotation
#!/bin/bash

# Generate new token via GitHub API
NEW_TOKEN=$(gh auth token)

# Update environment
export GITHUB_TOKEN=$NEW_TOKEN

# Update secret store
echo $NEW_TOKEN | secret-tool store --label="GitHub Token" service github

# Test new token
gitbridge validate --config config.yaml
```

## Environment-Specific Setup

### Local Development

Use a `.env` file (add to `.gitignore`):

```bash
# .env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_USERNAME=your-username
```

Load in shell:

```bash
source .env
gitbridge sync --config config.yaml
```

### CI/CD Pipelines

#### GitHub Actions

```yaml
# .github/workflows/sync.yml
name: Sync Repository
on:
  schedule:
    - cron: '0 0 * * *'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Sync Repository
        env:
          GITHUB_TOKEN: ${{ secrets.SYNC_TOKEN }}
        run: |
          pip install gitbridge
          gitbridge sync --config config.yaml
```

#### Jenkins

```groovy
pipeline {
    agent any
    environment {
        GITHUB_TOKEN = credentials('github-token')
    }
    stages {
        stage('Sync') {
            steps {
                sh 'gitbridge sync --config config.yaml'
            }
        }
    }
}
```

#### GitLab CI

```yaml
# .gitlab-ci.yml
sync:
  script:
    - export GITHUB_TOKEN=$GITHUB_TOKEN
    - gitbridge sync --config config.yaml
  variables:
    GITHUB_TOKEN: $GITHUB_TOKEN
```

### Docker Containers

```dockerfile
# Dockerfile
FROM python:3.11-slim

RUN pip install gitbridge

# Use build args for tokens (don't bake into image)
ARG GITHUB_TOKEN
ENV GITHUB_TOKEN=$GITHUB_TOKEN

CMD ["gitbridge", "sync", "--config", "/config/config.yaml"]
```

Build and run:

```bash
docker build --build-arg GITHUB_TOKEN=$GITHUB_TOKEN -t gitbridge .
docker run -e GITHUB_TOKEN=$GITHUB_TOKEN gitbridge
```

### Kubernetes Secrets

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: github-token
type: Opaque
data:
  token: Z2hwX3h4eHh4eHh4eHh4  # base64 encoded

---
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gitbridge
spec:
  template:
    spec:
      containers:
      - name: gitbridge
        image: gitbridge:latest
        env:
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: github-token
              key: token
```

## Authentication for Different Sync Methods

### API Method

The API method requires a token for private repositories:

```yaml
sync:
  method: api

auth:
  token: ${GITHUB_TOKEN}
```

### Browser Method

The browser method can work with or without tokens:

**With Token (Automated):**

```yaml
sync:
  method: browser

auth:
  token: ${GITHUB_TOKEN}  # Used for API validation

browser:
  headless: true
```

**Without Token (Manual Login):**

```yaml
sync:
  method: browser

browser:
  headless: false  # Shows browser for manual login
  user_data_dir: ~/.gitbridge/browser  # Saves session
```

## Rate Limits

GitHub enforces rate limits based on authentication:

| Authentication | Rate Limit | Reset |
|---------------|------------|-------|
| Anonymous | 60 requests/hour | Hourly |
| Personal Token | 5,000 requests/hour | Hourly |
| GitHub App | 5,000-15,000 requests/hour | Hourly |

Check rate limit status:

```bash
# Using curl
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# Using GitBridge
gitbridge status --show-rate-limit
```

## Multi-Account Setup

Configure multiple accounts using profiles:

```yaml
# ~/.gitbridge/profiles/personal.yaml
auth:
  token: ${PERSONAL_GITHUB_TOKEN}

# ~/.gitbridge/profiles/work.yaml
auth:
  token: ${WORK_GITHUB_TOKEN}
```

Use profiles:

```bash
# Personal account
GITHUB_TOKEN=$PERSONAL_TOKEN gitbridge sync --config personal.yaml

# Work account
GITHUB_TOKEN=$WORK_TOKEN gitbridge sync --config work.yaml
```

## OAuth App Authentication

For OAuth applications:

```python
from gitbridge import GitHubAPISync

# OAuth token from your app
oauth_token = get_oauth_token()

sync = GitHubAPISync(
    repo_url="https://github.com/user/repo",
    local_path="/path/to/local",
    token=oauth_token
)

sync.sync()
```

## Troubleshooting Authentication

### Common Issues

#### 1. Invalid Token

**Error:** `401 Unauthorized`

**Solution:**
```bash
# Verify token
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user

# Check token scopes
curl -I -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user | grep x-oauth-scopes
```

#### 2. Insufficient Permissions

**Error:** `403 Forbidden`

**Solution:**
- Check token scopes match repository requirements
- For private repos, ensure `repo` scope
- For org repos, may need `read:org`

#### 3. Token Expired

**Error:** `401 Bad credentials`

**Solution:**
- Generate new token
- Update environment variables
- Consider using tokens without expiration for automation

#### 4. Rate Limit Exceeded

**Error:** `403 API rate limit exceeded`

**Solution:**
```bash
# Check rate limit
gitbridge status --show-rate-limit

# Wait for reset or use different token
```

### Debug Authentication

Enable debug logging to troubleshoot:

```bash
gitbridge sync --config config.yaml -v --log-level DEBUG
```

This shows:
- Token validation attempts
- API requests with headers (tokens are masked)
- Rate limit information
- Authentication errors

## Two-Factor Authentication (2FA)

If 2FA is enabled on your GitHub account:

1. **Personal Access Tokens** work normally (recommended)
2. **Password authentication** won't work for API
3. **Browser method** handles 2FA during manual login

## Enterprise GitHub

For GitHub Enterprise Server:

```yaml
repository:
  url: https://github.company.com/user/repo
  api_url: https://github.company.com/api/v3  # Custom API endpoint

auth:
  token: ${GITHUB_ENTERPRISE_TOKEN}

network:
  ssl:
    verify: true
    ca_bundle: /path/to/company-ca.crt
```

## Token Security Checklist

- [ ] Token stored in environment variable or secret manager
- [ ] Token has minimal required permissions
- [ ] Token rotation schedule in place
- [ ] Token not in version control
- [ ] Token not in logs or error messages
- [ ] Different tokens for different environments
- [ ] Token expiration set appropriately
- [ ] Monitoring for token usage/abuse
- [ ] Backup authentication method available
- [ ] Documentation for token generation process

## Next Steps

- [Configure sync methods](sync-methods.md)
- [Set up for corporate environment](corporate-setup.md)
- [Configure proxy settings](proxy-configuration.md)
- [Troubleshoot authentication issues](../troubleshooting/authentication-errors.md)