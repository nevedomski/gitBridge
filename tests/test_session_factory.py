"""Tests for session_factory module."""

import os
from unittest.mock import patch

import requests

from gitsync.session_factory import SessionFactory


class TestSessionFactory:
    """Test cases for SessionFactory class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = SessionFactory()

    def test_create_session_basic(self):
        """Test basic session creation."""
        session = self.factory.create_session()

        assert isinstance(session, requests.Session)
        assert session.headers.get("Accept") == "application/vnd.github.v3+json"
        assert "Authorization" not in session.headers
        assert session.verify is True

    def test_create_session_with_token(self):
        """Test session creation with authentication token."""
        token = "test_token_123"
        session = self.factory.create_session(token=token)

        assert session.headers.get("Authorization") == f"token {token}"
        assert session.headers.get("Accept") == "application/vnd.github.v3+json"

    def test_create_session_ssl_disabled(self):
        """Test session creation with SSL verification disabled."""
        with patch("urllib3.disable_warnings") as mock_disable_warnings:
            session = self.factory.create_session(verify_ssl=False)

            assert session.verify is False
            mock_disable_warnings.assert_called_once()

    def test_create_session_with_ca_bundle(self):
        """Test session creation with custom CA bundle."""
        ca_bundle = "/path/to/ca-bundle.pem"
        session = self.factory.create_session(ca_bundle=ca_bundle)

        assert session.verify == ca_bundle

    @patch.dict(os.environ, {"HTTP_PROXY": "http://proxy:8080", "HTTPS_PROXY": "https://proxy:8080"})
    def test_create_session_with_proxy_env_vars(self):
        """Test session creation with proxy environment variables."""
        session = self.factory.create_session()

        assert session.proxies.get("http") == "http://proxy:8080"
        assert session.proxies.get("https") == "https://proxy:8080"

    @patch("gitsync.cert_support.get_combined_cert_bundle")
    def test_create_session_auto_cert_success(self, mock_get_bundle):
        """Test session creation with successful auto certificate detection."""
        mock_bundle_path = "/tmp/auto-cert-bundle.pem"
        mock_get_bundle.return_value = mock_bundle_path

        session = self.factory.create_session(auto_cert=True)

        assert session.verify == mock_bundle_path
        mock_get_bundle.assert_called_once()

    @patch("gitsync.cert_support.get_combined_cert_bundle")
    def test_create_session_auto_cert_failure(self, mock_get_bundle):
        """Test session creation with failed auto certificate detection."""
        mock_get_bundle.side_effect = Exception("Failed to get bundle")

        session = self.factory.create_session(auto_cert=True)

        # Should fall back to default SSL verification
        assert session.verify is True
        mock_get_bundle.assert_called_once()

    @patch("gitsync.pac_support.detect_and_configure_proxy")
    def test_create_session_auto_proxy_success(self, mock_detect_proxy):
        """Test session creation with successful auto proxy detection."""
        mock_proxies = {"http": "http://auto-proxy:8080", "https": "https://auto-proxy:8080"}
        mock_detect_proxy.return_value = mock_proxies

        session = self.factory.create_session(auto_proxy=True)

        assert session.proxies.get("http") == "http://auto-proxy:8080"
        assert session.proxies.get("https") == "https://auto-proxy:8080"
        mock_detect_proxy.assert_called_once()

    @patch("gitsync.pac_support.detect_and_configure_proxy")
    def test_create_session_auto_proxy_failure(self, mock_detect_proxy):
        """Test session creation with failed auto proxy detection."""
        mock_detect_proxy.side_effect = Exception("Failed to detect proxy")

        session = self.factory.create_session(auto_proxy=True)

        # Should work without proxy
        assert not session.proxies
        mock_detect_proxy.assert_called_once()

    @patch.dict(os.environ, {"HTTP_PROXY": "http://env-proxy:8080"})
    @patch("gitsync.pac_support.detect_and_configure_proxy")
    def test_env_proxy_overrides_auto_proxy(self, mock_detect_proxy):
        """Test that environment variables override auto-detected proxy."""
        mock_proxies = {"http": "http://auto-proxy:8080"}
        mock_detect_proxy.return_value = mock_proxies

        session = self.factory.create_session(auto_proxy=True)

        # Environment variable should take precedence
        assert session.proxies.get("http") == "http://env-proxy:8080"
        mock_detect_proxy.assert_called_once()

    def test_ca_bundle_overrides_auto_cert(self):
        """Test that explicit ca_bundle overrides auto certificate detection."""
        ca_bundle = "/explicit/ca-bundle.pem"

        with patch("gitsync.cert_support.get_combined_cert_bundle") as mock_get_bundle:
            session = self.factory.create_session(ca_bundle=ca_bundle, auto_cert=True)

            assert session.verify == ca_bundle
            # Should not call auto-detection when explicit bundle provided
            mock_get_bundle.assert_not_called()

    def test_configure_ssl_method(self):
        """Test configure_ssl method directly."""
        session = requests.Session()

        self.factory.configure_ssl(session, verify_ssl=True, ca_bundle="/test/bundle.pem")

        assert session.verify == "/test/bundle.pem"

    def test_configure_proxy_method(self):
        """Test configure_proxy method directly."""
        session = requests.Session()

        with patch.dict(os.environ, {"HTTP_PROXY": "http://test:8080"}):
            self.factory.configure_proxy(session, auto_proxy=False)

            assert session.proxies.get("http") == "http://test:8080"

    def test_configure_auth_method(self):
        """Test configure_auth method directly."""
        session = requests.Session()
        token = "test_token_456"

        self.factory.configure_auth(session, token=token)

        assert session.headers.get("Authorization") == f"token {token}"
        assert session.headers.get("Accept") == "application/vnd.github.v3+json"

    def test_configure_auth_method_no_token(self):
        """Test configure_auth method without token."""
        session = requests.Session()

        self.factory.configure_auth(session, token=None)

        assert "Authorization" not in session.headers
        assert session.headers.get("Accept") == "application/vnd.github.v3+json"
