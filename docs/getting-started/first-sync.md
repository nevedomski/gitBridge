# Your First Sync

This guide will walk you through your first repository synchronization with GitBridge. By the end, you'll have successfully synced a GitHub repository to your local machine.

## Prerequisites

Before starting, ensure you have:

- GitBridge installed ([Installation Guide](installation.md))
- Internet access to GitHub
- A GitHub repository URL to sync

## Step 1: Choose a Repository

For this tutorial, we'll use a public repository. You can also use your own:

```bash
# Example public repository
REPO_URL="https://github.com/github/gitignore"

# Or use your own repository
REPO_URL="https://github.com/yourusername/yourrepo"
```

## Step 2: Basic Sync Command

The simplest way to sync a repository:

```bash
gitbridge sync --repo $REPO_URL --local ./my-first-sync
```

This command will:
1. Connect to the GitHub repository
2. Download all files to `./my-first-sync` directory
3. Show progress during the sync
4. Save metadata for future incremental syncs

### Expected Output

```
GitBridge v0.2.0 - GitHub Repository Synchronization Tool
========================================================

Connecting to: https://github.com/github/gitignore
Local path: ./my-first-sync
Method: API
Reference: main

Fetching repository information... ✓
Resolving reference... ✓
Fetching file tree... ✓

Syncing files:
  Downloading: Python.gitignore [████████████] 100%
  Downloading: Node.gitignore [████████████] 100%
  Downloading: Java.gitignore [████████████] 100%
  ... more files ...

Sync completed successfully!
  Files synced: 234
  Total size: 456.7 KB
  Duration: 5.2 seconds
```

## Step 3: Verify the Sync

Check that files were downloaded:

```bash
# List the synced files
ls -la my-first-sync/

# Count the files
find my-first-sync -type f | wc -l

# Check the GitBridge metadata
ls -la my-first-sync/.gitbridge/
```

## Step 4: Try Incremental Sync

Run the same command again to see incremental sync in action:

```bash
gitbridge sync --repo $REPO_URL --local ./my-first-sync
```

### Expected Output (Incremental)

```
GitBridge v0.2.0 - GitHub Repository Synchronization Tool
========================================================

Connecting to: https://github.com/github/gitignore
Local path: ./my-first-sync
Method: API (Incremental)
Reference: main

Loading cached metadata... ✓
Checking for changes... ✓

No changes detected. Repository is up to date.

Sync completed successfully!
  Files checked: 234
  Files updated: 0
  Duration: 1.2 seconds
```

## Step 5: Sync a Different Branch

Try syncing a different branch or tag:

```bash
# List available branches
gitbridge list-branches --repo $REPO_URL

# Sync a specific branch
gitbridge sync --repo $REPO_URL --local ./my-branch-sync --ref develop
```

## Private Repository Sync

If you want to sync a private repository, you'll need authentication:

### Step 1: Create a GitHub Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Give it a name like "GitBridge"
4. Select scopes:
   - `repo` for private repositories
   - `public_repo` for public repositories only
5. Generate and copy the token

### Step 2: Use the Token

```bash
# Set token as environment variable (recommended)
export GITHUB_TOKEN="ghp_your_token_here"

# Sync private repository
gitbridge sync \
  --repo https://github.com/yourusername/private-repo \
  --local ./private-sync \
  --token $GITHUB_TOKEN
```

## Using a Configuration File

For repeated syncs, create a configuration file:

### Step 1: Create Configuration

Create `config.yaml`:

```yaml
repository:
  url: https://github.com/github/gitignore
  ref: main

local:
  path: ./my-configured-sync

sync:
  method: api
  incremental: true

logging:
  level: INFO
  console: true
```

### Step 2: Run with Configuration

```bash
gitbridge sync --config config.yaml
```

## Advanced First Sync Options

### Verbose Output

See detailed information during sync:

```bash
gitbridge sync --repo $REPO_URL --local ./verbose-sync --verbose
```

### Dry Run

See what would be synced without actually downloading:

```bash
gitbridge sync --repo $REPO_URL --local ./dry-run-test --dry-run
```

### Specific File Types

Sync only certain files:

```bash
# Create configuration with filters
cat > filtered-sync.yaml << EOF
repository:
  url: $REPO_URL

local:
  path: ./filtered-sync

sync:
  ignore_patterns:
    - "*.md"      # Skip markdown files
    - "docs/*"    # Skip docs directory
    - "*.test.*"  # Skip test files
EOF

gitbridge sync --config filtered-sync.yaml
```

## Troubleshooting Your First Sync

### Common Issues and Solutions

#### 1. "Repository not found"

```bash
# Check the URL is correct
curl -I https://github.com/username/repo

# For private repos, ensure token has access
gitbridge validate --repo $REPO_URL --token $GITHUB_TOKEN
```

#### 2. "Permission denied" for local directory

```bash
# Check directory permissions
ls -la ./

# Create directory with proper permissions
mkdir -p my-first-sync
chmod 755 my-first-sync
```

#### 3. "Rate limit exceeded"

```bash
# Check your rate limit
gitbridge status --show-rate-limit

# Use authentication to increase limits
export GITHUB_TOKEN="your_token"
gitbridge sync --repo $REPO_URL --local ./my-sync
```

#### 4. Network timeout

```bash
# Increase timeout and retry settings
gitbridge sync \
  --repo $REPO_URL \
  --local ./my-sync \
  --timeout 60 \
  --retry-count 5
```

## What's Next?

Now that you've completed your first sync:

### Learn More About:

1. **[Configuration](configuration-basics.md)** - Set up configuration files
2. **[Incremental Sync](../user-guide/incremental-sync.md)** - Understand how updates work
3. **[Authentication](../user-guide/authentication.md)** - Set up secure access
4. **[Sync Methods](../user-guide/sync-methods.md)** - API vs Browser methods

### Try These Exercises:

1. **Sync Multiple Repositories**
   ```bash
   for repo in repo1 repo2 repo3; do
     gitbridge sync --repo https://github.com/user/$repo --local ./$repo
   done
   ```

2. **Schedule Regular Syncs**
   ```bash
   # Add to crontab for hourly syncs
   0 * * * * gitbridge sync --config ~/gitbridge/config.yaml
   ```

3. **Sync Specific Tags**
   ```bash
   # Sync a release version
   gitbridge sync --repo $REPO_URL --local ./release --ref v1.0.0
   ```

4. **Compare Sync Methods**
   ```bash
   # Time API method
   time gitbridge sync --repo $REPO_URL --local ./api-sync --method api
   
   # Time Browser method
   time gitbridge sync --repo $REPO_URL --local ./browser-sync --method browser
   ```

## Quick Reference Card

Keep these commands handy:

```bash
# Basic sync
gitbridge sync --repo URL --local PATH

# With authentication
gitbridge sync --repo URL --local PATH --token TOKEN

# Specific branch/tag
gitbridge sync --repo URL --local PATH --ref BRANCH

# Using config file
gitbridge sync --config config.yaml

# Verbose mode
gitbridge sync --config config.yaml -v

# Dry run
gitbridge sync --config config.yaml --dry-run

# Force full sync
gitbridge sync --config config.yaml --force

# Check status
gitbridge status --config config.yaml

# Validate setup
gitbridge validate --config config.yaml
```

## Success Checklist

- [x] Successfully synced your first repository
- [x] Verified files were downloaded correctly
- [x] Tested incremental sync
- [x] Understood basic command options
- [ ] Created your own configuration file
- [ ] Set up authentication (if needed)
- [ ] Scheduled automated syncs (optional)

Congratulations! You've successfully completed your first sync with GitBridge. You're now ready to explore more advanced features and customize GitBridge for your workflow.