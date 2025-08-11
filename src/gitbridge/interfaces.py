"""Abstract interfaces for better abstraction and extensibility.

This module defines abstract base classes that provide clear contracts for different
components of the gitBridge system. These interfaces enable better separation of concerns,
easier testing, and future extensibility.

Key Interfaces:
    - SyncProvider: Interface for repository synchronization implementations
    - ProxyProvider: Interface for proxy configuration and detection
    - CertificateProvider: Interface for SSL certificate handling
    - AuthenticationProvider: Interface for authentication management

Design Principles:
    - Each interface focuses on a single responsibility
    - Methods are designed to be implementation-agnostic
    - Return types are consistent and well-defined
    - Error handling is delegated to implementations

Typical Usage:
    >>> from gitbridge.interfaces import SyncProvider
    >>> from gitbridge.api_sync import GitHubAPISync
    >>>
    >>> sync_provider: SyncProvider = GitHubAPISync(...)
    >>> if sync_provider.test_connection():
    ...     sync_provider.sync(ref="main")
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SyncProvider(ABC):
    """Abstract interface for repository synchronization implementations.

    This interface defines the contract that all synchronization providers must implement.
    It abstracts the underlying synchronization mechanism (API, browser automation, etc.)
    and provides a consistent interface for repository synchronization operations.

    The interface supports different synchronization methods while maintaining a unified
    API for client code. Implementations handle their own authentication, networking,
    and error handling strategies.

    Attributes:
        stats (SyncStats): Statistics tracking object for sync operations

    DOCDEV-NOTE: Interface Design - Strategy Pattern
        This interface enables the Strategy pattern, allowing different sync
        implementations (API, Browser, Git) to be swapped at runtime without
        changing client code. This is crucial for fallback mechanisms.

    DOCDEV-NOTE: Future Implementations
        Planned implementations include:
        - GitBridgeProvider: Direct git operations when available
        - S3SyncProvider: Sync from S3-hosted repositories
        - BitbucketSyncProvider: Support for Bitbucket repositories
        - GitLabSyncProvider: Support for GitLab repositories

    Methods:
        sync(): Main synchronization method
        test_connection(): Connection and authentication verification
        get_status(): Current provider status and configuration
    """

    @abstractmethod
    def sync(self, ref: str = "main", show_progress: bool = True) -> bool:
        """Synchronize repository to local directory.

        This is the main entry point for repository synchronization. The implementation
        should handle all aspects of downloading repository content including file
        comparison, incremental updates, progress reporting, and error handling.

        Args:
            ref: Git reference to synchronize (branch name, tag, or commit SHA).
                Defaults to "main" branch if not specified.
            show_progress: Whether to display progress indicators during sync.
                Implementations may use progress bars, status messages, or other
                visual feedback mechanisms.

        Returns:
            bool: True if synchronization completed successfully, False otherwise.
                Implementations should not raise exceptions for normal error conditions
                but may raise for critical failures (e.g., configuration errors).

        Note:
            Implementations should support incremental synchronization by comparing
            file hashes or timestamps to avoid unnecessary downloads. Progress
            reporting should be respectful of terminal capabilities and user preferences.
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test connectivity and authentication with the repository.

        This method verifies that the provider can successfully connect to the
        repository and authenticate if required. It should perform minimal operations
        to validate connectivity without triggering rate limits or heavy operations.

        Returns:
            bool: True if connection and authentication are successful, False otherwise.
                This method should not raise exceptions for connection failures but
                may raise for configuration errors.

        Note:
            Implementations should cache authentication tokens and connection state
            where possible to avoid repeated authentication attempts. The test should
            be lightweight and suitable for health checks or configuration validation.
        """
        pass

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """Get current synchronization provider status and metadata.

        Returns comprehensive information about the provider's current state including
        configuration, statistics, authentication status, and any relevant metadata
        for debugging or monitoring purposes.

        Returns:
            Dict[str, Any]: Status dictionary containing:
                - provider_type (str): Implementation type (e.g., "api", "browser")
                - repository (str): Repository identifier or URL
                - local_path (str): Local synchronization directory
                - last_sync (Optional[str]): Timestamp of last successful sync
                - authentication (str): Authentication status ("authenticated", "anonymous", "failed")
                - statistics (Dict): Sync statistics (files, bytes, duration, etc.)
                - configuration (Dict): Relevant configuration parameters
                - health (str): Overall health status ("healthy", "warning", "error")

        Note:
            Status information should be safe to log or display to users. Sensitive
            information like tokens should be masked or omitted. The status should
            reflect real-time state where possible.
        """
        pass


class ProxyProvider(ABC):
    """Abstract interface for proxy configuration and detection.

    This interface abstracts different methods of proxy configuration including
    manual configuration, automatic detection from system settings, PAC script
    parsing, and corporate environment integration.

    The interface allows for pluggable proxy detection strategies while providing
    a consistent API for HTTP client configuration.

    Methods:
        get_proxy_config(): Get proxy configuration for HTTP clients
        detect_proxy(): Auto-detect proxy settings from system
        validate_proxy(): Test proxy connectivity and configuration
    """

    @abstractmethod
    def get_proxy_config(self, url: str) -> dict[str, str | None]:
        """Get proxy configuration for a specific URL.

        Returns proxy configuration suitable for HTTP clients like requests.Session.
        The configuration should include both HTTP and HTTPS proxy settings if
        applicable, formatted for immediate use with HTTP libraries.

        Args:
            url: Target URL for which to determine proxy configuration.
                Different URLs may require different proxy settings in corporate
                environments with complex routing rules.

        Returns:
            Dict[str, Optional[str]]: Proxy configuration dictionary with keys:
                - http (Optional[str]): HTTP proxy URL (e.g., "http://proxy:8080")
                - https (Optional[str]): HTTPS proxy URL (e.g., "https://proxy:8443")
                - no_proxy (Optional[str]): Comma-separated list of hosts to bypass

                All values may be None if no proxy is configured or required.

        Note:
            Implementations should handle proxy bypass lists and corporate proxy
            authentication. The returned configuration should be immediately usable
            with requests.Session.proxies.
        """
        pass

    @abstractmethod
    def detect_proxy(self) -> bool:
        """Attempt to automatically detect proxy settings from the system.

        This method tries to discover proxy configuration from various sources
        including system settings, environment variables, PAC scripts, or
        corporate management tools. Detection success enables automatic proxy
        configuration without user intervention.

        Returns:
            bool: True if proxy settings were successfully detected and configured,
                False if no proxy was found or detection failed.

        Note:
            Implementations may cache detected settings for performance. Detection
            should be non-destructive and not modify existing explicit configuration.
            Multiple detection strategies may be attempted in order of preference.
        """
        pass

    @abstractmethod
    def validate_proxy(self, test_url: str = "https://api.github.com") -> bool:
        """Test proxy connectivity and configuration validity.

        Verifies that the configured proxy can successfully handle requests to
        the target URL. This helps identify proxy authentication issues, firewall
        blocks, or configuration errors before attempting actual synchronization.

        Args:
            test_url: URL to use for proxy testing. Should be representative of
                actual sync traffic (defaults to GitHub API endpoint).

        Returns:
            bool: True if proxy configuration is working correctly, False if
                proxy is configured but not functional.

        Note:
            Testing should be lightweight and not trigger security alerts or
            rate limiting. The test may involve HEAD requests or connection
            tests rather than full HTTP transactions.
        """
        pass


class CertificateProvider(ABC):
    """Abstract interface for SSL certificate handling and management.

    This interface abstracts certificate management including system certificate
    stores, custom CA bundles, corporate certificate injection, and certificate
    validation. It enables support for various corporate environments with
    custom certificate requirements.

    The interface supports both certificate discovery and export functionality
    to integrate with HTTP clients that require certificate bundle files.

    Methods:
        get_certificates(): Retrieve available certificates
        export_certificates(): Create certificate bundle files
        validate_certificates(): Test certificate functionality
    """

    @abstractmethod
    def get_certificates(self, store_names: list[str] | None = None) -> list[tuple[bytes, str, Any]]:
        """Retrieve SSL certificates from configured sources.

        Returns certificates from system stores, custom bundles, or other sources
        in a standardized format suitable for validation and export. This method
        provides access to the raw certificate data for further processing.

        Args:
            store_names: Optional list of certificate store names to query.
                Implementation-specific (e.g., Windows store names like "ROOT", "CA").
                If None, implementation chooses appropriate defaults.

        Returns:
            List[Tuple[bytes, str, Any]]: List of certificate tuples containing:
                - bytes: Certificate data in DER or PEM format
                - str: Encoding format ("x509_asn" for DER, "pem" for PEM)
                - Any: Additional metadata (trust flags, validity, issuer info)

        Note:
            Certificate data should be returned in standard formats compatible
            with SSL libraries. Implementations may filter certificates based
            on validity, trust status, or relevance to HTTPS connections.
        """
        pass

    @abstractmethod
    def export_certificates(self, output_path: str | None = None, include_system: bool = True) -> str | None:
        """Export certificates to a PEM bundle file for HTTP clients.

        Creates a certificate bundle file containing trusted certificates from
        various sources. The bundle is suitable for use with HTTP libraries
        that require CA certificate files for SSL verification.

        Args:
            output_path: Optional path for certificate bundle file. If None,
                implementation chooses appropriate temporary or cache location.
            include_system: Whether to include system/default certificates
                in addition to any custom certificates.

        Returns:
            Optional[str]: Path to created certificate bundle file, or None if
                export failed or no certificates were available.

        Note:
            Exported bundles should be in PEM format for maximum compatibility.
            Implementations may combine multiple certificate sources and should
            handle file permissions appropriately for security.
        """
        pass

    @abstractmethod
    def validate_certificates(self, test_url: str = "https://api.github.com") -> bool:
        """Test certificate bundle functionality with a target URL.

        Verifies that the current certificate configuration can successfully
        validate SSL connections to the target URL. This helps identify certificate
        issues, missing CA certificates, or configuration problems before
        attempting actual synchronization operations.

        Args:
            test_url: URL to use for certificate testing. Should use HTTPS and
                be representative of actual sync traffic.

        Returns:
            bool: True if certificate configuration successfully validates SSL
                connections, False if validation fails.

        Note:
            Testing should perform actual SSL handshake validation but avoid
            triggering security monitoring. The test should be representative
            of real SSL validation that will occur during synchronization.
        """
        pass


class AuthenticationProvider(ABC):
    """Abstract interface for authentication management.

    This interface abstracts various authentication methods including personal
    access tokens, OAuth flows, session cookies, and corporate authentication
    systems. It provides a consistent API for authentication regardless of
    the underlying mechanism.

    The interface supports both header-based and session-based authentication
    patterns used by different HTTP clients and synchronization methods.

    Methods:
        get_auth_headers(): Get authentication headers for HTTP requests
        validate_auth(): Test authentication validity and permissions
        refresh_auth(): Refresh or renew authentication credentials
    """

    @abstractmethod
    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for HTTP requests.

        Returns HTTP headers necessary for authenticating requests with the
        target service. The headers should be suitable for immediate use with
        HTTP clients like requests.Session.

        Returns:
            Dict[str, str]: Authentication headers dictionary. Common examples:
                - {"Authorization": "Bearer <token>"} for OAuth/PAT tokens
                - {"Authorization": "Basic <credentials>"} for basic auth
                - {"Cookie": "<session_cookies>"} for session-based auth
                - {} for anonymous/unauthenticated access

        Note:
            Headers should be formatted for immediate use with HTTP libraries.
            Sensitive values should be handled securely and not logged. The
            method should return current valid credentials or empty dict for
            anonymous access.
        """
        pass

    @abstractmethod
    def validate_auth(self) -> bool:
        """Test authentication validity and verify required permissions.

        Verifies that current authentication credentials are valid and have
        sufficient permissions for repository access. This helps identify
        authentication issues before attempting synchronization operations.

        Returns:
            bool: True if authentication is valid and has required permissions,
                False if authentication is invalid, expired, or lacks permissions.

        Note:
            Validation should test actual API access with minimal operations
            to avoid rate limiting. The test should verify both authentication
            and authorization for repository access operations.
        """
        pass

    @abstractmethod
    def refresh_auth(self) -> bool:
        """Refresh or renew authentication credentials if possible.

        Attempts to refresh expired or soon-to-expire authentication credentials
        using refresh tokens, re-authentication flows, or credential renewal
        mechanisms. This enables long-running synchronization operations.

        Returns:
            bool: True if credentials were successfully refreshed, False if
                refresh failed or is not supported by the authentication method.

        Note:
            Not all authentication methods support refresh (e.g., personal access
            tokens). Implementations should handle refresh gracefully and may
            require user interaction for some authentication flows.
        """
        pass


# DOCDEV-NOTE: Interface design principles
# These interfaces follow several key design principles:
# 1. Single Responsibility - Each interface focuses on one concern
# 2. Implementation Agnostic - No assumptions about underlying technology
# 3. Consistent Return Types - Predictable APIs across implementations
# 4. Error Handling - Implementations handle their own error strategies
# 5. Extensibility - Interfaces can evolve without breaking existing code

# DOCDEV-TODO: Future interface considerations
# 1. Consider adding async variants for better performance
# 2. Add metrics/monitoring interfaces for observability
# 3. Consider configuration validation interfaces
# 4. Add caching interfaces for performance optimization

# DOCDEV-QUESTION: Interface granularity
# Should we split these interfaces further? For example:
# - ProxyDetector vs ProxyConfiguration
# - CertificateDiscovery vs CertificateExport
# Current design balances simplicity with functionality, but may evolve.
