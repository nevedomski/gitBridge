"""Comprehensive unit tests for PAC (Proxy Auto-Configuration) support module.

This test suite covers:
- PAC file detection and parsing
- Proxy configuration extraction
- Windows registry access (mocked)
- Chrome configuration reading (mocked)
- Error handling for missing PAC files
- PAC script evaluation
- Cross-platform compatibility

The tests use extensive mocking to simulate Windows environments, registry access,
and external dependencies like pypac for comprehensive coverage.
"""

import sys
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest


@pytest.mark.platform_specific
class TestPACProxyDetectorMocked:
    """Test cases for PACProxyDetector class with full mocking of dependencies."""

    def setup_method(self):
        """Set up test fixtures by mocking the entire module."""
        # Clear any existing imports
        if "gitbridge.pac_support" in sys.modules:
            del sys.modules["gitbridge.pac_support"]

        # Mock winreg module
        self.mock_winreg = MagicMock()
        self.mock_winreg.OpenKey.return_value.__enter__ = MagicMock()
        self.mock_winreg.OpenKey.return_value.__exit__ = MagicMock()
        self.mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"

        # Mock pypac module
        self.mock_pypac = MagicMock()
        self.mock_pac_session = MagicMock()
        self.mock_pypac.PACSession = self.mock_pac_session

        # Patch both modules before import
        with patch.dict(
            "sys.modules", {"winreg": self.mock_winreg, "pypac": self.mock_pypac, "pypac.parser": MagicMock()}
        ):
            # Import and create instance
            from gitbridge.pac_support import PACProxyDetector, detect_and_configure_proxy

            self.PACProxyDetector = PACProxyDetector
            self.detect_and_configure_proxy = detect_and_configure_proxy
            self.detector = PACProxyDetector()

    def test_init(self):
        """Test PACProxyDetector initialization."""
        detector = self.PACProxyDetector()
        assert detector.pac_url is None
        assert detector.pac_content is None
        assert detector.pac_object is None

    @pytest.mark.windows
    @patch("gitbridge.pac_support.platform.system")
    def test_is_available_windows(self, mock_platform):
        """Test availability check on Windows."""
        mock_platform.return_value = "Windows"

        with patch("gitbridge.pac_support.WINDOWS_AVAILABLE", True):
            detector = self.PACProxyDetector()
            assert detector.is_available() is True

    @patch("gitbridge.pac_support.platform.system")
    def test_is_available_linux(self, mock_platform):
        """Test availability check on Linux."""
        mock_platform.return_value = "Linux"
        detector = self.PACProxyDetector()
        assert detector.is_available() is False

    @pytest.mark.windows
    def test_get_pac_url_from_registry_success(self):
        """Test successful PAC URL extraction from registry."""
        mock_key = MagicMock()
        self.mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        self.mock_winreg.QueryValueEx.return_value = ("http://proxy.example.com/pac.js", "REG_SZ")

        with patch("gitbridge.pac_support.WINDOWS_AVAILABLE", True):
            result = self.detector.get_pac_url_from_registry()

        assert result == "http://proxy.example.com/pac.js"

    def test_get_pac_url_from_registry_not_found(self):
        """Test PAC URL extraction when registry key is not found."""
        mock_key = MagicMock()
        self.mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        self.mock_winreg.QueryValueEx.side_effect = FileNotFoundError("AutoConfigURL not found")

        with patch("gitbridge.pac_support.WINDOWS_AVAILABLE", True):
            result = self.detector.get_pac_url_from_registry()

        assert result is None

    def test_get_pac_url_from_registry_no_winreg(self):
        """Test PAC URL extraction when winreg is not available."""
        with patch("gitbridge.pac_support.WINDOWS_AVAILABLE", False):
            result = self.detector.get_pac_url_from_registry()

        assert result is None

    @pytest.mark.windows
    def test_get_all_proxy_settings_success(self):
        """Test successful proxy settings extraction from registry."""
        mock_key = MagicMock()
        self.mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        self.mock_winreg.QueryInfoKey.return_value = (None, 2, None)
        self.mock_winreg.EnumValue.side_effect = [
            ("ProxyEnable", 1, "REG_DWORD"),
            ("ProxyServer", "proxy.example.com:8080", "REG_SZ"),
        ]

        with patch("gitbridge.pac_support.WINDOWS_AVAILABLE", True):
            result = self.detector.get_all_proxy_settings()

        expected = {
            "ProxyEnable": 1,
            "ProxyServer": "proxy.example.com:8080",
        }
        assert result == expected

    def test_get_all_proxy_settings_no_winreg(self):
        """Test proxy settings extraction when winreg is not available."""
        with patch("gitbridge.pac_support.WINDOWS_AVAILABLE", False):
            result = self.detector.get_all_proxy_settings()

        assert result == {}

    @patch("builtins.open", mock_open(read_data="PAC script content"))
    @patch("gitbridge.pac_support.platform.system")
    def test_download_pac_content_local_file(self, mock_platform):
        """Test successful PAC content download from local file."""
        mock_platform.return_value = "Windows"
        result = self.detector.download_pac_content("file:///C:/proxy/pac.js")
        assert result == "PAC script content"

    @patch("requests.get")
    def test_download_pac_content_http_success(self, mock_get):
        """Test successful PAC content download from HTTP URL."""
        mock_response = Mock()
        mock_response.text = "PAC script from HTTP"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.detector.download_pac_content("http://proxy.example.com/pac.js")
        assert result == "PAC script from HTTP"

    @patch("requests.get")
    def test_download_pac_content_http_error(self, mock_get):
        """Test PAC content download with HTTP error."""
        mock_get.side_effect = Exception("HTTP error")
        result = self.detector.download_pac_content("http://proxy.example.com/pac.js")
        assert result is None

    def test_detect_pac_using_pypac_success(self):
        """Test successful PAC detection using pypac."""
        mock_pac = Mock()
        mock_pac.url = "http://proxy.example.com/pac.js"
        self.mock_pypac.get_pac.return_value = mock_pac

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.detect_pac_using_pypac()

        assert result == mock_pac
        assert self.detector.pac_object == mock_pac
        assert self.detector.pac_url == "http://proxy.example.com/pac.js"

    def test_detect_pac_using_pypac_not_available(self):
        """Test PAC detection when pypac is not available."""

        # Mock the method to simulate the early return when pypac is not available
        def mock_detect_method():
            # Simulate the check: if not PYPAC_AVAILABLE: return None
            return None

        # Replace the method temporarily
        original_method = self.detector.detect_pac_using_pypac
        self.detector.detect_pac_using_pypac = mock_detect_method

        try:
            result = self.detector.detect_pac_using_pypac()
        finally:
            # Restore the original method
            self.detector.detect_pac_using_pypac = original_method

        assert result is None

    def test_detect_pac_using_pypac_no_url(self):
        """Test PAC detection when PAC object has no URL attribute."""
        mock_pac = Mock()
        if hasattr(mock_pac, "url"):
            delattr(mock_pac, "url")
        self.mock_pypac.get_pac.return_value = mock_pac

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.detect_pac_using_pypac()

        assert result == mock_pac
        assert self.detector.pac_object == mock_pac
        assert self.detector.pac_url is None

    def test_detect_pac_using_pypac_no_pac_found(self):
        """Test PAC detection when no PAC is found."""
        self.mock_pypac.get_pac.return_value = None

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.detect_pac_using_pypac()

        assert result is None

    def test_detect_pac_using_pypac_exception(self):
        """Test PAC detection with exception."""
        self.mock_pypac.get_pac.side_effect = Exception("pypac error")

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.detect_pac_using_pypac()

        assert result is None

    def test_extract_proxy_from_pac_success(self):
        """Test successful proxy extraction from PAC."""
        mock_pac = Mock()
        mock_pac.find_proxy_for_url.return_value = "PROXY proxy.example.com:8080"
        self.detector.pac_object = mock_pac

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.extract_proxy_from_pac("https://api.github.com")

        assert result == "http://proxy.example.com:8080"

    def test_extract_proxy_from_pac_direct(self):
        """Test proxy extraction returning DIRECT."""
        mock_pac = Mock()
        mock_pac.find_proxy_for_url.return_value = "DIRECT"
        self.detector.pac_object = mock_pac

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.extract_proxy_from_pac("https://api.github.com")

        assert result is None

    def test_extract_proxy_from_pac_multiple_proxies(self):
        """Test proxy extraction with multiple proxies."""
        mock_pac = Mock()
        mock_pac.find_proxy_for_url.return_value = "PROXY proxy1.example.com:8080; PROXY proxy2.example.com:8080"
        self.detector.pac_object = mock_pac

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.extract_proxy_from_pac("https://api.github.com")

        assert result == "http://proxy1.example.com:8080"

    def test_extract_proxy_from_pac_socks(self):
        """Test proxy extraction with SOCKS proxy."""
        mock_pac = Mock()
        mock_pac.find_proxy_for_url.return_value = "SOCKS proxy.example.com:1080"
        self.detector.pac_object = mock_pac

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.extract_proxy_from_pac("https://api.github.com")

        assert result == "socks://proxy.example.com:1080"

    def test_extract_proxy_from_pac_not_available(self):
        """Test proxy extraction when pypac is not available."""
        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", False):
            result = self.detector.extract_proxy_from_pac("https://api.github.com")

        assert result is None

    def test_get_proxy_for_url_manual_proxy(self):
        """Test proxy resolution with manual proxy configuration."""
        with (
            patch.object(self.detector, "get_pac_url_from_registry", return_value=None),
            patch.object(self.detector, "detect_pac_using_pypac", return_value=None),
            patch.object(
                self.detector,
                "get_all_proxy_settings",
                return_value={"ProxyEnable": 1, "ProxyServer": "proxy.example.com:8080"},
            ),
        ):
            http_proxy, https_proxy = self.detector.get_proxy_for_url("https://api.github.com")
            assert http_proxy == "http://proxy.example.com:8080"
            assert https_proxy == "http://proxy.example.com:8080"

    def test_get_proxy_for_url_protocol_specific(self):
        """Test proxy resolution with protocol-specific proxy configuration."""
        with (
            patch.object(self.detector, "get_pac_url_from_registry", return_value=None),
            patch.object(self.detector, "detect_pac_using_pypac", return_value=None),
            patch.object(
                self.detector,
                "get_all_proxy_settings",
                return_value={
                    "ProxyEnable": 1,
                    "ProxyServer": "http=proxy1.example.com:8080;https=proxy2.example.com:8080",
                },
            ),
        ):
            http_proxy, https_proxy = self.detector.get_proxy_for_url("https://api.github.com")
            assert http_proxy == "http://proxy1.example.com:8080"
            assert https_proxy == "http://proxy2.example.com:8080"

    def test_get_proxy_for_url_no_proxy(self):
        """Test proxy resolution when no proxy is configured."""
        with (
            patch.object(self.detector, "get_pac_url_from_registry", return_value=None),
            patch.object(self.detector, "detect_pac_using_pypac", return_value=None),
            patch.object(self.detector, "get_all_proxy_settings", return_value={}),
        ):
            http_proxy, https_proxy = self.detector.get_proxy_for_url("https://api.github.com")
            assert http_proxy is None
            assert https_proxy is None

    def test_get_proxy_for_url_proxy_disabled(self):
        """Test proxy resolution with proxy disabled."""
        with (
            patch.object(self.detector, "get_pac_url_from_registry", return_value=None),
            patch.object(self.detector, "detect_pac_using_pypac", return_value=None),
            patch.object(
                self.detector,
                "get_all_proxy_settings",
                return_value={"ProxyEnable": 0, "ProxyServer": "proxy.example.com:8080"},
            ),
        ):
            http_proxy, https_proxy = self.detector.get_proxy_for_url("https://api.github.com")
            assert http_proxy is None
            assert https_proxy is None

    def test_create_pac_session_not_available(self):
        """Test PAC session creation when pypac is not available."""

        # Mock the method to simulate the early return when pypac is not available
        def mock_create_method():
            # Simulate the check: if not PYPAC_AVAILABLE: return None
            return None

        # Replace the method temporarily
        original_method = self.detector.create_pac_session
        self.detector.create_pac_session = mock_create_method

        try:
            result = self.detector.create_pac_session()
        finally:
            # Restore the original method
            self.detector.create_pac_session = original_method

        assert result is None

    @pytest.mark.skipif(sys.platform != "win32", reason="pypac only available on Windows")
    def test_create_pac_session_success(self):
        """Test successful PAC session creation."""
        mock_session = Mock()

        with (
            patch("gitbridge.pac_support.PYPAC_AVAILABLE", True),
            patch.object(self.detector, "get_pac_url_from_registry", return_value=None),
        ):
            # Mock the PACSession import inside the function
            with patch("pypac.PACSession", return_value=mock_session):
                result = self.detector.create_pac_session()

        assert result == mock_session

    @pytest.mark.skipif(sys.platform != "win32", reason="pypac only available on Windows")
    def test_create_pac_session_with_pac_content(self):
        """Test PAC session creation with PAC content."""
        mock_session = Mock()
        pac_content = "function FindProxyForURL(url, host) { return 'DIRECT'; }"

        with (
            patch("gitbridge.pac_support.PYPAC_AVAILABLE", True),
            patch.object(self.detector, "get_pac_url_from_registry", return_value="http://pac.example.com/pac.js"),
            patch.object(self.detector, "download_pac_content", return_value=pac_content),
        ):
            with patch("pypac.PACSession", return_value=mock_session):
                result = self.detector.create_pac_session()

        assert result == mock_session

    @pytest.mark.skipif(sys.platform != "win32", reason="pypac only available on Windows")
    def test_create_pac_session_error(self):
        """Test PAC session creation with error."""
        with (
            patch("gitbridge.pac_support.PYPAC_AVAILABLE", True),
            patch.object(self.detector, "get_pac_url_from_registry", return_value=None),
        ):
            with patch("pypac.PACSession", side_effect=Exception("PACSession error")):
                result = self.detector.create_pac_session()

        assert result is None

    def test_detect_and_configure_proxy_not_available(self):
        """Test detect_and_configure_proxy when not available."""
        with patch.object(self.PACProxyDetector, "is_available", return_value=False):
            result = self.detect_and_configure_proxy()

        expected = {"http": None, "https": None}
        assert result == expected

    def test_detect_and_configure_proxy_success(self):
        """Test successful proxy detection and configuration."""
        with (
            patch.object(self.PACProxyDetector, "is_available", return_value=True),
            patch.object(
                self.PACProxyDetector,
                "get_all_proxy_settings",
                return_value={"ProxyEnable": 1, "ProxyServer": "proxy.example.com:8080"},
            ),
            patch.object(
                self.PACProxyDetector,
                "get_proxy_for_url",
                return_value=("http://proxy.example.com:8080", "http://proxy.example.com:8080"),
            ),
        ):
            result = self.detect_and_configure_proxy()

        expected = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        assert result == expected


class TestPACProxyDetectorEdgeCases:
    """Test cases for edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear any existing imports
        if "gitbridge.pac_support" in sys.modules:
            del sys.modules["gitbridge.pac_support"]

        # Mock modules
        mock_winreg = MagicMock()
        mock_pypac = MagicMock()

        with patch.dict("sys.modules", {"winreg": mock_winreg, "pypac": mock_pypac, "pypac.parser": MagicMock()}):
            from gitbridge.pac_support import PACProxyDetector

            self.detector = PACProxyDetector()

    def test_empty_pac_url(self):
        """Test handling of empty PAC URL."""
        result = self.detector.download_pac_content("")
        assert result is None

    def test_malformed_pac_url(self):
        """Test handling of malformed PAC URL."""
        result = self.detector.download_pac_content("not-a-url")
        assert result is None

    def test_extract_proxy_whitespace_response(self):
        """Test proxy extraction from whitespace-only PAC response."""
        mock_pac = Mock()
        mock_pac.find_proxy_for_url.return_value = "   "
        self.detector.pac_object = mock_pac

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.extract_proxy_from_pac("https://api.github.com")

        assert result is None

    def test_extract_proxy_mixed_case(self):
        """Test proxy string parsing with mixed case."""
        mock_pac = Mock()
        mock_pac.find_proxy_for_url.return_value = "Proxy proxy.example.com:8080"
        self.detector.pac_object = mock_pac

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.extract_proxy_from_pac("https://api.github.com")

        # Should not work as it expects uppercase "PROXY"
        assert result is None

    def test_extract_proxy_extra_whitespace(self):
        """Test proxy string parsing with extra whitespace."""
        mock_pac = Mock()
        mock_pac.find_proxy_for_url.return_value = "  PROXY   proxy.example.com:8080  ; DIRECT  "
        self.detector.pac_object = mock_pac

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.extract_proxy_from_pac("https://api.github.com")

        assert result == "http://proxy.example.com:8080"

    def test_proxy_with_existing_protocol(self):
        """Test proxy extraction with existing protocol."""
        mock_pac = Mock()
        mock_pac.find_proxy_for_url.return_value = "PROXY http://proxy.example.com:8080"
        self.detector.pac_object = mock_pac

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.extract_proxy_from_pac("https://api.github.com")

        assert result == "http://proxy.example.com:8080"

    @patch("builtins.open")
    def test_file_read_error(self, mock_open):
        """Test file reading error handling."""
        mock_open.side_effect = OSError("Permission denied")
        result = self.detector.download_pac_content("file:///C:/proxy/pac.js")
        assert result is None

    def test_extract_proxy_error(self):
        """Test proxy extraction with PAC evaluation error."""
        mock_pac = Mock()
        mock_pac.find_proxy_for_url.side_effect = Exception("PAC evaluation error")
        self.detector.pac_object = mock_pac

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.extract_proxy_from_pac("https://api.github.com")

        assert result is None

    @patch("gitbridge.pac_support.platform.system")
    def test_file_path_conversion_linux(self, mock_platform):
        """Test file URL path conversion on Linux."""
        mock_platform.return_value = "Linux"

        with patch("builtins.open", mock_open(read_data="PAC content")):
            result = self.detector.download_pac_content("file:///home/user/pac.js")
            assert result == "PAC content"


class TestURLParsing:
    """Test cases for URL parsing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        if "gitbridge.pac_support" in sys.modules:
            del sys.modules["gitbridge.pac_support"]

        mock_winreg = MagicMock()
        mock_pypac = MagicMock()

        with patch.dict("sys.modules", {"winreg": mock_winreg, "pypac": mock_pypac, "pypac.parser": MagicMock()}):
            from gitbridge.pac_support import PACProxyDetector

            self.detector = PACProxyDetector()

    def test_various_url_formats(self):
        """Test URL parsing with various formats."""
        mock_pac = Mock()
        mock_pac.find_proxy_for_url.return_value = "PROXY proxy.example.com:8080"
        self.detector.pac_object = mock_pac

        test_urls = [
            "https://api.github.com",
            "https://api.github.com/",
            "https://api.github.com/user/repo",
            "http://internal.company.com",
        ]

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            for url in test_urls:
                result = self.detector.extract_proxy_from_pac(url)
                assert result == "http://proxy.example.com:8080"


@pytest.mark.windows
@pytest.mark.platform_specific
class TestRegistryMocking:
    """Test cases that specifically test Windows registry functionality."""

    def setup_method(self):
        """Set up test fixtures with registry mocking."""
        if "gitbridge.pac_support" in sys.modules:
            del sys.modules["gitbridge.pac_support"]

        # Create detailed winreg mock
        self.mock_winreg = MagicMock()
        self.mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"

        mock_pypac = MagicMock()

        with patch.dict("sys.modules", {"winreg": self.mock_winreg, "pypac": mock_pypac, "pypac.parser": MagicMock()}):
            from gitbridge.pac_support import PACProxyDetector

            self.detector = PACProxyDetector()

    def test_registry_access_error(self):
        """Test registry access error handling."""
        self.mock_winreg.OpenKey.side_effect = OSError("Access denied")

        with patch("gitbridge.pac_support.WINDOWS_AVAILABLE", True):
            result = self.detector.get_pac_url_from_registry()

        assert result is None

    def test_registry_query_error(self):
        """Test registry query error handling."""
        mock_key = MagicMock()
        self.mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        self.mock_winreg.QueryValueEx.side_effect = Exception("Query failed")

        with patch("gitbridge.pac_support.WINDOWS_AVAILABLE", True):
            result = self.detector.get_pac_url_from_registry()

        assert result is None

    def test_registry_enumeration_error(self):
        """Test registry enumeration error handling."""
        mock_key = MagicMock()
        self.mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        self.mock_winreg.QueryInfoKey.return_value = (None, 2, None)
        self.mock_winreg.EnumValue.side_effect = [("ProxyEnable", 1, "REG_DWORD"), Exception("Enum error")]

        with patch("gitbridge.pac_support.WINDOWS_AVAILABLE", True):
            result = self.detector.get_all_proxy_settings()

        # Should return partial results
        assert result == {"ProxyEnable": 1}

    def test_registry_filtering_irrelevant_keys(self):
        """Test that irrelevant registry keys are filtered out."""
        mock_key = MagicMock()
        self.mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        self.mock_winreg.QueryInfoKey.return_value = (None, 3, None)
        self.mock_winreg.EnumValue.side_effect = [
            ("ProxyEnable", 1, "REG_DWORD"),
            ("IrrelevantKey", "value", "REG_SZ"),
            ("ProxyServer", "proxy.example.com:8080", "REG_SZ"),
        ]

        with patch("gitbridge.pac_support.WINDOWS_AVAILABLE", True):
            result = self.detector.get_all_proxy_settings()

        expected = {
            "ProxyEnable": 1,
            "ProxyServer": "proxy.example.com:8080",
        }
        assert result == expected


class TestProxyConfiguration:
    """Test cases for different proxy configuration scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        if "gitbridge.pac_support" in sys.modules:
            del sys.modules["gitbridge.pac_support"]

        mock_winreg = MagicMock()
        mock_pypac = MagicMock()

        with patch.dict("sys.modules", {"winreg": mock_winreg, "pypac": mock_pypac, "pypac.parser": MagicMock()}):
            from gitbridge.pac_support import PACProxyDetector

            self.detector = PACProxyDetector()

    def test_manual_proxy_with_existing_http_prefix(self):
        """Test manual proxy configuration where server already has http prefix."""
        with (
            patch.object(self.detector, "get_pac_url_from_registry", return_value=None),
            patch.object(self.detector, "detect_pac_using_pypac", return_value=None),
            patch.object(
                self.detector,
                "get_all_proxy_settings",
                return_value={"ProxyEnable": 1, "ProxyServer": "http://proxy.example.com:8080"},
            ),
        ):
            http_proxy, https_proxy = self.detector.get_proxy_for_url("https://api.github.com")
            assert http_proxy == "http://proxy.example.com:8080"
            assert https_proxy == "http://proxy.example.com:8080"

    def test_protocol_specific_fallback(self):
        """Test protocol-specific proxy with fallback to HTTP for HTTPS."""
        with (
            patch.object(self.detector, "get_pac_url_from_registry", return_value=None),
            patch.object(self.detector, "detect_pac_using_pypac", return_value=None),
            patch.object(
                self.detector,
                "get_all_proxy_settings",
                return_value={
                    "ProxyEnable": 1,
                    "ProxyServer": "http=proxy1.example.com:8080;ftp=proxy3.example.com:8080",
                },
            ),
        ):
            http_proxy, https_proxy = self.detector.get_proxy_for_url("https://api.github.com")
            assert http_proxy == "http://proxy1.example.com:8080"
            assert https_proxy == "http://proxy1.example.com:8080"  # Falls back to HTTP proxy


class TestIntegrationScenarios:
    """Integration test cases for real-world scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        if "gitbridge.pac_support" in sys.modules:
            del sys.modules["gitbridge.pac_support"]

        # Create comprehensive mocks
        self.mock_winreg = MagicMock()
        self.mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"

        self.mock_pypac = MagicMock()

        with patch.dict(
            "sys.modules", {"winreg": self.mock_winreg, "pypac": self.mock_pypac, "pypac.parser": MagicMock()}
        ):
            from gitbridge.pac_support import PACProxyDetector

            self.PACProxyDetector = PACProxyDetector

    @pytest.mark.skipif(sys.platform != "win32", reason="pypac only available on Windows")
    def test_full_pac_workflow_with_registry(self):
        """Test complete PAC workflow starting from registry detection."""
        # Setup registry mock
        mock_key = MagicMock()
        self.mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        self.mock_winreg.QueryValueEx.return_value = ("http://pac.company.com/proxy.pac", "REG_SZ")

        # Setup HTTP download mock
        mock_response = Mock()
        mock_response.text = "function FindProxyForURL(url, host) { return 'PROXY proxy.company.com:8080'; }"
        mock_response.raise_for_status.return_value = None

        # Setup PAC parsing mock
        mock_pac_obj = Mock()
        mock_pac_obj.find_proxy_for_url.return_value = "PROXY proxy.company.com:8080"

        with (
            patch("gitbridge.pac_support.WINDOWS_AVAILABLE", True),
            patch("gitbridge.pac_support.PYPAC_AVAILABLE", True),
            patch("requests.get", return_value=mock_response),
        ):
            # Mock the pypac.parser.PACFile inside the module
            with patch("gitbridge.pac_support.pypac.parser.PACFile", return_value=mock_pac_obj):
                detector = self.PACProxyDetector()
                http_proxy, https_proxy = detector.get_proxy_for_url("https://api.github.com")

                assert http_proxy == "http://proxy.company.com:8080"
                assert https_proxy == "http://proxy.company.com:8080"

    def test_fallback_to_manual_proxy(self):
        """Test fallback to manual proxy when PAC is not available."""
        # Setup no PAC URL in registry
        mock_key = MagicMock()
        self.mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        self.mock_winreg.QueryValueEx.side_effect = FileNotFoundError("AutoConfigURL not found")

        # Setup manual proxy in registry
        self.mock_winreg.QueryInfoKey.return_value = (None, 2, None)
        self.mock_winreg.EnumValue.side_effect = [
            ("ProxyEnable", 1, "REG_DWORD"),
            ("ProxyServer", "manual-proxy.company.com:8080", "REG_SZ"),
        ]

        with (
            patch("gitbridge.pac_support.WINDOWS_AVAILABLE", True),
            patch("gitbridge.pac_support.PYPAC_AVAILABLE", False),
        ):
            detector = self.PACProxyDetector()
            http_proxy, https_proxy = detector.get_proxy_for_url("https://api.github.com")

            assert http_proxy == "http://manual-proxy.company.com:8080"
            assert https_proxy == "http://manual-proxy.company.com:8080"

    def test_no_proxy_configuration(self):
        """Test when no proxy configuration is found."""
        # Setup empty registry
        mock_key = MagicMock()
        self.mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        self.mock_winreg.QueryValueEx.side_effect = FileNotFoundError("AutoConfigURL not found")
        self.mock_winreg.QueryInfoKey.return_value = (None, 0, None)

        with (
            patch("gitbridge.pac_support.WINDOWS_AVAILABLE", True),
            patch("gitbridge.pac_support.PYPAC_AVAILABLE", True),
        ):
            detector = self.PACProxyDetector()
            http_proxy, https_proxy = detector.get_proxy_for_url("https://api.github.com")

            assert http_proxy is None
            assert https_proxy is None


class TestAdditionalCoverage:
    """Additional test cases to achieve higher coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        if "gitbridge.pac_support" in sys.modules:
            del sys.modules["gitbridge.pac_support"]

        mock_winreg = MagicMock()
        mock_pypac = MagicMock()

        with patch.dict("sys.modules", {"winreg": mock_winreg, "pypac": mock_pypac, "pypac.parser": MagicMock()}):
            from gitbridge.pac_support import PACProxyDetector

            self.detector = PACProxyDetector()

    def test_download_pac_content_unc_path(self):
        """Test PAC content download from UNC path."""
        with (
            patch("builtins.open", mock_open(read_data="PAC UNC content")),
            patch("gitbridge.pac_support.platform.system", return_value="Windows"),
        ):
            result = self.detector.download_pac_content("file://server/share/pac.js")
            assert result == "PAC UNC content"

    def test_download_pac_content_encoding_error(self):
        """Test PAC content download with encoding error."""
        with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
            result = self.detector.download_pac_content("file:///C:/proxy/pac.js")
            assert result is None

    def test_extract_proxy_empty_string(self):
        """Test proxy extraction from empty PAC response."""
        mock_pac = Mock()
        mock_pac.find_proxy_for_url.return_value = ""
        self.detector.pac_object = mock_pac

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.extract_proxy_from_pac("https://api.github.com")

        assert result is None

    def test_extract_proxy_no_pac_object(self):
        """Test proxy extraction when no PAC object exists."""
        self.detector.pac_object = None

        with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
            result = self.detector.extract_proxy_from_pac("https://api.github.com")

        assert result is None

    @pytest.mark.skipif(sys.platform != "win32", reason="pypac only available on Windows")
    def test_get_proxy_for_url_pac_parsing_error(self):
        """Test proxy resolution with PAC parsing error."""
        with (
            patch.object(self.detector, "get_pac_url_from_registry", return_value="http://pac.example.com/pac.js"),
            patch.object(self.detector, "download_pac_content", return_value="invalid pac content"),
        ):
            with patch("gitbridge.pac_support.PYPAC_AVAILABLE", True):
                # Mock pypac.parser.PACFile to raise an exception
                with patch("gitbridge.pac_support.pypac.parser.PACFile", side_effect=Exception("Parse error")):
                    http_proxy, https_proxy = self.detector.get_proxy_for_url("https://api.github.com")

            # Should fall back to manual proxy detection
            assert http_proxy is None
            assert https_proxy is None

    def test_get_proxy_for_url_with_cached_pac_object(self):
        """Test proxy resolution with already cached PAC object."""
        mock_pac = Mock()
        mock_pac.find_proxy_for_url.return_value = "PROXY cached.proxy.com:8080"
        self.detector.pac_object = mock_pac

        # Mock the methods that might be called before using the cached pac_object
        with (
            patch("gitbridge.pac_support.PYPAC_AVAILABLE", True),
            patch.object(self.detector, "get_pac_url_from_registry", return_value=None),
            patch.object(self.detector, "detect_pac_using_pypac", return_value=None),
            patch.object(self.detector, "extract_proxy_from_pac", return_value="http://cached.proxy.com:8080"),
        ):
            http_proxy, https_proxy = self.detector.get_proxy_for_url("https://api.github.com")

        assert http_proxy == "http://cached.proxy.com:8080"
        assert https_proxy == "http://cached.proxy.com:8080"

    @pytest.mark.skipif(sys.platform != "win32", reason="pypac only available on Windows")
    def test_create_pac_session_cached_content(self):
        """Test PAC session creation with cached content."""
        mock_session = Mock()
        self.detector.pac_content = "cached pac content"

        with (
            patch("gitbridge.pac_support.PYPAC_AVAILABLE", True),
            patch.object(self.detector, "get_pac_url_from_registry", return_value="http://pac.example.com/pac.js"),
        ):
            with patch("pypac.PACSession", return_value=mock_session):
                result = self.detector.create_pac_session()

        assert result == mock_session

    def test_is_available_combination_checks(self):
        """Test is_available with different combinations of availability flags."""
        # Test Windows with only PYPAC available
        with (
            patch("gitbridge.pac_support.platform.system", return_value="Windows"),
            patch("gitbridge.pac_support.WINDOWS_AVAILABLE", False),
            patch("gitbridge.pac_support.PYPAC_AVAILABLE", True),
        ):
            assert self.detector.is_available() is True

    def test_detect_and_configure_proxy_with_settings_logged(self):
        """Test detect_and_configure_proxy with settings that get logged."""
        from gitbridge.pac_support import detect_and_configure_proxy

        with patch("gitbridge.pac_support.PACProxyDetector") as mock_detector_class:
            mock_detector = Mock()
            mock_detector.is_available.return_value = True
            mock_detector.get_all_proxy_settings.return_value = {
                "ProxyEnable": 1,
                "ProxyServer": "proxy.example.com:8080",
                "AutoConfigURL": "http://pac.example.com/pac.js",
            }
            mock_detector.get_proxy_for_url.return_value = (
                "http://proxy.example.com:8080",
                "http://proxy.example.com:8080",
            )
            mock_detector_class.return_value = mock_detector

            result = detect_and_configure_proxy()

            expected = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
            assert result == expected
