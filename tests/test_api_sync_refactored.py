"""Unit tests for refactored api_sync.py facade"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from gitbridge.api_sync import GitHubAPISync


class TestGitHubAPISyncFacade:
    """Test cases for GitHubAPISync facade class"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_url = "https://github.com/owner/repo"
        self.token = "test_token"

    @patch("gitbridge.api_sync.FileSynchronizer")
    @patch("gitbridge.api_sync.RepositoryManager")
    @patch("gitbridge.api_sync.GitHubAPIClient")
    @patch("gitbridge.api_sync.parse_github_url")
    def test_init_basic(self, mock_parse_url, mock_api_client, mock_repo_manager, mock_file_sync):
        """Test basic initialization of facade"""
        mock_parse_url.return_value = ("owner", "repo")
        mock_client = Mock()
        mock_api_client.return_value = mock_client
        mock_repository = Mock()
        mock_repo_manager.return_value = mock_repository
        mock_synchronizer = Mock()
        mock_file_sync.return_value = mock_synchronizer

        sync = GitHubAPISync(self.repo_url, self.temp_dir)

        assert sync.owner == "owner"
        assert sync.repo == "repo"
        assert sync.local_path == Path(self.temp_dir)
        assert sync.token is None
        assert sync.client == mock_client
        assert sync.repository == mock_repository
        assert sync.synchronizer == mock_synchronizer

        mock_parse_url.assert_called_once_with(self.repo_url)
        mock_api_client.assert_called_once_with(
            owner="owner",
            repo="repo",
            token=None,
            verify_ssl=True,
            ca_bundle=None,
            auto_proxy=False,
            auto_cert=False,
        )

    @patch("gitbridge.api_sync.FileSynchronizer")
    @patch("gitbridge.api_sync.RepositoryManager")
    @patch("gitbridge.api_sync.GitHubAPIClient")
    @patch("gitbridge.api_sync.parse_github_url")
    def test_init_with_options(self, mock_parse_url, mock_api_client, mock_repo_manager, mock_file_sync):
        """Test initialization with all options"""
        mock_parse_url.return_value = ("owner", "repo")
        mock_client = Mock()
        mock_api_client.return_value = mock_client
        mock_repository = Mock()
        mock_repo_manager.return_value = mock_repository
        mock_synchronizer = Mock()
        mock_file_sync.return_value = mock_synchronizer

        sync = GitHubAPISync(
            self.repo_url,
            self.temp_dir,
            token=self.token,
            verify_ssl=False,
            ca_bundle="/path/to/ca.pem",
            auto_proxy=True,
            auto_cert=True,
        )

        assert sync.token == self.token
        mock_api_client.assert_called_once_with(
            owner="owner",
            repo="repo",
            token=self.token,
            verify_ssl=False,
            ca_bundle="/path/to/ca.pem",
            auto_proxy=True,
            auto_cert=True,
        )

    @patch("gitbridge.api_sync.FileSynchronizer")
    @patch("gitbridge.api_sync.RepositoryManager")
    @patch("gitbridge.api_sync.GitHubAPIClient")
    @patch("gitbridge.api_sync.parse_github_url")
    def test_test_connection_success(self, mock_parse_url, mock_api_client, mock_repo_manager, mock_file_sync):
        """Test successful connection test delegation"""
        mock_parse_url.return_value = ("owner", "repo")
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_api_client.return_value = mock_client
        mock_repo_manager.return_value = Mock()
        mock_file_sync.return_value = Mock()

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.test_connection()

        assert result is True
        mock_client.test_connection.assert_called_once()

    @patch("gitbridge.api_sync.FileSynchronizer")
    @patch("gitbridge.api_sync.RepositoryManager")
    @patch("gitbridge.api_sync.GitHubAPIClient")
    @patch("gitbridge.api_sync.parse_github_url")
    def test_test_connection_exception(self, mock_parse_url, mock_api_client, mock_repo_manager, mock_file_sync):
        """Test connection test with exception handling"""
        mock_parse_url.return_value = ("owner", "repo")
        mock_client = Mock()
        mock_client.test_connection.side_effect = Exception("Network error")
        mock_api_client.return_value = mock_client
        mock_repo_manager.return_value = Mock()
        mock_file_sync.return_value = Mock()

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.test_connection()

        assert result is False

    @patch("gitbridge.api_sync.FileSynchronizer")
    @patch("gitbridge.api_sync.RepositoryManager")
    @patch("gitbridge.api_sync.GitHubAPIClient")
    @patch("gitbridge.api_sync.parse_github_url")
    def test_get_rate_limit(self, mock_parse_url, mock_api_client, mock_repo_manager, mock_file_sync):
        """Test rate limit delegation"""
        mock_parse_url.return_value = ("owner", "repo")
        mock_client = Mock()
        expected_rate_limit = {"rate": {"limit": 5000, "remaining": 4999}}
        mock_client.get_rate_limit.return_value = expected_rate_limit
        mock_api_client.return_value = mock_client
        mock_repo_manager.return_value = Mock()
        mock_file_sync.return_value = Mock()

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.get_rate_limit()

        assert result == expected_rate_limit
        mock_client.get_rate_limit.assert_called_once()

    @patch("gitbridge.api_sync.FileSynchronizer")
    @patch("gitbridge.api_sync.RepositoryManager")
    @patch("gitbridge.api_sync.GitHubAPIClient")
    @patch("gitbridge.api_sync.parse_github_url")
    def test_resolve_ref(self, mock_parse_url, mock_api_client, mock_repo_manager, mock_file_sync):
        """Test reference resolution delegation"""
        mock_parse_url.return_value = ("owner", "repo")
        mock_api_client.return_value = Mock()
        mock_repository = Mock()
        expected_sha = "abc123def456"
        mock_repository.resolve_ref.return_value = expected_sha
        mock_repo_manager.return_value = mock_repository
        mock_file_sync.return_value = Mock()

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.resolve_ref("main")

        assert result == expected_sha
        mock_repository.resolve_ref.assert_called_once_with("main")

    @patch("gitbridge.api_sync.FileSynchronizer")
    @patch("gitbridge.api_sync.RepositoryManager")
    @patch("gitbridge.api_sync.GitHubAPIClient")
    @patch("gitbridge.api_sync.parse_github_url")
    def test_get_repository_tree(self, mock_parse_url, mock_api_client, mock_repo_manager, mock_file_sync):
        """Test repository tree delegation"""
        mock_parse_url.return_value = ("owner", "repo")
        mock_api_client.return_value = Mock()
        mock_repository = Mock()
        expected_tree = [{"path": "file.txt", "sha": "abc123", "type": "blob"}]
        mock_repository.get_repository_tree.return_value = expected_tree
        mock_repo_manager.return_value = mock_repository
        mock_file_sync.return_value = Mock()

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.get_repository_tree("main", recursive=False)

        assert result == expected_tree
        mock_repository.get_repository_tree.assert_called_once_with("main", False)

    @patch("gitbridge.api_sync.ensure_dir")
    @patch("gitbridge.api_sync.ProgressTracker")
    @patch("gitbridge.api_sync.FileSynchronizer")
    @patch("gitbridge.api_sync.RepositoryManager")
    @patch("gitbridge.api_sync.GitHubAPIClient")
    @patch("gitbridge.api_sync.parse_github_url")
    def test_sync_success(self, mock_parse_url, mock_api_client, mock_repo_manager, mock_file_sync, mock_progress_tracker, mock_ensure_dir):
        """Test successful synchronization"""
        mock_parse_url.return_value = ("owner", "repo")

        # Mock client
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client.get_rate_limit.return_value = {"rate": {"remaining": 4999, "limit": 5000}}
        mock_api_client.return_value = mock_client

        # Mock repository
        mock_repository = Mock()
        expected_tree = [
            {"path": "file1.txt", "sha": "abc123", "type": "blob", "size": 100},
            {"path": "file2.txt", "sha": "def456", "type": "blob", "size": 200},
        ]
        mock_repository.get_repository_tree.return_value = expected_tree
        mock_repo_manager.return_value = mock_repository

        # Mock synchronizer
        mock_synchronizer = Mock()
        mock_synchronizer.should_download_file.side_effect = [True, False]  # First needs download, second skipped
        mock_synchronizer.sync_file.return_value = True
        mock_file_sync.return_value = mock_synchronizer

        # Mock progress tracker
        mock_tracker = Mock()
        mock_progress_tracker.return_value = mock_tracker

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.sync("main", show_progress=True)

        assert result is True

        # Verify the synchronization flow
        mock_client.test_connection.assert_called_once()
        mock_repository.get_repository_tree.assert_called_once_with("main", True)
        mock_synchronizer.set_current_ref.assert_called_once_with("main")
        mock_synchronizer.save_hash_cache.assert_called_once()
        mock_tracker.print_summary.assert_called_once()

    @patch("gitbridge.api_sync.FileSynchronizer")
    @patch("gitbridge.api_sync.RepositoryManager")
    @patch("gitbridge.api_sync.GitHubAPIClient")
    @patch("gitbridge.api_sync.parse_github_url")
    def test_sync_connection_failure(self, mock_parse_url, mock_api_client, mock_repo_manager, mock_file_sync):
        """Test sync with connection failure"""
        mock_parse_url.return_value = ("owner", "repo")

        # Mock client with connection failure
        mock_client = Mock()
        mock_client.test_connection.return_value = False
        mock_api_client.return_value = mock_client
        mock_repo_manager.return_value = Mock()
        mock_file_sync.return_value = Mock()

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.sync("main")

        assert result is False
        mock_client.test_connection.assert_called_once()

    @patch("gitbridge.api_sync.FileSynchronizer")
    @patch("gitbridge.api_sync.RepositoryManager")
    @patch("gitbridge.api_sync.GitHubAPIClient")
    @patch("gitbridge.api_sync.parse_github_url")
    def test_sync_tree_failure(self, mock_parse_url, mock_api_client, mock_repo_manager, mock_file_sync):
        """Test sync with tree retrieval failure"""
        mock_parse_url.return_value = ("owner", "repo")

        # Mock client with successful connection
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_api_client.return_value = mock_client

        # Mock repository with tree failure
        mock_repository = Mock()
        mock_repository.get_repository_tree.return_value = None
        mock_repo_manager.return_value = mock_repository
        mock_file_sync.return_value = Mock()

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.sync("main")

        assert result is False

    @patch("gitbridge.api_sync.FileSynchronizer")
    @patch("gitbridge.api_sync.RepositoryManager")
    @patch("gitbridge.api_sync.GitHubAPIClient")
    @patch("gitbridge.api_sync.parse_github_url")
    def test_backward_compatibility_methods(self, mock_parse_url, mock_api_client, mock_repo_manager, mock_file_sync):
        """Test backward compatibility delegation methods"""
        mock_parse_url.return_value = ("owner", "repo")
        mock_api_client.return_value = Mock()
        mock_repo_manager.return_value = Mock()

        mock_synchronizer = Mock()
        mock_synchronizer.download_file.return_value = b"file content"
        mock_synchronizer.download_blob.return_value = b"blob content"
        mock_synchronizer.should_download_file.return_value = True
        mock_synchronizer.sync_file.return_value = True
        mock_file_sync.return_value = mock_synchronizer

        sync = GitHubAPISync(self.repo_url, self.temp_dir)

        # Test download_file delegation
        result = sync.download_file("test.txt", "abc123")
        assert result == b"file content"
        mock_synchronizer.download_file.assert_called_once_with("test.txt", "abc123")

        # Test download_blob delegation
        result = sync.download_blob("abc123")
        assert result == b"blob content"
        mock_synchronizer.download_blob.assert_called_once_with("abc123")

        # Test should_download_file delegation
        result = sync.should_download_file("test.txt", "abc123")
        assert result is True
        mock_synchronizer.should_download_file.assert_called_once_with("test.txt", "abc123")

        # Test sync_file delegation
        entry = {"path": "test.txt", "sha": "abc123", "type": "blob"}
        result = sync.sync_file(entry)
        assert result is True
        mock_synchronizer.sync_file.assert_called_once_with(entry)

    @patch("gitbridge.api_sync.FileSynchronizer")
    @patch("gitbridge.api_sync.RepositoryManager")
    @patch("gitbridge.api_sync.GitHubAPIClient")
    @patch("gitbridge.api_sync.parse_github_url")
    def test_close_and_context_manager(self, mock_parse_url, mock_api_client, mock_repo_manager, mock_file_sync):
        """Test resource cleanup and context manager usage"""
        mock_parse_url.return_value = ("owner", "repo")
        mock_client = Mock()
        mock_api_client.return_value = mock_client
        mock_repo_manager.return_value = Mock()
        mock_file_sync.return_value = Mock()

        # Test explicit close
        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        sync.close()
        mock_client.close.assert_called_once()

        # Test context manager
        with GitHubAPISync(self.repo_url, self.temp_dir) as sync:
            assert isinstance(sync, GitHubAPISync)

        # Close should be called when exiting context
        assert mock_client.close.call_count == 2  # Once from explicit close, once from context manager

    @patch("gitbridge.api_sync.parse_github_url")
    def test_invalid_github_url(self, mock_parse_url):
        """Test initialization with invalid GitHub URL"""
        mock_parse_url.side_effect = ValueError("Invalid URL")

        with pytest.raises(ValueError):
            GitHubAPISync("invalid-url", self.temp_dir)
