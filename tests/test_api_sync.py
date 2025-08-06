"""Unit tests for api_sync.py module"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from gitsync.api_sync import GitHubAPISync


class TestGitHubAPISync:
    """Test cases for GitHubAPISync class"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_url = "https://github.com/owner/repo"
        self.token = "test_token"

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_init_basic(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test basic initialization without optional parameters"""
        sync = GitHubAPISync(self.repo_url, self.temp_dir)

        assert sync.owner == "owner"
        assert sync.repo == "repo"
        assert sync.local_path == Path(self.temp_dir)
        assert sync.token is None

        # Verify components were initialized correctly
        mock_client.assert_called_once_with(
            owner="owner",
            repo="repo",
            token=None,
            verify_ssl=True,
            ca_bundle=None,
            auto_proxy=False,
            auto_cert=False,
        )
        mock_repo_mgr.assert_called_once_with(mock_client.return_value)
        mock_file_sync.assert_called_once_with(mock_client.return_value, Path(self.temp_dir))

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_init_with_token(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test initialization with authentication token"""
        sync = GitHubAPISync(self.repo_url, self.temp_dir, token=self.token)

        assert sync.token == self.token

        mock_client.assert_called_once_with(
            owner="owner",
            repo="repo",
            token=self.token,
            verify_ssl=True,
            ca_bundle=None,
            auto_proxy=False,
            auto_cert=False,
        )

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_init_ssl_disabled(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test initialization with SSL verification disabled"""
        GitHubAPISync(self.repo_url, self.temp_dir, verify_ssl=False)

        mock_client.assert_called_once_with(
            owner="owner",
            repo="repo",
            token=None,
            verify_ssl=False,
            ca_bundle=None,
            auto_proxy=False,
            auto_cert=False,
        )

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_init_with_ca_bundle(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test initialization with custom CA bundle"""
        ca_bundle_path = "/path/to/ca-bundle.crt"

        GitHubAPISync(self.repo_url, self.temp_dir, ca_bundle=ca_bundle_path)

        mock_client.assert_called_once_with(
            owner="owner",
            repo="repo",
            token=None,
            verify_ssl=True,
            ca_bundle=ca_bundle_path,
            auto_proxy=False,
            auto_cert=False,
        )

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_init_auto_cert(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test initialization with auto certificate detection"""
        GitHubAPISync(self.repo_url, self.temp_dir, auto_cert=True)

        mock_client.assert_called_once_with(
            owner="owner",
            repo="repo",
            token=None,
            verify_ssl=True,
            ca_bundle=None,
            auto_proxy=False,
            auto_cert=True,
        )

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_init_auto_proxy(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test initialization with auto proxy detection"""
        GitHubAPISync(self.repo_url, self.temp_dir, auto_proxy=True)

        mock_client.assert_called_once_with(
            owner="owner",
            repo="repo",
            token=None,
            verify_ssl=True,
            ca_bundle=None,
            auto_proxy=True,
            auto_cert=False,
        )

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_test_connection_success(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test successful connection test"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.test_connection.return_value = True

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.test_connection()

        assert result is True
        mock_client_instance.test_connection.assert_called_once()

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_test_connection_failure(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test connection test failure"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.test_connection.side_effect = Exception("Connection failed")

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.test_connection()

        assert result is False

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_get_rate_limit(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test getting rate limit information"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        rate_limit_data = {"rate": {"limit": 5000, "remaining": 4999}}
        mock_client_instance.get_rate_limit.return_value = rate_limit_data

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.get_rate_limit()

        assert result == rate_limit_data
        mock_client_instance.get_rate_limit.assert_called_once()

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_resolve_ref(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test resolving a reference to a commit SHA"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_repo_instance = Mock()
        mock_repo_mgr.return_value = mock_repo_instance

        sha = "a1b2c3d4e5f6789012345678901234567890abcd"
        mock_repo_instance.resolve_ref.return_value = sha

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.resolve_ref("main")

        assert result == sha
        mock_repo_instance.resolve_ref.assert_called_once_with("main")

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_get_repository_tree(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test getting repository tree structure"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_repo_instance = Mock()
        mock_repo_mgr.return_value = mock_repo_instance

        tree_data = [
            {"path": "README.md", "type": "blob", "sha": "abc123"},
            {"path": "src", "type": "tree", "sha": "def456"},
        ]
        mock_repo_instance.get_repository_tree.return_value = tree_data

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.get_repository_tree("sha123")

        assert result == tree_data
        mock_repo_instance.get_repository_tree.assert_called_once_with("sha123", True)

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    @patch("gitsync.api_sync.ProgressTracker")
    @patch("gitsync.api_sync.ensure_dir")
    def test_sync_success(self, mock_ensure_dir, mock_progress_tracker, mock_file_sync, mock_repo_mgr, mock_client):
        """Test successful repository sync"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.test_connection.return_value = True
        mock_client_instance.get_rate_limit.return_value = {"rate": {"remaining": 5000}}

        mock_repo_instance = Mock()
        mock_repo_mgr.return_value = mock_repo_instance
        mock_repo_instance.get_repository_tree.return_value = [
            {"path": "README.md", "type": "blob", "sha": "file1", "size": 100},
        ]

        mock_sync_instance = Mock()
        mock_file_sync.return_value = mock_sync_instance
        mock_sync_instance.should_download_file.return_value = True
        mock_sync_instance.sync_file.return_value = True

        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance
        mock_tracker_instance.should_throttle.return_value = False

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.sync()

        assert result is True
        mock_repo_instance.get_repository_tree.assert_called_once_with("main", True)
        mock_sync_instance.sync_file.assert_called_once()

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    @patch("gitsync.api_sync.ProgressTracker")
    @patch("gitsync.api_sync.ensure_dir")
    def test_sync_with_ref(self, mock_ensure_dir, mock_progress_tracker, mock_file_sync, mock_repo_mgr, mock_client):
        """Test sync with specific reference"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.test_connection.return_value = True
        mock_client_instance.get_rate_limit.return_value = {}

        mock_repo_instance = Mock()
        mock_repo_mgr.return_value = mock_repo_instance
        mock_repo_instance.get_repository_tree.return_value = []

        mock_sync_instance = Mock()
        mock_file_sync.return_value = mock_sync_instance

        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.sync(ref="develop")

        assert result is True
        mock_repo_instance.get_repository_tree.assert_called_once_with("develop", True)

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_sync_ref_not_found(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test sync when reference is not found"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.test_connection.return_value = True

        mock_repo_instance = Mock()
        mock_repo_mgr.return_value = mock_repo_instance
        mock_repo_instance.get_repository_tree.return_value = None

        mock_sync_instance = Mock()
        mock_file_sync.return_value = mock_sync_instance

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.sync(ref="nonexistent")

        assert result is False

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_sync_tree_error(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test sync when getting tree fails"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.test_connection.return_value = True

        mock_repo_instance = Mock()
        mock_repo_mgr.return_value = mock_repo_instance
        mock_repo_instance.get_repository_tree.side_effect = Exception("Failed to get tree")

        mock_sync_instance = Mock()
        mock_file_sync.return_value = mock_sync_instance

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.sync()

        assert result is False

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    @patch("gitsync.api_sync.ProgressTracker")
    @patch("gitsync.api_sync.ensure_dir")
    def test_sync_with_progress(self, mock_ensure_dir, mock_progress_tracker, mock_file_sync, mock_repo_mgr, mock_client):
        """Test sync with progress tracking"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.test_connection.return_value = True
        mock_client_instance.get_rate_limit.return_value = {}

        mock_repo_instance = Mock()
        mock_repo_mgr.return_value = mock_repo_instance
        mock_repo_instance.get_repository_tree.return_value = [
            {"path": "file.txt", "type": "blob", "sha": "abc123", "size": 100}
        ]

        mock_sync_instance = Mock()
        mock_file_sync.return_value = mock_sync_instance
        mock_sync_instance.should_download_file.return_value = True
        mock_sync_instance.sync_file.return_value = True

        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance
        mock_tracker_instance.should_throttle.return_value = False

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.sync(show_progress=True)

        assert result is True
        mock_progress_tracker.assert_called_once_with(
            total_files=1, show_progress=True, desc="Syncing files"
        )

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    @patch("gitsync.api_sync.ProgressTracker")
    @patch("gitsync.api_sync.ensure_dir")
    def test_sync_skip_existing(self, mock_ensure_dir, mock_progress_tracker, mock_file_sync, mock_repo_mgr, mock_client):
        """Test sync skips existing files"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.test_connection.return_value = True
        mock_client_instance.get_rate_limit.return_value = {}

        mock_repo_instance = Mock()
        mock_repo_mgr.return_value = mock_repo_instance
        mock_repo_instance.get_repository_tree.return_value = [
            {"path": "existing.txt", "type": "blob", "sha": "abc123"}
        ]

        mock_sync_instance = Mock()
        mock_file_sync.return_value = mock_sync_instance
        # File should be skipped
        mock_sync_instance.should_download_file.return_value = False

        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.sync()

        assert result is True
        # Should not call sync_file if file is skipped
        mock_sync_instance.sync_file.assert_not_called()
        mock_tracker_instance.update_progress.assert_called_once_with("existing.txt", skipped=True)

    @patch("gitsync.api_sync.GitHubAPIClient")
    @patch("gitsync.api_sync.RepositoryManager")
    @patch("gitsync.api_sync.FileSynchronizer")
    def test_sync_connection_failure(self, mock_file_sync, mock_repo_mgr, mock_client):
        """Test sync fails when connection test fails"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.test_connection.return_value = False

        mock_repo_instance = Mock()
        mock_repo_mgr.return_value = mock_repo_instance

        mock_sync_instance = Mock()
        mock_file_sync.return_value = mock_sync_instance

        sync = GitHubAPISync(self.repo_url, self.temp_dir)
        result = sync.sync()

        assert result is False
        # Should not attempt to get tree if connection fails
        mock_repo_instance.get_repository_tree.assert_not_called()
