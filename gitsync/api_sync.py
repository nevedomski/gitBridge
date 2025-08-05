"""GitHub API synchronization implementation"""

import base64
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from tqdm import tqdm

from .utils import (
    SyncStats,
    ensure_dir,
    load_file_hashes,
    parse_github_url,
    save_file_hashes,
)

logger = logging.getLogger(__name__)


class GitHubAPISync:
    """Synchronize repository using GitHub REST API."""

    def __init__(self, repo_url: str, local_path: str, token: Optional[str] = None, verify_ssl: bool = True, ca_bundle: Optional[str] = None):
        """Initialize GitHub API sync.

        Args:
            repo_url: GitHub repository URL
            local_path: Local directory path
            token: GitHub personal access token (optional)
            verify_ssl: Whether to verify SSL certificates
            ca_bundle: Path to CA bundle file for corporate certificates
        """
        self.owner, self.repo = parse_github_url(repo_url)
        self.local_path = Path(local_path)
        self.token = token
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        # Configure SSL verification
        if not verify_ssl:
            self.session.verify = False
            # Suppress SSL warnings when disabled
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        elif ca_bundle:
            self.session.verify = ca_bundle

        # Set up authentication if token provided
        if self.token:
            self.session.headers.update(
                {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}
            )
        else:
            self.session.headers.update({"Accept": "application/vnd.github.v3+json"})

        # Cache file for tracking downloaded files
        self.hash_cache_file = self.local_path / ".gitsync" / "file_hashes.json"
        self.file_hashes = load_file_hashes(self.hash_cache_file)

        # Statistics
        self.stats = SyncStats()

    def test_connection(self) -> bool:
        """Test if API connection works."""
        try:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}"
            response = self.session.get(url)

            if response.status_code == 200:
                logger.info(f"Successfully connected to {self.owner}/{self.repo}")
                return True
            elif response.status_code == 401:
                logger.error("Authentication failed. Check your token.")
                return False
            elif response.status_code == 404:
                logger.error(f"Repository not found: {self.owner}/{self.repo}")
                return False
            else:
                logger.error(f"API request failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_rate_limit(self) -> Dict[str, Any]:
        """Get current API rate limit status."""
        try:
            response = self.session.get(f"{self.base_url}/rate_limit")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get rate limit: {e}")
        return {}

    def resolve_ref(self, ref: str) -> Optional[str]:
        """Resolve a reference (branch, tag, or commit SHA) to a commit SHA.

        Args:
            ref: Branch name, tag name, or commit SHA

        Returns:
            Commit SHA or None if not found
        """
        # Check if it's already a SHA (40 hex characters)
        if len(ref) == 40 and all(c in "0123456789abcdef" for c in ref.lower()):
            # Verify the commit exists
            commit_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/commits/{ref}"
            response = self.session.get(commit_url)
            if response.status_code == 200:
                return ref
            else:
                logger.error(f"Commit {ref} not found")
                return None

        # Try as branch
        branch_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/ref/heads/{ref}"
        response = self.session.get(branch_url)
        if response.status_code == 200:
            return response.json()["object"]["sha"]

        # Try as tag
        tag_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/ref/tags/{ref}"
        response = self.session.get(tag_url)
        if response.status_code == 200:
            tag_data = response.json()
            # Tags can point to either commits or tag objects
            if tag_data["object"]["type"] == "commit":
                return tag_data["object"]["sha"]
            else:
                # It's an annotated tag, need to get the commit it points to
                tag_obj_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/tags/{tag_data['object']['sha']}"
                tag_obj_response = self.session.get(tag_obj_url)
                if tag_obj_response.status_code == 200:
                    return tag_obj_response.json()["object"]["sha"]

        # Try short SHA (7+ characters)
        if len(ref) >= 7 and all(c in "0123456789abcdef" for c in ref.lower()):
            # Search for commit by SHA prefix
            commits_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/commits"
            response = self.session.get(commits_url, params={"sha": ref, "per_page": 1})
            if response.status_code == 200 and response.json():
                full_sha = response.json()[0]["sha"]
                if full_sha.startswith(ref):
                    return full_sha

        return None

    def get_repository_tree(self, ref: str = "main", recursive: bool = True) -> Optional[List[Dict]]:
        """Get repository file tree.

        Args:
            ref: Branch name, tag name, or commit SHA to sync
            recursive: Whether to get recursive tree

        Returns:
            List of tree entries or None if failed
        """
        try:
            # Resolve the reference to a commit SHA
            commit_sha = self.resolve_ref(ref)

            if not commit_sha:
                # Try 'master' if 'main' fails
                if ref == "main":
                    logger.info("Reference 'main' not found, trying 'master'")
                    return self.get_repository_tree("master", recursive)
                else:
                    logger.error(f"Reference '{ref}' not found")
                    return None

            # Get the tree
            tree_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/trees/{commit_sha}"
            if recursive:
                tree_url += "?recursive=1"

            tree_response = self.session.get(tree_url)

            if tree_response.status_code == 200:
                tree_data = tree_response.json()
                return tree_data.get("tree", [])
            else:
                logger.error(f"Failed to get tree: {tree_response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Failed to get repository tree: {e}")
            return None

    def download_file(self, file_path: str, sha: str) -> Optional[bytes]:
        """Download a single file from repository.

        Args:
            file_path: Path to file in repository
            sha: File SHA

        Returns:
            File content as bytes or None if failed
        """
        try:
            # Need to specify the ref when downloading from a specific branch/tag/commit
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{file_path}"
            params = {}
            if hasattr(self, '_current_ref') and self._current_ref:
                params['ref'] = self._current_ref
                
            response = self.session.get(url, params=params)

            if response.status_code == 200:
                data = response.json()

                # Check if file is too large for API
                if data.get("size", 0) > 1024 * 1024:  # 1MB limit for API
                    # Use git blob API for large files
                    return self.download_blob(sha)

                # Decode base64 content
                content = data.get("content", "")
                if content:
                    return base64.b64decode(content)

            elif response.status_code == 403:
                # Rate limit or file too large, try blob API
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
        """Download file using git blob API."""
        try:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/blobs/{sha}"
            response = self.session.get(url)

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                if content and data.get("encoding") == "base64":
                    return base64.b64decode(content)

        except Exception as e:
            logger.error(f"Failed to download blob {sha}: {e}")

        return None

    def should_download_file(self, file_path: str, sha: str) -> bool:
        """Check if file needs to be downloaded."""
        local_file = self.local_path / file_path

        # Always download if file doesn't exist
        if not local_file.exists():
            return True

        # Check if we have a hash for this file
        cached_hash = self.file_hashes.get(file_path)

        # If no cached hash or SHA changed, download
        if not cached_hash or cached_hash != sha:
            return True

        return False

    def sync_file(self, entry: Dict) -> bool:
        """Sync a single file.

        Args:
            entry: Tree entry from GitHub API

        Returns:
            True if successful, False otherwise
        """
        file_path = entry["path"]
        sha = entry["sha"]

        self.stats.files_checked += 1

        # Check if we need to download
        if not self.should_download_file(file_path, sha):
            self.stats.files_skipped += 1
            return True

        # Download file
        content = self.download_file(file_path, sha)
        if content is None:
            logger.error(f"Failed to download: {file_path}")
            self.stats.files_failed += 1
            return False

        # Save file
        local_file = self.local_path / file_path
        ensure_dir(local_file.parent)

        try:
            # Write as binary to preserve exact content
            local_file.write_bytes(content)

            # Update hash cache
            self.file_hashes[file_path] = sha

            self.stats.files_downloaded += 1
            self.stats.bytes_downloaded += len(content)

            return True

        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            self.stats.files_failed += 1
            return False

    def sync(self, ref: str = "main", show_progress: bool = True) -> bool:
        """Synchronize repository.

        Args:
            ref: Branch name, tag name, or commit SHA to sync
            show_progress: Whether to show progress bar

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting sync of {self.owner}/{self.repo} (ref: {ref}) to {self.local_path}")

        # Store the ref for use in download_file
        self._current_ref = ref

        # Test connection first
        if not self.test_connection():
            return False

        # Get repository tree
        tree = self.get_repository_tree(ref)
        if tree is None:
            return False

        # Filter only files (not directories)
        files = [entry for entry in tree if entry["type"] == "blob"]
        logger.info(f"Found {len(files)} files to sync")

        # Create local directory
        ensure_dir(self.local_path)

        # Sync files with progress bar
        if show_progress:
            progress_bar = tqdm(files, desc="Syncing files", unit="file")
            file_iterator = progress_bar
        else:
            file_iterator = files

        success = True
        for entry in file_iterator:
            if not self.sync_file(entry):
                success = False

            # Update progress description
            if show_progress:
                progress_bar.set_postfix(
                    {
                        "downloaded": self.stats.files_downloaded,
                        "skipped": self.stats.files_skipped,
                        "failed": self.stats.files_failed,
                    }
                )

            # Brief pause to avoid rate limiting
            if self.stats.files_downloaded % 100 == 0:
                time.sleep(0.1)

        # Save hash cache
        save_file_hashes(self.hash_cache_file, self.file_hashes)

        # Print statistics
        self.stats.print_summary()

        # Check rate limit
        rate_limit = self.get_rate_limit()
        if rate_limit:
            core_limit = rate_limit.get("rate", {})
            remaining = core_limit.get("remaining", "unknown")
            limit = core_limit.get("limit", "unknown")
            logger.info(f"API rate limit: {remaining}/{limit} requests remaining")

        return success
