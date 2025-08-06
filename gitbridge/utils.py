"""Common utilities for GitBridge"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def expand_path(path: str) -> str:
    """Expand user home directory and environment variables in a path.

    This function handles both user home directory expansion (~ characters)
    and environment variable expansion ($VAR or ${VAR} patterns).

    Args:
        path: The path string to expand

    Returns:
        The expanded path string

    Example:
        >>> expand_path("~/Documents/$USER/files")
        "/home/username/Documents/username/files"
    """
    if not path or not isinstance(path, str):
        return path

    # First expand user home directory (~)
    expanded = os.path.expanduser(path)

    # Then expand environment variables
    expanded = os.path.expandvars(expanded)

    return expanded


def parse_github_url(url: str) -> tuple[str, str]:
    """Parse GitHub URL to extract owner and repo name.

    Args:
        url: GitHub repository URL

    Returns:
        Tuple of (owner, repo)

    Raises:
        ConfigurationError: If URL is not a valid GitHub repository URL
    """
    try:
        parsed = urlparse(url)

        if parsed.netloc not in ["github.com", "www.github.com"]:
            raise ConfigurationError(
                f"Not a GitHub URL: {url}. Must be a github.com URL.", invalid_key="repository.url"
            )

        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) < 2:
            raise ConfigurationError(
                f"Invalid GitHub repository URL: {url}. Must be in format https://github.com/owner/repo",
                invalid_key="repository.url",
            )

        owner, repo = path_parts[0], path_parts[1]

        # Remove .git suffix if present
        if repo.endswith(".git"):
            repo = repo[:-4]

        return owner, repo
    except ConfigurationError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise ConfigurationError(
            f"Failed to parse GitHub URL: {url}", invalid_key="repository.url", original_error=e
        ) from e


def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def load_file_hashes(hash_file: Path) -> dict[str, str]:
    """Load file hashes from cache file."""
    if not hash_file.exists():
        return {}

    try:
        with open(hash_file) as f:
            data: dict[str, str] = json.load(f)
            return data
    except Exception as e:
        logger.warning(f"Failed to load hash cache: {e}")
        return {}


def save_file_hashes(hash_file: Path, hashes: dict[str, str]) -> None:
    """Save file hashes to cache file."""
    hash_file.parent.mkdir(parents=True, exist_ok=True)

    with open(hash_file, "w") as f:
        json.dump(hashes, f, indent=2)


def ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def is_binary_file(content: bytes, sample_size: int = 8192) -> bool:
    """Check if file content appears to be binary."""
    if not content:
        return False

    # Check for null bytes in the first chunk
    sample = content[: min(len(content), sample_size)]
    return b"\x00" in sample


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    size_float = float(size)
    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024.0:
            return f"{size_float:.1f} {unit}"
        size_float = size_float / 1024.0
    return f"{size_float:.1f} TB"


class SyncStats:
    """Track synchronization statistics."""

    def __init__(self) -> None:
        self.files_checked = 0
        self.files_downloaded = 0
        self.files_skipped = 0
        self.files_failed = 0
        self.bytes_downloaded = 0
        self.directories_created = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "files_checked": self.files_checked,
            "files_downloaded": self.files_downloaded,
            "files_skipped": self.files_skipped,
            "files_failed": self.files_failed,
            "bytes_downloaded": self.bytes_downloaded,
            "bytes_downloaded_formatted": format_size(self.bytes_downloaded),
            "directories_created": self.directories_created,
        }

    def print_summary(self) -> None:
        """Print summary of sync statistics."""
        print("\n=== Sync Summary ===")
        print(f"Files checked: {self.files_checked}")
        print(f"Files downloaded: {self.files_downloaded}")
        print(f"Files skipped: {self.files_skipped}")
        print(f"Files failed: {self.files_failed}")
        print(f"Data transferred: {format_size(self.bytes_downloaded)}")
        print(f"Directories created: {self.directories_created}")
