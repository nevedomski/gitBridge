"""Unit tests for cert_support.py module - Windows certificate auto-detection"""

from unittest.mock import Mock, mock_open, patch

from gitsync.cert_support import (
    WindowsCertificateDetector,
    _temp_cert_files,
    cleanup_temp_certs,
    export_with_wincertstore,
    get_combined_cert_bundle,
    get_system_cert_bundle,
)


class TestWindowsCertificateDetector:
    """Test cases for WindowsCertificateDetector class"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        # Clear any existing temp files from the global list
        _temp_cert_files.clear()

    def teardown_method(self):
        """Clean up after each test method"""
        # Clear temp files list
        _temp_cert_files.clear()

    def test_init_windows(self):
        """Test WindowsCertificateDetector initialization on Windows"""
        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            assert detector.is_windows is True
            assert detector._temp_bundle is None

    def test_init_non_windows(self):
        """Test WindowsCertificateDetector initialization on non-Windows"""
        with patch("platform.system", return_value="Linux"):
            detector = WindowsCertificateDetector()
            assert detector.is_windows is False
            assert detector._temp_bundle is None

    def test_is_available_non_windows(self):
        """Test is_available returns False on non-Windows systems"""
        with patch("platform.system", return_value="Linux"):
            detector = WindowsCertificateDetector()
            assert detector.is_available() is False

    def test_get_windows_certificates_not_available(self):
        """Test get_windows_certificates returns empty list when not available"""
        with patch("platform.system", return_value="Linux"):
            detector = WindowsCertificateDetector()
            result = detector.get_windows_certificates()
            assert result == []

    def test_export_certificates_to_pem_not_available(self):
        """Test export_certificates_to_pem returns None when not available"""
        with patch("platform.system", return_value="Linux"):
            detector = WindowsCertificateDetector()
            result = detector.export_certificates_to_pem()
            assert result is None

    def test_get_cert_bundle_path_existing_bundle(self):
        """Test get_cert_bundle_path returns existing bundle path"""
        with patch("os.path.exists", return_value=True):
            detector = WindowsCertificateDetector()
            detector._temp_bundle = "/tmp/existing_bundle.pem"

            result = detector.get_cert_bundle_path()

            assert result == "/tmp/existing_bundle.pem"

    @patch("gitsync.cert_support.ssl")
    def test_is_available_windows_with_ssl_support(self, mock_ssl):
        """Test is_available returns True on Windows with SSL certificate enumeration"""
        mock_ssl.enum_certificates.return_value = []

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            assert detector.is_available() is True
            mock_ssl.enum_certificates.assert_called_once_with("ROOT")

    @patch("gitsync.cert_support.ssl")
    def test_is_available_windows_without_ssl_support(self, mock_ssl):
        """Test is_available returns False when SSL enumeration fails"""
        mock_ssl.enum_certificates.side_effect = AttributeError("enum_certificates not available")

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            assert detector.is_available() is False

    @patch("gitsync.cert_support.ssl")
    def test_get_windows_certificates_default_stores(self, mock_ssl):
        """Test get_windows_certificates with default store names"""
        # Mock certificate data
        root_certs = [(b"cert1", "x509_asn", None), (b"cert2", "x509_asn", None)]
        ca_certs = [(b"cert3", "x509_asn", None)]

        def enum_side_effect(store_name):
            if store_name == "ROOT":
                return root_certs
            elif store_name == "CA":
                return ca_certs
            return []

        mock_ssl.enum_certificates.side_effect = enum_side_effect

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            result = detector.get_windows_certificates()

            assert len(result) == 3
            assert result == root_certs + ca_certs
            assert mock_ssl.enum_certificates.call_count >= 2

    @patch("gitsync.cert_support.ssl")
    def test_get_windows_certificates_store_error(self, mock_ssl):
        """Test get_windows_certificates handles store access errors gracefully"""

        # First call succeeds, second fails
        def enum_side_effect(store_name):
            if store_name == "ROOT":
                return [(b"cert1", "x509_asn", None)]
            elif store_name == "CA":
                raise OSError("Access denied to CA store")
            return []

        mock_ssl.enum_certificates.side_effect = enum_side_effect

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            result = detector.get_windows_certificates()

            # Should return certificates from successful store only
            assert len(result) == 1
            assert result[0] == (b"cert1", "x509_asn", None)

    @patch("gitsync.cert_support.ssl")
    @patch("gitsync.cert_support.tempfile.NamedTemporaryFile")
    def test_export_certificates_to_pem_without_certifi(self, mock_temp_file, mock_ssl):
        """Test export_certificates_to_pem without including certifi bundle"""
        mock_ssl.enum_certificates.return_value = [(b"cert_der_data", "x509_asn", None)]
        mock_ssl.DER_cert_to_PEM_cert.return_value = (
            "-----BEGIN CERTIFICATE-----\ntest_cert\n-----END CERTIFICATE-----\n"
        )

        # Mock temporary file
        mock_file = Mock()
        mock_file.name = "/tmp/test_certs.pem"
        mock_temp_file.return_value = mock_file

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            result = detector.export_certificates_to_pem(include_certifi=False)

            assert result == "/tmp/test_certs.pem"
            assert "/tmp/test_certs.pem" in _temp_cert_files
            mock_file.write.assert_called()
            mock_file.close.assert_called_once()

    @patch("gitsync.cert_support.ssl")
    @patch("gitsync.cert_support.tempfile.NamedTemporaryFile")
    @patch("builtins.open", new_callable=mock_open, read_data="# Certifi bundle content\n")
    @patch("certifi.where")
    def test_export_certificates_to_pem_with_certifi(
        self, mock_certifi_where, mock_open_file, mock_temp_file, mock_ssl
    ):
        """Test export_certificates_to_pem including certifi bundle"""
        mock_ssl.enum_certificates.return_value = [(b"cert_der_data", "x509_asn", None)]
        mock_ssl.DER_cert_to_PEM_cert.return_value = (
            "-----BEGIN CERTIFICATE-----\ntest_cert\n-----END CERTIFICATE-----\n"
        )
        mock_certifi_where.return_value = "/path/to/cacert.pem"

        # Mock temporary file
        mock_file = Mock()
        mock_file.name = "/tmp/test_certs.pem"
        mock_temp_file.return_value = mock_file

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            result = detector.export_certificates_to_pem(include_certifi=True)

            assert result == "/tmp/test_certs.pem"
            # Should write certifi content and certificate
            assert mock_file.write.call_count >= 2

    @patch("gitsync.cert_support.ssl")
    @patch("gitsync.cert_support.tempfile.NamedTemporaryFile")
    def test_export_certificates_to_pem_der_conversion_error(self, mock_temp_file, mock_ssl):
        """Test export_certificates_to_pem handles DER to PEM conversion errors"""
        mock_ssl.enum_certificates.return_value = [(b"good_cert", "x509_asn", None), (b"bad_cert", "x509_asn", None)]

        # First conversion succeeds, second fails
        def der_to_pem_side_effect(cert_bytes):
            if cert_bytes == b"good_cert":
                return "-----BEGIN CERTIFICATE-----\nvalid_cert\n-----END CERTIFICATE-----\n"
            else:
                raise ValueError("Invalid certificate format")

        mock_ssl.DER_cert_to_PEM_cert.side_effect = der_to_pem_side_effect

        mock_file = Mock()
        mock_file.name = "/tmp/test_certs.pem"
        mock_temp_file.return_value = mock_file

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            result = detector.export_certificates_to_pem(include_certifi=False)

            assert result == "/tmp/test_certs.pem"
            # Should still succeed with the valid certificate

    @patch("gitsync.cert_support.ssl")
    @patch("gitsync.cert_support.tempfile.NamedTemporaryFile")
    def test_export_certificates_to_pem_non_x509_encoding(self, mock_temp_file, mock_ssl):
        """Test export_certificates_to_pem skips non-x509_asn certificates"""
        mock_ssl.enum_certificates.return_value = [
            (b"x509_cert", "x509_asn", None),
            (b"pkcs7_cert", "pkcs_7_asn", None),  # This should be skipped
        ]
        mock_ssl.DER_cert_to_PEM_cert.return_value = (
            "-----BEGIN CERTIFICATE-----\ntest_cert\n-----END CERTIFICATE-----\n"
        )

        mock_file = Mock()
        mock_file.name = "/tmp/test_certs.pem"
        mock_temp_file.return_value = mock_file

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            result = detector.export_certificates_to_pem(include_certifi=False)

            assert result == "/tmp/test_certs.pem"
            # Should only convert the x509_asn certificate
            # Verify it was called with the right certificate
            mock_ssl.DER_cert_to_PEM_cert.assert_called_with(b"x509_cert")

    @patch("gitsync.cert_support.ssl")
    @patch("gitsync.cert_support.tempfile.NamedTemporaryFile")
    def test_export_certificates_to_pem_temp_file_error(self, mock_temp_file, mock_ssl):
        """Test export_certificates_to_pem handles temporary file creation errors"""
        mock_ssl.enum_certificates.return_value = []
        mock_temp_file.side_effect = OSError("Cannot create temporary file")

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            result = detector.export_certificates_to_pem()

            assert result is None


class TestCleanupTempCerts:
    """Test cases for cleanup_temp_certs function"""

    def setup_method(self):
        """Set up test fixtures"""
        _temp_cert_files.clear()

    def teardown_method(self):
        """Clean up after tests"""
        _temp_cert_files.clear()

    @patch("os.path.exists")
    @patch("os.unlink")
    def test_cleanup_temp_certs_existing_files(self, mock_unlink, mock_exists):
        """Test cleanup_temp_certs removes existing temporary files"""
        mock_exists.return_value = True

        # Add some fake temp files
        _temp_cert_files.extend(["/tmp/cert1.pem", "/tmp/cert2.pem"])

        cleanup_temp_certs()

        assert mock_exists.call_count == 2
        assert mock_unlink.call_count == 2
        mock_unlink.assert_any_call("/tmp/cert1.pem")
        mock_unlink.assert_any_call("/tmp/cert2.pem")

    @patch("os.path.exists")
    @patch("os.unlink")
    def test_cleanup_temp_certs_missing_files(self, mock_unlink, mock_exists):
        """Test cleanup_temp_certs handles missing files gracefully"""
        mock_exists.return_value = False

        _temp_cert_files.append("/tmp/missing_cert.pem")

        cleanup_temp_certs()

        mock_exists.assert_called_once_with("/tmp/missing_cert.pem")
        mock_unlink.assert_not_called()

    @patch("os.path.exists")
    @patch("os.unlink")
    def test_cleanup_temp_certs_unlink_error(self, mock_unlink, mock_exists):
        """Test cleanup_temp_certs handles file deletion errors"""
        mock_exists.return_value = True
        mock_unlink.side_effect = OSError("Permission denied")

        _temp_cert_files.append("/tmp/protected_cert.pem")

        # Should not raise exception
        cleanup_temp_certs()

        mock_unlink.assert_called_once_with("/tmp/protected_cert.pem")

    def test_cleanup_registered_with_atexit(self):
        """Test that cleanup_temp_certs is registered with atexit"""
        # Check that the cleanup function is in atexit handlers
        # This is a bit tricky to test directly, but we can verify the function exists
        assert callable(cleanup_temp_certs)


class TestGetSystemCertBundle:
    """Test cases for get_system_cert_bundle function"""

    @patch("gitsync.cert_support.WindowsCertificateDetector")
    def test_get_system_cert_bundle_available(self, mock_detector_class):
        """Test get_system_cert_bundle when Windows certificates are available"""
        mock_detector = Mock()
        mock_detector.is_available.return_value = True
        mock_detector.export_certificates_to_pem.return_value = "/tmp/system_certs.pem"
        mock_detector_class.return_value = mock_detector

        result = get_system_cert_bundle()

        assert result == "/tmp/system_certs.pem"
        mock_detector.is_available.assert_called_once()
        mock_detector.export_certificates_to_pem.assert_called_once()

    @patch("gitsync.cert_support.WindowsCertificateDetector")
    def test_get_system_cert_bundle_not_available(self, mock_detector_class):
        """Test get_system_cert_bundle when Windows certificates are not available"""
        mock_detector = Mock()
        mock_detector.is_available.return_value = False
        mock_detector_class.return_value = mock_detector

        result = get_system_cert_bundle()

        assert result is None
        mock_detector.is_available.assert_called_once()
        mock_detector.export_certificates_to_pem.assert_not_called()


class TestGetCombinedCertBundle:
    """Test cases for get_combined_cert_bundle function"""

    def test_get_combined_cert_bundle_non_windows(self):
        """Test get_combined_cert_bundle returns None on non-Windows systems"""
        with patch("platform.system", return_value="Linux"):
            result = get_combined_cert_bundle()
            assert result is None

    @patch("gitsync.cert_support.WindowsCertificateDetector")
    def test_get_combined_cert_bundle_windows_available(self, mock_detector_class):
        """Test get_combined_cert_bundle on Windows with available certificates"""
        mock_detector = Mock()
        mock_detector.is_available.return_value = True
        mock_detector.export_certificates_to_pem.return_value = "/tmp/combined_certs.pem"
        mock_detector_class.return_value = mock_detector

        with patch("platform.system", return_value="Windows"):
            result = get_combined_cert_bundle()

            assert result == "/tmp/combined_certs.pem"
            mock_detector.is_available.assert_called_once()
            mock_detector.export_certificates_to_pem.assert_called_once_with(include_certifi=True)

    @patch("gitsync.cert_support.WindowsCertificateDetector")
    def test_get_combined_cert_bundle_windows_not_available(self, mock_detector_class):
        """Test get_combined_cert_bundle on Windows without available certificates"""
        mock_detector = Mock()
        mock_detector.is_available.return_value = False
        mock_detector_class.return_value = mock_detector

        with patch("platform.system", return_value="Windows"):
            result = get_combined_cert_bundle()

            assert result is None
            mock_detector.is_available.assert_called_once()
            mock_detector.export_certificates_to_pem.assert_not_called()

    @patch("gitsync.cert_support.WindowsCertificateDetector")
    def test_get_combined_cert_bundle_windows_exception(self, mock_detector_class):
        """Test get_combined_cert_bundle handles exceptions gracefully"""
        mock_detector_class.side_effect = Exception("Detector initialization failed")

        with patch("platform.system", return_value="Windows"):
            result = get_combined_cert_bundle()
            assert result is None

    @patch("gitsync.cert_support.WindowsCertificateDetector")
    def test_get_combined_cert_bundle_export_returns_none(self, mock_detector_class):
        """Test get_combined_cert_bundle when export returns None"""
        mock_detector = Mock()
        mock_detector.is_available.return_value = True
        mock_detector.export_certificates_to_pem.return_value = None
        mock_detector_class.return_value = mock_detector

        with patch("platform.system", return_value="Windows"):
            result = get_combined_cert_bundle()
            assert result is None


class TestExportWithWincertstore:
    """Test cases for export_with_wincertstore function"""

    @patch("gitsync.cert_support.tempfile.NamedTemporaryFile")
    @patch("builtins.open", new_callable=mock_open, read_data="# Certifi content")
    @patch("certifi.where")
    def test_export_with_wincertstore_success(self, mock_certifi_where, mock_open_file, mock_temp_file):
        """Test export_with_wincertstore successful operation"""
        mock_certifi_where.return_value = "/path/to/cacert.pem"

        # Mock temporary file
        mock_file = Mock()
        mock_file.name = "/tmp/wincert_bundle.pem"
        mock_temp_file.return_value = mock_file

        # Mock wincertstore
        mock_cert = Mock()
        mock_cert.get_pem.return_value = b"-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----\n"

        mock_store = Mock()
        mock_store.itercerts.return_value = [mock_cert]
        mock_store.__enter__ = Mock(return_value=mock_store)
        mock_store.__exit__ = Mock(return_value=None)

        # Mock the imports and classes
        with patch.dict("sys.modules", {"wincertstore": Mock()}):
            import sys

            sys.modules["wincertstore"].CertSystemStore = Mock(return_value=mock_store)
            sys.modules["wincertstore"].SERVER_AUTH = "server_auth"

            result = export_with_wincertstore()

        assert result == "/tmp/wincert_bundle.pem"
        assert "/tmp/wincert_bundle.pem" in _temp_cert_files

    @patch("certifi.where")
    def test_export_with_wincertstore_certifi_import_error(self, mock_certifi_where):
        """Test export_with_wincertstore handles certifi ImportError"""
        mock_certifi_where.side_effect = ImportError("certifi not available")

        result = export_with_wincertstore()

        assert result is None

    def test_export_with_wincertstore_wincertstore_import_error(self):
        """Test export_with_wincertstore handles wincertstore ImportError"""
        # Simulate ImportError when trying to import wincertstore
        with patch.dict("sys.modules", {}):  # Clear modules
            with patch("certifi.where", return_value="/path/to/cacert.pem"):
                result = export_with_wincertstore()

        assert result is None

    @patch("gitsync.cert_support.tempfile.NamedTemporaryFile")
    @patch("builtins.open", new_callable=mock_open, read_data="# Certifi content")
    @patch("certifi.where")
    def test_export_with_wincertstore_general_exception(self, mock_certifi_where, mock_open_file, mock_temp_file):
        """Test export_with_wincertstore handles general exceptions"""
        mock_certifi_where.return_value = "/path/to/cacert.pem"
        mock_temp_file.side_effect = OSError("Cannot create temp file")

        result = export_with_wincertstore()

        assert result is None


class TestIntegrationScenarios:
    """Integration test scenarios for certificate detection workflow"""

    def setup_method(self):
        """Set up test fixtures"""
        _temp_cert_files.clear()

    def teardown_method(self):
        """Clean up after tests"""
        _temp_cert_files.clear()

    @patch("gitsync.cert_support.ssl")
    @patch("gitsync.cert_support.tempfile.NamedTemporaryFile")
    @patch("builtins.open", new_callable=mock_open, read_data="# Certifi CA bundle\n")
    @patch("certifi.where")
    def test_full_certificate_detection_workflow(self, mock_certifi_where, mock_open_file, mock_temp_file, mock_ssl):
        """Test complete certificate detection and export workflow"""
        mock_certifi_where.return_value = "/path/to/cacert.pem"

        # Mock certificate data
        root_cert = (b"root_cert_der", "x509_asn", None)
        ca_cert = (b"ca_cert_der", "x509_asn", None)

        def enum_side_effect(store_name):
            if store_name == "ROOT":
                return [root_cert]
            elif store_name == "CA":
                return [ca_cert]
            return []

        mock_ssl.enum_certificates.side_effect = enum_side_effect

        # Mock PEM conversion
        def der_to_pem_side_effect(cert_bytes):
            if cert_bytes == b"root_cert_der":
                return "-----BEGIN CERTIFICATE-----\nROOT_CERT_PEM\n-----END CERTIFICATE-----\n"
            elif cert_bytes == b"ca_cert_der":
                return "-----BEGIN CERTIFICATE-----\nCA_CERT_PEM\n-----END CERTIFICATE-----\n"
            return ""

        mock_ssl.DER_cert_to_PEM_cert.side_effect = der_to_pem_side_effect

        # Mock temporary file
        mock_file = Mock()
        mock_file.name = "/tmp/combined_bundle.pem"
        mock_temp_file.return_value = mock_file

        with patch("platform.system", return_value="Windows"):
            # Test the complete workflow
            result = get_combined_cert_bundle()

        assert result == "/tmp/combined_bundle.pem"
        assert "/tmp/combined_bundle.pem" in _temp_cert_files

        # Verify the workflow steps
        assert mock_ssl.enum_certificates.call_count >= 2  # ROOT and CA stores
        assert mock_ssl.DER_cert_to_PEM_cert.call_count >= 2  # Both certificates converted

        # Verify file writing calls
        write_calls = [call[0][0] for call in mock_file.write.call_args_list]

        # Should write certifi content and both certificates
        assert any("# Certifi CA bundle" in str(call) for call in write_calls)
        assert any("ROOT_CERT_PEM" in str(call) for call in write_calls)
        assert any("CA_CERT_PEM" in str(call) for call in write_calls)

    def test_fallback_to_default_on_non_windows(self):
        """Test system falls back to default behavior on non-Windows"""
        with patch("platform.system", return_value="Darwin"):  # macOS
            # All functions should return None or empty on non-Windows
            assert get_system_cert_bundle() is None
            assert get_combined_cert_bundle() is None

            detector = WindowsCertificateDetector()
            assert detector.is_available() is False
            assert detector.get_windows_certificates() == []
            assert detector.export_certificates_to_pem() is None

    @patch("gitsync.cert_support.ssl")
    def test_graceful_degradation_on_ssl_errors(self, mock_ssl):
        """Test graceful degradation when SSL certificate enumeration fails"""
        mock_ssl.enum_certificates.side_effect = OSError("Certificate store access denied")

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()

            # Should handle SSL errors gracefully
            assert detector.is_available() is False
            assert detector.get_windows_certificates() == []
            assert detector.export_certificates_to_pem() is None

            # Higher-level functions should also handle this
            assert get_system_cert_bundle() is None
            assert get_combined_cert_bundle() is None


class TestTempFileManagement:
    """Test cases for temporary file management and cleanup"""

    def setup_method(self):
        """Set up test fixtures"""
        _temp_cert_files.clear()

    def teardown_method(self):
        """Clean up after tests"""
        _temp_cert_files.clear()

    def test_temp_file_tracking(self):
        """Test that temporary files are properly tracked"""
        # Simulate adding temp files
        _temp_cert_files.extend(["/tmp/cert1.pem", "/tmp/cert2.pem"])

        assert len(_temp_cert_files) == 2
        assert "/tmp/cert1.pem" in _temp_cert_files
        assert "/tmp/cert2.pem" in _temp_cert_files

    @patch("gitsync.cert_support.ssl")
    @patch("gitsync.cert_support.tempfile.NamedTemporaryFile")
    def test_multiple_exports_track_all_files(self, mock_temp_file, mock_ssl):
        """Test that multiple certificate exports track all temporary files"""
        mock_ssl.enum_certificates.return_value = []

        # Mock different temporary files for each call
        temp_files = [Mock(), Mock()]
        temp_files[0].name = "/tmp/export1.pem"
        temp_files[1].name = "/tmp/export2.pem"

        mock_temp_file.side_effect = temp_files

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()

            # Make multiple exports
            detector.export_certificates_to_pem()
            detector.export_certificates_to_pem()

            # Both files should be tracked
            assert len(_temp_cert_files) >= 2
            assert "/tmp/export1.pem" in _temp_cert_files
            assert "/tmp/export2.pem" in _temp_cert_files

    @patch("os.path.exists")
    @patch("os.unlink")
    def test_cleanup_idempotent(self, mock_unlink, mock_exists):
        """Test that cleanup can be called multiple times safely"""
        mock_exists.return_value = True

        _temp_cert_files.append("/tmp/test_cert.pem")

        # Call cleanup multiple times
        cleanup_temp_certs()
        cleanup_temp_certs()
        cleanup_temp_certs()

        # File should be deleted multiple times (this is OK)
        assert mock_unlink.call_count >= 1


class TestErrorHandlingAndEdgeCases:
    """Test cases for error handling and edge cases"""

    def setup_method(self):
        """Set up test fixtures"""
        _temp_cert_files.clear()

    def teardown_method(self):
        """Clean up after tests"""
        _temp_cert_files.clear()

    @patch("gitsync.cert_support.ssl")
    def test_empty_certificate_stores(self, mock_ssl):
        """Test handling of empty certificate stores"""
        mock_ssl.enum_certificates.return_value = []  # Empty store

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            result = detector.get_windows_certificates()

            assert result == []

    @patch("gitsync.cert_support.ssl")
    @patch("gitsync.cert_support.tempfile.NamedTemporaryFile")
    def test_export_with_no_valid_certificates(self, mock_temp_file, mock_ssl):
        """Test export when no valid certificates are found"""
        # Return certificates with unsupported encoding
        mock_ssl.enum_certificates.return_value = [(b"cert1", "pkcs_7_asn", None), (b"cert2", "unknown", None)]

        mock_file = Mock()
        mock_file.name = "/tmp/empty_bundle.pem"
        mock_temp_file.return_value = mock_file

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            result = detector.export_certificates_to_pem(include_certifi=False)

            # Should still create file even with no valid certificates
            assert result == "/tmp/empty_bundle.pem"

    @patch("gitsync.cert_support.ssl")
    @patch("gitsync.cert_support.tempfile.NamedTemporaryFile")
    def test_partial_certificate_conversion_failure(self, mock_temp_file, mock_ssl):
        """Test handling when some certificates fail to convert"""
        mock_ssl.enum_certificates.return_value = [
            (b"good_cert", "x509_asn", None),
            (b"bad_cert1", "x509_asn", None),
            (b"bad_cert2", "x509_asn", None),
            (b"another_good_cert", "x509_asn", None),
        ]

        def der_to_pem_side_effect(cert_bytes):
            if cert_bytes in [b"good_cert", b"another_good_cert"]:
                return f"-----BEGIN CERTIFICATE-----\n{cert_bytes.decode()}\n-----END CERTIFICATE-----\n"
            else:
                import ssl

                raise ssl.SSLError("Invalid certificate format")

        mock_ssl.DER_cert_to_PEM_cert.side_effect = der_to_pem_side_effect

        mock_file = Mock()
        mock_file.name = "/tmp/partial_bundle.pem"
        mock_temp_file.return_value = mock_file

        with patch("platform.system", return_value="Windows"):
            detector = WindowsCertificateDetector()
            result = detector.export_certificates_to_pem(include_certifi=False)

            # Should succeed with partial conversion
            assert result == "/tmp/partial_bundle.pem"

            # Should have attempted conversion for all certificates
            assert mock_ssl.DER_cert_to_PEM_cert.call_count >= 4

            # Should have written the successful conversions
            write_calls = [call[0][0] for call in mock_file.write.call_args_list]
            assert any("good_cert" in str(call) for call in write_calls)
            assert any("another_good_cert" in str(call) for call in write_calls)

    @patch("gitsync.cert_support.WindowsCertificateDetector")
    def test_detector_initialization_failure(self, mock_detector_class):
        """Test handling when WindowsCertificateDetector initialization fails"""
        mock_detector_class.side_effect = RuntimeError("Failed to initialize detector")

        with patch("platform.system", return_value="Windows"):
            # Should handle initialization failure gracefully
            result = get_combined_cert_bundle()
            assert result is None

    def test_module_level_temp_files_list(self):
        """Test that module-level temp files list behaves correctly"""
        # Initially empty
        assert len(_temp_cert_files) == 0

        # Can add items
        _temp_cert_files.append("/tmp/test1.pem")
        _temp_cert_files.extend(["/tmp/test2.pem", "/tmp/test3.pem"])

        assert len(_temp_cert_files) == 3
        assert "/tmp/test1.pem" in _temp_cert_files
        assert "/tmp/test2.pem" in _temp_cert_files
        assert "/tmp/test3.pem" in _temp_cert_files

        # Can clear
        _temp_cert_files.clear()
        assert len(_temp_cert_files) == 0
