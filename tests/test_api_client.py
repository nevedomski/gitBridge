"""Unit tests for api_client.py module"""

from unittest.mock import Mock, patch

import pytest
import requests

from gitbridge.api_client import GitHubAPIClient
from gitbridge.exceptions import AuthenticationError, NetworkError, RateLimitError, RepositoryNotFoundError


class TestGitHubAPIClient:
    """Test cases for GitHubAPIClient class"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.owner = "test_owner"
        self.repo = "test_repo"
        self.token = "test_token"

    @patch("gitbridge.api_client.SessionFactory")
    def test_init_basic(self, mock_session_factory):
        """Test basic initialization"""
        mock_factory = Mock()
        mock_session = Mock()
        mock_factory.create_session.return_value = mock_session
        mock_session_factory.return_value = mock_factory

        client = GitHubAPIClient(self.owner, self.repo)

        assert client.owner == self.owner
        assert client.repo == self.repo
        assert client.token is None
        assert client.base_url == "https://api.github.com"
        assert client.session == mock_session
        mock_factory.create_session.assert_called_once_with(
            token=None,
            verify_ssl=True,
            ca_bundle=None,
            auto_proxy=False,
            auto_cert=False,
        )

    @patch("gitbridge.api_client.SessionFactory")
    def test_init_with_options(self, mock_session_factory):
        """Test initialization with all options"""
        mock_factory = Mock()
        mock_session = Mock()
        mock_factory.create_session.return_value = mock_session
        mock_session_factory.return_value = mock_factory

        client = GitHubAPIClient(
            self.owner,
            self.repo,
            token=self.token,
            verify_ssl=False,
            ca_bundle="/path/to/ca.pem",
            auto_proxy=True,
            auto_cert=True,
        )

        assert client.token == self.token
        mock_factory.create_session.assert_called_once_with(
            token=self.token,
            verify_ssl=False,
            ca_bundle="/path/to/ca.pem",
            auto_proxy=True,
            auto_cert=True,
        )

    def test_test_connection_success(self):
        """Test successful connection test"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        mock_response = Mock()
        mock_response.status_code = 200
        client.session.get.return_value = mock_response

        result = client.test_connection()

        assert result is True
        client.session.get.assert_called_once_with(f"https://api.github.com/repos/{self.owner}/{self.repo}")

    def test_test_connection_auth_error(self):
        """Test connection test with authentication error"""
        client = GitHubAPIClient(self.owner, self.repo, token=self.token)
        client.session = Mock()

        mock_response = Mock()
        mock_response.status_code = 401
        client.session.get.return_value = mock_response

        with pytest.raises(AuthenticationError):
            client.test_connection()

    def test_test_connection_not_found(self):
        """Test connection test with repository not found"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        mock_response = Mock()
        mock_response.status_code = 404
        client.session.get.return_value = mock_response

        with pytest.raises(RepositoryNotFoundError):
            client.test_connection()

    def test_test_connection_rate_limit(self):
        """Test connection test with rate limit"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1234567890"}
        client.session.get.return_value = mock_response

        with pytest.raises(RateLimitError):
            client.test_connection()

    def test_test_connection_network_error(self):
        """Test connection test with network error"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        client.session.get.side_effect = requests.ConnectionError("Network error")

        with pytest.raises(NetworkError):
            client.test_connection()

    def test_get_rate_limit_success(self):
        """Test successful rate limit retrieval"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        expected_data = {"rate": {"limit": 5000, "remaining": 4999}}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        client.session.get.return_value = mock_response

        result = client.get_rate_limit()

        assert result == expected_data
        client.session.get.assert_called_once_with("https://api.github.com/rate_limit")

    def test_get_rate_limit_failure(self):
        """Test rate limit retrieval failure"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        mock_response = Mock()
        mock_response.status_code = 500
        client.session.get.return_value = mock_response

        result = client.get_rate_limit()

        assert result == {}

    def test_get_repository_info_success(self):
        """Test successful repository info retrieval"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        expected_data = {"name": self.repo, "default_branch": "main"}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        client.session.get.return_value = mock_response

        result = client.get_repository_info()

        assert result == expected_data

    def test_get_repository_info_not_found(self):
        """Test repository info retrieval with not found"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        mock_response = Mock()
        mock_response.status_code = 404
        client.session.get.return_value = mock_response

        with pytest.raises(RepositoryNotFoundError):
            client.get_repository_info()

    def test_get_success(self):
        """Test successful GET request"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        mock_response = Mock()
        mock_response.status_code = 200
        client.session.get.return_value = mock_response

        result = client.get("repos/owner/repo")

        assert result == mock_response
        client.session.get.assert_called_once_with("https://api.github.com/repos/owner/repo", params=None)

    def test_get_with_params(self):
        """Test GET request with parameters"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        mock_response = Mock()
        mock_response.status_code = 200
        client.session.get.return_value = mock_response

        params = {"per_page": 100}
        result = client.get("repos/owner/repo/branches", params=params)

        assert result == mock_response
        client.session.get.assert_called_once_with("https://api.github.com/repos/owner/repo/branches", params=params)

    def test_get_auth_error(self):
        """Test GET request with authentication error"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        mock_response = Mock()
        mock_response.status_code = 401
        client.session.get.return_value = mock_response

        with pytest.raises(AuthenticationError):
            client.get("repos/owner/repo")

    def test_get_not_found(self):
        """Test GET request with not found"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        mock_response = Mock()
        mock_response.status_code = 404
        client.session.get.return_value = mock_response

        with pytest.raises(RepositoryNotFoundError):
            client.get("repos/owner/repo")

    def test_close(self):
        """Test resource cleanup"""
        client = GitHubAPIClient(self.owner, self.repo)
        client.session = Mock()

        client.close()

        client.session.close.assert_called_once()
