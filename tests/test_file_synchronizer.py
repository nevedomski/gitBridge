"""Unit tests for file_synchronizer.py module"""

import base64
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from gitbridge.api_client import GitHubAPIClient
from gitbridge.file_synchronizer import FileSynchronizer


class TestFileSynchronizer:
    """Test cases for FileSynchronizer class"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.local_path = Path(self.temp_dir)
        self.mock_client = Mock(spec=GitHubAPIClient)
        self.mock_client.owner = "test_owner"
        self.mock_client.repo = "test_repo"
        self.mock_client.config = {}  # Add config attribute

    @patch("gitbridge.file_synchronizer.load_file_hashes")
    def test_init(self, mock_load_hashes):
        """Test initialization"""
        mock_load_hashes.return_value = {"file1.txt": "abc123"}

        synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        assert synchronizer.client == self.mock_client
        assert synchronizer.local_path == self.local_path
        assert synchronizer.current_ref is None
        assert synchronizer.file_hashes == {"file1.txt": "abc123"}
        assert synchronizer.hash_cache_file == self.local_path / ".gitbridge" / "file_hashes.json"

    def test_set_current_ref(self):
        """Test setting current reference"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        synchronizer.set_current_ref("main")

        assert synchronizer.current_ref == "main"

    def test_should_download_file_new_file(self):
        """Test should download for new file"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        # File doesn't exist locally
        result = synchronizer.should_download_file("new_file.txt", "abc123")

        assert result is True

    def test_should_download_file_changed_hash(self):
        """Test should download for file with changed hash"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={"file1.txt": "old_hash"}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        # Create the file locally
        test_file = self.local_path / "file1.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test content")

        result = synchronizer.should_download_file("file1.txt", "new_hash")

        assert result is True

    def test_should_download_file_unchanged(self):
        """Test should not download for unchanged file"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={"file1.txt": "same_hash"}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        # Create the file locally
        test_file = self.local_path / "file1.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test content")

        result = synchronizer.should_download_file("file1.txt", "same_hash")

        assert result is False

    def test_download_file_success(self):
        """Test successful file download via Contents API"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        synchronizer.set_current_ref("main")

        # Mock successful API response
        test_content = "Hello, World!"
        encoded_content = base64.b64encode(test_content.encode()).decode()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": encoded_content, "size": len(test_content)}
        self.mock_client.get_with_limits.return_value = mock_response

        result = synchronizer.download_file("test.txt", "abc123")

        assert result == test_content.encode()
        self.mock_client.get_with_limits.assert_called_once_with("repos/test_owner/test_repo/contents/test.txt", params={"ref": "main"})

    def test_download_file_large_file_fallback(self):
        """Test file download fallback to Blob API for large files"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        # Mock Contents API response indicating large file
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "size": 2 * 1024 * 1024,  # 2MB - exceeds 1MB limit
            "content": "",
        }
        self.mock_client.get_with_limits.return_value = mock_response

        # Mock download_blob method
        test_content = b"Large file content"
        synchronizer.download_blob = Mock(return_value=test_content)

        result = synchronizer.download_file("large_file.txt", "abc123")

        assert result == test_content
        synchronizer.download_blob.assert_called_once_with("abc123")

    def test_download_file_rate_limit_fallback(self):
        """Test file download fallback to Blob API on rate limit"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        # Mock Contents API 403 response (rate limit)
        mock_response = Mock()
        mock_response.status_code = 403
        self.mock_client.get_with_limits.return_value = mock_response

        # Mock download_blob method
        test_content = b"File content"
        synchronizer.download_blob = Mock(return_value=test_content)

        result = synchronizer.download_file("file.txt", "abc123")

        assert result == test_content
        synchronizer.download_blob.assert_called_once_with("abc123")

    def test_download_file_not_found(self):
        """Test file download with 404 error"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        mock_response = Mock()
        mock_response.status_code = 404
        self.mock_client.get_with_limits.return_value = mock_response

        result = synchronizer.download_file("nonexistent.txt", "abc123")

        assert result is None

    def test_download_blob_success(self):
        """Test successful blob download"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        test_content = "Blob content"
        encoded_content = base64.b64encode(test_content.encode()).decode()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": encoded_content, "encoding": "base64"}
        self.mock_client.get.return_value = mock_response

        result = synchronizer.download_blob("abc123")

        assert result == test_content.encode()
        self.mock_client.get.assert_called_once_with("repos/test_owner/test_repo/git/blobs/abc123")

    def test_download_blob_failure(self):
        """Test blob download failure"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        mock_response = Mock()
        mock_response.status_code = 404
        self.mock_client.get.return_value = mock_response

        result = synchronizer.download_blob("abc123")

        assert result is None

    @patch("gitbridge.file_synchronizer.ensure_dir")
    def test_sync_file_success(self, mock_ensure_dir):
        """Test successful file synchronization"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        entry = {"path": "test.txt", "sha": "abc123", "type": "blob"}

        # Mock should_download_file and download_file
        synchronizer.should_download_file = Mock(return_value=True)
        test_content = b"File content"
        synchronizer.download_file = Mock(return_value=test_content)

        result = synchronizer.sync_file(entry)

        assert result is True
        assert synchronizer.file_hashes["test.txt"] == "abc123"
        synchronizer.should_download_file.assert_called_once_with("test.txt", "abc123")
        synchronizer.download_file.assert_called_once_with("test.txt", "abc123")

    def test_sync_file_skip_unchanged(self):
        """Test file sync skip for unchanged file"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        entry = {"path": "test.txt", "sha": "abc123", "type": "blob"}

        # Mock should_download_file to return False (skip)
        synchronizer.should_download_file = Mock(return_value=False)

        result = synchronizer.sync_file(entry)

        assert result is True
        synchronizer.should_download_file.assert_called_once_with("test.txt", "abc123")

    def test_sync_file_download_failure(self):
        """Test file sync with download failure"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        entry = {"path": "test.txt", "sha": "abc123", "type": "blob"}

        # Mock should_download_file and download_file failure
        synchronizer.should_download_file = Mock(return_value=True)
        synchronizer.download_file = Mock(return_value=None)

        result = synchronizer.sync_file(entry)

        assert result is False

    @patch("gitbridge.file_synchronizer.save_file_hashes")
    def test_save_hash_cache(self, mock_save_hashes):
        """Test saving hash cache"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={"file1.txt": "abc123"}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        synchronizer.save_hash_cache()

        mock_save_hashes.assert_called_once_with(synchronizer.hash_cache_file, {"file1.txt": "abc123"})

    def test_get_cached_files(self):
        """Test getting cached files"""
        cached_hashes = {"file1.txt": "abc123", "file2.txt": "def456"}
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value=cached_hashes):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        result = synchronizer.get_cached_files()

        assert result == {"file1.txt", "file2.txt"}

    def test_clear_hash_cache(self):
        """Test clearing hash cache"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={"file1.txt": "abc123"}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        # Create a fake hash cache file
        cache_file = synchronizer.hash_cache_file
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.touch()

        synchronizer.clear_hash_cache()

        assert not cache_file.exists()
        assert synchronizer.file_hashes == {}

    def test_get_file_info_exists(self):
        """Test getting file info for cached file"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={"test.txt": "abc123"}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        # Create test file
        test_file = self.local_path / "test.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test content")

        result = synchronizer.get_file_info("test.txt")

        assert result["cached_sha"] == "abc123"
        assert result["local_exists"] is True
        assert result["local_size"] == len("test content")

    def test_get_file_info_not_cached(self):
        """Test getting file info for non-cached file"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        result = synchronizer.get_file_info("test.txt")

        assert result is None

    def test_sync_files_multiple(self):
        """Test syncing multiple files"""
        with patch("gitbridge.file_synchronizer.load_file_hashes", return_value={}):
            synchronizer = FileSynchronizer(self.mock_client, self.local_path)

        files = [
            {"path": "file1.txt", "sha": "abc123", "type": "blob", "size": 10},
            {"path": "file2.txt", "sha": "def456", "type": "blob", "size": 20},
        ]

        # Mock sync_file to succeed for first file, fail for second
        def sync_file_side_effect(entry):
            return entry["path"] == "file1.txt"

        synchronizer.sync_file = Mock(side_effect=sync_file_side_effect)
        synchronizer.should_download_file = Mock(return_value=True)

        result = synchronizer.sync_files(files)

        assert result["checked"] == 2
        assert result["downloaded"] == 1
        assert result["skipped"] == 0
        assert result["failed"] == 1
        assert result["bytes_downloaded"] == 10
