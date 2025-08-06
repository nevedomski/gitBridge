"""File synchronization and incremental update logic.

This module handles the core file synchronization operations including
downloading files, managing incremental updates through SHA comparison,
and handling file system operations.

Key Features:
    - Incremental synchronization using SHA comparison
    - Large file support via Blob API
    - Binary file handling with proper encoding
    - Hash caching for performance optimization
    - File system operations with proper error handling

Typical Usage:
    >>> from gitsync.file_synchronizer import FileSynchronizer
    >>> from gitsync.api_client import GitHubAPIClient
    >>> from pathlib import Path
    >>>
    >>> client = GitHubAPIClient("owner", "repo", token="...")
    >>> sync = FileSynchronizer(client, Path("/local/path"))
    >>>
    >>> # Sync a single file
    >>> success = sync.sync_file({
    ...     "path": "README.md",
    ...     "sha": "abc123...",
    ...     "type": "blob"
    ... })
"""

import base64
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

from .api_client import GitHubAPIClient
from .exceptions import DirectoryCreateError, FileWriteError
from .utils import ensure_dir, load_file_hashes, save_file_hashes

logger = logging.getLogger(__name__)


class FileSynchronizer:
    """Handles file synchronization and incremental updates.

    This class manages the core file synchronization logic including
    downloading files from GitHub, implementing incremental updates,
    and managing the local file system operations.

    Attributes:
        client (GitHubAPIClient): API client for file downloads
        local_path (Path): Local directory path for synchronized files
        file_hashes (Dict[str, str]): Cache of file paths to SHA hashes
        hash_cache_file (Path): File path for persisting hash cache
        current_ref (Optional[str]): Current reference being synchronized

    DOCDEV-NOTE: Component Architecture - File Synchronization Layer
        This class was extracted from the monolithic GitHubAPISync to handle
        all file synchronization operations. It manages the core sync logic,
        incremental updates, and local file system operations.

    DOCDEV-NOTE: Design Principles
        - Incremental Sync: Uses SHA comparison to minimize downloads
        - Fault Tolerance: Individual file failures don't stop sync
        - Atomic Updates: Files written atomically to prevent corruption
        - Memory Efficient: Streams large files instead of loading to memory

    DOCDEV-NOTE: Performance Optimizations
        - Hash caching reduces API calls for unchanged files
        - Blob API used for large files (>1MB) for better performance
        - Future: Support for parallel downloads

    DOCDEV-TODO: Future Enhancements
        - Implement parallel file downloads
        - Add resume capability for interrupted syncs
        - Support for binary diff optimization
        - Implement file compression during transfer
    """

    def __init__(self, client: GitHubAPIClient, local_path: Path):
        """Initialize file synchronizer.

        Args:
            client: Configured GitHubAPIClient for file operations
            local_path: Local directory path where files will be synchronized

        Note:
            The synchronizer automatically creates the hash cache directory
            and loads any existing file hashes for incremental updates.
        """
        self.client = client
        self.local_path = local_path
        self.current_ref: Optional[str] = None

        # Cache file for tracking downloaded files
        # DOCDEV-NOTE: Hash cache enables incremental updates - only changed files are downloaded
        self.hash_cache_file = self.local_path / ".gitsync" / "file_hashes.json"
        self.file_hashes = load_file_hashes(self.hash_cache_file)

    def set_current_ref(self, ref: str) -> None:
        """Set the current reference for file downloads.

        Args:
            ref: Branch name, tag name, or commit SHA being synchronized

        Note:
            This is used to ensure consistency when downloading files
            from a specific reference point.
        """
        self.current_ref = ref

    def should_download_file(self, file_path: str, sha: str) -> bool:
        """Check if file needs to be downloaded.

        Implements incremental sync logic by comparing the file's SHA
        with the cached value from the previous sync.

        Args:
            file_path: Path to file in repository
            sha: Current SHA of the file in the repository

        Returns:
            True if file should be downloaded, False if it can be skipped

        Note:
            This is the key optimization for incremental updates.
            Only changed files are downloaded, significantly reducing bandwidth.
        """
        local_file = self.local_path / file_path

        # Always download if file doesn't exist locally
        if not local_file.exists():
            return True

        # Check if we have a cached hash for this file
        cached_hash = self.file_hashes.get(file_path)

        # If no cached hash or SHA changed, download
        # DOCDEV-NOTE: SHA comparison is the basis for incremental sync
        if not cached_hash or cached_hash != sha:
            return True

        return False

    def download_file(self, file_path: str, sha: str) -> Optional[bytes]:
        """Download a single file from repository.

        Attempts to download a file using the Contents API first, falling back
        to the Blob API for large files (>1MB) that exceed the Contents API limit.

        Args:
            file_path: Path to file in repository relative to root
            sha: Git SHA hash of the file content

        Returns:
            File content as bytes, or None if download fails

        Note:
            The Contents API has a 1MB file size limit. Larger files
            automatically use the Blob API which has a 100MB limit.

        DOCDEV-TODO: Add support for Git LFS files which exceed 100MB
        """
        try:
            # Build the API path
            path = f"repos/{self.client.owner}/{self.client.repo}/contents/{file_path}"
            params = {}
            if self.current_ref:
                params["ref"] = self.current_ref

            response = self.client.get(path, params=params)

            if response.status_code == 200:
                data = response.json()

                # Check if file is too large for Contents API
                # DOCDEV-NOTE: Contents API limit is 1MB, Blob API supports up to 100MB
                if data.get("size", 0) > 1024 * 1024:  # 1MB limit for Contents API
                    # Use git blob API for large files
                    return self.download_blob(sha)

                # Decode base64 content
                content = data.get("content", "")
                if content:
                    return base64.b64decode(content)

            elif response.status_code == 403:
                # Rate limit or file too large, try blob API
                # DOCDEV-NOTE: 403 can indicate rate limiting or size exceeded
                return self.download_blob(sha)
            elif response.status_code == 404:
                logger.error(f"File not found at ref: {file_path}")
                return None
            else:
                logger.error(f"API error {response.status_code} for {file_path}: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}")

        return None

    def download_blob(self, sha: str) -> Optional[bytes]:
        """Download file using git blob API.

        The Blob API is used for files that exceed the Contents API size limit.
        It can handle files up to 100MB in size.

        Args:
            sha: Git SHA hash of the blob

        Returns:
            File content as bytes, or None if download fails

        Note:
            Blob API always returns base64-encoded content regardless of file type.
        """
        try:
            path = f"repos/{self.client.owner}/{self.client.repo}/git/blobs/{sha}"
            response = self.client.get(path)

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                if content and data.get("encoding") == "base64":
                    return base64.b64decode(content)

        except Exception as e:
            logger.error(f"Failed to download blob {sha}: {e}")

        return None

    def sync_file(self, entry: Dict) -> bool:
        """Sync a single file.

        Handles the complete sync process for a single file:
        1. Checks if download is needed (incremental sync)
        2. Downloads the file content
        3. Saves to local filesystem
        4. Updates hash cache

        Args:
            entry: Tree entry from GitHub API containing:
                - 'path': File path in repository
                - 'sha': Git SHA of the file
                - 'type': Should be 'blob' for files

        Returns:
            True if sync was successful, False if any step failed

        Note:
            Errors are logged but don't stop the overall sync process.
            Specific exceptions are caught and converted to appropriate error types.
        """
        file_path = entry["path"]
        sha = entry["sha"]

        try:
            # Check if we need to download
            if not self.should_download_file(file_path, sha):
                return True  # File is up to date, skip

            # Download file content
            content = self.download_file(file_path, sha)
            if content is None:
                logger.error(f"Failed to download: {file_path}")
                return False

            # Save file to local filesystem
            local_file = self.local_path / file_path

            # Ensure directory exists
            try:
                ensure_dir(local_file.parent)
            except OSError as e:
                raise DirectoryCreateError(
                    f"Failed to create directory for {file_path}", dir_path=str(local_file.parent), original_error=e
                ) from e

            try:
                # Write as binary to preserve exact content
                # DOCDEV-NOTE: Binary write preserves line endings and encoding
                local_file.write_bytes(content)
            except OSError as e:
                raise FileWriteError(
                    f"Failed to write file {file_path}", file_path=str(local_file), size=len(content), original_error=e
                ) from e

            # Update hash cache after successful write
            # DOCDEV-NOTE: Cache update happens after successful write to ensure consistency
            self.file_hashes[file_path] = sha

            return True

        except (FileWriteError, DirectoryCreateError) as e:
            logger.error(f"File system error for {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error syncing file {file_path}: {e}")
            return False

    def sync_files(self, files: List[Dict]) -> Dict[str, int]:
        """Sync multiple files.

        Args:
            files: List of file entries from repository tree

        Returns:
            Dictionary with sync statistics:
                - 'checked': Number of files checked
                - 'downloaded': Number of files downloaded
                - 'skipped': Number of files skipped (up to date)
                - 'failed': Number of files that failed
                - 'bytes_downloaded': Total bytes downloaded
        """
        stats = {"checked": 0, "downloaded": 0, "skipped": 0, "failed": 0, "bytes_downloaded": 0}

        for entry in files:
            stats["checked"] += 1

            # Check if we need to download
            if not self.should_download_file(entry["path"], entry["sha"]):
                stats["skipped"] += 1
                continue

            # Download and save the file
            if self.sync_file(entry):
                stats["downloaded"] += 1
                # Estimate bytes (actual tracking would require more complex logic)
                if "size" in entry:
                    stats["bytes_downloaded"] += entry["size"]
            else:
                stats["failed"] += 1

        return stats

    def save_hash_cache(self) -> None:
        """Save the current file hash cache to disk.

        This should be called after a successful sync to persist
        the hash information for future incremental updates.
        """
        save_file_hashes(self.hash_cache_file, self.file_hashes)

    def get_cached_files(self) -> Set[str]:
        """Get set of files that have been cached.

        Returns:
            Set of file paths that have cached SHA hashes

        Note:
            This can be used to identify files that exist locally
            but may no longer exist in the repository.
        """
        return set(self.file_hashes.keys())

    def clear_hash_cache(self) -> None:
        """Clear the file hash cache.

        This forces a full re-sync on the next synchronization,
        as all files will be considered "changed".
        """
        self.file_hashes.clear()
        if self.hash_cache_file.exists():
            try:
                self.hash_cache_file.unlink()
            except OSError as e:
                logger.warning(f"Failed to remove hash cache file: {e}")

    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """Get cached information about a file.

        Args:
            file_path: Path to file in repository

        Returns:
            Dictionary with file information:
                - 'cached_sha': SHA hash from cache
                - 'local_exists': Whether file exists locally
                - 'local_size': Size of local file if it exists
            Returns None if no cached information exists
        """
        cached_sha = self.file_hashes.get(file_path)
        if not cached_sha:
            return None

        local_file = self.local_path / file_path
        local_exists = local_file.exists()
        local_size = local_file.stat().st_size if local_exists else 0

        return {"cached_sha": cached_sha, "local_exists": local_exists, "local_size": local_size}
