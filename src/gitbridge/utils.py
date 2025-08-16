"""Common utilities for GitBridge"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .exceptions import ConfigurationError, SecurityError

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


def validate_safe_path(base_path: Path, file_path: str) -> Path:
    """Validate that file_path doesn't escape base_path (prevent path traversal).

    This function ensures that the resolved file path stays within the
    intended base directory, preventing directory traversal attacks.

    Args:
        base_path: The base directory that files should be contained within
        file_path: The relative file path to validate

    Returns:
        The validated absolute Path object

    Raises:
        SecurityError: If path traversal is detected

    Example:
        >>> base = Path("/home/user/repo")
        >>> validate_safe_path(base, "src/main.py")  # OK
        >>> validate_safe_path(base, "../etc/passwd")  # Raises SecurityError

    DOCDEV-NOTE: Critical security function - prevents path traversal attacks
    """
    # Resolve base path to absolute
    base = base_path.resolve()

    # Combine and resolve the target path
    target = (base / file_path).resolve()

    # Check if target is within base directory
    try:
        # This will raise ValueError if target is not relative to base
        target.relative_to(base)
        return target
    except ValueError as err:
        # Path escapes the base directory - security violation
        raise SecurityError(
            f"Path traversal attempt detected: '{file_path}' would escape base directory",
            violation_type="path_traversal",
            attempted_path=str(file_path),
            details={"base_path": str(base), "resolved_target": str(target)},
        ) from err


def validate_proxy_url(proxy_url: str | None) -> dict[str, Any]:
    """Validate and parse proxy URL safely.

    Validates proxy URLs to prevent injection attacks and ensure
    they conform to expected patterns.

    Args:
        proxy_url: The proxy URL to validate (e.g., "http://proxy:8080")

    Returns:
        Dict with validated proxy configuration:
            - server: The validated proxy server URL
            - username: Optional username (if present)
            - password: Optional password (if present)

    Raises:
        ConfigurationError: If proxy URL is invalid or malformed

    Example:
        >>> validate_proxy_url("http://proxy.example.com:8080")
        {'server': 'http://proxy.example.com:8080', 'username': None, 'password': None}

    DOCDEV-NOTE: Security validation for proxy URLs to prevent injection
    """
    if not proxy_url:
        raise ConfigurationError("Empty proxy URL provided", invalid_key="proxy_url")

    # Check for control characters in the URL before parsing
    suspicious_chars = ["\n", "\r", "\t", "\0"]
    if any(char in proxy_url for char in suspicious_chars):
        raise SecurityError("Proxy URL contains control characters", violation_type="malicious_proxy_url", attempted_path=proxy_url)

    try:
        parsed = urlparse(proxy_url)

        # Validate scheme - only allow safe protocols
        allowed_schemes = {"http", "https", "socks5", "socks5h"}
        if parsed.scheme not in allowed_schemes:
            raise SecurityError(
                f"Invalid proxy scheme '{parsed.scheme}'. Allowed: {allowed_schemes}",
                violation_type="invalid_proxy_scheme",
                attempted_path=proxy_url,
            )

        # Validate hostname
        if not parsed.hostname:
            raise ConfigurationError(f"Proxy URL missing hostname: {proxy_url}", invalid_key="proxy_url")

        # Validate hostname doesn't contain suspicious characters
        suspicious_chars = ["<", ">", '"', "'", "\\", "\n", "\r", "\t"]
        if any(char in parsed.hostname for char in suspicious_chars):
            raise SecurityError(
                "Proxy hostname contains suspicious characters", violation_type="malicious_proxy_url", attempted_path=proxy_url
            )

        # Validate port (must be 1-65535)
        # Check for explicit port 0 which urlparse might accept
        if parsed.port is not None and parsed.port == 0:
            raise ConfigurationError(f"Invalid proxy port: 0. Must be between 1 and 65535. URL: {proxy_url}", invalid_key="proxy_port")

        default_ports = {"http": 80, "https": 443, "socks5": 1080, "socks5h": 1080}
        port = parsed.port or default_ports.get(parsed.scheme, 80)
        if not 1 <= port <= 65535:
            raise ConfigurationError(f"Invalid proxy port: {port}. Must be between 1 and 65535. URL: {proxy_url}", invalid_key="proxy_port")

        # Build validated proxy configuration
        proxy_config: dict[str, Any] = {"server": f"{parsed.scheme}://{parsed.hostname}:{port}"}

        # Add credentials if present (but validate them)
        if parsed.username:
            # Validate username doesn't contain control characters
            if any(ord(char) < 32 for char in parsed.username):
                raise SecurityError(
                    "Proxy username contains control characters", violation_type="malicious_proxy_credentials", attempted_path=proxy_url
                )
            proxy_config["username"] = parsed.username

        if parsed.password:
            # Don't validate password content but ensure it exists
            proxy_config["password"] = parsed.password

        return proxy_config

    except (ConfigurationError, SecurityError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Wrap any other parsing errors
        raise ConfigurationError(f"Failed to parse proxy URL: {e}", invalid_key="proxy_url", original_error=e) from e


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
            raise ConfigurationError(f"Not a GitHub URL: {url}. Must be a github.com URL.", invalid_key="repository.url")

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
        raise ConfigurationError(f"Failed to parse GitHub URL: {url}", invalid_key="repository.url", original_error=e) from e


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
