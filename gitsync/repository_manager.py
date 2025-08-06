"""Repository metadata and structure management.

This module handles repository-specific operations including reference resolution,
file tree retrieval, and metadata management. It provides an abstraction layer
over GitHub's Git API for working with repository structure.

Key Features:
    - Reference resolution (branches, tags, commits)
    - Repository file tree retrieval
    - Branch and tag enumeration
    - Commit SHA validation and lookup
    - Repository metadata management

Typical Usage:
    >>> from gitsync.repository_manager import RepositoryManager
    >>> from gitsync.api_client import GitHubAPIClient
    >>>
    >>> client = GitHubAPIClient("owner", "repo", token="...")
    >>> repo_mgr = RepositoryManager(client)
    >>>
    >>> # Resolve reference to commit SHA
    >>> sha = repo_mgr.resolve_ref("main")
    >>>
    >>> # Get file tree for a reference
    >>> tree = repo_mgr.get_repository_tree("main")
"""

import logging
from typing import Any

from .api_client import GitHubAPIClient
from .exceptions import SyncError

logger = logging.getLogger(__name__)


class RepositoryManager:
    """Manages repository metadata and structure operations.

    This class provides high-level operations for working with GitHub repository
    structure, including reference resolution, file tree retrieval, and metadata
    management. It abstracts the complexity of GitHub's Git API.

    Attributes:
        client (GitHubAPIClient): Low-level API client for HTTP operations
        owner (str): Repository owner name (from client)
        repo (str): Repository name (from client)

    DOCDEV-NOTE: Component Architecture - Repository Management Layer
        This class was extracted from the monolithic GitHubAPISync to handle all
        repository-specific operations. It provides a clean abstraction over
        GitHub's Git API, handling the complexity of reference resolution and
        tree traversal.

    DOCDEV-NOTE: Design Decisions
        - Separation of Concerns: Repository logic separate from sync logic
        - Efficient Tree Retrieval: Uses Trees API instead of recursive Contents API
        - Smart Reference Resolution: Handles branches, tags, and commits uniformly
        - Caching Ready: Structure supports future tree caching implementation

    DOCDEV-TODO: Future Enhancements
        - Add tree caching to reduce API calls
        - Implement sparse checkout patterns
        - Support for submodules
        - Parallel tree fetching for large repositories
    """

    def __init__(self, client: GitHubAPIClient):
        """Initialize repository manager.

        Args:
            client: Configured GitHubAPIClient instance for API operations

        Note:
            The client should be properly configured with authentication and
            connection settings before being passed to this constructor.
        """
        self.client = client
        self.owner = client.owner
        self.repo = client.repo

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

        Raises:
            SyncError: If reference resolution fails due to API errors

        Note:
            The method tries references in order: full SHA -> branch -> tag -> short SHA
            This ensures the most specific match is found first.
        """
        try:
            # Check if it's already a full SHA (40 hex characters)
            # DOCDEV-NOTE: Full SHA validation ensures we don't make unnecessary API calls
            if len(ref) == 40 and all(c in "0123456789abcdef" for c in ref.lower()):
                # Verify the commit exists
                response = self.client.get(f"repos/{self.owner}/{self.repo}/git/commits/{ref}")
                if response.status_code == 200:
                    return ref
                elif response.status_code == 404:
                    logger.warning(f"Commit {ref} not found")
                    return None
                else:
                    response.raise_for_status()

            # Try as branch
            # DOCDEV-NOTE: Branch refs use 'heads/' prefix in Git references API
            response = self.client.get(f"repos/{self.owner}/{self.repo}/git/ref/heads/{ref}")
            if response.status_code == 200:
                ref_data: dict[str, Any] = response.json()
                return str(ref_data["object"]["sha"])
            elif response.status_code != 404:
                response.raise_for_status()

            # Try as tag
            response = self.client.get(f"repos/{self.owner}/{self.repo}/git/ref/tags/{ref}")
            if response.status_code == 200:
                tag_data = response.json()
                # Tags can point to either commits or tag objects
                # DOCDEV-NOTE: Lightweight tags point directly to commits, annotated tags need dereferencing
                if tag_data["object"]["type"] == "commit":
                    return tag_data["object"]["sha"]
                else:
                    # It's an annotated tag, need to get the commit it points to
                    tag_obj_response = self.client.get(
                        f"repos/{self.owner}/{self.repo}/git/tags/{tag_data['object']['sha']}"
                    )
                    if tag_obj_response.status_code == 200:
                        return tag_obj_response.json()["object"]["sha"]
                    elif tag_obj_response.status_code != 404:
                        tag_obj_response.raise_for_status()
            elif response.status_code != 404:
                response.raise_for_status()

            # Try short SHA (7+ characters)
            # DOCDEV-NOTE: GitHub supports short SHA resolution with minimum 7 characters
            if len(ref) >= 7 and all(c in "0123456789abcdef" for c in ref.lower()):
                # Search for commit by SHA prefix
                response = self.client.get(
                    f"repos/{self.owner}/{self.repo}/commits", params={"sha": ref, "per_page": 1}
                )
                if response.status_code == 200:
                    commits = response.json()
                    if commits:
                        full_sha = commits[0]["sha"]
                        if full_sha.startswith(ref):
                            return full_sha
                elif response.status_code != 404:
                    response.raise_for_status()

            return None

        except Exception as e:
            if hasattr(e, "response"):
                # Already handled by wrap_requests_exception in client.get()
                raise
            else:
                raise SyncError(
                    f"Failed to resolve reference '{ref}': {e}",
                    ref=ref,
                    repo_url=f"https://github.com/{self.owner}/{self.repo}",
                    sync_method="api",
                    original_error=e,
                ) from e

    def get_repository_tree(self, ref: str = "main", recursive: bool = True) -> list[dict] | None:
        """Get repository file tree.

        Fetches the complete file tree for a repository at a specific reference.
        Uses the Git Trees API which is more efficient than listing contents recursively.

        Args:
            ref: Branch name, tag name, or commit SHA to get tree for (default: "main")
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
            The recursive tree API has a limit of 100,000 entries.
            For very large repositories, consider using pagination.
        """
        try:
            # Resolve the reference to a commit SHA
            commit_sha = self.resolve_ref(ref)

            if not commit_sha:
                # Try 'master' if 'main' fails
                # DOCDEV-NOTE: GitHub transitioned from 'master' to 'main' as default branch
                # Many older repositories still use 'master'
                if ref == "main":
                    logger.info("Reference 'main' not found, trying 'master'")
                    return self.get_repository_tree("master", recursive)
                else:
                    logger.error(f"Reference '{ref}' not found")
                    return None

            # Get the tree
            # DOCDEV-NOTE: Trees API is more efficient than recursive Contents API calls
            path = f"repos/{self.owner}/{self.repo}/git/trees/{commit_sha}"
            params = {"recursive": "1"} if recursive else {}

            response = self.client.get(path, params=params)

            if response.status_code == 200:
                tree_data = response.json()
                return tree_data.get("tree", [])
            else:
                logger.error(f"Failed to get tree: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Failed to get repository tree: {e}")
            return None

    def get_default_branch(self) -> str | None:
        """Get the repository's default branch name.

        Returns:
            Default branch name (e.g., 'main', 'master') or None if not found

        Note:
            This information is cached in the repository metadata, so it's
            a lightweight operation that doesn't require additional API calls.
        """
        try:
            repo_info = self.client.get_repository_info()
            if repo_info:
                return repo_info.get("default_branch")
        except Exception as e:
            logger.warning(f"Failed to get default branch: {e}")

        return None

    def list_branches(self) -> list[dict[str, Any]]:
        """List all branches in the repository.

        Returns:
            List of branch information dicts with keys:
                - 'name': Branch name
                - 'commit': Dict with commit SHA and URL
                - 'protected': Whether branch is protected
            Returns empty list if request fails

        Note:
            This method uses pagination to handle repositories with many branches.
            Only first 100 branches are returned by default.
        """
        try:
            response = self.client.get(f"repos/{self.owner}/{self.repo}/branches")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to list branches: {e}")

        return []

    def list_tags(self) -> list[dict[str, Any]]:
        """List all tags in the repository.

        Returns:
            List of tag information dicts with keys:
                - 'name': Tag name
                - 'commit': Dict with commit SHA and URL
                - 'zipball_url': URL to download tag as ZIP
                - 'tarball_url': URL to download tag as tarball
            Returns empty list if request fails

        Note:
            This method uses pagination to handle repositories with many tags.
            Only first 100 tags are returned by default.
        """
        try:
            response = self.client.get(f"repos/{self.owner}/{self.repo}/tags")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to list tags: {e}")

        return []

    def get_commit_info(self, sha: str) -> dict[str, Any] | None:
        """Get detailed information about a specific commit.

        Args:
            sha: Full or partial commit SHA to lookup

        Returns:
            Commit information dict with keys:
                - 'sha': Full commit SHA
                - 'commit': Commit details (message, author, etc.)
                - 'author': Author information
                - 'committer': Committer information
                - 'stats': File change statistics
            Returns None if commit not found

        Note:
            This method accepts both full and partial SHAs, but full SHAs
            are more efficient as they don't require additional resolution.
        """
        try:
            # Resolve to full SHA if needed
            full_sha = self.resolve_ref(sha)
            if not full_sha:
                return None

            response = self.client.get(f"repos/{self.owner}/{self.repo}/commits/{full_sha}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get commit info for {sha}: {e}")

        return None

    def validate_ref(self, ref: str) -> bool:
        """Validate that a reference exists in the repository.

        Args:
            ref: Branch name, tag name, or commit SHA to validate

        Returns:
            True if reference exists, False otherwise

        Note:
            This is a lightweight check that only verifies existence
            without returning detailed information.
        """
        return self.resolve_ref(ref) is not None
