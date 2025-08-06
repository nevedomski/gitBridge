# API Reference

Welcome to the GitSync API Reference. This documentation covers the Python API for programmatic use of GitSync.

## Overview

GitSync provides a comprehensive Python API for integrating repository synchronization into your applications. The API is designed to be simple for basic use cases while providing advanced features for complex scenarios.

## Quick Start

```python
from gitsync.api_sync import GitHubAPISync

# Basic synchronization
sync = GitHubAPISync(
    repo_url="https://github.com/user/repo",
    local_path="/path/to/local/repo"
)

# Perform sync
success = sync.sync()
if success:
    print("Synchronization completed successfully")
```

## Core Modules

### [gitsync](gitsync.md)
Main package initialization and version information.

### [api_sync](api_sync.md)
GitHub API-based synchronization with component architecture:
- `GitHubAPISync` - Main facade class
- `GitHubAPIClient` - Low-level API operations
- `RepositoryManager` - Repository metadata management
- `FileSynchronizer` - File synchronization engine
- `ProgressTracker` - Progress reporting

### [browser_sync](browser_sync.md)
Playwright-based browser automation for fallback synchronization:
- `GitHubBrowserSync` - Browser automation sync

### [config](config.md)
Configuration management:
- `Config` - Configuration loader and validator
- `ConfigValidator` - Configuration validation

### [interfaces](interfaces.md)
Abstract interfaces for extensibility:
- `SyncProvider` - Base interface for sync implementations
- `ProxyProvider` - Proxy configuration interface
- `CertificateProvider` - Certificate management interface
- `AuthenticationProvider` - Authentication interface

### [utils](utils.md)
Utility functions:
- Path manipulation
- File operations
- Network utilities
- Progress helpers

### [pac_support](pac_support.md)
PAC (Proxy Auto-Configuration) support:
- `PACProxyDetector` - PAC script detection and parsing
- Windows registry integration

### [cert_support](cert_support.md)
Certificate management:
- `WindowsCertificateDetector` - Windows certificate store access
- Certificate bundle creation

## Basic Usage

### Simple Sync

```python
from gitsync import GitHubAPISync

# Initialize sync client
sync = GitHubAPISync(
    repo_url="https://github.com/torvalds/linux",
    local_path="/home/user/linux-kernel"
)

# Test connection
if sync.test_connection():
    # Perform synchronization
    result = sync.sync(ref="master")
    print(f"Synced successfully: {result}")
else:
    print("Connection failed")
```

### Authenticated Sync

```python
import os
from gitsync import GitHubAPISync

# Using token from environment
token = os.getenv("GITHUB_TOKEN")

sync = GitHubAPISync(
    repo_url="https://github.com/company/private-repo",
    local_path="/path/to/local",
    token=token
)

# Sync with authentication
sync.sync()
```

### Browser-Based Sync

```python
from gitsync.browser_sync import GitHubBrowserSync

# Use browser automation when API is blocked
browser_sync = GitHubBrowserSync(
    repo_url="https://github.com/user/repo",
    local_path="/path/to/local",
    browser_type="chromium",
    headless=True
)

# Perform browser-based sync
browser_sync.sync()
```

## Advanced Usage

### Custom Configuration

```python
from gitsync import GitHubAPISync
from gitsync.config import Config

# Load configuration from file
config = Config.from_file("config.yaml")

# Create sync with configuration
sync = GitHubAPISync(
    repo_url=config.repository.url,
    local_path=config.local.path,
    token=config.auth.token,
    proxy=config.network.proxy,
    verify_ssl=config.network.ssl.verify
)
```

### Progress Callbacks

```python
def progress_callback(current, total, message):
    """Custom progress handler."""
    percent = (current / total) * 100 if total > 0 else 0
    print(f"[{percent:3.0f}%] {message}")

sync = GitHubAPISync(
    repo_url="https://github.com/user/repo",
    local_path="/path/to/local",
    progress_callback=progress_callback
)

sync.sync()
```

### Error Handling

```python
from gitsync import GitHubAPISync
from gitsync.exceptions import (
    AuthenticationError,
    NetworkError,
    RateLimitError,
    RepositoryError
)

sync = GitHubAPISync(repo_url, local_path, token)

try:
    sync.sync()
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Handle authentication error
except RateLimitError as e:
    print(f"Rate limit exceeded. Reset at: {e.reset_time}")
    # Wait or use different token
except NetworkError as e:
    print(f"Network error: {e}")
    # Retry or check connection
except RepositoryError as e:
    print(f"Repository error: {e}")
    # Check repository URL
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Component-Based Architecture

```python
from gitsync.api_client import GitHubAPIClient
from gitsync.repository_manager import RepositoryManager
from gitsync.file_synchronizer import FileSynchronizer
from gitsync.session_factory import SessionFactory

# Create individual components
session_factory = SessionFactory(config)
session = session_factory.create_session()

api_client = GitHubAPIClient(session, repo_url)
repo_manager = RepositoryManager(api_client, repo_url)
file_sync = FileSynchronizer(api_client, local_path)

# Use components directly
if api_client.test_connection():
    sha = repo_manager.resolve_ref("main")
    tree = repo_manager.get_tree(sha)
    file_sync.sync_files(tree)
```

### Custom Sync Provider

```python
from gitsync.interfaces import SyncProvider
from typing import Dict, Any

class CustomSyncProvider(SyncProvider):
    """Custom sync implementation."""
    
    def sync(self, ref: str = "main", show_progress: bool = True) -> bool:
        """Implement custom sync logic."""
        # Your implementation here
        return True
    
    def test_connection(self) -> bool:
        """Test connectivity."""
        # Your implementation here
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get sync status."""
        return {
            "provider_type": "custom",
            "status": "ready"
        }
```

### Proxy Configuration

```python
from gitsync import GitHubAPISync
from gitsync.pac_support import PACProxyDetector

# Auto-detect proxy
detector = PACProxyDetector()
if detector.detect_proxy():
    proxy_config = detector.get_proxy_config("https://github.com")
else:
    proxy_config = None

# Use detected proxy
sync = GitHubAPISync(
    repo_url="https://github.com/user/repo",
    local_path="/path/to/local",
    proxy=proxy_config
)
```

### Certificate Management

```python
from gitsync import GitHubAPISync
from gitsync.cert_support import WindowsCertificateDetector

# Auto-detect certificates (Windows)
cert_detector = WindowsCertificateDetector()
cert_bundle = cert_detector.export_certificates()

# Use custom certificates
sync = GitHubAPISync(
    repo_url="https://github.enterprise.com/repo",
    local_path="/path/to/local",
    verify_ssl=cert_bundle  # Path to certificate bundle
)
```

## Integration Examples

### Flask Web Application

```python
from flask import Flask, jsonify
from gitsync import GitHubAPISync

app = Flask(__name__)

@app.route('/sync/<owner>/<repo>')
def sync_repo(owner, repo):
    """Sync repository endpoint."""
    sync = GitHubAPISync(
        repo_url=f"https://github.com/{owner}/{repo}",
        local_path=f"/repos/{owner}/{repo}"
    )
    
    try:
        success = sync.sync()
        return jsonify({"status": "success" if success else "failed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

### Celery Task

```python
from celery import Celery
from gitsync import GitHubAPISync

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def sync_repository(repo_url, local_path, ref="main"):
    """Async repository sync task."""
    sync = GitHubAPISync(repo_url, local_path)
    return sync.sync(ref=ref)
```

### Scheduled Sync

```python
import schedule
import time
from gitsync import GitHubAPISync

def sync_job():
    """Scheduled sync job."""
    sync = GitHubAPISync(
        repo_url="https://github.com/user/repo",
        local_path="/path/to/local"
    )
    
    if sync.sync():
        print(f"Sync completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("Sync failed")

# Schedule hourly syncs
schedule.every(1).hours.do(sync_job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## API Conventions

### Return Values

- Methods return `True`/`False` for success/failure
- Complex results return dictionaries
- Errors raise exceptions with descriptive messages

### Parameter Naming

- `repo_url` - Full GitHub repository URL
- `local_path` - Local directory path
- `ref` - Git reference (branch/tag/commit)
- `token` - Authentication token
- `show_progress` - Boolean for progress display

### Exception Hierarchy

```
GitSyncError (base)
├── ConfigurationError
├── AuthenticationError
│   └── TokenError
├── NetworkError
│   ├── RateLimitError
│   ├── ProxyError
│   └── SSLError
├── RepositoryError
│   └── InvalidRefError
├── FileSystemError
│   └── PermissionError
└── BrowserError
    └── BrowserNotFoundError
```

## Performance Considerations

### Memory Usage

```python
# Stream large files instead of loading to memory
sync = GitHubAPISync(
    repo_url=repo_url,
    local_path=local_path,
    stream_large_files=True,
    large_file_threshold=52428800  # 50MB
)
```

### Connection Pooling

```python
# Reuse connections for better performance
from gitsync.session_factory import SessionFactory

factory = SessionFactory(config)
session = factory.create_session()

# Session maintains connection pool
sync1 = GitHubAPISync(repo1_url, path1, session=session)
sync2 = GitHubAPISync(repo2_url, path2, session=session)
```

### Parallel Operations

```python
import concurrent.futures
from gitsync import GitHubAPISync

repos = [
    ("https://github.com/user/repo1", "/path/to/repo1"),
    ("https://github.com/user/repo2", "/path/to/repo2"),
    ("https://github.com/user/repo3", "/path/to/repo3"),
]

def sync_repo(repo_url, local_path):
    sync = GitHubAPISync(repo_url, local_path)
    return sync.sync()

# Sync multiple repositories in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(sync_repo, url, path) for url, path in repos]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
```

## Testing

### Unit Testing

```python
import unittest
from unittest.mock import Mock, patch
from gitsync import GitHubAPISync

class TestGitSync(unittest.TestCase):
    @patch('gitsync.api_sync.requests.Session')
    def test_sync(self, mock_session):
        """Test repository sync."""
        # Mock API responses
        mock_response = Mock()
        mock_response.json.return_value = {"sha": "abc123"}
        mock_session.return_value.get.return_value = mock_response
        
        # Test sync
        sync = GitHubAPISync(
            "https://github.com/user/repo",
            "/tmp/test"
        )
        result = sync.sync()
        
        self.assertTrue(result)
```

### Integration Testing

```python
import tempfile
import shutil
from gitsync import GitHubAPISync

def test_real_sync():
    """Integration test with real repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sync = GitHubAPISync(
            "https://github.com/github/gitignore",
            tmpdir
        )
        
        # Test connection
        assert sync.test_connection()
        
        # Perform sync
        assert sync.sync()
        
        # Verify files exist
        assert os.path.exists(os.path.join(tmpdir, "Python.gitignore"))
```

## Best Practices

1. **Always handle exceptions** - Network operations can fail
2. **Use environment variables for secrets** - Never hardcode tokens
3. **Enable incremental sync** - Reduces bandwidth and time
4. **Implement retry logic** - Handle transient failures
5. **Log operations** - Aid debugging and monitoring
6. **Clean up resources** - Close connections and clean temp files
7. **Validate input** - Check URLs and paths before use
8. **Use type hints** - Improve code maintainability

## Next Steps

- Explore individual [module documentation](api_sync.md)
- Review [interface definitions](interfaces.md)
- Check [examples repository](https://github.com/nevedomski/gitsync-examples)
- Read the [developer guide](../contributing/index.md)