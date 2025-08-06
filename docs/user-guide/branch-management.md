# Branch Management Guide

GitSync provides flexible options for synchronizing specific branches, tags, or commits from your GitHub repository. This guide covers all aspects of managing different repository references.

## Understanding References

### Reference Types

GitSync supports three types of Git references:

| Type | Format | Example | Use Case |
|------|--------|---------|----------|
| **Branch** | Branch name | `main`, `develop` | Track ongoing development |
| **Tag** | Tag name | `v1.0.0`, `release-2.0` | Sync specific releases |
| **Commit** | SHA hash | `abc123def456` | Pin to exact state |

### Default Behavior

If no reference is specified, GitSync uses these defaults in order:

1. `main` branch
2. `master` branch (if `main` doesn't exist)
3. Repository's default branch

## Specifying References

### Configuration File

```yaml
repository:
  url: https://github.com/user/repo
  ref: develop  # Branch name
  # ref: v1.2.3  # Tag
  # ref: abc123def456  # Commit SHA
```

### Command Line

```bash
# Sync specific branch
gitsync sync --repo https://github.com/user/repo \
             --local ~/projects/repo \
             --ref develop

# Sync specific tag
gitsync sync --repo https://github.com/user/repo \
             --local ~/projects/repo \
             --ref v1.2.3

# Sync specific commit
gitsync sync --repo https://github.com/user/repo \
             --local ~/projects/repo \
             --ref abc123def456789
```

### Python API

```python
from gitsync.api_sync import GitHubAPISync

# Sync branch
sync = GitHubAPISync(repo_url, local_path)
sync.sync(ref="develop")

# Sync tag
sync.sync(ref="v1.2.3")

# Sync commit
sync.sync(ref="abc123def456789")
```

## Working with Branches

### Listing Available Branches

```bash
# List all branches
gitsync list-branches --repo https://github.com/user/repo

# Output:
# Available branches:
#   * main (default)
#   - develop
#   - feature/new-feature
#   - hotfix/urgent-fix
```

### Switching Branches

```bash
# Switch to different branch
gitsync sync --config config.yaml --ref feature/new-feature

# This will:
# 1. Fetch the new branch
# 2. Update local files to match
# 3. Update metadata for tracking
```

### Branch Tracking

GitSync tracks which branch you're syncing:

```json
// .gitsync/metadata.json
{
  "repository": {
    "url": "https://github.com/user/repo",
    "ref": "develop",
    "resolved_sha": "abc123def456",
    "ref_type": "branch"
  }
}
```

### Protected Branches

For protected branches requiring authentication:

```yaml
repository:
  ref: protected-branch

auth:
  token: ${GITHUB_TOKEN}  # Token needs appropriate permissions
```

## Working with Tags

### Listing Tags

```bash
# List all tags
gitsync list-tags --repo https://github.com/user/repo

# List tags with pattern
gitsync list-tags --repo https://github.com/user/repo --pattern "v*"

# Output:
# Available tags:
#   - v2.0.0 (latest)
#   - v1.2.3
#   - v1.2.2
#   - v1.2.1
```

### Syncing Release Tags

```yaml
# Sync specific release
repository:
  ref: v1.2.3

# Always sync latest tag
repository:
  ref: latest  # Special keyword for latest tag
```

### Semantic Version Support

```python
from gitsync import GitHubAPISync

# Sync latest v1.x release
sync = GitHubAPISync(repo_url, local_path)
latest_v1 = sync.get_latest_tag(pattern="v1.*")
sync.sync(ref=latest_v1)
```

## Working with Commits

### Specifying Commits

```bash
# Full SHA
gitsync sync --ref abc123def456789012345678901234567890abcd

# Short SHA (minimum 7 characters)
gitsync sync --ref abc123d
```

### Finding Commits

```bash
# Get latest commit on branch
gitsync show-ref --repo https://github.com/user/repo --ref main

# Output:
# Reference: main
# Type: branch
# SHA: abc123def456789012345678901234567890abcd
# Author: John Doe
# Date: 2025-01-20 10:30:00
# Message: Fix critical bug
```

### Pinning to Commits

Use commits for reproducible syncs:

```yaml
# Dockerfile example
FROM python:3.11
RUN pip install gitsync
RUN gitsync sync \
    --repo https://github.com/user/repo \
    --local /app \
    --ref abc123def456  # Pin to specific commit
```

## Advanced Reference Management

### Dynamic Reference Resolution

```python
from gitsync.repository_manager import RepositoryManager
from gitsync.api_client import GitHubAPIClient

# Create managers
client = GitHubAPIClient(session, repo_url)
repo_mgr = RepositoryManager(client, repo_url)

# Resolve reference to SHA
sha = repo_mgr.resolve_ref("main")
print(f"main branch is at: {sha}")

# Check if reference exists
if repo_mgr.ref_exists("v1.0.0"):
    print("Tag v1.0.0 exists")

# Get reference type
ref_type = repo_mgr.get_ref_type("develop")
print(f"'develop' is a {ref_type}")  # Output: 'develop' is a branch
```

### Reference Patterns

```yaml
# Configuration with patterns
repository:
  ref_pattern: "release-*"  # Sync latest matching tag
  ref_type: tag             # Specify type for pattern matching
```

### Automatic Updates

```yaml
# Auto-update to latest commit on branch
sync:
  auto_update: true
  update_interval: 3600  # Check every hour

repository:
  ref: main
  follow_ref: true  # Follow branch updates
```

## Multi-Reference Workflows

### Syncing Multiple Branches

```bash
#!/bin/bash
# Sync multiple branches to different directories

branches=("main" "develop" "staging")

for branch in "${branches[@]}"; do
    gitsync sync \
        --repo https://github.com/user/repo \
        --local ~/projects/repo-$branch \
        --ref $branch
done
```

### Environment-Based References

```yaml
# development.yaml
repository:
  ref: develop

# staging.yaml
repository:
  ref: staging

# production.yaml
repository:
  ref: main
```

Use based on environment:

```bash
ENV=${ENV:-development}
gitsync sync --config ${ENV}.yaml
```

### A/B Testing Setup

```python
import random
from gitsync import GitHubAPISync

# A/B test between branches
branch = random.choice(['feature-a', 'feature-b'])
sync = GitHubAPISync(repo_url, f"/deploy/{branch}")
sync.sync(ref=branch)
```

## Reference Validation

### Checking Reference Validity

```bash
# Validate reference before sync
gitsync validate-ref \
    --repo https://github.com/user/repo \
    --ref feature/new-feature

# Output:
# ✓ Reference 'feature/new-feature' is valid
# Type: branch
# SHA: abc123def456
# Last updated: 2 hours ago
```

### Handling Invalid References

```python
from gitsync.exceptions import InvalidRefError

try:
    sync.sync(ref="non-existent-branch")
except InvalidRefError as e:
    print(f"Invalid reference: {e}")
    # Fallback to default
    sync.sync(ref="main")
```

## Performance Considerations

### Reference Caching

```yaml
cache:
  cache_refs: true
  ref_ttl: 300  # Cache references for 5 minutes
```

### Shallow Syncs

For large repositories, use shallow syncs:

```yaml
sync:
  shallow: true
  depth: 1  # Only get latest commit
```

### Reference-Specific Optimization

```yaml
# Different settings per reference type
optimization:
  branches:
    incremental: true
    cache_ttl: 300
  tags:
    incremental: false  # Full sync for tags
    cache_ttl: 86400   # Cache tags for 24 hours
  commits:
    incremental: false
    cache_ttl: -1      # Cache forever (commits don't change)
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/sync.yml
name: Sync Repository
on:
  push:
    branches: [main, develop]
    tags: ['v*']

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Determine ref
        id: ref
        run: echo "REF=${GITHUB_REF#refs/*/}" >> $GITHUB_OUTPUT
      
      - name: Sync repository
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          pip install gitsync
          gitsync sync \
            --repo ${{ github.repository }} \
            --local ./repo \
            --ref ${{ steps.ref.outputs.REF }}
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    parameters {
        choice(
            name: 'BRANCH',
            choices: ['main', 'develop', 'staging'],
            description: 'Branch to sync'
        )
    }
    stages {
        stage('Sync') {
            steps {
                sh """
                    gitsync sync \
                        --repo https://github.com/user/repo \
                        --local ./repo \
                        --ref ${params.BRANCH}
                """
            }
        }
    }
}
```

## Troubleshooting

### Common Issues

#### Reference Not Found

**Error**: `Reference 'feature/xyz' not found`

**Solutions**:
```bash
# Check if reference exists
gitsync list-branches --repo https://github.com/user/repo | grep xyz

# Use full reference name
gitsync sync --ref refs/heads/feature/xyz
```

#### Ambiguous Reference

**Error**: `Reference 'release' is ambiguous`

**Solutions**:
```yaml
# Specify reference type
repository:
  ref: release
  ref_type: branch  # or 'tag'
```

#### Access Denied to Branch

**Error**: `403 Forbidden accessing branch 'protected'`

**Solutions**:
```bash
# Ensure token has appropriate permissions
gitsync validate --config config.yaml --check-auth

# Check branch protection rules on GitHub
```

### Debug Reference Resolution

```bash
# Enable debug logging for references
GITSYNC_DEBUG=refs gitsync sync --config config.yaml -v

# Trace reference resolution
gitsync sync --config config.yaml --trace-refs
```

## Best Practices

### 1. Use Semantic Versioning for Tags

```bash
# Good tag names
v1.0.0
v2.1.3-beta
release-2025.01.20

# Avoid
version1
final
latest-working
```

### 2. Document Reference Strategy

```yaml
# Add comments explaining reference choice
repository:
  # We track 'develop' for integration testing
  # Production uses 'main' branch
  ref: develop
```

### 3. Implement Reference Policies

```python
# Enforce reference policies
ALLOWED_BRANCHES = ['main', 'develop', 'staging']

def validate_ref(ref):
    if ref not in ALLOWED_BRANCHES:
        raise ValueError(f"Branch {ref} not allowed in production")
```

### 4. Monitor Reference Changes

```bash
# Set up notifications for reference updates
gitsync watch \
    --repo https://github.com/user/repo \
    --ref main \
    --notify-on-change
```

## Next Steps

- [Configure incremental sync](incremental-sync.md)
- [Set up authentication](authentication.md)
- [Learn about sync methods](sync-methods.md)
- [Automate with CI/CD](../cli/index.md)