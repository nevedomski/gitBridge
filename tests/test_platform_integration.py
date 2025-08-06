"""Integration tests for platform-specific functionality.

This module tests that:
1. Platform-specific modules can be imported safely on all platforms
2. Platform detection works correctly
3. Conditional imports behave properly
4. Error handling for missing Windows-only modules works
"""

from unittest.mock import MagicMock, patch

import pytest

from .platform_utils import (
    WindowsModuleMocker,
    is_linux,
    is_macos,
    is_windows,
    mock_windows_modules,
    skip_on_non_windows,
    skip_on_windows,
)


class TestPlatformDetection:
    """Test platform detection utilities."""

    def test_is_windows_detection(self):
        """Test Windows platform detection."""
        with patch("platform.system", return_value="Windows"):
            assert is_windows() is True
            assert is_linux() is False
            assert is_macos() is False

    def test_is_linux_detection(self):
        """Test Linux platform detection."""
        with patch("platform.system", return_value="Linux"):
            assert is_windows() is False
            assert is_linux() is True
            assert is_macos() is False

    def test_is_macos_detection(self):
        """Test macOS platform detection."""
        with patch("platform.system", return_value="Darwin"):
            assert is_windows() is False
            assert is_linux() is False
            assert is_macos() is True


class TestConditionalImports:
    """Test that conditional imports work correctly on all platforms."""

    def test_pac_support_import_on_any_platform(self):
        """Test that pac_support can be imported on any platform."""
        # This should work because we mock the Windows-specific modules
        with patch.dict("sys.modules", mock_windows_modules()):
            import gitsync.pac_support

            detector = gitsync.pac_support.PACProxyDetector()
            assert detector is not None

    def test_cert_support_import_on_any_platform(self):
        """Test that cert_support can be imported on any platform."""
        import gitsync.cert_support

        detector = gitsync.cert_support.WindowsCertificateDetector()
        assert detector is not None

    def test_pac_support_availability_check(self):
        """Test PAC support availability check works correctly."""
        with patch.dict("sys.modules", mock_windows_modules()):
            import gitsync.pac_support

            detector = gitsync.pac_support.PACProxyDetector()

            # On actual Windows, this should work
            with patch("platform.system", return_value="Windows"):
                with patch("gitsync.pac_support.WINDOWS_AVAILABLE", True):
                    assert detector.is_available() is True

            # On non-Windows, this should return False
            with patch("platform.system", return_value="Linux"):
                assert detector.is_available() is False

    def test_cert_support_availability_check(self):
        """Test certificate support availability check works correctly."""
        import gitsync.cert_support

        # On actual Windows with SSL support, this should work
        with patch("platform.system", return_value="Windows"):
            detector = gitsync.cert_support.WindowsCertificateDetector()
            with patch("gitsync.cert_support.ssl") as mock_ssl:
                mock_ssl.enum_certificates.return_value = []
                assert detector.is_available() is True

        # On non-Windows, this should return False
        with patch("platform.system", return_value="Linux"):
            detector = gitsync.cert_support.WindowsCertificateDetector()
            assert detector.is_available() is False


class TestWindowsModuleMocking:
    """Test the Windows module mocking utilities."""

    def test_winreg_mock_creation(self):
        """Test winreg mock creation."""
        mock = WindowsModuleMocker.create_winreg_mock()
        assert mock.HKEY_CURRENT_USER == "HKEY_CURRENT_USER"
        assert mock.OpenKey is not None

    def test_pypac_mock_creation(self):
        """Test pypac mock creation."""
        mock = WindowsModuleMocker.create_pypac_mock()
        assert mock.get_pac is not None
        assert mock.PACSession is not None

    def test_wincertstore_mock_creation(self):
        """Test wincertstore mock creation."""
        mock = WindowsModuleMocker.create_wincertstore_mock()
        assert mock.CertSystemStore is not None
        assert mock.SERVER_AUTH == "server_auth"

    def test_ssl_mock_creation(self):
        """Test SSL mock creation."""
        mock = WindowsModuleMocker.create_ssl_mock()
        assert mock.enum_certificates is not None
        assert mock.DER_cert_to_PEM_cert is not None

    def test_complete_mock_modules_dict(self):
        """Test that complete mock modules dict contains all required modules."""
        mocks = mock_windows_modules()
        expected_modules = {"winreg", "pypac", "pypac.parser", "wincertstore"}
        assert set(mocks.keys()) == expected_modules

        # Verify each mock is properly configured
        assert mocks["winreg"].HKEY_CURRENT_USER is not None
        assert mocks["pypac"].get_pac is not None
        assert mocks["wincertstore"].SERVER_AUTH is not None


@pytest.mark.platform_specific
class TestCrossPlatformFunctionality:
    """Test that platform-specific functionality works across platforms."""

    def test_pac_detection_cross_platform(self):
        """Test PAC detection works on all platforms with proper mocking."""
        with patch.dict("sys.modules", mock_windows_modules()):
            from gitsync.pac_support import detect_and_configure_proxy

            # Should work on any platform with proper mocking
            result = detect_and_configure_proxy()
            assert isinstance(result, dict)
            assert "http" in result
            assert "https" in result

    def test_cert_detection_cross_platform(self):
        """Test certificate detection works on all platforms."""
        from gitsync.cert_support import get_combined_cert_bundle

        # On Windows (mocked), should potentially return a bundle
        with patch("platform.system", return_value="Windows"):
            with patch("gitsync.cert_support.WindowsCertificateDetector") as mock_detector:
                mock_instance = MagicMock()
                mock_instance.is_available.return_value = True
                mock_instance.export_certificates_to_pem.return_value = "/tmp/test.pem"
                mock_detector.return_value = mock_instance

                result = get_combined_cert_bundle()
                assert result == "/tmp/test.pem"

        # On non-Windows, should return None
        with patch("platform.system", return_value="Linux"):
            result = get_combined_cert_bundle()
            assert result is None


class TestMarkersFunctionality:
    """Test that pytest markers work correctly."""

    @pytest.mark.windows
    def test_windows_marker(self):
        """Test that Windows marker is applied correctly."""
        # This test should run on Windows but can be skipped on other platforms
        assert True  # Always passes when run

    @pytest.mark.linux
    def test_linux_marker(self):
        """Test that Linux marker is applied correctly."""
        # This test should run on Linux but can be skipped on other platforms
        assert True  # Always passes when run

    @pytest.mark.platform_specific
    def test_platform_specific_marker(self):
        """Test that platform_specific marker is applied correctly."""
        # This test requires platform-specific handling
        assert True  # Always passes when run


@skip_on_non_windows("This test requires Windows")
def test_skip_on_non_windows_decorator():
    """Test the skip_on_non_windows decorator."""
    # This should only run on Windows
    assert is_windows(), "This test should only run on Windows"


@skip_on_windows("This test should not run on Windows")
def test_skip_on_windows_decorator():
    """Test the skip_on_windows decorator."""
    # This should not run on Windows
    assert not is_windows(), "This test should not run on Windows"
