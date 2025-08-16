"""Custom exception classes for GitBridge.

This module defines a comprehensive exception hierarchy for better error handling
throughout the GitBridge application. The exceptions provide specific error types
for different failure scenarios and include context information for debugging.

Exception Hierarchy:
    GitBridgeError (base)
    ├── AuthenticationError
    ├── NetworkError
    │   ├── RateLimitError
    │   └── ProxyError
    ├── ConfigurationError
    ├── RepositoryNotFoundError
    ├── FileSystemError
    │   ├── FileWriteError
    │   └── DirectoryCreateError
    ├── BrowserError
    │   ├── WebDriverError
    │   └── PageLoadError
    └── SyncError

Usage:
    try:
        syncer.sync()
    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e}")
        # Handle rate limiting
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        # Handle auth failure
    except GitBridgeError as e:
        # Catch all other GitBridge-specific errors
        logger.error(f"Sync failed: {e}")
"""

from typing import Any


class GitBridgeError(Exception):
    """Base exception for all GitBridge-related errors.

    This is the base class for all custom exceptions in GitBridge.
    It provides common functionality for error handling and context preservation.

    Attributes:
        message (str): Human-readable error message
        details (Dict[str, Any]): Additional error context and details
        original_error (Optional[Exception]): Original exception that caused this error
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None, original_error: Exception | None = None):
        """Initialize GitBridge base exception.

        Args:
            message: Human-readable error message
            details: Additional error context (e.g., {'url': '...', 'status_code': 404})
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_error = original_error

    def __str__(self) -> str:
        """Return formatted error message with context."""
        if self.details:
            context = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({context})"
        return self.message

    def get_context(self) -> dict[str, Any]:
        """Get full error context including details and original error."""
        context = {"message": self.message, "type": self.__class__.__name__, "details": self.details}
        if self.original_error:
            context["original_error"] = {
                "type": self.original_error.__class__.__name__,
                "message": str(self.original_error),
            }
        return context


class SecurityError(GitBridgeError):
    """Security-related errors.

    Raised when security violations are detected, such as:
    - Path traversal attempts
    - Invalid or malicious proxy URLs
    - File size limit violations (DoS prevention)
    - Unsafe certificate operations

    This is a critical error type that should be logged and monitored.
    """

    def __init__(
        self,
        message: str = "Security violation detected",
        violation_type: str | None = None,
        attempted_path: str | None = None,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize security error.

        Args:
            message: Specific security error message
            violation_type: Type of security violation (e.g., 'path_traversal', 'size_limit')
            attempted_path: Path or resource that triggered the violation
            details: Additional security context
            original_error: Original exception if any
        """
        sec_details = details or {}
        if violation_type:
            sec_details["violation_type"] = violation_type
        if attempted_path:
            sec_details["attempted_path"] = attempted_path
        super().__init__(message, sec_details, original_error)


class AuthenticationError(GitBridgeError):
    """Authentication-related errors.

    Raised when GitHub authentication fails due to invalid tokens,
    insufficient permissions, or other auth-related issues.

    Common scenarios:
        - Invalid or expired GitHub token
        - Insufficient repository permissions
        - Rate limit exceeded due to lack of authentication
        - Two-factor authentication required
    """

    def __init__(
        self,
        message: str = "GitHub authentication failed",
        token_provided: bool = False,
        repo_url: str | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize authentication error.

        Args:
            message: Specific authentication error message
            token_provided: Whether a token was provided for authentication
            repo_url: Repository URL that failed authentication
            original_error: Original exception that caused this error
        """
        details = {"token_provided": token_provided, "repo_url": repo_url}
        super().__init__(message, {k: v for k, v in details.items() if v is not None}, original_error)


class NetworkError(GitBridgeError):
    """Network-related errors.

    Base class for all network connectivity issues including
    connection timeouts, DNS resolution failures, and proxy issues.
    """

    def __init__(
        self,
        message: str = "Network error occurred",
        url: str | None = None,
        status_code: int | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize network error.

        Args:
            message: Network error description
            url: URL that failed to connect
            status_code: HTTP status code if applicable
            original_error: Original network exception
        """
        details = {"url": url, "status_code": status_code}
        super().__init__(message, {k: v for k, v in details.items() if v is not None}, original_error)


class RateLimitError(NetworkError):
    """GitHub API rate limit exceeded.

    Raised when the GitHub API rate limit is exceeded. Contains information
    about current rate limit status and when it resets.
    """

    def __init__(
        self,
        message: str = "GitHub API rate limit exceeded",
        remaining: int | None = None,
        limit: int | None = None,
        reset_time: int | None = None,
        url: str | None = None,
        status_code: int | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize rate limit error.

        Args:
            message: Rate limit error message
            remaining: Remaining API requests
            limit: Total API request limit
            reset_time: Unix timestamp when rate limit resets
            url: URL that triggered the rate limit
            status_code: HTTP status code (typically 403 or 429)
            original_error: Original exception
        """
        # Pass url and status_code to parent NetworkError
        super().__init__(message, url=url, status_code=status_code, original_error=original_error)
        # Add rate limit specific details
        rate_limit_details = {"remaining": remaining, "limit": limit, "reset_time": reset_time}
        self.details.update({k: v for k, v in rate_limit_details.items() if v is not None})


class ProxyError(NetworkError):
    """Proxy configuration or connection errors.

    Raised when proxy auto-detection fails or proxy connections cannot be established.
    """

    def __init__(
        self,
        message: str = "Proxy configuration error",
        proxy_url: str | None = None,
        auto_detection_failed: bool = False,
        url: str | None = None,
        status_code: int | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize proxy error.

        Args:
            message: Proxy error description
            proxy_url: Proxy URL that failed
            auto_detection_failed: Whether proxy auto-detection failed
            url: URL that triggered the proxy error
            status_code: HTTP status code if applicable
            original_error: Original exception
        """
        # Pass url and status_code to parent NetworkError
        super().__init__(message, url=url, status_code=status_code, original_error=original_error)
        # Add proxy specific details
        proxy_details = {"proxy_url": proxy_url, "auto_detection_failed": auto_detection_failed}
        self.details.update({k: v for k, v in proxy_details.items() if v is not None})


class ConfigurationError(GitBridgeError):
    """Configuration validation and loading errors.

    Raised when configuration files are invalid, required settings are missing,
    or configuration values are out of range.
    """

    def __init__(
        self,
        message: str = "Configuration error",
        config_file: str | None = None,
        invalid_key: str | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize configuration error.

        Args:
            message: Configuration error description
            config_file: Path to configuration file with error
            invalid_key: Configuration key that is invalid
            original_error: Original exception
        """
        details = {"config_file": config_file, "invalid_key": invalid_key}
        super().__init__(message, {k: v for k, v in details.items() if v is not None}, original_error)


class RepositoryNotFoundError(GitBridgeError):
    """Repository not found or not accessible.

    Raised when a GitHub repository doesn't exist, is private without
    proper authentication, or the URL is malformed.
    """

    def __init__(
        self,
        message: str = "Repository not found or not accessible",
        repo_url: str | None = None,
        owner: str | None = None,
        repo: str | None = None,
        is_private: bool | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize repository not found error.

        Args:
            message: Repository error description
            repo_url: Full repository URL
            owner: Repository owner/organization
            repo: Repository name
            is_private: Whether repository appears to be private
            original_error: Original exception
        """
        details = {"repo_url": repo_url, "owner": owner, "repo": repo, "is_private": is_private}
        super().__init__(message, {k: v for k, v in details.items() if v is not None}, original_error)


class FileSystemError(GitBridgeError):
    """File system operation errors.

    Base class for all file system related errors including
    permission issues, disk space problems, and path errors.
    """

    def __init__(
        self,
        message: str = "File system error",
        path: str | None = None,
        operation: str | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize file system error.

        Args:
            message: File system error description
            path: File or directory path that caused the error
            operation: Operation that failed (e.g., 'write', 'create', 'delete')
            original_error: Original file system exception
        """
        details = {"path": path, "operation": operation}
        super().__init__(message, {k: v for k, v in details.items() if v is not None}, original_error)


class FileWriteError(FileSystemError):
    """File write operation failed.

    Raised when writing files to the local filesystem fails due to
    permissions, disk space, or other I/O issues.
    """

    def __init__(
        self,
        message: str = "Failed to write file",
        file_path: str | None = None,
        size: int | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize file write error.

        Args:
            message: Write error description
            file_path: Path to file that couldn't be written
            size: Size of content that failed to write
            original_error: Original I/O exception
        """
        super().__init__(message, file_path, "write", original_error)
        if size is not None:
            self.details["size"] = size


class DirectoryCreateError(FileSystemError):
    """Directory creation failed.

    Raised when creating directories fails due to permissions
    or other file system issues.
    """

    def __init__(
        self,
        message: str = "Failed to create directory",
        dir_path: str | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize directory creation error.

        Args:
            message: Directory creation error description
            dir_path: Path to directory that couldn't be created
            original_error: Original file system exception
        """
        super().__init__(message, dir_path, "create", original_error)


class BrowserError(GitBridgeError):
    """Browser automation errors.

    Base class for all Selenium WebDriver and browser automation
    related errors.
    """

    def __init__(
        self,
        message: str = "Browser automation error",
        browser: str | None = None,
        url: str | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize browser error.

        Args:
            message: Browser error description
            browser: Browser type (e.g., 'chrome', 'firefox')
            url: URL that caused the error
            original_error: Original Selenium exception
        """
        details = {"browser": browser, "url": url}
        super().__init__(message, {k: v for k, v in details.items() if v is not None}, original_error)


class WebDriverError(BrowserError):
    """WebDriver initialization or operation failed.

    Raised when WebDriver cannot be initialized or WebDriver
    operations fail.
    """

    def __init__(
        self,
        message: str = "WebDriver error",
        driver_path: str | None = None,
        browser_binary: str | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize WebDriver error.

        Args:
            message: WebDriver error description
            driver_path: Path to WebDriver binary
            browser_binary: Path to browser binary
            original_error: Original Selenium WebDriver exception
        """
        details = {"driver_path": driver_path, "browser_binary": browser_binary}
        super().__init__(message, "chrome", None, original_error)
        self.details.update({k: v for k, v in details.items() if v is not None})


class PageLoadError(BrowserError):
    """Web page loading failed.

    Raised when browser fails to load a web page or page
    elements cannot be found.
    """

    def __init__(
        self,
        message: str = "Page load error",
        url: str | None = None,
        timeout: int | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize page load error.

        Args:
            message: Page load error description
            url: URL that failed to load
            timeout: Timeout value in seconds
            original_error: Original Selenium exception
        """
        super().__init__(message, "chrome", url, original_error)
        if timeout is not None:
            self.details["timeout"] = timeout


class SyncError(GitBridgeError):
    """General synchronization process errors.

    Raised for sync-specific errors that don't fit into other
    categories, such as reference resolution failures or
    tree parsing errors.
    """

    def __init__(
        self,
        message: str = "Synchronization error",
        ref: str | None = None,
        repo_url: str | None = None,
        sync_method: str | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize sync error.

        Args:
            message: Sync error description
            ref: Git reference that failed (branch/tag/commit)
            repo_url: Repository URL being synced
            sync_method: Sync method used ('api' or 'browser')
            original_error: Original exception
        """
        details = {"ref": ref, "repo_url": repo_url, "sync_method": sync_method}
        super().__init__(message, {k: v for k, v in details.items() if v is not None}, original_error)


# DOCDEV-NOTE: Exception utility functions for common error scenarios
def wrap_requests_exception(error: Exception, url: str) -> GitBridgeError:
    """Convert requests exceptions to appropriate GitBridge exceptions.

    Args:
        error: Original requests exception
        url: URL that caused the error

    Returns:
        Appropriate GitBridge exception with context
    """
    import requests

    if isinstance(error, requests.exceptions.ConnectionError):
        return NetworkError("Connection failed", url=url, original_error=error)
    elif isinstance(error, requests.exceptions.Timeout):
        return NetworkError("Request timeout", url=url, original_error=error)
    elif isinstance(error, requests.exceptions.HTTPError):
        status_code = getattr(error.response, "status_code", None)
        if status_code == 401:
            return AuthenticationError("Authentication failed", repo_url=url, original_error=error)
        elif status_code == 403:
            # Could be rate limit or authentication
            if "rate limit" in str(error).lower():
                return RateLimitError("API rate limit exceeded", url=url, status_code=403, original_error=error)
            else:
                return AuthenticationError("Access forbidden", repo_url=url, original_error=error)
        elif status_code == 404:
            return RepositoryNotFoundError("Repository not found", repo_url=url, original_error=error)
        else:
            return NetworkError(f"HTTP error {status_code}", url=url, status_code=status_code, original_error=error)
    else:
        return NetworkError("Network request failed", url=url, original_error=error)


def wrap_file_operation_exception(error: Exception, path: str, operation: str) -> FileSystemError:
    """Convert file operation exceptions to appropriate GitBridge exceptions.

    Args:
        error: Original file system exception
        path: File or directory path
        operation: Operation type ('read', 'write', 'create', 'delete')

    Returns:
        Appropriate FileSystemError subclass
    """
    if operation == "write":
        return FileWriteError(f"Failed to write file: {error}", file_path=path, original_error=error)
    elif operation == "create" and "directory" in str(error).lower():
        return DirectoryCreateError(f"Failed to create directory: {error}", dir_path=path, original_error=error)
    else:
        return FileSystemError(f"File system operation failed: {error}", path=path, operation=operation, original_error=error)


def wrap_playwright_exception(error: Exception, url: str | None = None) -> BrowserError:
    """Convert Playwright exceptions to appropriate GitBridge exceptions.

    Args:
        error: Original Playwright exception
        url: URL that caused the error

    Returns:
        Appropriate BrowserError subclass
    """
    try:
        from playwright._impl._errors import Error as PlaywrightError
        from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError

        if isinstance(error, PlaywrightTimeoutError):
            return PageLoadError(f"Page load timeout: {error}", url=url, original_error=error)
        elif isinstance(error, PlaywrightError):
            if "browser" in str(error).lower() or "launch" in str(error).lower():
                return WebDriverError(f"Browser initialization failed: {error}", original_error=error)
            else:
                return PageLoadError(f"Page operation failed: {error}", url=url, original_error=error)
        else:
            return BrowserError(f"Browser automation failed: {error}", url=url, original_error=error)
    except ImportError:
        # Playwright not available, treat as generic browser error
        return BrowserError(f"Browser automation failed: {error}", url=url, original_error=error)
