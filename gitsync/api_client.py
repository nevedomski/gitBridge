"""Low-level GitHub API client for HTTP operations.

This module provides the foundational HTTP client for interacting with the GitHub REST API.
It handles authentication, rate limiting, and basic API operations without implementing
synchronization logic.

Key Features:
    - Low-level HTTP operations with proper error handling
    - Rate limit monitoring and retrieval
    - Authentication management
    - Connection testing and validation
    - Support for corporate environments via SessionFactory

Typical Usage:
    >>> from gitsync.api_client import GitHubAPIClient
    >>> client = GitHubAPIClient(
    ...     owner="user",
    ...     repo="repository",
    ...     token="github_token"
    ... )
    >>> if client.test_connection():
    ...     rate_limit = client.get_rate_limit()
"""

import logging
from typing import Any, Dict, Optional

import requests

from .exceptions import (
    AuthenticationError,
    NetworkError,
    RateLimitError,
    RepositoryNotFoundError,
    wrap_requests_exception,
)
from .session_factory import SessionFactory

logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """Low-level GitHub API client for HTTP operations.

    This class handles the foundational HTTP operations for the GitHub REST API,
    including authentication, session management, and basic connectivity testing.
    It focuses purely on API communication without implementing sync logic.

    Attributes:
        owner (str): GitHub repository owner/organization name
        repo (str): GitHub repository name
        base_url (str): Base URL for GitHub API (https://api.github.com)
        token (Optional[str]): GitHub personal access token
        session (requests.Session): Configured HTTP session for API requests

    DOCDEV-NOTE: Component Architecture - API Communication Layer
        This class is the result of refactoring the monolithic GitHubAPISync class.
        It encapsulates all GitHub API communication logic, providing a clean
        interface for higher-level components like RepositoryManager and FileSynchronizer.

    DOCDEV-NOTE: Design Principles
        - Single Responsibility: Only handles API communication
        - Dependency Injection: Uses SessionFactory for session configuration
        - Error Abstraction: Wraps HTTP errors in domain-specific exceptions
        - Stateless Operations: Each method is independent, no internal state tracking
    """

    def __init__(
        self,
        owner: str,
        repo: str,
        token: Optional[str] = None,
        verify_ssl: bool = True,
        ca_bundle: Optional[str] = None,
        auto_proxy: bool = False,
        auto_cert: bool = False,
    ):
        """Initialize GitHub API client.

        Args:
            owner: GitHub repository owner/organization name
            repo: GitHub repository name
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

        Note:
            Environment variables HTTP_PROXY and HTTPS_PROXY take precedence
            over auto-detected proxy settings.
        """
        self.owner = owner
        self.repo = repo
        self.token = token
        self.base_url = "https://api.github.com"

        # Create configured session using SessionFactory
        # DOCDEV-NOTE: SessionFactory centralizes session configuration logic
        session_factory = SessionFactory()
        self.session = session_factory.create_session(
            token=token,
            verify_ssl=verify_ssl,
            ca_bundle=ca_bundle,
            auto_proxy=auto_proxy,
            auto_cert=auto_cert,
        )

    def test_connection(self) -> bool:
        """Test if API connection works.

        Verifies that the API is accessible and the repository exists.
        Also validates authentication if a token is provided.

        Returns:
            bool: True if connection is successful

        Raises:
            AuthenticationError: If authentication fails (401)
            RepositoryNotFoundError: If repository is not found (404)
            NetworkError: If network connection fails
            RateLimitError: If rate limit is exceeded (403)

        Note:
            This method should be called before other operations to fail fast
            if there are connection or authentication issues.
        """
        try:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}"
            response = self.session.get(url)

            # DOCDEV-NOTE: Different status codes indicate specific failure modes
            if response.status_code == 200:
                logger.info(f"Successfully connected to {self.owner}/{self.repo}")
                return True
            elif response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check your token.",
                    token_provided=self.token is not None,
                    repo_url=f"https://github.com/{self.owner}/{self.repo}",
                )
            elif response.status_code == 403:
                # Could be rate limiting or forbidden
                rate_limit_remaining = response.headers.get("X-RateLimit-Remaining", "0")
                if rate_limit_remaining == "0":
                    raise RateLimitError(
                        "API rate limit exceeded",
                        remaining=0,
                        reset_time=int(response.headers.get("X-RateLimit-Reset", "0")),
                    )
                else:
                    raise AuthenticationError(
                        f"Access forbidden: {response.text}",
                        token_provided=self.token is not None,
                        repo_url=f"https://github.com/{self.owner}/{self.repo}",
                    )
            elif response.status_code == 404:
                raise RepositoryNotFoundError(
                    f"Repository not found: {self.owner}/{self.repo}",
                    owner=self.owner,
                    repo=self.repo,
                )
            else:
                logger.error(f"API request failed: {response.status_code}: {response.text}")
                raise NetworkError(f"API request failed with status {response.status_code}")

        except requests.RequestException as e:
            raise wrap_requests_exception(e, "test API connection") from e

    def get_rate_limit(self) -> Dict[str, Any]:
        """Get current API rate limit status.

        Queries the GitHub API rate limit endpoint to check remaining requests.

        Returns:
            Dict containing rate limit information with keys:
                - 'rate': Core API rate limit info
                - 'resources': Detailed limits for different API endpoints
            Returns empty dict if request fails

        Note:
            Authenticated requests have 5000 requests/hour limit.
            Unauthenticated requests have 60 requests/hour limit.
        """
        try:
            response = self.session.get(f"{self.base_url}/rate_limit")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get rate limit: {e}")
        return {}

    def get_repository_info(self) -> Optional[Dict[str, Any]]:
        """Get basic repository information.

        Fetches repository metadata including default branch, description, etc.

        Returns:
            Repository information dict or None if request fails

        Raises:
            AuthenticationError: If authentication fails
            RepositoryNotFoundError: If repository is not found
            NetworkError: If request fails due to network issues
        """
        try:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}"
            response = self.session.get(url)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed while fetching repository info",
                    token_provided=self.token is not None,
                    repo_url=f"https://github.com/{self.owner}/{self.repo}",
                )
            elif response.status_code == 404:
                raise RepositoryNotFoundError(
                    f"Repository not found: {self.owner}/{self.repo}",
                    owner=self.owner,
                    repo=self.repo,
                )
            else:
                response.raise_for_status()

        except requests.RequestException as e:
            raise wrap_requests_exception(e, "get repository information") from e

        return None

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """Perform GET request to GitHub API.

        Generic method for making GET requests to any GitHub API endpoint.

        Args:
            path: API path relative to base_url (should not start with /)
            params: Optional query parameters

        Returns:
            Response object from the API request

        Raises:
            NetworkError: If request fails due to network issues
            AuthenticationError: If authentication fails (401)
            RateLimitError: If rate limit is exceeded (403)
            RepositoryNotFoundError: If endpoint is not found (404)

        Note:
            This is a low-level method for API access. Most users should use
            higher-level methods in other components.
        """
        try:
            url = f"{self.base_url}/{path.lstrip('/')}"
            response = self.session.get(url, params=params)

            # Handle common error cases
            if response.status_code == 401:
                raise AuthenticationError(
                    f"Authentication failed for {path}",
                    token_provided=self.token is not None,
                    repo_url=f"https://github.com/{self.owner}/{self.repo}",
                )
            elif response.status_code == 403:
                rate_limit_remaining = response.headers.get("X-RateLimit-Remaining", "0")
                if rate_limit_remaining == "0":
                    raise RateLimitError(
                        "API rate limit exceeded",
                        remaining=0,
                        reset_time=int(response.headers.get("X-RateLimit-Reset", "0")),
                    )
            elif response.status_code == 404:
                raise RepositoryNotFoundError(
                    f"API endpoint not found: {path}",
                    owner=self.owner,
                    repo=self.repo,
                )

            return response

        except requests.RequestException as e:
            raise wrap_requests_exception(e, f"GET {path}") from e

    def close(self) -> None:
        """Close the HTTP session and cleanup resources.

        Should be called when the client is no longer needed to free up
        connection pool resources.
        """
        if hasattr(self, "session"):
            self.session.close()
