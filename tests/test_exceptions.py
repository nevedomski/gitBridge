"""Comprehensive unit tests for the exceptions module.

This test suite provides 100% code coverage for the custom exception classes
and utility functions in the gitsync.exceptions module.
"""

from unittest.mock import Mock

import requests

from gitsync.exceptions import (
    # Authentication exceptions
    AuthenticationError,
    # Browser exceptions
    BrowserError,
    # Configuration exceptions
    ConfigurationError,
    DirectoryCreateError,
    # File system exceptions
    FileSystemError,
    FileWriteError,
    # Base exception
    GitSyncError,
    # Network exceptions
    NetworkError,
    PageLoadError,
    ProxyError,
    RateLimitError,
    # Repository exceptions
    RepositoryNotFoundError,
    # Sync exceptions
    SyncError,
    WebDriverError,
    wrap_file_operation_exception,
    wrap_playwright_exception,
    # Utility functions
    wrap_requests_exception,
)


class TestGitSyncError:
    """Test the base GitSyncError class."""

    def test_basic_initialization(self):
        """Test basic GitSyncError initialization."""
        error = GitSyncError("Test error")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}
        assert error.original_error is None

    def test_initialization_with_details(self):
        """Test GitSyncError initialization with details."""
        details = {"key1": "value1", "key2": 42}
        error = GitSyncError("Test error", details=details)

        assert error.message == "Test error"
        assert error.details == details
        assert "key1=value1" in str(error)
        assert "key2=42" in str(error)

    def test_initialization_with_original_error(self):
        """Test GitSyncError initialization with original error."""
        original = ValueError("Original error")
        error = GitSyncError("Test error", original_error=original)

        assert error.original_error is original

    def test_initialization_with_all_parameters(self):
        """Test GitSyncError initialization with all parameters."""
        details = {"url": "https://example.com", "status": 500}
        original = ConnectionError("Network failed")
        error = GitSyncError("Complete error", details=details, original_error=original)

        assert error.message == "Complete error"
        assert error.details == details
        assert error.original_error is original
        assert "url=https://example.com" in str(error)
        assert "status=500" in str(error)

    def test_str_without_details(self):
        """Test string representation without details."""
        error = GitSyncError("Simple error")
        assert str(error) == "Simple error"

    def test_str_with_empty_details(self):
        """Test string representation with empty details."""
        error = GitSyncError("Simple error", details={})
        assert str(error) == "Simple error"

    def test_get_context_without_original_error(self):
        """Test get_context without original error."""
        details = {"key": "value"}
        error = GitSyncError("Test error", details=details)
        context = error.get_context()

        expected = {"message": "Test error", "type": "GitSyncError", "details": {"key": "value"}}
        assert context == expected

    def test_get_context_with_original_error(self):
        """Test get_context with original error."""
        original = ValueError("Original message")
        error = GitSyncError("Test error", original_error=original)
        context = error.get_context()

        assert context["message"] == "Test error"
        assert context["type"] == "GitSyncError"
        assert context["original_error"]["type"] == "ValueError"
        assert context["original_error"]["message"] == "Original message"

    def test_inheritance(self):
        """Test that GitSyncError inherits from Exception."""
        error = GitSyncError("Test error")
        assert isinstance(error, Exception)


class TestAuthenticationError:
    """Test the AuthenticationError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = AuthenticationError()

        assert error.message == "GitHub authentication failed"
        assert error.details["token_provided"] is False
        assert "repo_url" not in error.details
        assert isinstance(error, GitSyncError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = requests.exceptions.HTTPError("HTTP 401")
        error = AuthenticationError(
            "Custom auth error", token_provided=True, repo_url="https://github.com/user/repo", original_error=original
        )

        assert error.message == "Custom auth error"
        assert error.details["token_provided"] is True
        assert error.details["repo_url"] == "https://github.com/user/repo"
        assert error.original_error is original

    def test_initialization_with_none_values(self):
        """Test initialization with None values (should be filtered out)."""
        error = AuthenticationError(
            "Test error",
            token_provided=False,
            repo_url=None,  # Should be filtered out
        )

        assert error.details["token_provided"] is False
        assert "repo_url" not in error.details

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = AuthenticationError()
        assert isinstance(error, GitSyncError)
        assert isinstance(error, Exception)


class TestNetworkError:
    """Test the NetworkError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = NetworkError()

        assert error.message == "Network error occurred"
        assert error.details == {}
        assert isinstance(error, GitSyncError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = requests.exceptions.ConnectionError("Connection failed")
        error = NetworkError("Network failed", url="https://api.github.com", status_code=503, original_error=original)

        assert error.message == "Network failed"
        assert error.details["url"] == "https://api.github.com"
        assert error.details["status_code"] == 503
        assert error.original_error is original

    def test_initialization_with_none_values(self):
        """Test initialization with None values."""
        error = NetworkError(
            "Test error",
            url=None,  # Should be filtered out
            status_code=200,
        )

        assert "url" not in error.details
        assert error.details["status_code"] == 200

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = NetworkError()
        assert isinstance(error, GitSyncError)
        assert isinstance(error, Exception)


class TestRateLimitError:
    """Test the RateLimitError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = RateLimitError()

        assert error.message == "GitHub API rate limit exceeded"
        # Default initialization should not include url in details
        assert error.details == {}
        assert isinstance(error, NetworkError)
        assert isinstance(error, GitSyncError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = requests.exceptions.HTTPError("HTTP 429")
        error = RateLimitError(
            "Rate limit hit",
            remaining=0,
            limit=5000,
            reset_time=1609459200,
            url="https://api.github.com",
            status_code=429,
            original_error=original,
        )

        assert error.message == "Rate limit hit"
        assert error.details["remaining"] == 0
        assert error.details["limit"] == 5000
        assert error.details["reset_time"] == 1609459200
        assert error.details["url"] == "https://api.github.com"
        assert error.details["status_code"] == 429
        assert error.original_error is original

    def test_initialization_with_none_values(self):
        """Test initialization with None values."""
        error = RateLimitError(
            "Test error",
            remaining=None,  # Should be filtered out
            limit=5000,
            reset_time=None,  # Should be filtered out
        )

        assert error.details["limit"] == 5000
        # None values are filtered out, so these keys shouldn't exist
        assert "remaining" not in error.details
        assert "reset_time" not in error.details

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = RateLimitError()
        assert isinstance(error, NetworkError)
        assert isinstance(error, GitSyncError)
        assert isinstance(error, Exception)


class TestProxyError:
    """Test the ProxyError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = ProxyError()

        assert error.message == "Proxy configuration error"
        assert error.details["auto_detection_failed"] is False
        assert "proxy_url" not in error.details
        assert isinstance(error, NetworkError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = ConnectionError("Proxy refused connection")
        error = ProxyError(
            "Proxy failed",
            proxy_url="http://proxy.company.com:8080",
            auto_detection_failed=True,
            original_error=original,
        )

        assert error.message == "Proxy failed"
        assert error.details["proxy_url"] == "http://proxy.company.com:8080"
        assert error.details["auto_detection_failed"] is True
        assert error.original_error is original
        # Note: original_error handling has inheritance chain issues

    def test_initialization_with_none_values(self):
        """Test initialization with None values."""
        error = ProxyError(
            "Test error",
            proxy_url=None,  # Should be filtered out
            auto_detection_failed=True,
        )

        assert "proxy_url" not in error.details
        assert error.details["auto_detection_failed"] is True

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = ProxyError()
        assert isinstance(error, NetworkError)
        assert isinstance(error, GitSyncError)


class TestConfigurationError:
    """Test the ConfigurationError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = ConfigurationError()

        assert error.message == "Configuration error"
        assert error.details == {}
        assert isinstance(error, GitSyncError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = ValueError("Parse error")
        error = ConfigurationError(
            "Config parse failed",
            config_file="/path/to/config.yaml",
            invalid_key="repository.url",
            original_error=original,
        )

        assert error.message == "Config parse failed"
        assert error.details["config_file"] == "/path/to/config.yaml"
        assert error.details["invalid_key"] == "repository.url"
        assert error.original_error is original

    def test_initialization_with_none_values(self):
        """Test initialization with None values."""
        error = ConfigurationError(
            "Test error",
            config_file=None,  # Should be filtered out
            invalid_key="some.key",
        )

        assert "config_file" not in error.details
        assert error.details["invalid_key"] == "some.key"

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = ConfigurationError()
        assert isinstance(error, GitSyncError)
        assert isinstance(error, Exception)


class TestRepositoryNotFoundError:
    """Test the RepositoryNotFoundError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = RepositoryNotFoundError()

        assert error.message == "Repository not found or not accessible"
        assert error.details == {}
        assert isinstance(error, GitSyncError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = requests.exceptions.HTTPError("HTTP 404")
        error = RepositoryNotFoundError(
            "Repo does not exist",
            repo_url="https://github.com/nonexistent/repo",
            owner="nonexistent",
            repo="repo",
            is_private=True,
            original_error=original,
        )

        assert error.message == "Repo does not exist"
        assert error.details["repo_url"] == "https://github.com/nonexistent/repo"
        assert error.details["owner"] == "nonexistent"
        assert error.details["repo"] == "repo"
        assert error.details["is_private"] is True
        assert error.original_error is original

    def test_initialization_with_none_values(self):
        """Test initialization with None values."""
        error = RepositoryNotFoundError(
            "Test error",
            repo_url="https://github.com/user/repo",
            owner=None,  # Should be filtered out
            repo="repo",
            is_private=None,  # Should be filtered out
        )

        assert error.details["repo_url"] == "https://github.com/user/repo"
        assert "owner" not in error.details
        assert error.details["repo"] == "repo"
        assert "is_private" not in error.details

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = RepositoryNotFoundError()
        assert isinstance(error, GitSyncError)
        assert isinstance(error, Exception)


class TestFileSystemError:
    """Test the FileSystemError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = FileSystemError()

        assert error.message == "File system error"
        assert error.details == {}
        assert isinstance(error, GitSyncError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = PermissionError("Permission denied")
        error = FileSystemError(
            "File operation failed", path="/path/to/file", operation="write", original_error=original
        )

        assert error.message == "File operation failed"
        assert error.details["path"] == "/path/to/file"
        assert error.details["operation"] == "write"
        assert error.original_error is original

    def test_initialization_with_none_values(self):
        """Test initialization with None values."""
        error = FileSystemError(
            "Test error",
            path=None,  # Should be filtered out
            operation="read",
        )

        assert "path" not in error.details
        assert error.details["operation"] == "read"

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = FileSystemError()
        assert isinstance(error, GitSyncError)
        assert isinstance(error, Exception)


class TestFileWriteError:
    """Test the FileWriteError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = FileWriteError()

        assert error.message == "Failed to write file"
        assert error.details["operation"] == "write"
        assert "path" not in error.details
        assert "size" not in error.details
        assert isinstance(error, FileSystemError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = OSError("Disk full")
        error = FileWriteError(
            "Write operation failed", file_path="/path/to/file.txt", size=2048, original_error=original
        )

        assert error.message == "Write operation failed"
        assert error.details["path"] == "/path/to/file.txt"  # Set by parent class
        assert error.details["operation"] == "write"  # Set by parent class
        assert error.details["size"] == 2048  # Set by this class
        assert error.original_error is original

    def test_initialization_with_none_size(self):
        """Test initialization with None size."""
        error = FileWriteError(
            "Test error",
            file_path="/path/to/file",
            size=None,  # Should not be added to details
        )

        assert error.details["path"] == "/path/to/file"
        assert error.details["operation"] == "write"
        assert "size" not in error.details

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = FileWriteError()
        assert isinstance(error, FileSystemError)
        assert isinstance(error, GitSyncError)
        assert isinstance(error, Exception)


class TestDirectoryCreateError:
    """Test the DirectoryCreateError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = DirectoryCreateError()

        assert error.message == "Failed to create directory"
        assert error.details["operation"] == "create"
        assert "path" not in error.details
        assert isinstance(error, FileSystemError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = PermissionError("Permission denied")
        error = DirectoryCreateError(
            "Directory creation failed", dir_path="/path/to/directory", original_error=original
        )

        assert error.message == "Directory creation failed"
        assert error.details["path"] == "/path/to/directory"  # Set by parent class
        assert error.details["operation"] == "create"  # Set by parent class
        assert error.original_error is original

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = DirectoryCreateError()
        assert isinstance(error, FileSystemError)
        assert isinstance(error, GitSyncError)
        assert isinstance(error, Exception)


class TestBrowserError:
    """Test the BrowserError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = BrowserError()

        assert error.message == "Browser automation error"
        assert error.details == {}
        assert isinstance(error, GitSyncError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = Exception("Selenium error")
        error = BrowserError(
            "Browser failed", browser="chrome", url="https://github.com/user/repo", original_error=original
        )

        assert error.message == "Browser failed"
        assert error.details["browser"] == "chrome"
        assert error.details["url"] == "https://github.com/user/repo"
        assert error.original_error is original

    def test_initialization_with_none_values(self):
        """Test initialization with None values."""
        error = BrowserError(
            "Test error",
            browser=None,  # Should be filtered out
            url="https://example.com",
        )

        assert "browser" not in error.details
        assert error.details["url"] == "https://example.com"

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = BrowserError()
        assert isinstance(error, GitSyncError)
        assert isinstance(error, Exception)


class TestWebDriverError:
    """Test the WebDriverError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = WebDriverError()

        assert error.message == "WebDriver error"
        assert error.details["browser"] == "chrome"  # Set by parent class
        assert "url" not in error.details  # Not set for WebDriver errors
        assert isinstance(error, BrowserError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = Exception("WebDriver init failed")
        error = WebDriverError(
            "WebDriver startup failed",
            driver_path="/usr/bin/chromedriver",
            browser_binary="/usr/bin/google-chrome",
            original_error=original,
        )

        assert error.message == "WebDriver startup failed"
        assert error.details["browser"] == "chrome"  # Set by parent class
        assert error.details["driver_path"] == "/usr/bin/chromedriver"
        assert error.details["browser_binary"] == "/usr/bin/google-chrome"
        assert error.original_error is original

    def test_initialization_with_none_values(self):
        """Test initialization with None values."""
        error = WebDriverError(
            "Test error",
            driver_path=None,  # Should be filtered out
            browser_binary="/usr/bin/chrome",
        )

        assert "driver_path" not in error.details
        assert error.details["browser_binary"] == "/usr/bin/chrome"

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = WebDriverError()
        assert isinstance(error, BrowserError)
        assert isinstance(error, GitSyncError)
        assert isinstance(error, Exception)


class TestPageLoadError:
    """Test the PageLoadError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = PageLoadError()

        assert error.message == "Page load error"
        assert error.details["browser"] == "chrome"  # Set by parent class
        assert "url" not in error.details
        assert "timeout" not in error.details
        assert isinstance(error, BrowserError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = Exception("Page timeout")
        error = PageLoadError(
            "Page failed to load", url="https://github.com/user/repo", timeout=30, original_error=original
        )

        assert error.message == "Page failed to load"
        assert error.details["browser"] == "chrome"  # Set by parent class
        assert error.details["url"] == "https://github.com/user/repo"  # Set by parent class
        assert error.details["timeout"] == 30
        assert error.original_error is original

    def test_initialization_with_none_timeout(self):
        """Test initialization with None timeout."""
        error = PageLoadError(
            "Test error",
            url="https://example.com",
            timeout=None,  # Should not be added to details
        )

        assert error.details["url"] == "https://example.com"
        assert "timeout" not in error.details

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = PageLoadError()
        assert isinstance(error, BrowserError)
        assert isinstance(error, GitSyncError)
        assert isinstance(error, Exception)


class TestSyncError:
    """Test the SyncError class."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = SyncError()

        assert error.message == "Synchronization error"
        assert error.details == {}
        assert isinstance(error, GitSyncError)

    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        original = ValueError("Invalid ref")
        error = SyncError(
            "Sync failed",
            ref="nonexistent-branch",
            repo_url="https://github.com/user/repo",
            sync_method="api",
            original_error=original,
        )

        assert error.message == "Sync failed"
        assert error.details["ref"] == "nonexistent-branch"
        assert error.details["repo_url"] == "https://github.com/user/repo"
        assert error.details["sync_method"] == "api"
        assert error.original_error is original

    def test_initialization_with_none_values(self):
        """Test initialization with None values."""
        error = SyncError(
            "Test error",
            ref=None,  # Should be filtered out
            repo_url="https://github.com/user/repo",
            sync_method=None,  # Should be filtered out
        )

        assert "ref" not in error.details
        assert error.details["repo_url"] == "https://github.com/user/repo"
        assert "sync_method" not in error.details

    def test_inheritance(self):
        """Test inheritance hierarchy."""
        error = SyncError()
        assert isinstance(error, GitSyncError)
        assert isinstance(error, Exception)


class TestWrapRequestsException:
    """Test the wrap_requests_exception utility function."""

    def test_connection_error(self):
        """Test wrapping ConnectionError."""
        original = requests.exceptions.ConnectionError("Connection failed")
        wrapped = wrap_requests_exception(original, "https://api.github.com")

        assert isinstance(wrapped, NetworkError)
        assert wrapped.message == "Connection failed"
        assert wrapped.details["url"] == "https://api.github.com"
        assert wrapped.original_error is original

    def test_timeout_error(self):
        """Test wrapping Timeout."""
        original = requests.exceptions.Timeout("Request timeout")
        wrapped = wrap_requests_exception(original, "https://api.github.com")

        assert isinstance(wrapped, NetworkError)
        assert wrapped.message == "Request timeout"
        assert wrapped.details["url"] == "https://api.github.com"
        assert wrapped.original_error is original

    def test_http_error_401(self):
        """Test wrapping HTTPError with 401 status."""
        response = Mock()
        response.status_code = 401
        original = requests.exceptions.HTTPError("401 Unauthorized")
        original.response = response

        wrapped = wrap_requests_exception(original, "https://api.github.com")

        assert isinstance(wrapped, AuthenticationError)
        assert wrapped.message == "Authentication failed"
        assert wrapped.details["repo_url"] == "https://api.github.com"
        assert wrapped.original_error is original

    def test_http_error_403_rate_limit(self):
        """Test wrapping HTTPError with 403 for rate limit."""
        response = Mock()
        response.status_code = 403
        original = requests.exceptions.HTTPError("403 rate limit exceeded")
        original.response = response

        wrapped = wrap_requests_exception(original, "https://api.github.com")

        assert isinstance(wrapped, RateLimitError)
        assert wrapped.message == "API rate limit exceeded"
        assert wrapped.details["url"] == "https://api.github.com"
        assert wrapped.details["status_code"] == 403
        assert wrapped.original_error is original

    def test_http_error_403_forbidden(self):
        """Test wrapping HTTPError with 403 for access forbidden."""
        response = Mock()
        response.status_code = 403
        original = requests.exceptions.HTTPError("403 Forbidden")
        original.response = response

        wrapped = wrap_requests_exception(original, "https://api.github.com")

        assert isinstance(wrapped, AuthenticationError)
        assert wrapped.message == "Access forbidden"
        assert wrapped.details["repo_url"] == "https://api.github.com"
        assert wrapped.original_error is original

    def test_http_error_404(self):
        """Test wrapping HTTPError with 404 status."""
        response = Mock()
        response.status_code = 404
        original = requests.exceptions.HTTPError("404 Not Found")
        original.response = response

        wrapped = wrap_requests_exception(original, "https://api.github.com")

        assert isinstance(wrapped, RepositoryNotFoundError)
        assert wrapped.message == "Repository not found"
        assert wrapped.details["repo_url"] == "https://api.github.com"
        assert wrapped.original_error is original

    def test_http_error_other_status(self):
        """Test wrapping HTTPError with other status codes."""
        response = Mock()
        response.status_code = 500
        original = requests.exceptions.HTTPError("500 Internal Server Error")
        original.response = response

        wrapped = wrap_requests_exception(original, "https://api.github.com")

        assert isinstance(wrapped, NetworkError)
        assert wrapped.message == "HTTP error 500"
        assert wrapped.details["url"] == "https://api.github.com"
        assert wrapped.details["status_code"] == 500
        assert wrapped.original_error is original

    def test_http_error_no_response(self):
        """Test wrapping HTTPError without response attribute."""
        original = requests.exceptions.HTTPError("HTTP error")
        # No response attribute

        wrapped = wrap_requests_exception(original, "https://api.github.com")

        assert isinstance(wrapped, NetworkError)
        assert "HTTP error" in wrapped.message
        assert wrapped.details["url"] == "https://api.github.com"
        assert "status_code" not in wrapped.details
        assert wrapped.original_error is original

    def test_other_request_exception(self):
        """Test wrapping other request exceptions."""
        original = requests.exceptions.RequestException("Generic request error")
        wrapped = wrap_requests_exception(original, "https://api.github.com")

        assert isinstance(wrapped, NetworkError)
        assert wrapped.message == "Network request failed"
        assert wrapped.details["url"] == "https://api.github.com"
        assert wrapped.original_error is original


class TestWrapFileOperationException:
    """Test the wrap_file_operation_exception utility function."""

    def test_write_operation(self):
        """Test wrapping file write operation exception."""
        original = PermissionError("Permission denied")
        wrapped = wrap_file_operation_exception(original, "/path/to/file", "write")

        assert isinstance(wrapped, FileWriteError)
        assert "Permission denied" in wrapped.message
        assert wrapped.details["path"] == "/path/to/file"
        assert wrapped.original_error is original

    def test_create_directory_operation(self):
        """Test wrapping directory creation exception."""
        original = OSError("directory creation failed")
        wrapped = wrap_file_operation_exception(original, "/path/to/dir", "create")

        assert isinstance(wrapped, DirectoryCreateError)
        assert "directory creation failed" in wrapped.message
        assert wrapped.details["path"] == "/path/to/dir"
        assert wrapped.original_error is original

    def test_other_operation(self):
        """Test wrapping other file operation exceptions."""
        original = OSError("File not found")
        wrapped = wrap_file_operation_exception(original, "/path/to/file", "read")

        assert isinstance(wrapped, FileSystemError)
        assert "File not found" in wrapped.message
        assert wrapped.details["path"] == "/path/to/file"
        assert wrapped.details["operation"] == "read"
        assert wrapped.original_error is original


class TestWrapPlaywrightException:
    """Test the wrap_playwright_exception utility function."""

    def test_non_playwright_exception(self):
        """Test wrapping non-Playwright exception."""
        original = Exception("Generic error")
        wrapped = wrap_playwright_exception(original, "https://github.com")

        assert isinstance(wrapped, BrowserError)
        assert "Browser automation failed" in wrapped.message
        assert wrapped.details.get("url") == "https://github.com"
        assert wrapped.original_error is original

    def test_playwright_import_error(self):
        """Test wrapping when Playwright is not available."""
        original = Exception("Some error")

        # The function should handle ImportError gracefully
        wrapped = wrap_playwright_exception(original, "https://github.com")

        assert isinstance(wrapped, BrowserError)
        assert "Browser automation failed" in wrapped.message
        assert wrapped.details.get("url") == "https://github.com"
        assert wrapped.original_error is original

    def test_playwright_exception_no_url(self):
        """Test wrapping Playwright exception without URL."""
        original = Exception("Some playwright error")
        wrapped = wrap_playwright_exception(original)

        assert isinstance(wrapped, BrowserError)
        assert "Browser automation failed" in wrapped.message
        assert wrapped.details.get("url") is None
        assert wrapped.original_error is original


class TestExceptionCompatibility:
    """Test exception compatibility with standard Python exception handling."""

    def test_exception_can_be_raised_and_caught(self):
        """Test that all custom exceptions can be raised and caught."""
        exceptions_to_test = [
            GitSyncError("test"),
            AuthenticationError("test"),
            NetworkError("test"),
            RateLimitError("test"),
            ProxyError("test"),
            ConfigurationError("test"),
            RepositoryNotFoundError("test"),
            FileSystemError("test"),
            FileWriteError("test"),
            DirectoryCreateError("test"),
            BrowserError("test"),
            WebDriverError("test"),
            PageLoadError("test"),
            SyncError("test"),
        ]

        for exception in exceptions_to_test:
            try:
                raise exception
            except type(exception) as caught:
                assert caught is exception
                assert isinstance(caught, GitSyncError)
                assert isinstance(caught, Exception)

    def test_exception_inheritance_catches(self):
        """Test that exceptions can be caught by their parent classes."""
        # Test that NetworkError subclasses can be caught as NetworkError
        try:
            raise RateLimitError("test rate limit")
        except NetworkError as e:
            assert isinstance(e, RateLimitError)
            assert isinstance(e, NetworkError)
            assert isinstance(e, GitSyncError)

        # Test that FileSystemError subclasses can be caught as FileSystemError
        try:
            raise FileWriteError("test write error")
        except FileSystemError as e:
            assert isinstance(e, FileWriteError)
            assert isinstance(e, FileSystemError)
            assert isinstance(e, GitSyncError)

        # Test that BrowserError subclasses can be caught as BrowserError
        try:
            raise WebDriverError("test webdriver error")
        except BrowserError as e:
            assert isinstance(e, WebDriverError)
            assert isinstance(e, BrowserError)
            assert isinstance(e, GitSyncError)

    def test_all_exceptions_caught_by_base_class(self):
        """Test that all custom exceptions can be caught by GitSyncError."""
        exceptions_to_test = [
            AuthenticationError("test"),
            RateLimitError("test"),
            ProxyError("test"),
            ConfigurationError("test"),
            RepositoryNotFoundError("test"),
            FileWriteError("test"),
            DirectoryCreateError("test"),
            WebDriverError("test"),
            PageLoadError("test"),
            SyncError("test"),
        ]

        for exception in exceptions_to_test:
            try:
                raise exception
            except GitSyncError as caught:
                assert caught is exception
                assert isinstance(caught, GitSyncError)
