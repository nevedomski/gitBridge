# GitBridge Module Documentation

## Module Overview

The `gitbridge` package provides a robust solution for synchronizing GitHub repositories to local directories when direct git access is blocked. It's designed specifically for corporate environments with network restrictions, proxy requirements, and custom certificate configurations.

**Version**: 0.5.0b1  
**Python Support**: 3.10+  
**Test Coverage**: 83% (with Codecov integration)

## Architecture

### Current Architecture Status
The codebase has been successfully refactored from a monolithic design into a component-based architecture using the Facade pattern. The GitHubAPISync class now acts as a facade coordinating specialized components.

### Refactoring Benefits
The component-based architecture provides several key improvements:

#### **Improved Maintainability**
- Each component has a single, well-defined responsibility
- Changes to one component don't affect others
- Easier to locate and fix bugs in specific functionality

#### **Enhanced Testability**
- Components can be tested in isolation with mocked dependencies
- Higher test coverage through focused unit tests
- Easier to test edge cases and error conditions

#### **Better Code Organization**
- Related functionality is grouped into cohesive components
- Clear separation of concerns between API, repository, file, and progress operations
- Reduced cognitive load when working on specific features

#### **Backward Compatibility**
- Public API remains unchanged - existing code continues to work
- Internal complexity is hidden behind the facade pattern
- Gradual migration path for future enhancements

### Core Components

#### Component Relationships and Data Flow

The refactored architecture follows a clean layered design with well-defined component interactions:

```
User/CLI Layer
    │
    ▼
GitHubAPISync (Facade)
    │
    ├──> RepositoryManager    (Repository operations)
    │       └──> GitHubAPIClient
    │
    ├──> FileSynchronizer     (File sync operations)
    │       ├──> GitHubAPIClient
    │       └──> Cache Management
    │
    └──> ProgressTracker      (Progress reporting)
            └──> SyncStats
```

**Key Design Principles:**
- **Facade Pattern**: GitHubAPISync provides a simple interface while coordinating complex subsystems
- **Dependency Injection**: Components receive dependencies through constructors
- **Single Responsibility**: Each component handles one specific aspect
- **Interface Segregation**: Components expose minimal, focused interfaces

#### 1. **api_sync.py** - GitHub API Synchronization Facade
- **Purpose**: High-level facade coordinating specialized components
- **Key Class**: `GitHubAPISync` (facade pattern)
- **Architecture**: Coordinates four specialized components
- **Responsibilities**:
  - Provide simple public interface hiding internal complexity
  - Coordinate component interactions for complete synchronization
  - Maintain backward compatibility with existing code
  - Orchestrate synchronization workflow
- **Components Coordinated**:
  - `GitHubAPIClient`: Low-level HTTP/API operations
  - `RepositoryManager`: Repository metadata and structure
  - `FileSynchronizer`: File sync logic and incremental updates
  - `ProgressTracker`: Progress reporting and statistics

#### 1a. **api_client.py** - Low-level GitHub API Client
- **Purpose**: Handle foundational HTTP operations for GitHub API
- **Key Class**: `GitHubAPIClient`
- **Responsibilities**:
  - HTTP session management via SessionFactory
  - Authentication and rate limit handling
  - Connection testing and validation
  - Generic API request handling
- **Features**: Corporate environment support, proper error handling

#### 1b. **repository_manager.py** - Repository Metadata Manager
- **Purpose**: Handle repository-specific operations and metadata
- **Key Class**: `RepositoryManager`
- **Responsibilities**:
  - Reference resolution (branches, tags, commits)
  - Repository file tree retrieval
  - Branch and tag enumeration
  - Repository metadata management
- **Features**: Smart reference resolution, tree API optimization

#### 1c. **file_synchronizer.py** - File Synchronization Engine
- **Purpose**: Handle file synchronization and incremental updates
- **Key Class**: `FileSynchronizer`
- **Responsibilities**:
  - Incremental sync using SHA comparison
  - File downloading (Contents + Blob API)
  - Hash caching for performance
  - Local file system operations
- **Features**: Large file support, binary handling, error recovery

#### 1d. **progress_tracker.py** - Progress and Statistics Tracker
- **Purpose**: Handle progress reporting and statistics collection
- **Key Class**: `ProgressTracker`
- **Responsibilities**:
  - Real-time progress tracking with tqdm
  - Synchronization statistics collection
  - Performance metrics calculation
  - Summary reporting
- **Features**: Thread-safe updates, customizable reporting, throttling support

#### 2. **session_factory.py** - HTTP Session Factory
- **Purpose**: Centralized factory for creating and configuring HTTP sessions
- **Key Class**: `SessionFactory`
- **Responsibilities**:
  - SSL/TLS certificate configuration with Windows auto-detection
  - HTTP/HTTPS proxy configuration with PAC script auto-detection
  - GitHub authentication header setup
  - Corporate environment support
- **Methods**:
  - `create_session()`: Main factory method
  - `configure_ssl()`: SSL certificate and verification setup
  - `configure_proxy()`: Proxy detection and configuration
  - `configure_auth()`: GitHub authentication setup

#### 3. **browser_sync.py** - Browser Automation Fallback
- **Purpose**: Fallback synchronization using browser automation
- **Key Class**: `GitHubBrowserSync`
- **Current State**: Mixed Playwright/Selenium implementation (needs cleanup)
- **Responsibilities**:
  - Browser-based repository access when API is blocked
  - ZIP-based file list extraction
  - Individual file downloads via raw.githubusercontent.com
  - Incremental sync with hash caching
  - Corporate proxy and SSL support

#### 4. **pac_support.py** - Proxy Auto-Configuration
- **Purpose**: Auto-detect proxy settings from PAC scripts
- **Key Functions**: `detect_and_configure_proxy()`
- **Capabilities**:
  - Windows registry proxy detection
  - Chrome PAC script parsing
  - Automatic proxy URL extraction

#### 5. **cert_support.py** - Certificate Management
- **Purpose**: Handle corporate SSL certificates
- **Key Functions**: `get_combined_cert_bundle()`
- **Capabilities**:
  - Windows certificate store extraction
  - Certificate bundle creation
  - Corporate CA integration

#### 6. **config.py** - Configuration Management
- **Purpose**: Handle configuration files and settings
- **Key Class**: `Config`
- **Features**:
  - YAML configuration parsing
  - Environment variable expansion
  - Path normalization
  - Multi-level configuration (file -> env -> CLI)

#### 7. **cli.py** - Command-Line Interface
- **Purpose**: User-facing CLI using Click framework
- **Commands**:
  - `sync`: Main synchronization command
  - `test`: Connection testing
  - `init`: Configuration initialization

#### 8. **utils.py** - Shared Utilities
- **Purpose**: Common helper functions
- **Key Components**:
  - `SyncStats`: Statistics tracking
  - `parse_github_url()`: URL parsing
  - File hash management functions
  - Binary file detection

### New Refactored Components

#### 9. **api_client.py** - Low-level GitHub API Client
- **Purpose**: Encapsulate all GitHub REST API communication
- **Key Class**: `GitHubAPIClient`
- **Responsibilities**:
  - HTTP session management with connection pooling
  - Authentication header configuration
  - Rate limit monitoring and reporting
  - Error wrapping and exception handling
  - Raw API request/response handling
- **Design Notes**:
  - Stateless operations for thread safety
  - Uses SessionFactory for configuration
  - Returns domain-specific exceptions
  - No business logic, pure API communication

#### 10. **repository_manager.py** - Repository Structure Management
- **Purpose**: Handle repository metadata and tree operations
- **Key Class**: `RepositoryManager`
- **Responsibilities**:
  - Reference resolution (branch/tag/commit)
  - Repository tree retrieval and caching
  - Branch and tag enumeration
  - Commit SHA validation
  - Path normalization
- **Design Features**:
  - Efficient tree API usage
  - Smart reference resolution
  - Future support for sparse checkouts
  - Repository metadata caching

#### 11. **file_synchronizer.py** - File Synchronization Engine
- **Purpose**: Orchestrate file download and local storage
- **Key Class**: `FileSynchronizer`
- **Responsibilities**:
  - Incremental sync using SHA comparison
  - File download orchestration
  - Local file system operations
  - Hash cache management
  - Binary file detection and handling
- **Performance Features**:
  - SHA-based change detection
  - Blob API for large files
  - Atomic file writes
  - Future parallel download support

#### 12. **progress_tracker.py** - Progress and Statistics Tracking
- **Purpose**: Provide comprehensive progress feedback
- **Key Class**: `ProgressTracker`
- **Responsibilities**:
  - Real-time progress bar display
  - Statistics collection and reporting
  - Performance metrics tracking
  - Rate limit status monitoring
  - Summary report generation
- **User Experience**:
  - Visual feedback with tqdm
  - Customizable verbosity levels
  - Detailed error reporting
  - ETA calculations (future)

## Migration Notes and Breaking Changes

### Refactoring Impact (2025-08-05)

#### Backward Compatibility
The refactoring maintains **100% backward compatibility** through the Facade pattern:
- All public APIs remain unchanged
- Existing code continues to work without modification
- Internal implementation details are hidden

#### Internal Changes
For developers working with the codebase:
- **GitHubAPISync** is now a facade coordinating specialized components
- Direct instantiation of internal components is possible but not recommended
- Use the facade for stability across versions

#### Usage Examples

**Classic Usage (Still Works):**
```python
from gitbridge.api_sync import GitHubAPISync

sync = GitHubAPISync(
    repo_url="https://github.com/owner/repo",
    local_path="/local/path",
    token="github_token"
)
sync.sync(ref="main")
```

**Component-Based Usage (Advanced):**
```python
from gitbridge.api_client import GitHubAPIClient
from gitbridge.repository_manager import RepositoryManager
from gitbridge.file_synchronizer import FileSynchronizer
from gitbridge.progress_tracker import ProgressTracker

# Create components individually
client = GitHubAPIClient("owner", "repo", token="...")
repo_mgr = RepositoryManager(client)
file_sync = FileSynchronizer(client, Path("/local"))
tracker = ProgressTracker()

# Use components directly for custom workflows
sha = repo_mgr.resolve_ref("main")
tree = repo_mgr.get_repository_tree("main")
for file in tree:
    if file_sync.should_download(file["path"], file["sha"]):
        file_sync.sync_file(file)
        tracker.update_progress(file["path"], downloaded=True)
```

#### Testing Improvements
The refactoring significantly improves testability:
- Components can be tested in isolation
- Dependencies can be easily mocked
- Test coverage increased from ~80% to 94%+

## Key Design Decisions

### 1. **Session Management Architecture**
- **Decision**: Extract session configuration into separate SessionFactory class
- **Rationale**: Improve separation of concerns and testability
- **Implementation**:
  - `SessionFactory`: Centralized HTTP session creation and configuration
  - `GitHubAPISync`: Focus on synchronization logic only
  - Clean separation of SSL, proxy, and authentication concerns
- **Benefits**: Easier testing, better maintainability, single responsibility principle

### 2. **Incremental Synchronization**
- **Decision**: Use Git SHA comparison for change detection
- **Rationale**: Minimizes bandwidth usage and API calls
- **Implementation**: 
  - Store file SHAs in `.gitbridge/file_hashes.json`
  - Compare remote SHA with cached value
  - Only download changed files
- **Trade-offs**: Requires local cache maintenance

### 2. **API vs Browser Approach**
- **Decision**: Prioritize GitHub REST API over browser automation
- **Rationale**:
  - More efficient and reliable
  - Better rate limiting control
  - Cleaner implementation
- **Fallback**: Browser automation implemented as secondary method
- **Browser Implementation Status**:
  - Basic functionality working with requests library
  - Browser automation framework in transition (Playwright vs Selenium)
  - Uses ZIP download for file list, then individual file downloads
  - DOCDEV-NOTE: Current implementation is hybrid - uses requests for downloads

### 3. **Corporate Environment Support**
- **Decision**: Built-in proxy and certificate auto-detection
- **Rationale**: Many corporate users face these challenges
- **Implementation**:
  - Optional auto-detection flags (`--auto-proxy`, `--auto-cert`)
  - Manual override options
  - Environment variable support
- **DOCDEV-NOTE**: Windows-focused currently, macOS/Linux support planned

### 4. **Error Handling Philosophy**
- **Decision**: Fault-tolerant synchronization
- **Rationale**: Partial sync is better than no sync
- **Implementation**:
  - Individual file failures don't stop sync
  - Comprehensive error logging
  - Statistics tracking for failed files
- **DOCDEV-QUESTION**: Should we add a strict mode that fails on first error?

### 5. **Rate Limiting Strategy**
- **Decision**: Passive monitoring with basic throttling
- **Rationale**: Balance speed with API limits
- **Current Implementation**:
  - 100ms pause every 100 files
  - Rate limit status reporting
- **DOCDEV-TODO**: Implement adaptive throttling based on remaining quota

## API Interaction Patterns

### Authentication Flow
```python
# Token-based authentication (recommended)
session.headers['Authorization'] = f"token {token}"

# Unauthenticated (limited to 60 requests/hour)
# No Authorization header
```

### Reference Resolution Pattern
1. Check if input is full SHA (40 chars)
2. Try as branch name (`refs/heads/{ref}`)
3. Try as tag name (`refs/tags/{ref}`)
4. Try as short SHA (7+ chars)
5. Fallback: 'main' -> 'master' for default branch

### File Download Strategy
1. Use Contents API for files < 1MB
2. Fallback to Blob API for larger files (up to 100MB)
3. DOCDEV-TODO: Add Git LFS support for files > 100MB

### Error Recovery
- **401 Unauthorized**: Invalid or missing token
- **403 Forbidden**: Rate limit or file size exceeded
- **404 Not Found**: Repository, branch, or file doesn't exist
- **Connection errors**: Proxy/certificate misconfiguration

## Browser Sync Implementation

### Current State
The browser sync module (`browser_sync.py`) is in a transitional state:
- **Imports**: Mixed Playwright and Selenium imports
- **Implementation**: Uses requests library for actual downloads
- **Browser Automation**: Not fully implemented (placeholder methods)

### Design Decisions
1. **ZIP-based File Discovery**
   - Downloads repository ZIP to extract file list
   - More efficient than scraping web interface
   - DOCDEV-NOTE: URL pattern differs for branches vs tags

2. **Individual File Downloads**
   - Uses raw.githubusercontent.com for direct file access
   - Preserves exact file content (binary mode)
   - Implements incremental sync with SHA-256 hashing

3. **Browser Automation Role**
   - Originally intended for full browser automation
   - Currently simplified to use requests library
   - Browser would be needed for:
     - Private repositories with complex authentication
     - Sites that block programmatic access
     - Dynamic content that requires JavaScript execution

### Implementation Issues
- **DOCDEV-TODO**: Complete transition to either Playwright or Selenium
- **DOCDEV-TODO**: Implement actual browser automation methods
- **DOCDEV-TODO**: Add proper token-based authentication
- **DOCDEV-TODO**: Support for different ref types (branches, tags, commits)
- **DOCDEV-QUESTION**: Should we keep the hybrid approach or go full browser?

### Recommended Approach
1. **Keep Hybrid Model**: Use requests for efficiency, browser only when needed
2. **Choose Playwright**: Better cross-browser support and modern API
3. **Implement Progressive Enhancement**:
   - Try requests first (fastest)
   - Fall back to browser if requests fail
   - Use browser for authentication if needed

## Configuration Requirements

### Minimal Configuration
```yaml
repository:
  url: https://github.com/owner/repo
  local_path: ~/local/repo
```

### Full Configuration
```yaml
repository:
  url: https://github.com/owner/repo
  local_path: ~/local/repo
  ref: main  # or specific branch/tag/commit

auth:
  token: ${GITHUB_TOKEN}  # from environment

network:
  verify_ssl: true
  ca_bundle: /path/to/corporate-ca.pem
  auto_proxy: true
  auto_cert: true

sync:
  show_progress: true
```

### Environment Variables
- `GITHUB_TOKEN`: Personal access token
- `HTTP_PROXY`, `HTTPS_PROXY`: Proxy settings
- `GITSYNC_CONFIG`: Default config file path

## Performance Considerations

### API Rate Limits
- **Authenticated**: 5,000 requests/hour
- **Unauthenticated**: 60 requests/hour
- **Per-file cost**: 1-2 API calls (tree + content)
- **Large repos**: Consider spreading sync over time

### Memory Usage
- File tree cached in memory (can be large for huge repos)
- Files downloaded individually (streaming not required)
- Hash cache grows with repository size

### Network Optimization
- Incremental updates reduce bandwidth
- Parallel downloads not implemented (DOCDEV-TODO)
- Compression handled by HTTP layer

## Testing Strategies

### Unit Testing Focus Areas
1. URL parsing edge cases
2. SHA validation and resolution
3. Incremental sync logic
4. Error handling paths
5. Configuration merging

### Integration Testing
1. API connection with various auth methods
2. Proxy configuration scenarios
3. Certificate validation
4. Large file handling
5. Rate limit behavior

### Manual Testing Checklist
- [ ] Public repository sync
- [ ] Private repository with token
- [ ] Specific branch/tag/commit sync
- [ ] Corporate proxy configuration
- [ ] Custom certificate bundle
- [ ] Incremental update (second sync)
- [ ] Large file handling (>1MB)
- [ ] Rate limit monitoring

## Common Issues and Solutions

### 1. SSL Certificate Errors
**Problem**: `SSL: CERTIFICATE_VERIFY_FAILED`
**Solutions**:
- Use `--auto-cert` flag on Windows
- Provide custom CA bundle with `--ca-bundle`
- Last resort: `--no-verify-ssl` (not recommended)

### 2. Proxy Connection Failed
**Problem**: Connection timeout or proxy errors
**Solutions**:
- Use `--auto-proxy` flag for auto-detection
- Set `HTTP_PROXY` and `HTTPS_PROXY` environment variables
- Specify proxy in config file

### 3. Rate Limit Exceeded
**Problem**: 403 errors, API rate limit hit
**Solutions**:
- Add authentication token (increases limit to 5000/hour)
- Reduce sync frequency
- Use incremental sync to minimize API calls

### 4. Large Repository Sync
**Problem**: Sync takes too long or times out
**Solutions**:
- Use incremental sync (automatic after first sync)
- Sync specific directories (not yet implemented)
- Consider using sparse checkout patterns (future feature)

## Future Enhancements

### High Priority
- [x] **DOCDEV-TODO**: Browser automation fallback for when API is blocked (partially implemented)
- [ ] **DOCDEV-TODO**: Git LFS support for large files
- [ ] **DOCDEV-TODO**: Parallel file downloads for faster sync
- [ ] **DOCDEV-TODO**: Selective sync (include/exclude patterns)

### Medium Priority
- [ ] **DOCDEV-TODO**: GitHub Enterprise support
- [ ] **DOCDEV-TODO**: Webhook-triggered sync
- [ ] **DOCDEV-TODO**: Conflict resolution for local changes
- [ ] **DOCDEV-TODO**: macOS Keychain certificate support

### Low Priority
- [ ] **DOCDEV-TODO**: Git submodule support
- [ ] **DOCDEV-TODO**: Binary diff optimization
- [ ] **DOCDEV-TODO**: Sync history/commits (not just files)
- [ ] **DOCDEV-TODO**: Multi-repository sync

## Development Guidelines

### Adding New Features
1. Check existing DOCDEV-TODO comments for planned work
2. Maintain backward compatibility with config files
3. Follow separation of concerns (e.g., use SessionFactory for session config)
4. Add comprehensive docstrings (Google style)
5. Update this AGENTS.md with architectural changes
6. Add unit tests for new functionality

### Code Style
- Follow Google Python style guide
- Use type hints for all public methods
- Add DOCDEV-NOTE comments for complex logic
- Add DOCDEV-TODO for known improvements
- Add DOCDEV-QUESTION for design decisions needing review

### Testing Requirements
- Minimum 80% code coverage for new code
- Test both success and failure paths
- Mock external API calls in unit tests
- Document manual testing procedures

## Security Considerations

### Token Management
- **NEVER** commit tokens to repository
- Use environment variables or secure config files
- Recommend minimal token scopes (public_repo or repo)
- Consider token rotation policy

### SSL/TLS
- Default to SSL verification enabled
- Certificate pinning not implemented (consider for high security)
- Support corporate certificate chains

### Local Storage
- Hash cache is not sensitive (only SHAs)
- Downloaded files maintain original permissions
- No encryption of local files (rely on filesystem)

## Support Matrix

### Python Versions
- Python 3.11+ (required for modern typing)
- Tested on 3.11, 3.12

### Operating Systems
- **Full support**: Windows 10/11
- **Partial support**: macOS, Linux (no auto-detect features)
- **Docker**: Compatible with containerized environments

### GitHub Compatibility
- GitHub.com (fully supported)
- GitHub Enterprise (planned, not tested)
- GitHub API v3 (REST API)
- Git LFS (not yet supported)

## Contact and Contribution

For questions about architecture or design decisions, refer to:
1. DOCDEV-NOTE comments in code for implementation details
2. DOCDEV-TODO comments for planned improvements
3. DOCDEV-QUESTION comments for open design questions
4. PROJECT_STATUS.md for project roadmap
5. This AGENTS.md for module-level documentation

When contributing:
- Update relevant documentation
- Follow existing patterns and conventions
- Add appropriate DOCDEV comments
- Ensure backward compatibility