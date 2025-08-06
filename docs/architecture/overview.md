# Architecture Overview

GitSync is designed with a modular architecture that provides flexibility, reliability, and extensibility. This document provides a comprehensive overview of the system architecture.

## System Architecture

```mermaid
graph TB
    subgraph "User Interface"
        CLI[CLI Interface]
        CONFIG[Configuration Files]
    end
    
    subgraph "Core Components"
        SYNC[Sync Manager]
        API[API Sync Engine]
        BROWSER[Browser Sync Engine]
        CACHE[Cache Manager]
    end
    
    subgraph "Support Modules"
        PROXY[Proxy Handler]
        CERT[Certificate Manager]
        AUTH[Authentication]
        UTILS[Utilities]
    end
    
    subgraph "External Services"
        GITHUB[GitHub API]
        WEB[GitHub Website]
    end
    
    subgraph "Local Storage"
        FILES[Local Files]
        META[Metadata Cache]
    end
    
    CLI --> SYNC
    CONFIG --> SYNC
    SYNC --> API
    SYNC --> BROWSER
    API --> PROXY
    BROWSER --> PROXY
    PROXY --> CERT
    API --> AUTH
    API --> GITHUB
    BROWSER --> WEB
    API --> CACHE
    BROWSER --> CACHE
    CACHE --> META
    SYNC --> FILES
```

## Core Design Principles

### 1. Modularity

Each component has a single, well-defined responsibility:

- **Sync Engines**: Handle the actual synchronization logic
- **Support Modules**: Provide cross-cutting concerns (auth, proxy, SSL)
- **Cache Manager**: Manages metadata and incremental updates
- **CLI**: Provides user interface and orchestration

### 2. Flexibility

GitSync adapts to various environments:

- **Dual sync methods**: API and browser automation
- **Auto-detection**: Proxy and certificate discovery
- **Configuration layers**: Files, environment variables, command-line

### 3. Reliability

Built-in resilience and error handling:

- **Automatic retries**: For transient network failures
- **Fallback mechanisms**: Browser method when API fails
- **Incremental updates**: Resume interrupted syncs
- **Data integrity**: SHA verification for all files

### 4. Performance

Optimized for efficiency:

- **Parallel downloads**: Multiple concurrent file transfers
- **Incremental syncing**: Only transfer changed files
- **Intelligent caching**: Minimize API calls
- **Chunk-based transfers**: For large files

## Component Architecture

### Sync Manager

The central orchestrator that coordinates all sync operations:

```python
class SyncManager:
    """Orchestrates synchronization operations."""
    
    def __init__(self, config: Config):
        self.config = config
        self.sync_engine = self._select_engine()
        self.cache_manager = CacheManager()
    
    def sync(self) -> SyncResult:
        """Execute synchronization."""
        # 1. Validate configuration
        # 2. Select sync method
        # 3. Perform sync
        # 4. Update cache
        # 5. Return results
```

**Responsibilities:**
- Configuration validation
- Sync method selection
- Error handling and recovery
- Progress reporting
- Result aggregation

### API Sync Engine

Implements GitHub API-based synchronization:

```python
class GitHubAPISync:
    """GitHub API synchronization engine."""
    
    def sync(self) -> Dict[str, Any]:
        """Perform API-based sync."""
        # 1. Fetch repository tree
        # 2. Compare with local cache
        # 3. Download changed files
        # 4. Update metadata
```

**Key Features:**
- Tree API for efficient file listing
- Blob API for content retrieval
- Parallel download support
- Rate limit management
- SHA-based change detection

### Browser Sync Engine

Implements browser automation fallback:

```python
class GitHubBrowserSync:
    """Browser-based synchronization engine."""
    
    def sync(self) -> Dict[str, Any]:
        """Perform browser-based sync."""
        # 1. Launch browser
        # 2. Navigate to repository
        # 3. Download ZIP archive
        # 4. Extract and compare
        # 5. Update changed files
```

**Key Features:**
- Selenium WebDriver integration
- Chrome/Chromium support
- Headless mode operation
- Cookie persistence
- JavaScript execution

### Cache Manager

Manages metadata for incremental updates:

```python
class CacheManager:
    """Manages sync metadata and cache."""
    
    def get_file_metadata(self, path: str) -> FileMetadata:
        """Get cached file metadata."""
    
    def update_metadata(self, files: List[FileInfo]):
        """Update cache with new metadata."""
    
    def get_changed_files(self, remote_files: List[FileInfo]) -> List[FileInfo]:
        """Identify changed files."""
```

**Cache Structure:**
```json
{
  "version": "1.0",
  "repository": {
    "url": "https://github.com/user/repo",
    "ref": "main",
    "last_commit": "abc123"
  },
  "files": {
    "README.md": {
      "sha": "def456",
      "size": 1234,
      "modified": "2025-01-15T10:30:00Z"
    }
  },
  "sync": {
    "last_sync": "2025-01-15T10:30:00Z",
    "method": "api"
  }
}
```

## Data Flow

### API Sync Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant APISync
    participant Cache
    participant GitHub
    participant FileSystem
    
    User->>CLI: gitsync sync
    CLI->>APISync: Initialize sync
    APISync->>Cache: Load metadata
    Cache-->>APISync: Previous sync data
    APISync->>GitHub: GET /repos/{owner}/{repo}/git/trees
    GitHub-->>APISync: Repository tree
    APISync->>APISync: Compare SHAs
    APISync->>GitHub: GET /repos/{owner}/{repo}/contents/{path}
    GitHub-->>APISync: File content
    APISync->>FileSystem: Write file
    APISync->>Cache: Update metadata
    APISync-->>CLI: Sync complete
    CLI-->>User: Success message
```

### Browser Sync Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BrowserSync
    participant Browser
    participant GitHub
    participant FileSystem
    
    User->>CLI: gitsync sync --method browser
    CLI->>BrowserSync: Initialize sync
    BrowserSync->>Browser: Launch Chrome
    Browser->>GitHub: Navigate to repository
    BrowserSync->>Browser: Click "Code" → "Download ZIP"
    Browser->>GitHub: Download repository ZIP
    GitHub-->>Browser: ZIP file
    BrowserSync->>BrowserSync: Extract file list from ZIP
    BrowserSync->>FileSystem: Compare with local files
    BrowserSync->>Browser: Download changed files
    Browser->>GitHub: GET individual files
    GitHub-->>Browser: File contents
    BrowserSync->>FileSystem: Write files
    BrowserSync-->>CLI: Sync complete
    CLI-->>User: Success message
```

## Configuration Architecture

### Configuration Layers

Configuration is resolved in priority order:

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Configuration file**
4. **Default values** (lowest priority)

```python
class ConfigResolver:
    """Resolves configuration from multiple sources."""
    
    def resolve(self) -> Config:
        config = self.load_defaults()
        config.merge(self.load_file())
        config.merge(self.load_environment())
        config.merge(self.load_cli_args())
        return config
```

### Configuration Schema

```yaml
# Complete configuration schema
repository:
  url: str              # Required: GitHub repository URL
  ref: str              # Branch, tag, or commit (default: main)

local:
  path: str             # Required: Local directory path

auth:
  token: str            # GitHub personal access token
  username: str         # For basic auth (browser method)
  password: str         # For basic auth (browser method)

sync:
  method: enum          # api, browser, or auto
  incremental: bool     # Enable incremental updates
  force: bool           # Force full sync
  parallel_downloads: int
  chunk_size: int
  retry_count: int
  retry_delay: float
  ignore_patterns: list
  skip_large_files: bool
  large_file_size: int

network:
  proxy:
    http: str
    https: str
    no_proxy: list
    auth:
      username: str
      password: str
  ssl:
    verify: bool
    ca_bundle: str
    cert_file: str
    key_file: str
  pac:
    url: str
    file: str
    cache: bool

browser:
  type: enum            # chrome, chromium, edge
  path: str             # Browser executable path
  driver_path: str      # ChromeDriver path
  headless: bool
  window_size: str
  timeout: int
  download_timeout: int
  user_agent: str
  cookie_file: str
  reuse_session: bool

logging:
  level: enum           # DEBUG, INFO, WARNING, ERROR
  file: str             # Log file path
  format: str           # Log format string
  console: bool         # Enable console output
```

## Security Architecture

### Authentication

```mermaid
graph LR
    subgraph "Authentication Methods"
        TOKEN[GitHub Token]
        BASIC[Basic Auth]
        COOKIE[Browser Cookies]
    end
    
    subgraph "Storage"
        ENV[Environment Variables]
        CONFIG[Config File]
        KEYRING[System Keyring]
    end
    
    subgraph "Usage"
        API_AUTH[API Authentication]
        BROWSER_AUTH[Browser Authentication]
    end
    
    TOKEN --> ENV
    TOKEN --> CONFIG
    TOKEN --> KEYRING
    BASIC --> CONFIG
    COOKIE --> BROWSER_AUTH
    ENV --> API_AUTH
    CONFIG --> API_AUTH
    KEYRING --> API_AUTH
```

### Certificate Handling

```mermaid
graph TB
    subgraph "Certificate Sources"
        SYSTEM[System Store]
        WINDOWS[Windows Store]
        CUSTOM[Custom Bundle]
        CERTIFI[Certifi Bundle]
    end
    
    subgraph "Certificate Manager"
        LOADER[Certificate Loader]
        COMBINER[Bundle Combiner]
        VALIDATOR[Certificate Validator]
    end
    
    subgraph "Usage"
        REQUESTS[Requests Library]
        SELENIUM[Selenium Browser]
    end
    
    SYSTEM --> LOADER
    WINDOWS --> LOADER
    CUSTOM --> LOADER
    CERTIFI --> LOADER
    LOADER --> COMBINER
    COMBINER --> VALIDATOR
    VALIDATOR --> REQUESTS
    VALIDATOR --> SELENIUM
```

## Error Handling Strategy

### Error Hierarchy

```python
class GitSyncError(Exception):
    """Base exception for GitSync."""

class ConfigurationError(GitSyncError):
    """Configuration-related errors."""

class AuthenticationError(GitSyncError):
    """Authentication failures."""

class NetworkError(GitSyncError):
    """Network-related errors."""

class RateLimitError(NetworkError):
    """API rate limit exceeded."""

class RepositoryError(GitSyncError):
    """Repository access errors."""
```

### Retry Logic

```python
class RetryHandler:
    """Handles retry logic for transient failures."""
    
    def __init__(self, max_retries=3, backoff_factor=2):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except TransientError as e:
                if attempt == self.max_retries - 1:
                    raise
                delay = self.backoff_factor ** attempt
                time.sleep(delay)
```

## Performance Optimizations

### Parallel Downloads

```python
class ParallelDownloader:
    """Downloads multiple files concurrently."""
    
    def download_files(self, files: List[FileInfo], max_workers=5):
        """Download files in parallel."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.download_file, file): file
                for file in files
            }
            
            for future in as_completed(futures):
                file = futures[future]
                try:
                    result = future.result()
                    yield file, result
                except Exception as e:
                    self.handle_error(file, e)
```

### Incremental Updates

```python
class IncrementalSync:
    """Manages incremental synchronization."""
    
    def get_changes(self, remote_tree, local_cache):
        """Identify changed files."""
        changes = {
            'new': [],
            'modified': [],
            'deleted': [],
            'unchanged': []
        }
        
        for remote_file in remote_tree:
            local_file = local_cache.get(remote_file.path)
            
            if not local_file:
                changes['new'].append(remote_file)
            elif local_file.sha != remote_file.sha:
                changes['modified'].append(remote_file)
            else:
                changes['unchanged'].append(remote_file)
        
        # Check for deleted files
        for local_path in local_cache:
            if local_path not in remote_tree:
                changes['deleted'].append(local_path)
        
        return changes
```

## Extension Points

### Custom Sync Engines

```python
class CustomSyncEngine(BaseSyncEngine):
    """Template for custom sync engines."""
    
    def sync(self) -> SyncResult:
        """Implement custom sync logic."""
        raise NotImplementedError
    
    def validate_config(self) -> bool:
        """Validate engine-specific configuration."""
        raise NotImplementedError
```

### Plugin Architecture

```python
class PluginManager:
    """Manages GitSync plugins."""
    
    def load_plugins(self, plugin_dir: str):
        """Load plugins from directory."""
        for plugin_file in Path(plugin_dir).glob("*.py"):
            spec = importlib.util.spec_from_file_location(
                plugin_file.stem, plugin_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Register plugin
            if hasattr(module, 'register'):
                module.register(self)
```

## Monitoring and Telemetry

### Metrics Collection

```python
class MetricsCollector:
    """Collects performance metrics."""
    
    def __init__(self):
        self.metrics = {
            'sync_duration': [],
            'files_processed': 0,
            'bytes_transferred': 0,
            'api_calls': 0,
            'errors': []
        }
    
    def record_sync(self, duration, files, bytes_transferred):
        """Record sync metrics."""
        self.metrics['sync_duration'].append(duration)
        self.metrics['files_processed'] += files
        self.metrics['bytes_transferred'] += bytes_transferred
```

### Logging Architecture

```python
class LogManager:
    """Manages logging configuration."""
    
    def setup_logging(self, config):
        """Configure logging based on config."""
        handlers = []
        
        # Console handler
        if config.logging.console:
            handlers.append(logging.StreamHandler())
        
        # File handler
        if config.logging.file:
            handlers.append(logging.FileHandler(config.logging.file))
        
        logging.basicConfig(
            level=config.logging.level,
            format=config.logging.format,
            handlers=handlers
        )
```

## Future Architecture Considerations

### Planned Enhancements

1. **Plugin System**: Extensible architecture for custom sync methods
2. **Distributed Caching**: Share cache across multiple machines
3. **Webhook Integration**: Real-time sync triggers
4. **Multi-repository Support**: Sync multiple repos simultaneously
5. **Partial Sync**: Sync specific directories or file patterns
6. **Compression**: Compress transfers for bandwidth optimization

### Scalability Considerations

- **Connection Pooling**: Reuse HTTP connections
- **Async Operations**: Async/await for I/O operations
- **Memory Management**: Stream large files instead of loading
- **Rate Limiting**: Respect and adapt to rate limits
- **Caching Strategy**: LRU cache for frequently accessed data

## Conclusion

GitSync's architecture is designed to be:

- **Flexible**: Adapts to various network environments
- **Reliable**: Handles failures gracefully
- **Efficient**: Optimizes for performance
- **Extensible**: Supports future enhancements
- **Maintainable**: Clean separation of concerns

The modular design allows for easy testing, debugging, and enhancement of individual components without affecting the entire system.