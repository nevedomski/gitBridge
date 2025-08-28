"""GitHub browser synchronization implementation using Playwright"""

import logging
import os
import time
import zipfile
from pathlib import Path
from typing import Any

from tqdm import tqdm

# Try to import playwright - it's optional
try:
    from playwright._impl._errors import Error as PlaywrightError
    from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    # Define dummy classes for type hints when playwright is not available
    PlaywrightError = Exception  # type: ignore
    PlaywrightTimeoutError = Exception  # type: ignore
    Browser = Any  # type: ignore
    BrowserContext = Any  # type: ignore
    Page = Any  # type: ignore
    Playwright = Any  # type: ignore

from .interfaces import SyncProvider
from .utils import (
    SyncStats,
    ensure_dir,
    load_file_hashes,
    parse_github_url,
    save_file_hashes,
    validate_proxy_url,
)

logger = logging.getLogger(__name__)


class GitHubBrowserSync(SyncProvider):
    """Synchronize repository using browser automation via Playwright."""

    def __init__(
        self,
        repo_url: str,
        local_path: str,
        token: str | None = None,
        verify_ssl: bool = True,
        ca_bundle: str | None = None,
        auto_proxy: bool = False,
        auto_cert: bool = False,
        headless: bool = True,
        browser_binary: str | None = None,
        driver_path: str | None = None,  # Kept for compatibility but unused in Playwright
    ):
        """Initialize GitHub browser sync.

        Args:
            repo_url: GitHub repository URL
            local_path: Local directory path
            token: GitHub personal access token (optional)
            verify_ssl: Whether to verify SSL certificates (affects proxy settings)
            ca_bundle: Path to CA bundle file for corporate certificates
            auto_proxy: Whether to auto-detect proxy from Windows/Chrome PAC
            auto_cert: Whether to auto-detect certificates from Windows store
            headless: Whether to run browser in headless mode
            browser_binary: Path to Chrome/Chromium binary
            driver_path: Path to ChromeDriver binary (unused in Playwright, kept for compatibility)
        """
        # Check if playwright is available
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. Please install it with: pip install 'gitbridge[browser]' or pip install playwright"
            )

        self.owner, self.repo = parse_github_url(repo_url)
        self.local_path = Path(local_path)
        self.token = token
        self.headless = headless
        self.browser_binary = browser_binary
        self.driver_path = driver_path  # Kept for compatibility
        self.verify_ssl = verify_ssl
        self.ca_bundle = ca_bundle
        self.auto_proxy = auto_proxy
        self.auto_cert = auto_cert

        # Playwright instances
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

        # Cache file for tracking downloaded files
        self.hash_cache_file = self.local_path / ".gitbridge" / "file_hashes.json"
        self.file_hashes = load_file_hashes(self.hash_cache_file)

        # Statistics
        self.stats = SyncStats()

        # GitHub URLs
        self.base_url = f"https://github.com/{self.owner}/{self.repo}"
        self.api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"

    def _get_browser_launch_options(self) -> dict[str, Any]:
        """Get browser launch options for Playwright."""
        args_list: list[str] = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-images",  # Speed up loading
        ]
        launch_options: dict[str, Any] = {
            "headless": self.headless,
            "args": args_list,
        }

        # Custom browser binary
        if self.browser_binary:
            launch_options["executable_path"] = self.browser_binary

        # Configure proxy
        proxy_config = None
        if self.auto_proxy:
            try:
                from .pac_support import detect_and_configure_proxy

                detected_proxies = detect_and_configure_proxy()
                if detected_proxies.get("http"):
                    proxy_url = detected_proxies["http"]
                    # DOCDEV-NOTE: Proxy URL validation prevents injection attacks
                    proxy_config = validate_proxy_url(proxy_url)
                    logger.info(f"Using auto-detected proxy: {proxy_config['server']}")
            except Exception as e:
                logger.warning(f"Failed to auto-detect proxy: {e}")

        # Manual proxy from environment
        if not proxy_config:
            http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
            if http_proxy:
                # DOCDEV-NOTE: Validate proxy URL from environment variable
                proxy_config = validate_proxy_url(http_proxy)
                logger.info(f"Using proxy from environment: {proxy_config['server']}")

        if proxy_config:
            launch_options["proxy"] = proxy_config

        # SSL certificate handling
        if not self.verify_ssl:
            ssl_args = ["--ignore-certificate-errors", "--ignore-ssl-errors", "--allow-running-insecure-content"]
            args_list.extend(ssl_args)
            launch_options["ignore_https_errors"] = True
            logger.warning("SSL certificate verification disabled")

        return launch_options

    def _setup_browser(self) -> None:
        """Initialize Playwright browser."""
        try:
            # Initialize Playwright
            self.playwright = sync_playwright().start()

            # Launch browser with options
            launch_options = self._get_browser_launch_options()
            self.browser = self.playwright.chromium.launch(**launch_options)

            # Create browser context with user agent
            context_options: dict[str, Any] = {"user_agent": "GitBridge/1.0 (+https://github.com/browser-automation)"}

            # Add CA bundle if specified
            if self.ca_bundle and os.path.exists(self.ca_bundle):
                context_options["extra_http_headers"] = {"X-Custom-CA-Bundle": self.ca_bundle}

            self.context = self.browser.new_context(**context_options)

            # Set default timeouts
            self.context.set_default_timeout(30000)  # 30 seconds
            self.context.set_default_navigation_timeout(30000)

            # Create page
            self.page = self.context.new_page()

            logger.info("Playwright browser initialized successfully")

        except PlaywrightError as e:
            logger.error(f"Failed to initialize Playwright browser: {e}")
            raise

    def _login_if_needed(self) -> bool:
        """Login to GitHub if token is provided."""
        if not self.token:
            return True  # No login needed for public repos

        if not self.page:
            logger.error("Browser page not initialized")
            return False

        try:
            # Navigate to GitHub login
            self.page.goto("https://github.com/login")

            # Wait for page to load and check if we need to login
            self.page.wait_for_load_state("networkidle")

            # Check if we need to login (not already logged in)
            if "login" not in self.page.url.lower():
                logger.info("Already logged in to GitHub")
                return True

            logger.info("Attempting to login to GitHub using token...")

            # For now, we'll navigate directly to the repo and handle authentication
            # via browser's saved credentials or manual intervention
            # Token-based browser login is complex and would require additional steps
            logger.warning(
                "Token-based browser login not fully implemented. Please ensure you're logged in to GitHub in this browser session."
            )

            return True

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def test_connection(self) -> bool:
        """Test if browser can access the repository."""
        try:
            if not self.page:
                self._setup_browser()

            # Navigate to repository
            if self.page:
                self.page.goto(self.base_url)
                # Wait for page to load
                self.page.wait_for_load_state("networkidle")

            # Check if repository exists and is accessible
            try:
                # Look for repository elements with timeout
                selectors = [
                    "[data-testid='repository-container']",
                    ".repository-content",
                    "#repository-container-header",
                ]

                # Try to find any of the repository elements
                found = False
                for selector in selectors:
                    try:
                        if self.page:
                            element = self.page.wait_for_selector(selector, timeout=5000)
                        else:
                            continue
                        if element:
                            found = True
                            break
                    except PlaywrightTimeoutError:
                        continue

                if found:
                    logger.info(f"Successfully accessed repository: {self.owner}/{self.repo}")
                    return True

                # Check for error messages if no repository elements found
                try:
                    error_selectors = [".blankslate h3", ".flash-error", ".flash-alert"]
                    error_text = ""

                    for error_selector in error_selectors:
                        try:
                            if self.page:
                                error_element = self.page.wait_for_selector(error_selector, timeout=2000)
                                if error_element:
                                    error_text = error_element.text_content() or ""
                                    break
                            else:
                                continue
                        except PlaywrightTimeoutError:
                            continue

                    if "404" in error_text or "not found" in error_text.lower():
                        logger.error(f"Repository not found: {self.owner}/{self.repo}")
                    elif "private" in error_text.lower():
                        logger.error(f"Repository is private and authentication failed: {self.owner}/{self.repo}")
                    else:
                        logger.error(f"Repository access error: {error_text}")

                except PlaywrightTimeoutError:
                    logger.error(f"Unknown error accessing repository: {self.owner}/{self.repo}")

                return False

            except PlaywrightTimeoutError:
                logger.error(f"Timeout accessing repository: {self.owner}/{self.repo}")
                return False

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_file_list_from_zip(self, ref: str = "main") -> list[str] | None:
        """Get list of files by downloading and inspecting repository ZIP using Playwright.

        Args:
            ref: Branch name, tag name, or commit SHA

        Returns:
            List of file paths or None if failed
        """
        try:
            if not self.page:
                self._setup_browser()

            # Navigate to repository first to ensure we're authenticated
            repo_url = f"{self.base_url}/tree/{ref}"
            if self.page:
                self.page.goto(repo_url)
                # Wait for page to load
                self.page.wait_for_load_state("networkidle")

            # Get the download URL directly (GitHub pattern)
            download_url = f"{self.base_url}/archive/refs/heads/{ref}.zip"

            # Use Playwright context to download the ZIP file via API request
            if self.context:
                # Use context.request to download the file instead of page navigation
                response = self.context.request.get(download_url)
                if response.status != 200:
                    logger.error(f"Failed to download ZIP: HTTP {response.status}")
                    return None

                # Get the content
                zip_content = response.body()
            else:
                return None

            # Save ZIP temporarily
            temp_zip = self.local_path / ".gitbridge" / "temp_repo.zip"
            ensure_dir(temp_zip.parent)

            # Write the ZIP content to file
            temp_zip.write_bytes(zip_content)

            # Extract file list from ZIP
            file_list = []
            with zipfile.ZipFile(temp_zip, "r") as zip_ref:
                for info in zip_ref.infolist():
                    if not info.is_dir():
                        # Remove the root folder prefix (repo-branch/)
                        file_path = "/".join(info.filename.split("/")[1:])
                        if file_path:  # Skip empty paths
                            file_list.append(file_path)

            # Clean up temp file
            temp_zip.unlink()

            logger.info(f"Found {len(file_list)} files in repository")
            return file_list

        except PlaywrightTimeoutError:
            logger.error(f"Timeout downloading repository ZIP for ref: {ref}")
            return None
        except Exception as e:
            logger.error(f"Failed to get file list: {e}")
            return None

    def download_file_content(self, file_path: str, ref: str = "main") -> bytes | None:
        """Download content of a single file from GitHub using Playwright.

        Args:
            file_path: Path to file in repository
            ref: Branch name, tag name, or commit SHA

        Returns:
            File content as bytes or None if failed
        """
        try:
            if not self.page:
                self._setup_browser()

            # Navigate to raw file URL
            raw_url = f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/{ref}/{file_path}"

            # Use Playwright's request context to download file content
            # This respects all browser settings (proxy, SSL, headers, etc.)
            if self.context:
                response = self.context.request.get(raw_url)
            else:
                return None

            if response.status == 200:
                return response.body()
            elif response.status == 404:
                logger.error(f"File not found: {file_path}")
                return None
            else:
                logger.error(f"Failed to download file {file_path}: HTTP {response.status}")
                return None

        except PlaywrightTimeoutError:
            logger.error(f"Timeout downloading file: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}")
            return None

    def should_download_file(self, file_path: str, content: bytes) -> bool:
        """Check if file needs to be downloaded based on content hash."""
        local_file = self.local_path / file_path

        # Always download if file doesn't exist
        if not local_file.exists():
            return True

        # Calculate SHA for content (simplified hash for browser mode)
        import hashlib

        content_hash = hashlib.sha256(content).hexdigest()

        # Check if we have a hash for this file
        cached_hash = self.file_hashes.get(file_path)

        # If no cached hash or content changed, download
        if not cached_hash or cached_hash != content_hash:
            return True

        return False

    def sync_file(self, file_path: str, ref: str = "main") -> bool:
        """Sync a single file.

        Args:
            file_path: Path to file in repository
            ref: Branch name, tag name, or commit SHA

        Returns:
            True if successful, False otherwise
        """
        self.stats.files_checked += 1

        # Download file content
        content = self.download_file_content(file_path, ref)
        if content is None:
            logger.error(f"Failed to download: {file_path}")
            self.stats.files_failed += 1
            return False

        # Check if we need to save it
        if not self.should_download_file(file_path, content):
            self.stats.files_skipped += 1
            return True

        # Save file
        local_file = self.local_path / file_path

        try:
            ensure_dir(local_file.parent)
        except OSError as e:
            logger.error(f"Failed to create directory for {file_path}: {e}")
            self.stats.files_failed += 1
            return False

        try:
            # Write as binary to preserve exact content
            local_file.write_bytes(content)

            # Update hash cache (using content hash for browser mode)
            import hashlib

            content_hash = hashlib.sha256(content).hexdigest()
            self.file_hashes[file_path] = content_hash

            self.stats.files_downloaded += 1
            self.stats.bytes_downloaded += len(content)

            return True

        except OSError as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            self.stats.files_failed += 1
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving file {file_path}: {e}")
            self.stats.files_failed += 1
            return False

    def sync(self, ref: str = "main", show_progress: bool = True) -> bool:
        """Synchronize repository using browser automation.

        Args:
            ref: Branch name, tag name, or commit SHA to sync
            show_progress: Whether to show progress bar

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting browser sync of {self.owner}/{self.repo} (ref: {ref}) to {self.local_path}")

        try:
            # Set up Playwright browser
            if not self.page:
                self._setup_browser()

            # Test connection first
            if not self.test_connection():
                return False

            # Login if needed
            if not self._login_if_needed():
                return False

            # Get file list
            file_list = self.get_file_list_from_zip(ref)
            if file_list is None:
                return False

            logger.info(f"Found {len(file_list)} files to sync")

            # Create local directory
            ensure_dir(self.local_path)

            # Sync files with progress bar
            file_iterator: list[str] | tqdm[str]
            if show_progress:
                progress_bar = tqdm(file_list, desc="Syncing files", unit="file")
                file_iterator = progress_bar
            else:
                file_iterator = file_list

            success = True
            for file_path in file_iterator:
                if not self.sync_file(file_path, ref):
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

                # Brief pause to avoid overwhelming the server
                time.sleep(0.1)

            # Save hash cache
            save_file_hashes(self.hash_cache_file, self.file_hashes)

            # Print statistics
            self.stats.print_summary()

            return success

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return False

        finally:
            self.cleanup()

    def get_status(self) -> dict[str, Any]:
        """Get current synchronization provider status and metadata.

        Returns comprehensive information about the browser sync provider's current state
        including configuration, statistics, browser status, and relevant metadata
        for debugging or monitoring purposes.

        Returns:
            Dict[str, Any]: Status dictionary containing provider information,
                repository details, sync statistics, and health indicators.

        Note:
            Browser-specific status includes WebDriver state, browser configuration,
            and automation capabilities. Sensitive information is masked for security.
        """
        # DOCDEV-NOTE: Browser sync status includes browser automation state
        # and capabilities in addition to standard sync provider information

        # Determine browser status
        browser_status = "not_initialized"
        if self.playwright:
            if self.browser:
                if self.context and self.page:
                    browser_status = "ready"
                else:
                    browser_status = "initialized"
            else:
                browser_status = "playwright_started"

        # Determine authentication status
        auth_status = "anonymous"
        if self.token:
            auth_status = "token_configured"
            # Note: Browser auth testing is complex and may trigger login flows
            # For now, we just indicate token presence

        # Test connection to determine health
        health = "unknown"
        try:
            if self.test_connection():
                health = "healthy"
            else:
                health = "error"
        except Exception:
            health = "error"

        # Get last sync timestamp from cache file
        last_sync = None
        try:
            if self.hash_cache_file.exists():
                import os

                last_sync_timestamp = os.path.getmtime(self.hash_cache_file)
                from datetime import datetime

                last_sync = datetime.fromtimestamp(last_sync_timestamp).isoformat()
        except Exception:
            pass

        return {
            "provider_type": "browser",
            "repository": f"{self.owner}/{self.repo}",
            "repository_url": f"https://github.com/{self.owner}/{self.repo}",
            "local_path": str(self.local_path),
            "last_sync": last_sync,
            "authentication": auth_status,
            "statistics": {
                "files_checked": self.stats.files_checked,
                "files_downloaded": self.stats.files_downloaded,
                "files_skipped": self.stats.files_skipped,
                "files_failed": self.stats.files_failed,
                "bytes_downloaded": self.stats.bytes_downloaded,
                "directories_created": self.stats.directories_created,
                "total_files": len(self.file_hashes) if hasattr(self, "file_hashes") else 0,
            },
            "configuration": {
                "headless": self.headless,
                "verify_ssl": self.verify_ssl,
                "auto_proxy": self.auto_proxy,
                "auto_cert": self.auto_cert,
                "has_custom_ca_bundle": bool(self.ca_bundle),
                "has_custom_browser_binary": bool(self.browser_binary),
                "token_configured": bool(self.token),
            },
            "browser_automation": {
                "status": browser_status,
                "playwright_available": bool(self.playwright),
                "browser_available": bool(self.browser),
                "context_available": bool(self.context),
                "page_available": bool(self.page),
                "browser_binary_path": self.browser_binary or "default",
            },
            "health": health,
        }

    def cleanup(self) -> None:
        """Clean up resources (close Playwright browser)."""
        try:
            if self.page:
                self.page.close()
                self.page = None

            if self.context:
                self.context.close()
                self.context = None

            if self.browser:
                self.browser.close()
                self.browser = None

            if self.playwright:
                self.playwright.stop()
                self.playwright = None

            logger.info("Playwright browser closed successfully")

        except Exception as e:
            logger.warning(f"Error closing Playwright browser: {e}")
        finally:
            # Ensure all references are cleared
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
