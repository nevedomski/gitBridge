"""GitHub API synchronization facade.

This module provides a high-level facade for synchronizing GitHub repositories
to local directories. It coordinates multiple specialized components to provide
a clean, simple interface while maintaining all the advanced functionality.

The facade pattern is used to:
    - Simplify the public API by hiding internal complexity
    - Coordinate multiple specialized components
    - Maintain backward compatibility with existing code
    - Provide a single entry point for synchronization operations

Key Features:
    - Efficient incremental synchronization using file SHA comparison
    - Support for branches, tags, and specific commit SHAs
    - Automatic proxy detection from PAC scripts (Windows/Chrome)
    - Certificate bundle auto-detection from Windows store
    - Rate limit monitoring and handling
    - Large file support using GitHub Blob API
    - Progress tracking with visual feedback

Components Coordinated:
    - GitHubAPIClient: Low-level HTTP/API operations
    - RepositoryManager: Repository metadata and structure
    - FileSynchronizer: File sync logic and incremental updates
    - ProgressTracker: Progress reporting and statistics

Typical Usage:
    >>> from gitbridge.api_sync import GitHubAPISync
    >>> sync = GitHubAPISync(
    ...     repo_url="https://github.com/owner/repo",
    ...     local_path="/path/to/local",
    ...     token="github_token"
    ... )
    >>> sync.sync(ref="main")
"""

import logging
from pathlib import Path
from typing import Any

from .api_client import GitHubAPIClient
from .exceptions import SyncError
from .file_synchronizer import FileSynchronizer
from .interfaces import SyncProvider
from .progress_tracker import ProgressTracker
from .repository_manager import RepositoryManager
from .utils import ensure_dir, parse_github_url

logger = logging.getLogger(__name__)


class GitHubAPISync(SyncProvider):
    """Facade for GitHub API synchronization using coordinated components.

    This class acts as a facade that coordinates multiple specialized components
    to provide repository synchronization functionality. It maintains the same
    public interface as before while internally using a more modular architecture.

    The class orchestrates:
    - GitHubAPIClient for low-level HTTP operations
    - RepositoryManager for repository metadata and structure
    - FileSynchronizer for file operations and incremental sync
    - ProgressTracker for progress reporting and statistics

    Attributes:
        owner (str): GitHub repository owner/organization name
        repo (str): GitHub repository name
        local_path (Path): Local directory path for synchronization
        token (Optional[str]): GitHub personal access token for authentication

        # Internal components
        client (GitHubAPIClient): Low-level API client
        repository (RepositoryManager): Repository structure manager
        synchronizer (FileSynchronizer): File synchronization manager
    """

    def __init__(
        self,
        repo_url: str,
        local_path: str,
        token: str | None = None,
        verify_ssl: bool = True,
        ca_bundle: str | None = None,
        auto_proxy: bool = False,
        auto_cert: bool = False,
        config: dict[str, Any] | None = None,
    ):
        """Initialize GitHub API sync facade.

        Args:
            repo_url: GitHub repository URL (e.g., "https://github.com/owner/repo")
            local_path: Local directory path where files will be synchronized
            token: GitHub personal access token for authentication. Required for
                private repositories and recommended for public ones to avoid
                rate limiting (60 requests/hour without token, 5000 with token)
            verify_ssl: Whether to verify SSL certificates. Set to False only
                in trusted environments with self-signed certificates
            ca_bundle: Path to custom CA bundle file for corporate certificates.
                Takes precedence over auto-detected certificates
            auto_proxy: Whether to auto-detect proxy settings from Windows registry
                or Chrome PAC scripts. Useful in corporate environments
            auto_cert: Whether to auto-detect certificates from Windows certificate
                store. Useful for corporate environments with custom CAs
            config: Optional configuration dictionary with download limits and other settings

        Raises:
            ValueError: If the repository URL is invalid or cannot be parsed

        Note:
            Environment variables HTTP_PROXY and HTTPS_PROXY take precedence
            over auto-detected proxy settings.
        """
        # DOCDEV-NOTE: Parse URL and initialize basic attributes
        self.owner, self.repo = parse_github_url(repo_url)
        self.local_path = Path(local_path)
        self.token = token

        # Initialize coordinated components
        # DOCDEV-NOTE: Component initialization order matters - client first, then dependent components
        self.client = GitHubAPIClient(
            owner=self.owner,
            repo=self.repo,
            token=token,
            verify_ssl=verify_ssl,
            ca_bundle=ca_bundle,
            auto_proxy=auto_proxy,
            auto_cert=auto_cert,
            config=config,
        )

        self.repository = RepositoryManager(self.client)
        self.synchronizer = FileSynchronizer(self.client, self.local_path)

    def test_connection(self) -> bool:
        """Test if API connection works.

        Verifies that the API is accessible and the repository exists.
        Also validates authentication if a token is provided.

        Returns:
            bool: True if connection is successful, False otherwise

        Note:
            This method delegates to the GitHubAPIClient component.
            Exceptions are caught and converted to boolean return value.
        """
        try:
            return self.client.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_rate_limit(self) -> dict[str, Any]:
        """Get current API rate limit status.

        Queries the GitHub API rate limit endpoint to check remaining requests.

        Returns:
            Dict containing rate limit information with keys:
                - 'rate': Core API rate limit info
                - 'resources': Detailed limits for different API endpoints
            Returns empty dict if request fails

        Note:
            This method delegates to the GitHubAPIClient component.
        """
        return self.client.get_rate_limit()

    def resolve_ref(self, ref: str) -> str | None:
        """Resolve a reference (branch, tag, or commit SHA) to a commit SHA.

        This method handles multiple reference types:
        - Full commit SHA (40 hex characters)
        - Short commit SHA (7+ hex characters)
        - Branch names (e.g., 'main', 'develop')
        - Tag names (both lightweight and annotated)

        Args:
            ref: Branch name, tag name, or commit SHA to resolve

        Returns:
            Full commit SHA if found, None if not found

        Note:
            This method delegates to the RepositoryManager component.
        """
        return self.repository.resolve_ref(ref)

    def get_repository_tree(self, ref: str = "main", recursive: bool = True) -> list[dict[str, Any]] | None:
        """Get repository file tree.

        Fetches the complete file tree for a repository at a specific reference.
        Uses the Git Trees API which is more efficient than listing contents recursively.

        Args:
            ref: Branch name, tag name, or commit SHA to sync (default: "main")
            recursive: Whether to get recursive tree including all subdirectories
                (default: True). Setting to False only returns root level items.

        Returns:
            List of tree entries, where each entry is a dict with keys:
                - 'path': File path relative to repository root
                - 'sha': Git SHA of the file content
                - 'type': 'blob' for files, 'tree' for directories
                - 'size': File size in bytes (for blobs)
            Returns None if the request fails

        Note:
            This method delegates to the RepositoryManager component.

        DOCDEV-NOTE: Component Responsibility - RepositoryManager
            Tree traversal and repository structure management would be
            handled by the RepositoryManager component, which would cache
            tree data and handle incremental updates efficiently
        """
        return self.repository.get_repository_tree(ref, recursive)

    def sync(self, ref: str = "main", show_progress: bool = True) -> bool:
        """Synchronize repository.

        Main entry point for repository synchronization. Performs a complete
        sync of the specified reference to the local directory by coordinating
        all the internal components.

        The sync process:
        1. Tests API connection and authentication (via GitHubAPIClient)
        2. Resolves the reference to a commit SHA (via RepositoryManager)
        3. Fetches the complete file tree (via RepositoryManager)
        4. Downloads new or changed files (via FileSynchronizer + ProgressTracker)
        5. Saves hash cache for future incremental updates (via FileSynchronizer)
        6. Reports statistics and rate limit status (via ProgressTracker)

        Args:
            ref: Branch name, tag name, or commit SHA to sync (default: "main")
            show_progress: Whether to show progress bar with tqdm (default: True)

        Returns:
            True if sync completed (even with some failed files),
            False if sync couldn't start due to connection/auth issues

        Note:
            The method is fault-tolerant - individual file failures don't
            stop the overall sync. Check the returned statistics for details.
        """
        logger.info(f"Starting sync of {self.owner}/{self.repo} (ref: {ref}) to {self.local_path}")

        try:
            # Step 1: Test connection
            # DOCDEV-NOTE: Early connection test helps fail fast on auth/network issues
            if not self.test_connection():
                logger.error("Connection test failed")
                return False

            # Step 2: Get repository tree
            tree = self.get_repository_tree(ref)
            if tree is None:
                raise SyncError(
                    f"Failed to get repository tree for reference '{ref}'",
                    ref=ref,
                    repo_url=f"https://github.com/{self.owner}/{self.repo}",
                    sync_method="api",
                )

        except SyncError as e:
            logger.error(f"Sync initialization failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during sync initialization: {e}")
            return False

        # Filter only files (not directories)
        # DOCDEV-NOTE: Tree contains both 'blob' (files) and 'tree' (directories)
        # We only need to sync blobs as directories are created automatically
        files = [entry for entry in tree if entry["type"] == "blob"]
        logger.info(f"Found {len(files)} files to sync")

        # Create local directory
        ensure_dir(self.local_path)

        # Step 3: Initialize progress tracker
        tracker = ProgressTracker(total_files=len(files), show_progress=show_progress, desc="Syncing files")

        try:
            # Step 4: Set current ref in synchronizer for consistency
            self.synchronizer.set_current_ref(ref)

            # Step 5: Sync files with progress tracking
            success = True
            for i, entry in enumerate(files):
                file_path = entry["path"]
                sha = entry["sha"]

                # Check if we need to download
                if not self.synchronizer.should_download_file(file_path, sha):
                    tracker.update_progress(file_path, skipped=True)
                    continue

                # Sync the file
                if self.synchronizer.sync_file(entry):
                    tracker.update_progress(file_path, downloaded=True, size=entry.get("size", 0))
                else:
                    tracker.update_progress(file_path, failed=True)
                    success = False

                # Throttling to avoid rate limits
                # DOCDEV-NOTE: Throttling helps avoid hitting rate limits on large repos
                if tracker.should_throttle(i + 1):
                    tracker.log_throttle_pause(0.1)

            # Step 6: Save hash cache and cleanup
            self.synchronizer.save_hash_cache()

            # Step 7: Print summary with rate limit info
            rate_limit = self.get_rate_limit()
            tracker.print_summary(show_rate_limit=True, rate_limit_info=rate_limit)

            return success

        finally:
            # Ensure progress tracker is properly cleaned up
            tracker.close()

    # Backward compatibility methods - delegate to components
    def download_file(self, file_path: str, sha: str) -> bytes | None:
        """Download a single file from repository.

        Note: This method is provided for backward compatibility.
        Consider using the synchronizer component directly for new code.
        """
        return self.synchronizer.download_file(file_path, sha)

    def download_blob(self, sha: str) -> bytes | None:
        """Download file using git blob API.

        Note: This method is provided for backward compatibility.
        Consider using the synchronizer component directly for new code.
        """
        return self.synchronizer.download_blob(sha)

    def should_download_file(self, file_path: str, sha: str) -> bool:
        """Check if file needs to be downloaded.

        Note: This method is provided for backward compatibility.
        Consider using the synchronizer component directly for new code.
        """
        return self.synchronizer.should_download_file(file_path, sha)

    def sync_file(self, entry: dict[str, Any]) -> bool:
        """Sync a single file.

        Note: This method is provided for backward compatibility.
        Consider using the synchronizer component directly for new code.
        """
        return self.synchronizer.sync_file(entry)

    def close(self) -> None:
        """Close and cleanup all resources.

        Should be called when the sync instance is no longer needed
        to properly cleanup HTTP connections and other resources.
        """
        if hasattr(self, "client"):
            self.client.close()

    def __enter__(self) -> "GitHubAPISync":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - cleanup resources."""
        self.close()

    def get_status(self) -> dict[str, Any]:
        """Get current synchronization provider status and metadata.

        Returns comprehensive information about the API sync provider's current state
        including configuration, statistics, authentication status, and relevant metadata
        for debugging or monitoring purposes.

        Returns:
            Dict[str, Any]: Status dictionary containing provider information,
                repository details, sync statistics, and health indicators.

        Note:
            Sensitive information like tokens is masked for security. Status reflects
            real-time state where possible, including recent rate limit information.
        """
        # DOCDEV-NOTE: Status method provides comprehensive provider information
        # for debugging, monitoring, and user feedback purposes

        # Get current rate limit info if possible
        rate_info = {}
        try:
            rate_limit_data = self.get_rate_limit()
            if rate_limit_data:
                core_limit = rate_limit_data.get("rate", {})
                rate_info = {
                    "remaining": core_limit.get("remaining", "unknown"),
                    "limit": core_limit.get("limit", "unknown"),
                    "reset_time": core_limit.get("reset", "unknown"),
                }
        except Exception:
            # Don't fail status check if rate limit query fails
            pass

        # Determine authentication status
        auth_status = "anonymous"
        if self.token:
            auth_status = "authenticated"
            # Test if token is still valid by checking connection
            try:
                if self.test_connection():
                    auth_status = "authenticated"
                else:
                    auth_status = "failed"
            except Exception:
                auth_status = "failed"

        # Determine health status
        health = "healthy"
        if auth_status == "failed":
            health = "error"
        elif rate_info.get("remaining") is not None:
            remaining = rate_info["remaining"]
            limit = rate_info.get("limit")
            if isinstance(remaining, int) and isinstance(limit, int):
                if remaining < limit * 0.1:  # Less than 10% remaining
                    health = "warning"

        # Get synchronizer statistics - note that synchronizer doesn't maintain permanent stats
        # Stats are calculated per-sync operation and reported via ProgressTracker
        stats_dict = {
            "files_checked": 0,
            "files_downloaded": 0,
            "files_skipped": 0,
            "files_failed": 0,
            "bytes_downloaded": 0,
            "directories_created": 0,
        }

        # Get last sync timestamp from cache file
        last_sync = None
        try:
            if hasattr(self, "synchronizer") and self.synchronizer:
                cache_file = self.synchronizer.hash_cache_file
                if cache_file.exists():
                    import os

                    last_sync_timestamp = os.path.getmtime(cache_file)
                    from datetime import datetime

                    last_sync = datetime.fromtimestamp(last_sync_timestamp).isoformat()
        except Exception:
            pass

        return {
            "provider_type": "api",
            "repository": f"{self.owner}/{self.repo}",
            "repository_url": f"https://github.com/{self.owner}/{self.repo}",
            "local_path": str(self.local_path),
            "last_sync": last_sync,
            "authentication": auth_status,
            "statistics": stats_dict,
            "configuration": {
                "verify_ssl": getattr(self, "verify_ssl", True),
                "auto_proxy": getattr(self, "auto_proxy", False),
                "auto_cert": getattr(self, "auto_cert", False),
                "has_custom_ca_bundle": bool(getattr(self, "ca_bundle", None)),
                "token_configured": bool(self.token),
            },
            "api_rate_limit": rate_info,
            "health": health,
        }
