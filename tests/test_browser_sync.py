"""Unit tests for browser_sync module"""

import hashlib
import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest
from playwright._impl._errors import Error as PlaywrightError
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError

from gitbridge.browser_sync import GitHubBrowserSync
from gitbridge.exceptions import ConfigurationError
from gitbridge.utils import SyncStats


class TestGitHubBrowserSync:
    """Test class for GitHubBrowserSync"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def browser_sync(self, temp_dir):
        """Create a GitHubBrowserSync instance for testing"""
        sync = GitHubBrowserSync(
            repo_url="https://github.com/testuser/testrepo",
            local_path=str(temp_dir),
            token="test_token",
            headless=True,
        )
        # Ensure clean state for each test
        sync.playwright = None
        sync.browser = None
        sync.context = None
        sync.page = None
        yield sync
        # Cleanup after test
        try:
            sync.cleanup()
        except Exception:
            pass  # Ignore cleanup errors in tests

    @pytest.fixture
    def browser_sync_no_token(self, temp_dir):
        """Create a GitHubBrowserSync instance without token"""
        sync = GitHubBrowserSync(
            repo_url="https://github.com/testuser/testrepo",
            local_path=str(temp_dir),
            headless=True,
        )
        # Ensure clean state for each test
        sync.playwright = None
        sync.browser = None
        sync.context = None
        sync.page = None
        yield sync
        # Cleanup after test
        try:
            sync.cleanup()
        except Exception:
            pass  # Ignore cleanup errors in tests

    def test_init(self, temp_dir):
        """Test GitHubBrowserSync initialization"""
        sync = GitHubBrowserSync(
            repo_url="https://github.com/testuser/testrepo",
            local_path=str(temp_dir),
            token="test_token",
            verify_ssl=False,
            ca_bundle="/path/to/ca.pem",
            auto_proxy=True,
            auto_cert=True,
            headless=False,
            browser_binary="/path/to/chrome",
            driver_path="/path/to/chromedriver",
        )

        assert sync.owner == "testuser"
        assert sync.repo == "testrepo"
        assert sync.local_path == temp_dir
        assert sync.token == "test_token"
        assert sync.headless is False
        assert sync.browser_binary == "/path/to/chrome"
        assert sync.driver_path == "/path/to/chromedriver"
        assert sync.verify_ssl is False
        assert sync.ca_bundle == "/path/to/ca.pem"
        assert sync.auto_proxy is True
        assert sync.auto_cert is True
        assert sync.playwright is None
        assert sync.browser is None
        assert sync.context is None
        assert sync.page is None
        assert isinstance(sync.stats, SyncStats)
        assert sync.base_url == "https://github.com/testuser/testrepo"
        assert sync.api_url == "https://api.github.com/repos/testuser/testrepo"

    def test_init_invalid_repo_url(self, temp_dir):
        """Test GitHubBrowserSync initialization with invalid repo URL"""
        with pytest.raises(ConfigurationError):
            GitHubBrowserSync(
                repo_url="https://invalid-url",
                local_path=str(temp_dir),
            )

    def test_get_browser_launch_options_headless(self, browser_sync):
        """Test browser launch options in headless mode"""
        options = browser_sync._get_browser_launch_options()

        assert isinstance(options, dict)
        # Check that headless is True
        assert options["headless"] is True
        assert "--no-sandbox" in options["args"]
        assert "--disable-dev-shm-usage" in options["args"]
        assert "--disable-gpu" in options["args"]
        assert "--disable-extensions" in options["args"]
        assert "--disable-plugins" in options["args"]
        assert "--disable-images" in options["args"]

    def test_get_browser_launch_options_not_headless(self, temp_dir):
        """Test browser launch options in non-headless mode"""
        sync = GitHubBrowserSync(
            repo_url="https://github.com/testuser/testrepo",
            local_path=str(temp_dir),
            headless=False,
        )
        options = sync._get_browser_launch_options()

        assert options["headless"] is False

    def test_get_browser_launch_options_with_binary(self, temp_dir):
        """Test browser launch options with custom binary"""
        browser_binary = "/custom/path/to/chrome"
        sync = GitHubBrowserSync(
            repo_url="https://github.com/testuser/testrepo",
            local_path=str(temp_dir),
            browser_binary=browser_binary,
        )
        options = sync._get_browser_launch_options()

        assert options["executable_path"] == browser_binary

    @patch.dict(os.environ, {"HTTP_PROXY": "http://proxy.example.com:8080"})
    def test_get_browser_launch_options_with_env_proxy(self, temp_dir):
        """Test browser launch options with proxy from environment"""
        sync = GitHubBrowserSync(
            repo_url="https://github.com/testuser/testrepo",
            local_path=str(temp_dir),
            auto_proxy=False,  # Should still use env proxy
        )
        options = sync._get_browser_launch_options()

        assert "proxy" in options
        assert options["proxy"]["server"] == "http://proxy.example.com:8080"

    def test_get_browser_launch_options_ssl_disabled(self, temp_dir):
        """Test browser launch options with SSL verification disabled"""
        sync = GitHubBrowserSync(
            repo_url="https://github.com/testuser/testrepo",
            local_path=str(temp_dir),
            verify_ssl=False,
        )
        options = sync._get_browser_launch_options()

        assert "--ignore-certificate-errors" in options["args"]
        assert "--ignore-ssl-errors" in options["args"]
        assert "--allow-running-insecure-content" in options["args"]
        assert options["ignore_https_errors"] is True

    def test_setup_browser_success(self, browser_sync):
        """Test successful Playwright browser setup"""

        # Mock the Playwright chain
        mock_playwright = Mock()
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()

        import gitbridge.browser_sync as browser_sync_module

        with patch.object(browser_sync_module, "sync_playwright") as mock_sync_playwright:
            # Set up the full mock chain: sync_playwright() returns an object
            # that when start() is called returns the playwright object
            mock_sync_playwright.return_value.start.return_value = mock_playwright
            mock_playwright.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page

            browser_sync._setup_browser()

            # Verify the mock chain was called correctly
            mock_sync_playwright.assert_called_once()
            mock_sync_playwright.return_value.start.assert_called_once()
            mock_playwright.chromium.launch.assert_called_once()
            mock_browser.new_context.assert_called_once()
            mock_context.new_page.assert_called_once()

            # Verify the objects were set correctly
            assert browser_sync.playwright == mock_playwright
            assert browser_sync.browser == mock_browser
            assert browser_sync.context == mock_context
            assert browser_sync.page == mock_page

            # Verify context configuration
            mock_context.set_default_timeout.assert_called_with(30000)
            mock_context.set_default_navigation_timeout.assert_called_with(30000)

    def test_setup_browser_failure(self, browser_sync):
        """Test Playwright browser setup failure"""
        import gitbridge.browser_sync as browser_sync_module

        with patch.object(browser_sync_module, "sync_playwright") as mock_sync_playwright:
            mock_sync_playwright.return_value.start.side_effect = PlaywrightError("Browser not found")

            with pytest.raises(PlaywrightError):
                browser_sync._setup_browser()

            assert browser_sync.playwright is None
            assert browser_sync.browser is None
            assert browser_sync.context is None
            assert browser_sync.page is None

    def test_login_if_needed_no_token(self, browser_sync_no_token):
        """Test login when no token is provided"""
        result = browser_sync_no_token._login_if_needed()
        assert result is True

    def test_login_if_needed_with_token_already_logged_in(self, browser_sync):
        """Test login when already logged in"""
        mock_page = Mock()
        mock_page.url = "https://github.com/dashboard"
        browser_sync.page = mock_page

        result = browser_sync._login_if_needed()
        assert result is True
        mock_page.goto.assert_called_once_with("https://github.com/login")
        mock_page.wait_for_load_state.assert_called_once_with("networkidle")

    def test_login_if_needed_with_token_needs_login(self, browser_sync):
        """Test login when token is provided and login is needed"""
        mock_page = Mock()
        mock_page.url = "https://github.com/login"
        browser_sync.page = mock_page

        result = browser_sync._login_if_needed()
        assert result is True  # Always returns True for now
        mock_page.goto.assert_called_once_with("https://github.com/login")
        mock_page.wait_for_load_state.assert_called_once_with("networkidle")

    def test_login_if_needed_exception(self, browser_sync):
        """Test login exception handling"""
        mock_page = Mock()
        mock_page.goto.side_effect = Exception("Network error")
        browser_sync.page = mock_page

        result = browser_sync._login_if_needed()
        assert result is False

    def test_test_connection_success(self, browser_sync):
        """Test successful connection test"""
        mock_page = Mock()
        browser_sync._setup_browser = Mock()
        browser_sync.page = mock_page

        # Mock successful element finding
        mock_element = Mock()
        mock_page.wait_for_selector.return_value = mock_element

        result = browser_sync.test_connection()

        assert result is True
        mock_page.goto.assert_called_once_with("https://github.com/testuser/testrepo")
        mock_page.wait_for_load_state.assert_called_once_with("networkidle")

    def test_test_connection_timeout_404(self, browser_sync):
        """Test connection test with 404 error"""
        mock_page = Mock()
        browser_sync._setup_browser = Mock()
        browser_sync.page = mock_page

        # Mock timeout for repository elements
        mock_page.wait_for_selector.side_effect = [
            PlaywrightTimeoutError("Timeout"),  # First selector fails
            PlaywrightTimeoutError("Timeout"),  # Second selector fails
            PlaywrightTimeoutError("Timeout"),  # Third selector fails
        ]

        # Mock finding error element
        error_element = Mock()
        error_element.text_content.return_value = "404 - Repository not found"

        def mock_error_selector(selector, timeout=None):
            if selector in [".blankslate h3", ".flash-error", ".flash-alert"]:
                return error_element
            raise PlaywrightTimeoutError("Timeout")

        mock_page.wait_for_selector.side_effect = mock_error_selector

        result = browser_sync.test_connection()

        assert result is False

    def test_test_connection_timeout_private(self, browser_sync):
        """Test connection test with private repository error"""
        mock_page = Mock()
        browser_sync._setup_browser = Mock()
        browser_sync.page = mock_page

        # Mock timeout for repository elements
        mock_page.wait_for_selector.side_effect = [
            PlaywrightTimeoutError("Timeout"),  # First selector fails
            PlaywrightTimeoutError("Timeout"),  # Second selector fails
            PlaywrightTimeoutError("Timeout"),  # Third selector fails
        ]

        # Mock finding error element with private repo message
        error_element = Mock()
        error_element.text_content.return_value = "This repository is private"

        def mock_error_selector(selector, timeout=None):
            if selector in [".blankslate h3", ".flash-error", ".flash-alert"]:
                return error_element
            raise PlaywrightTimeoutError("Timeout")

        mock_page.wait_for_selector.side_effect = mock_error_selector

        result = browser_sync.test_connection()

        assert result is False

    def test_test_connection_timeout_unknown_error(self, browser_sync):
        """Test connection test with unknown error"""
        mock_page = Mock()
        browser_sync._setup_browser = Mock()
        browser_sync.page = mock_page

        # Mock timeout for repository elements
        mock_page.wait_for_selector.side_effect = [
            PlaywrightTimeoutError("Timeout"),  # First selector fails
            PlaywrightTimeoutError("Timeout"),  # Second selector fails
            PlaywrightTimeoutError("Timeout"),  # Third selector fails
        ]

        # Mock finding error element with unknown error
        error_element = Mock()
        error_element.text_content.return_value = "Some unknown error occurred"

        def mock_error_selector(selector, timeout=None):
            if selector in [".blankslate h3", ".flash-error", ".flash-alert"]:
                return error_element
            raise PlaywrightTimeoutError("Timeout")

        mock_page.wait_for_selector.side_effect = mock_error_selector

        result = browser_sync.test_connection()

        assert result is False

    def test_test_connection_timeout_no_error_element(self, browser_sync):
        """Test connection test when no error element is found"""
        mock_page = Mock()
        browser_sync._setup_browser = Mock()
        browser_sync.page = mock_page

        # Mock timeout for all selectors
        mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("Timeout")

        result = browser_sync.test_connection()

        assert result is False

    def test_test_connection_exception(self, browser_sync):
        """Test connection test exception handling"""
        browser_sync._setup_browser = Mock(side_effect=Exception("Browser initialization failed"))

        result = browser_sync.test_connection()

        assert result is False

    def test_get_file_list_from_zip_success(self, browser_sync, temp_dir):
        """Test successful file list extraction from ZIP using Playwright"""
        mock_page = Mock()
        mock_context = Mock()
        mock_response = Mock()

        browser_sync._setup_browser = Mock()
        browser_sync.page = mock_page
        browser_sync.context = mock_context

        # Mock the API request response
        mock_response.status = 200

        # Create a fake ZIP file content
        import io

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("testrepo-main/file1.txt", "content1")
            zf.writestr("testrepo-main/dir/file2.py", "content2")
            zf.writestr("testrepo-main/", "")  # directory entry

        mock_response.body.return_value = zip_buffer.getvalue()
        mock_context.request.get.return_value = mock_response

        # Mock page navigation
        mock_page.goto.return_value = None
        mock_page.wait_for_load_state.return_value = None

        with patch("pathlib.Path.unlink"):
            result = browser_sync.get_file_list_from_zip("main")

        assert result == ["file1.txt", "dir/file2.py"]
        mock_page.goto.assert_called_once_with("https://github.com/testuser/testrepo/tree/main")
        mock_context.request.get.assert_called_once_with("https://github.com/testuser/testrepo/archive/refs/heads/main.zip")

    def test_get_file_list_from_zip_timeout(self, browser_sync):
        """Test file list extraction with Playwright timeout"""
        mock_page = Mock()
        browser_sync._setup_browser = Mock()
        browser_sync.page = mock_page

        # Mock expect_download to raise timeout
        mock_page.expect_download.side_effect = PlaywrightTimeoutError("Download timeout")

        result = browser_sync.get_file_list_from_zip("main")

        assert result is None

    def test_get_file_list_from_zip_download_failure(self, browser_sync):
        """Test file list extraction with download failure"""
        mock_page = Mock()
        browser_sync._setup_browser = Mock()
        browser_sync.page = mock_page

        # Mock expect_download to raise exception
        mock_page.expect_download.side_effect = Exception("Download failed")

        result = browser_sync.get_file_list_from_zip("main")

        assert result is None

    def test_get_file_list_from_zip_no_browser_setup(self, browser_sync) -> None:
        """Test file list extraction when browser needs to be set up"""
        # Don't mock _setup_browser to ensure it gets called
        browser_sync.page = None
        browser_sync.context = None

        mock_page = Mock()
        mock_context = Mock()
        mock_response = Mock()

        # Mock the API request response
        mock_response.status = 200

        # Create a fake ZIP file content with no files
        import io

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w"):
            pass  # Empty ZIP

        mock_response.body.return_value = zip_buffer.getvalue()
        mock_context.request.get.return_value = mock_response

        # Mock page navigation
        mock_page.goto.return_value = None
        mock_page.wait_for_load_state.return_value = None

        def setup_browser_side_effect():
            browser_sync.page = mock_page
            browser_sync.context = mock_context

        browser_sync._setup_browser = Mock(side_effect=setup_browser_side_effect)

        with patch("pathlib.Path.unlink"):
            result = browser_sync.get_file_list_from_zip("main")

        assert result == []
        # Verify browser was set up
        browser_sync._setup_browser.assert_called_once()
        assert browser_sync.page == mock_page

    def test_download_file_content_success(self, browser_sync):
        """Test successful file content download using Playwright"""
        mock_context = Mock()
        mock_request = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.body.return_value = b"file content"
        mock_request.get.return_value = mock_response
        mock_context.request = mock_request

        browser_sync._setup_browser = Mock()
        browser_sync.context = mock_context
        browser_sync.page = Mock()  # Just to pass the None check

        result = browser_sync.download_file_content("test.txt", "main")

        assert result == b"file content"
        mock_request.get.assert_called_once_with("https://raw.githubusercontent.com/testuser/testrepo/main/test.txt")

    def test_download_file_content_not_found(self, browser_sync):
        """Test file content download with 404 error using Playwright"""
        mock_context = Mock()
        mock_request = Mock()
        mock_response = Mock()
        mock_response.status = 404
        mock_request.get.return_value = mock_response
        mock_context.request = mock_request

        browser_sync._setup_browser = Mock()
        browser_sync.context = mock_context
        browser_sync.page = Mock()  # Just to pass the None check

        result = browser_sync.download_file_content("nonexistent.txt", "main")

        assert result is None

    def test_download_file_content_ssl_disabled(self, temp_dir):
        """Test file content download with SSL verification disabled using Playwright"""
        sync = GitHubBrowserSync(
            repo_url="https://github.com/testuser/testrepo",
            local_path=str(temp_dir),
            verify_ssl=False,
        )

        mock_context = Mock()
        mock_request = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.body.return_value = b"file content"
        mock_request.get.return_value = mock_response
        mock_context.request = mock_request

        sync._setup_browser = Mock()
        sync.context = mock_context
        sync.page = Mock()  # Just to pass the None check

        result = sync.download_file_content("test.txt", "main")

        assert result == b"file content"
        # SSL verification is handled at browser level, not per request

    def test_download_file_content_with_ca_bundle(self, temp_dir):
        """Test file content download with CA bundle using Playwright"""
        ca_bundle = "/path/to/ca.pem"
        sync = GitHubBrowserSync(
            repo_url="https://github.com/testuser/testrepo",
            local_path=str(temp_dir),
            ca_bundle=ca_bundle,
        )

        mock_context = Mock()
        mock_request = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.body.return_value = b"file content"
        mock_request.get.return_value = mock_response
        mock_context.request = mock_request

        sync._setup_browser = Mock()
        sync.context = mock_context
        sync.page = Mock()  # Just to pass the None check

        result = sync.download_file_content("test.txt", "main")

        assert result == b"file content"
        # CA bundle is handled at browser context level, not per request

    def test_download_file_content_exception(self, browser_sync):
        """Test file content download with exception using Playwright"""
        mock_context = Mock()
        mock_request = Mock()
        mock_request.get.side_effect = Exception("Network error")
        mock_context.request = mock_request

        browser_sync._setup_browser = Mock()
        browser_sync.context = mock_context
        browser_sync.page = Mock()  # Just to pass the None check

        result = browser_sync.download_file_content("test.txt", "main")

        assert result is None

    def test_download_file_content_no_browser_setup(self, browser_sync):
        """Test file content download when browser needs to be set up"""
        # Don't mock _setup_browser to ensure it gets called
        browser_sync.page = None
        browser_sync.context = None

        mock_context = Mock()
        mock_request = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.body.return_value = b"file content"
        mock_request.get.return_value = mock_response
        mock_context.request = mock_request
        mock_page = Mock()

        def setup_browser_side_effect():
            browser_sync.page = mock_page
            browser_sync.context = mock_context

        browser_sync._setup_browser = Mock(side_effect=setup_browser_side_effect)

        result = browser_sync.download_file_content("test.txt", "main")

        assert result == b"file content"
        # Verify browser was set up
        browser_sync._setup_browser.assert_called_once()
        assert browser_sync.page == mock_page
        assert browser_sync.context == mock_context

    def test_should_download_file_new_file(self, browser_sync, temp_dir):
        """Test should_download_file with new file"""
        content = b"test content"
        result = browser_sync.should_download_file("newfile.txt", content)

        assert result is True

    def test_should_download_file_existing_unchanged(self, browser_sync, temp_dir):
        """Test should_download_file with existing unchanged file"""
        content = b"test content"
        content_hash = hashlib.sha256(content).hexdigest()

        # Create existing file
        test_file = temp_dir / "existing.txt"
        test_file.write_bytes(content)

        # Set hash in cache
        browser_sync.file_hashes["existing.txt"] = content_hash

        result = browser_sync.should_download_file("existing.txt", content)

        assert result is False

    def test_should_download_file_existing_changed(self, browser_sync, temp_dir):
        """Test should_download_file with existing changed file"""
        old_content = b"old content"
        new_content = b"new content"
        old_hash = hashlib.sha256(old_content).hexdigest()

        # Create existing file
        test_file = temp_dir / "changed.txt"
        test_file.write_bytes(old_content)

        # Set old hash in cache
        browser_sync.file_hashes["changed.txt"] = old_hash

        result = browser_sync.should_download_file("changed.txt", new_content)

        assert result is True

    def test_should_download_file_no_cached_hash(self, browser_sync, temp_dir):
        """Test should_download_file with existing file but no cached hash"""
        content = b"test content"

        # Create existing file
        test_file = temp_dir / "nocache.txt"
        test_file.write_bytes(content)

        result = browser_sync.should_download_file("nocache.txt", content)

        assert result is True

    @patch.object(GitHubBrowserSync, "download_file_content")
    def test_sync_file_success(self, mock_download, browser_sync, temp_dir):
        """Test successful file sync"""
        content = b"test file content"
        mock_download.return_value = content

        result = browser_sync.sync_file("test.txt", "main")

        assert result is True
        assert browser_sync.stats.files_checked == 1
        assert browser_sync.stats.files_downloaded == 1
        assert browser_sync.stats.files_skipped == 0
        assert browser_sync.stats.files_failed == 0
        assert browser_sync.stats.bytes_downloaded == len(content)

        # Check file was created
        test_file = temp_dir / "test.txt"
        assert test_file.exists()
        assert test_file.read_bytes() == content

        # Check hash was cached
        content_hash = hashlib.sha256(content).hexdigest()
        assert browser_sync.file_hashes["test.txt"] == content_hash

    @patch.object(GitHubBrowserSync, "download_file_content")
    def test_sync_file_download_failure(self, mock_download, browser_sync):
        """Test file sync with download failure"""
        mock_download.return_value = None

        result = browser_sync.sync_file("test.txt", "main")

        assert result is False
        assert browser_sync.stats.files_checked == 1
        assert browser_sync.stats.files_downloaded == 0
        assert browser_sync.stats.files_skipped == 0
        assert browser_sync.stats.files_failed == 1

    @patch.object(GitHubBrowserSync, "download_file_content")
    @patch.object(GitHubBrowserSync, "should_download_file")
    def test_sync_file_skipped(self, mock_should_download, mock_download, browser_sync):
        """Test file sync when file should be skipped"""
        content = b"test file content"
        mock_download.return_value = content
        mock_should_download.return_value = False

        result = browser_sync.sync_file("test.txt", "main")

        assert result is True
        assert browser_sync.stats.files_checked == 1
        assert browser_sync.stats.files_downloaded == 0
        assert browser_sync.stats.files_skipped == 1
        assert browser_sync.stats.files_failed == 0

    @patch.object(GitHubBrowserSync, "download_file_content")
    def test_sync_file_save_error(self, mock_download, browser_sync, temp_dir):
        """Test file sync with save error"""
        content = b"test file content"
        mock_download.return_value = content

        # Create a directory with the same name to cause save error
        test_path = temp_dir / "test.txt"
        test_path.mkdir()

        result = browser_sync.sync_file("test.txt", "main")

        assert result is False
        assert browser_sync.stats.files_checked == 1
        assert browser_sync.stats.files_downloaded == 0
        assert browser_sync.stats.files_skipped == 0
        assert browser_sync.stats.files_failed == 1

    @patch.object(GitHubBrowserSync, "_setup_browser")
    @patch.object(GitHubBrowserSync, "test_connection")
    @patch.object(GitHubBrowserSync, "_login_if_needed")
    @patch.object(GitHubBrowserSync, "get_file_list_from_zip")
    @patch.object(GitHubBrowserSync, "sync_file")
    @patch.object(GitHubBrowserSync, "cleanup")
    def test_sync_success(
        self,
        mock_cleanup,
        mock_sync_file,
        mock_get_files,
        mock_login,
        mock_test_conn,
        mock_setup_browser,
        browser_sync,
    ):
        """Test successful repository sync"""
        import gitbridge.browser_sync as browser_sync_module

        with patch.object(browser_sync_module, "save_file_hashes") as mock_save_hashes:
            # Mock all dependencies
            browser_sync.page = Mock()  # Set page to avoid setup
            mock_test_conn.return_value = True
            mock_login.return_value = True
            mock_get_files.return_value = ["file1.txt", "file2.py"]
            mock_sync_file.return_value = True

            result = browser_sync.sync("main", show_progress=False)

            assert result is True
            mock_test_conn.assert_called_once()
            mock_login.assert_called_once()
            mock_get_files.assert_called_once_with("main")
            assert mock_sync_file.call_count == 2
            mock_sync_file.assert_has_calls([call("file1.txt", "main"), call("file2.py", "main")])
            mock_save_hashes.assert_called_once()
            mock_cleanup.assert_called_once()

    @patch.object(GitHubBrowserSync, "test_connection")
    @patch.object(GitHubBrowserSync, "cleanup")
    def test_sync_connection_failure(self, mock_cleanup, mock_test_conn, browser_sync):
        """Test sync with connection failure"""
        browser_sync.page = Mock()  # Set page to avoid setup
        mock_test_conn.return_value = False

        result = browser_sync.sync("main")

        assert result is False
        mock_cleanup.assert_called_once()

    @patch.object(GitHubBrowserSync, "test_connection")
    @patch.object(GitHubBrowserSync, "_login_if_needed")
    @patch.object(GitHubBrowserSync, "cleanup")
    def test_sync_login_failure(self, mock_cleanup, mock_login, mock_test_conn, browser_sync):
        """Test sync with login failure"""
        browser_sync.page = Mock()  # Set page to avoid setup
        mock_test_conn.return_value = True
        mock_login.return_value = False

        result = browser_sync.sync("main")

        assert result is False
        mock_cleanup.assert_called_once()

    @patch.object(GitHubBrowserSync, "test_connection")
    @patch.object(GitHubBrowserSync, "_login_if_needed")
    @patch.object(GitHubBrowserSync, "get_file_list_from_zip")
    @patch.object(GitHubBrowserSync, "cleanup")
    def test_sync_file_list_failure(self, mock_cleanup, mock_get_files, mock_login, mock_test_conn, browser_sync):
        """Test sync with file list retrieval failure"""
        browser_sync.page = Mock()  # Set page to avoid setup
        mock_test_conn.return_value = True
        mock_login.return_value = True
        mock_get_files.return_value = None

        result = browser_sync.sync("main")

        assert result is False
        mock_cleanup.assert_called_once()

    @patch.object(GitHubBrowserSync, "test_connection")
    @patch.object(GitHubBrowserSync, "_login_if_needed")
    @patch.object(GitHubBrowserSync, "get_file_list_from_zip")
    @patch.object(GitHubBrowserSync, "sync_file")
    @patch.object(GitHubBrowserSync, "cleanup")
    def test_sync_partial_failure(
        self,
        mock_cleanup,
        mock_sync_file,
        mock_get_files,
        mock_login,
        mock_test_conn,
        browser_sync,
    ):
        """Test sync with some file failures"""
        import gitbridge.browser_sync as browser_sync_module

        with patch.object(browser_sync_module, "save_file_hashes"):
            browser_sync.page = Mock()  # Set page to avoid setup
            mock_test_conn.return_value = True
            mock_login.return_value = True
            mock_get_files.return_value = ["file1.txt", "file2.py"]
            mock_sync_file.side_effect = [True, False]  # First succeeds, second fails

            result = browser_sync.sync("main", show_progress=False)

            assert result is False  # Overall failure due to one file failing
            mock_cleanup.assert_called_once()

    @patch.object(GitHubBrowserSync, "_setup_browser")
    @patch.object(GitHubBrowserSync, "cleanup")
    def test_sync_exception_handling(self, mock_cleanup, mock_setup_browser, browser_sync):
        """Test sync exception handling"""
        browser_sync.page = None  # Force browser setup
        mock_setup_browser.side_effect = Exception("Setup failed")

        result = browser_sync.sync("main")

        assert result is False
        mock_cleanup.assert_called_once()

    @patch.object(GitHubBrowserSync, "test_connection")
    @patch.object(GitHubBrowserSync, "_login_if_needed")
    @patch.object(GitHubBrowserSync, "get_file_list_from_zip")
    @patch.object(GitHubBrowserSync, "sync_file")
    @patch.object(GitHubBrowserSync, "cleanup")
    def test_sync_with_progress(
        self,
        mock_cleanup,
        mock_sync_file,
        mock_get_files,
        mock_login,
        mock_test_conn,
        browser_sync,
    ):
        """Test sync with progress bar enabled"""
        import gitbridge.browser_sync as browser_sync_module

        with patch.object(browser_sync_module, "save_file_hashes"):
            with patch.object(browser_sync_module, "tqdm") as mock_tqdm:
                # Setup mocks
                browser_sync.page = Mock()  # Set page to avoid setup
                mock_test_conn.return_value = True
                mock_login.return_value = True
                mock_get_files.return_value = ["file1.txt", "file2.py"]
                mock_sync_file.return_value = True

                # Mock tqdm
                mock_progress_bar = Mock()
                mock_tqdm.return_value = mock_progress_bar
                mock_progress_bar.__iter__ = Mock(return_value=iter(["file1.txt", "file2.py"]))

                result = browser_sync.sync("main", show_progress=True)

                assert result is True
                mock_tqdm.assert_called_once_with(["file1.txt", "file2.py"], desc="Syncing files", unit="file")
                assert mock_progress_bar.set_postfix.call_count == 2  # Called for each file

    def test_cleanup_with_playwright_objects(self, browser_sync):
        """Test cleanup when Playwright objects exist"""
        mock_page = Mock()
        mock_context = Mock()
        mock_browser = Mock()
        mock_playwright = Mock()

        browser_sync.page = mock_page
        browser_sync.context = mock_context
        browser_sync.browser = mock_browser
        browser_sync.playwright = mock_playwright

        browser_sync.cleanup()

        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()
        assert browser_sync.page is None
        assert browser_sync.context is None
        assert browser_sync.browser is None
        assert browser_sync.playwright is None

    def test_cleanup_without_playwright_objects(self, browser_sync):
        """Test cleanup when Playwright objects are None"""
        browser_sync.page = None
        browser_sync.context = None
        browser_sync.browser = None
        browser_sync.playwright = None

        # Should not raise any exception
        browser_sync.cleanup()

        assert browser_sync.page is None
        assert browser_sync.context is None
        assert browser_sync.browser is None
        assert browser_sync.playwright is None

    def test_cleanup_with_exception(self, browser_sync):
        """Test cleanup when close() methods raise exceptions"""
        mock_page = Mock()
        mock_context = Mock()
        mock_browser = Mock()
        mock_playwright = Mock()

        mock_page.close.side_effect = Exception("Close failed")
        mock_context.close.side_effect = Exception("Close failed")
        mock_browser.close.side_effect = Exception("Close failed")
        mock_playwright.stop.side_effect = Exception("Stop failed")

        browser_sync.page = mock_page
        browser_sync.context = mock_context
        browser_sync.browser = mock_browser
        browser_sync.playwright = mock_playwright

        # Should not raise exception, just log warning
        browser_sync.cleanup()

        assert browser_sync.page is None
        assert browser_sync.context is None
        assert browser_sync.browser is None
        assert browser_sync.playwright is None

    @patch("gitbridge.pac_support.detect_and_configure_proxy")
    def test_get_browser_launch_options_auto_proxy_success(self, mock_detect_proxy, temp_dir):
        """Test browser launch options with successful auto proxy detection"""
        mock_detect_proxy.return_value = {"http": "http://proxy.example.com:8080"}

        sync = GitHubBrowserSync(
            repo_url="https://github.com/testuser/testrepo",
            local_path=str(temp_dir),
            auto_proxy=True,
        )
        options = sync._get_browser_launch_options()

        assert "proxy" in options
        assert options["proxy"]["server"] == "http://proxy.example.com:8080"

    @patch("gitbridge.pac_support.detect_and_configure_proxy")
    def test_get_browser_launch_options_auto_proxy_failure(self, mock_detect_proxy, temp_dir):
        """Test browser launch options with auto proxy detection failure"""
        mock_detect_proxy.side_effect = Exception("PAC detection failed")

        sync = GitHubBrowserSync(
            repo_url="https://github.com/testuser/testrepo",
            local_path=str(temp_dir),
            auto_proxy=True,
        )
        options = sync._get_browser_launch_options()

        # Should not contain proxy when detection fails
        assert "proxy" not in options or options.get("proxy") is None

    def test_hash_cache_initialization(self, browser_sync, temp_dir):
        """Test that hash cache is properly initialized"""
        # Hash cache file should be created in .gitbridge subdirectory
        expected_cache_file = temp_dir / ".gitbridge" / "file_hashes.json"
        assert browser_sync.hash_cache_file == expected_cache_file

        # file_hashes should be initialized (empty dict if file doesn't exist)
        assert isinstance(browser_sync.file_hashes, dict)

    def test_repository_urls(self, browser_sync):
        """Test that repository URLs are correctly constructed"""
        assert browser_sync.base_url == "https://github.com/testuser/testrepo"
        assert browser_sync.api_url == "https://api.github.com/repos/testuser/testrepo"

    def test_stats_initialization(self, browser_sync):
        """Test that statistics are properly initialized"""
        assert isinstance(browser_sync.stats, SyncStats)
        assert browser_sync.stats.files_checked == 0
        assert browser_sync.stats.files_downloaded == 0
        assert browser_sync.stats.files_skipped == 0
        assert browser_sync.stats.files_failed == 0
        assert browser_sync.stats.bytes_downloaded == 0
