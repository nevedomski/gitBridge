"""Platform detection utilities and common mocking patterns for cross-platform testing.

This module provides utilities for:
- Platform detection and conditional test execution
- Common mocking patterns for Windows-specific modules
- Test utilities for cross-platform compatibility
"""

import platform
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest


def is_windows() -> bool:
    """Check if the current platform is Windows."""
    return platform.system() == "Windows"


def is_linux() -> bool:
    """Check if the current platform is Linux."""
    return platform.system() == "Linux"


def is_macos() -> bool:
    """Check if the current platform is macOS (Darwin)."""
    return platform.system() == "Darwin"


def skip_on_non_windows(reason: str = "Windows-only functionality") -> pytest.MarkDecorator:
    """Skip test on non-Windows platforms."""
    return pytest.mark.skipif(not is_windows(), reason=reason)


def skip_on_windows(reason: str = "Non-Windows functionality") -> pytest.MarkDecorator:
    """Skip test on Windows platforms."""
    return pytest.mark.skipif(is_windows(), reason=reason)


def skip_on_linux(reason: str = "Non-Linux functionality") -> pytest.MarkDecorator:
    """Skip test on Linux platforms."""
    return pytest.mark.skipif(is_linux(), reason=reason)


def skip_on_macos(reason: str = "Non-macOS functionality") -> pytest.MarkDecorator:
    """Skip test on macOS platforms."""
    return pytest.mark.skipif(is_macos(), reason=reason)


# Custom pytest markers
windows_only = pytest.mark.windows
platform_specific = pytest.mark.platform_specific


class WindowsModuleMocker:
    """Utility class for mocking Windows-specific modules."""

    @staticmethod
    def create_winreg_mock() -> MagicMock:
        """Create a mock for the winreg module."""
        mock_winreg = MagicMock()
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        mock_winreg.HKEY_LOCAL_MACHINE = "HKEY_LOCAL_MACHINE"

        # Configure OpenKey to return a context manager
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__ = Mock(return_value=mock_key)
        mock_winreg.OpenKey.return_value.__exit__ = Mock(return_value=None)

        return mock_winreg

    @staticmethod
    def create_pypac_mock() -> MagicMock:
        """Create a mock for the pypac module."""
        mock_pypac = MagicMock()
        mock_pypac.get_pac.return_value = None

        # Mock PACSession
        mock_session = MagicMock()
        mock_pypac.PACSession = Mock(return_value=mock_session)

        return mock_pypac

    @staticmethod
    def create_wincertstore_mock() -> MagicMock:
        """Create a mock for the wincertstore module."""
        mock_wincertstore = MagicMock()

        # Mock certificate store
        mock_store = MagicMock()
        mock_store.itercerts.return_value = []
        mock_store.__enter__ = Mock(return_value=mock_store)
        mock_store.__exit__ = Mock(return_value=None)

        mock_wincertstore.CertSystemStore = Mock(return_value=mock_store)
        mock_wincertstore.SERVER_AUTH = "server_auth"

        return mock_wincertstore

    @staticmethod
    def create_ssl_mock() -> MagicMock:
        """Create a mock for Windows-specific SSL functionality."""
        mock_ssl = MagicMock()
        mock_ssl.enum_certificates.return_value = []
        mock_ssl.DER_cert_to_PEM_cert.return_value = "-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----\n"

        return mock_ssl


def mock_windows_modules() -> dict[str, Any]:
    """Create a complete set of Windows module mocks.

    Returns:
        Dictionary suitable for use with patch.dict('sys.modules', ...)
    """
    mocker = WindowsModuleMocker()

    return {
        "winreg": mocker.create_winreg_mock(),
        "pypac": mocker.create_pypac_mock(),
        "pypac.parser": MagicMock(),
        "wincertstore": mocker.create_wincertstore_mock(),
    }


def setup_windows_test_environment():
    """Set up test environment for Windows-specific functionality.

    This should be used as a fixture or called at the beginning of Windows tests.
    """
    # Mock platform.system to return "Windows" if not already on Windows
    if not is_windows():
        import unittest.mock

        return unittest.mock.patch("platform.system", return_value="Windows")
    return unittest.mock.MagicMock()  # Return a no-op mock


# Common test data for Windows functionality
SAMPLE_REGISTRY_DATA = {
    "ProxyEnable": 1,
    "ProxyServer": "proxy.example.com:8080",
    "AutoConfigURL": "http://pac.example.com/pac.js",
}

SAMPLE_PAC_SCRIPT = """
function FindProxyForURL(url, host) {
    if (shExpMatch(host, "*.local")) {
        return "DIRECT";
    }
    return "PROXY proxy.example.com:8080";
}
"""

SAMPLE_CERTIFICATE_DATA = [
    (b"cert_der_data_1", "x509_asn", None),
    (b"cert_der_data_2", "x509_asn", None),
]

SAMPLE_PEM_CERTIFICATE = """-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKoK/heBjcOuMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTcxMTExMTQwNzExWhcNMTgxMTExMTQwNzExWjBF
-----END CERTIFICATE-----"""


def get_platform_specific_test_data() -> dict[str, Any]:
    """Get platform-specific test data."""
    return {
        "windows": {
            "registry_data": SAMPLE_REGISTRY_DATA,
            "pac_script": SAMPLE_PAC_SCRIPT,
            "certificate_data": SAMPLE_CERTIFICATE_DATA,
            "pem_certificate": SAMPLE_PEM_CERTIFICATE,
        }
    }
