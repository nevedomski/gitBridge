"""Session factory for HTTP session configuration.

This module provides a centralized factory for creating and configuring HTTP sessions
with support for corporate environments including proxy auto-detection, certificate
management, and authentication setup.

The SessionFactory class separates session configuration concerns from the main
GitHubAPISync class, improving maintainability and testability.

Key Features:
    - SSL/TLS certificate configuration with Windows auto-detection
    - Proxy configuration with PAC script auto-detection
    - GitHub authentication setup
    - Centralized session management
    - Corporate environment support

Typical Usage:
    >>> from gitbridge.session_factory import SessionFactory
    >>> factory = SessionFactory()
    >>> session = factory.create_session(
    ...     token="github_token",
    ...     verify_ssl=True,
    ...     auto_proxy=True,
    ...     auto_cert=True
    ... )
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)


class SessionFactory:
    """Factory class for creating and configuring HTTP sessions.

    This factory encapsulates all session configuration logic including SSL/TLS
    setup, proxy configuration, and authentication. It provides a clean separation
    of concerns from the main synchronization logic.

    The factory supports various corporate environment configurations:
    - Custom SSL certificates and CA bundles
    - HTTP/HTTPS proxy configurations with auto-detection
    - GitHub personal access token authentication
    - Windows-specific auto-detection features

    Methods:
        create_session(): Main factory method to create configured session
        configure_ssl(): Configure SSL/TLS certificate verification
        configure_proxy(): Configure HTTP/HTTPS proxy settings
        configure_auth(): Configure GitHub authentication headers
    """

    def create_session(
        self,
        token: str | None = None,
        verify_ssl: bool = True,
        ca_bundle: str | None = None,
        auto_proxy: bool = False,
        auto_cert: bool = False,
    ) -> requests.Session:
        """Create and configure an HTTP session for GitHub API requests.

        This is the main factory method that creates a requests.Session instance
        with all necessary configuration for GitHub API access in corporate
        environments.

        Args:
            token: GitHub personal access token for authentication. Required for
                private repositories and recommended for public ones to avoid
                rate limiting (60 requests/hour without token, 5000 with token)
            verify_ssl: Whether to verify SSL certificates. Set to False only
                in trusted environments with self-signed certificates
            ca_bundle: Path to custom CA bundle file for corporate certificates.
                Takes precedence over auto-detected certificates
            auto_proxy: Whether to auto-detect proxy settings from Windows registry
                or Chrome PAC scripts. Useful in corporate environments
            auto_cert: Whether to auto-detect certificates from Windows certificate
                store. Useful for corporate environments with custom CAs

        Returns:
            Configured requests.Session instance ready for GitHub API calls

        Note:
            The session is configured in this order:
            1. SSL/TLS certificates (explicit > auto-detected > default)
            2. Proxy settings (auto-detected > environment variables)
            3. Authentication headers (if token provided)
        """
        # DOCDEV-NOTE: Session factory centralizes configuration to improve maintainability
        session = requests.Session()

        # Configure SSL/TLS certificate verification
        self.configure_ssl(session, verify_ssl, ca_bundle, auto_cert)

        # Configure proxy settings
        self.configure_proxy(session, auto_proxy)

        # Configure authentication
        self.configure_auth(session, token)

        return session

    def configure_ssl(
        self,
        session: requests.Session,
        verify_ssl: bool,
        ca_bundle: str | None = None,
        auto_cert: bool = False,
    ) -> None:
        """Configure SSL/TLS certificate verification for the session.

        Handles certificate configuration in corporate environments where custom
        CA certificates are required. The configuration priority is:
        1. Explicit ca_bundle parameter
        2. Auto-detected certificates from Windows store
        3. Default system certificates

        Args:
            session: The requests session to configure
            verify_ssl: Whether to enable SSL certificate verification
            ca_bundle: Path to custom CA bundle file
            auto_cert: Whether to auto-detect certificates from Windows store

        Note:
            When verify_ssl is False, SSL warnings are suppressed to reduce noise.
            This should only be used in trusted environments.
        """
        # DOCDEV-NOTE: Certificate configuration order: explicit ca_bundle > auto-detected > default
        cert_bundle = ca_bundle  # Start with explicit ca_bundle if provided

        # Auto-detect certificates from Windows store if enabled
        # DOCDEV-TODO: Add support for macOS Keychain certificate extraction
        if auto_cert and not ca_bundle:
            try:
                from .cert_support import get_combined_cert_bundle

                detected_bundle = get_combined_cert_bundle()
                if detected_bundle:
                    cert_bundle = detected_bundle
                    logger.info(f"Auto-detected certificate bundle: {cert_bundle}")
            except Exception as e:
                # DOCDEV-NOTE: Non-fatal - falls back to default certificates
                logger.warning(f"Failed to auto-detect certificates: {e}")

        # Configure SSL verification
        # DOCDEV-NOTE: SSL verification critical for security - only disable in trusted environments
        if not verify_ssl:
            session.verify = False
            # Suppress SSL warnings when disabled
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        elif cert_bundle:
            session.verify = cert_bundle
            logger.info(f"Using certificate bundle: {cert_bundle}")

    def configure_proxy(
        self,
        session: requests.Session,
        auto_proxy: bool = False,
    ) -> None:
        """Configure HTTP/HTTPS proxy settings for the session.

        Handles proxy configuration in corporate environments with automatic
        detection from Windows registry and Chrome PAC scripts. Environment
        variables take precedence over auto-detected settings.

        Args:
            session: The requests session to configure
            auto_proxy: Whether to auto-detect proxy settings from system

        Note:
            Environment variables HTTP_PROXY and HTTPS_PROXY override
            auto-detected proxy settings for consistency with standard tools.
        """
        proxies = {}

        # First try auto-detection if enabled
        # DOCDEV-NOTE: Proxy auto-detection uses Windows registry and Chrome PAC scripts
        if auto_proxy:
            try:
                from .pac_support import detect_and_configure_proxy

                detected_proxies = detect_and_configure_proxy()
                # Filter out None values to satisfy type checker
                for key, value in detected_proxies.items():
                    if value:
                        proxies[key] = value
                if proxies:
                    logger.info(f"Auto-detected proxy configuration: {proxies}")
            except Exception as e:
                # DOCDEV-NOTE: Non-fatal - falls back to environment variables or direct connection
                logger.warning(f"Failed to auto-detect proxy: {e}")

        # Environment variables override auto-detection
        # DOCDEV-NOTE: Standard proxy environment variables take precedence for consistency
        http_proxy = os.environ.get("HTTP_PROXY")
        if http_proxy:
            proxies["http"] = http_proxy
        https_proxy = os.environ.get("HTTPS_PROXY")
        if https_proxy:
            proxies["https"] = https_proxy

        if proxies:
            session.proxies.update(proxies)
            if not auto_proxy or os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY"):
                logger.info(f"Using proxy configuration: {proxies}")

    def configure_auth(
        self,
        session: requests.Session,
        token: str | None = None,
    ) -> None:
        """Configure GitHub authentication headers for the session.

        Sets up the necessary headers for GitHub API authentication using
        personal access tokens. Also configures the Accept header for
        GitHub API v3 compatibility.

        Args:
            session: The requests session to configure
            token: GitHub personal access token for authentication

        Note:
            Token format is "token <PAT>" for personal access tokens.
            Without authentication, rate limit is 60 requests/hour.
            With authentication, rate limit is 5000 requests/hour.
        """
        # Set up authentication if token provided
        # DOCDEV-NOTE: Token format is "token <PAT>" for personal access tokens
        # DOCDEV-TODO: Add support for GitHub App authentication (JWT tokens)
        if token:
            session.headers.update({"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"})
        else:
            session.headers.update({"Accept": "application/vnd.github.v3+json"})
