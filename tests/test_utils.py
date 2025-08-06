"""Unit tests for utils.py module"""

import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from gitsync.exceptions import ConfigurationError
from gitsync.utils import (
    SyncStats,
    calculate_file_hash,
    ensure_dir,
    expand_path,
    format_size,
    is_binary_file,
    load_file_hashes,
    parse_github_url,
    save_file_hashes,
)


class TestParseGitHubUrl:
    """Test cases for parse_github_url function"""

    def test_parse_basic_github_url(self):
        """Test parsing basic GitHub URL"""
        owner, repo = parse_github_url("https://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_github_url_with_www(self):
        """Test parsing GitHub URL with www prefix"""
        owner, repo = parse_github_url("https://www.github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_github_url_with_git_suffix(self):
        """Test parsing GitHub URL with .git suffix"""
        owner, repo = parse_github_url("https://github.com/owner/repo.git")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_github_url_with_trailing_slash(self):
        """Test parsing GitHub URL with trailing slash"""
        owner, repo = parse_github_url("https://github.com/owner/repo/")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_github_url_with_subpaths(self):
        """Test parsing GitHub URL with additional subpaths"""
        owner, repo = parse_github_url("https://github.com/owner/repo/tree/main/src")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_invalid_domain(self):
        """Test parsing URL with invalid domain"""
        with pytest.raises(ConfigurationError, match="Not a GitHub URL"):
            parse_github_url("https://gitlab.com/owner/repo")

    def test_parse_missing_repo(self):
        """Test parsing URL with missing repository name"""
        with pytest.raises(ConfigurationError, match="Invalid GitHub repository URL"):
            parse_github_url("https://github.com/owner")

    def test_parse_empty_path(self):
        """Test parsing URL with empty path"""
        with pytest.raises(ConfigurationError, match="Invalid GitHub repository URL"):
            parse_github_url("https://github.com/")


class TestExpandPath:
    """Test cases for expand_path function"""

    def test_expand_path_none(self):
        """Test expand_path with None input"""
        assert expand_path(None) is None

    def test_expand_path_empty_string(self):
        """Test expand_path with empty string"""
        assert expand_path("") == ""

    def test_expand_path_non_string(self):
        """Test expand_path with non-string input"""
        assert expand_path(123) == 123

    def test_expand_path_no_expansion_needed(self):
        """Test expand_path with path needing no expansion"""
        result = expand_path("/absolute/path/file.txt")
        assert result == "/absolute/path/file.txt"

    @patch("os.path.expanduser")
    @patch("os.path.expandvars")
    def test_expand_path_with_user_home(self, mock_expandvars, mock_expanduser):
        """Test expand_path with user home directory"""
        mock_expanduser.return_value = "/home/user/docs"
        mock_expandvars.return_value = "/home/user/docs"

        result = expand_path("~/docs")

        mock_expanduser.assert_called_once_with("~/docs")
        mock_expandvars.assert_called_once_with("/home/user/docs")
        assert result == "/home/user/docs"

    @patch("os.path.expanduser")
    @patch("os.path.expandvars")
    def test_expand_path_with_env_vars(self, mock_expandvars, mock_expanduser):
        """Test expand_path with environment variables"""
        mock_expanduser.return_value = "/home/$USER/files"
        mock_expandvars.return_value = "/home/testuser/files"

        result = expand_path("/home/$USER/files")

        mock_expanduser.assert_called_once_with("/home/$USER/files")
        mock_expandvars.assert_called_once_with("/home/$USER/files")
        assert result == "/home/testuser/files"

    @patch("os.path.expanduser")
    @patch("os.path.expandvars")
    def test_expand_path_with_both(self, mock_expandvars, mock_expanduser):
        """Test expand_path with both user home and environment variables"""
        mock_expanduser.return_value = "/home/user/$PROJECT/files"
        mock_expandvars.return_value = "/home/user/myproject/files"

        result = expand_path("~/$PROJECT/files")

        mock_expanduser.assert_called_once_with("~/$PROJECT/files")
        mock_expandvars.assert_called_once_with("/home/user/$PROJECT/files")
        assert result == "/home/user/myproject/files"


class TestCalculateFileHash:
    """Test cases for calculate_file_hash function"""

    def test_calculate_hash_simple_content(self):
        """Test calculating hash for simple content"""
        content = b"Hello, World!"
        hash_value = calculate_file_hash(content)

        # Verify it's a proper SHA256 hash
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_calculate_hash_empty_content(self):
        """Test calculating hash for empty content"""
        content = b""
        hash_value = calculate_file_hash(content)

        # SHA256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_value == expected

    def test_calculate_hash_binary_content(self):
        """Test calculating hash for binary content"""
        content = bytes([0, 1, 2, 3, 255])
        hash_value = calculate_file_hash(content)

        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_calculate_hash_same_content_same_hash(self):
        """Test that same content produces same hash"""
        content = b"Test content"
        hash1 = calculate_file_hash(content)
        hash2 = calculate_file_hash(content)

        assert hash1 == hash2

    def test_calculate_hash_different_content_different_hash(self):
        """Test that different content produces different hash"""
        content1 = b"Test content 1"
        content2 = b"Test content 2"
        hash1 = calculate_file_hash(content1)
        hash2 = calculate_file_hash(content2)

        assert hash1 != hash2


class TestLoadFileHashes:
    """Test cases for load_file_hashes function"""

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file"""
        non_existent_file = Path("/non/existent/file.json")
        result = load_file_hashes(non_existent_file)

        assert result == {}

    def test_load_valid_json_file(self):
        """Test loading valid JSON file"""
        test_data = {"file1.txt": "hash1", "file2.txt": "hash2"}

        with (
            patch("builtins.open", mock_open(read_data=json.dumps(test_data))),
            patch("pathlib.Path.exists", return_value=True),
        ):
            result = load_file_hashes(Path("test.json"))

            assert result == test_data

    def test_load_invalid_json_file(self):
        """Test loading invalid JSON file"""
        with (
            patch("builtins.open", mock_open(read_data="invalid json")),
            patch("pathlib.Path.exists", return_value=True),
        ):
            result = load_file_hashes(Path("test.json"))

            assert result == {}

    def test_load_file_read_error(self):
        """Test loading file with read error"""
        with patch("builtins.open", side_effect=OSError("Read error")), patch("pathlib.Path.exists", return_value=True):
            result = load_file_hashes(Path("test.json"))

            assert result == {}


class TestSaveFileHashes:
    """Test cases for save_file_hashes function"""

    def test_save_file_hashes(self):
        """Test saving file hashes"""
        test_data = {"file1.txt": "hash1", "file2.txt": "hash2"}
        mock_file = mock_open()

        with patch("builtins.open", mock_file), patch("pathlib.Path.mkdir"):
            save_file_hashes(Path("test.json"), test_data)

            # Verify file was opened for writing
            mock_file.assert_called_once_with(Path("test.json"), "w")

            # Verify JSON was written
            written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
            parsed_content = json.loads(written_content)
            assert parsed_content == test_data

    def test_save_file_creates_directory(self):
        """Test that saving creates parent directory"""
        test_data = {"file1.txt": "hash1"}

        with patch("builtins.open", mock_open()), patch("pathlib.Path.mkdir") as mock_mkdir:
            save_file_hashes(Path("/test/dir/file.json"), test_data)

            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestEnsureDir:
    """Test cases for ensure_dir function"""

    def test_ensure_dir_creates_directory(self):
        """Test that ensure_dir creates directory"""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            ensure_dir(Path("/test/dir"))

            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestIsBinaryFile:
    """Test cases for is_binary_file function"""

    def test_empty_content(self):
        """Test with empty content"""
        assert is_binary_file(b"") is False

    def test_text_content(self):
        """Test with text content"""
        content = b"This is plain text content"
        assert is_binary_file(content) is False

    def test_binary_content_with_null_byte(self):
        """Test with binary content containing null byte"""
        content = b"Some text\x00with null byte"
        assert is_binary_file(content) is True

    def test_binary_content_various_bytes(self):
        """Test with various binary bytes"""
        content = bytes(range(256))  # All possible byte values
        assert is_binary_file(content) is True

    def test_utf8_content(self):
        """Test with UTF-8 encoded content"""
        content = "Hello, 世界! 🌍".encode()
        assert is_binary_file(content) is False

    def test_large_content_sample_check(self):
        """Test that only sample is checked for large content"""
        # Create content larger than sample size with null byte at the end
        large_content = b"a" * 10000 + b"\x00"

        # Should only check first 8192 bytes (sample_size)
        assert is_binary_file(large_content) is False


class TestFormatSize:
    """Test cases for format_size function"""

    def test_bytes(self):
        """Test formatting bytes"""
        assert format_size(0) == "0.0 B"
        assert format_size(512) == "512.0 B"
        assert format_size(1023) == "1023.0 B"

    def test_kilobytes(self):
        """Test formatting kilobytes"""
        assert format_size(1024) == "1.0 KB"
        assert format_size(1536) == "1.5 KB"
        assert format_size(1024 * 1023) == "1023.0 KB"

    def test_megabytes(self):
        """Test formatting megabytes"""
        assert format_size(1024 * 1024) == "1.0 MB"
        assert format_size(int(1.5 * 1024 * 1024)) == "1.5 MB"

    def test_gigabytes(self):
        """Test formatting gigabytes"""
        assert format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_size(int(2.5 * 1024 * 1024 * 1024)) == "2.5 GB"

    def test_terabytes(self):
        """Test formatting terabytes"""
        assert format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"
        assert format_size(int(1.5 * 1024 * 1024 * 1024 * 1024)) == "1.5 TB"


class TestSyncStats:
    """Test cases for SyncStats class"""

    def test_init(self):
        """Test SyncStats initialization"""
        stats = SyncStats()

        assert stats.files_checked == 0
        assert stats.files_downloaded == 0
        assert stats.files_skipped == 0
        assert stats.files_failed == 0
        assert stats.bytes_downloaded == 0
        assert stats.directories_created == 0

    def test_to_dict(self):
        """Test converting stats to dictionary"""
        stats = SyncStats()
        stats.files_checked = 10
        stats.files_downloaded = 5
        stats.files_skipped = 3
        stats.files_failed = 2
        stats.bytes_downloaded = 1024
        stats.directories_created = 1

        result = stats.to_dict()

        expected = {
            "files_checked": 10,
            "files_downloaded": 5,
            "files_skipped": 3,
            "files_failed": 2,
            "bytes_downloaded": 1024,
            "bytes_downloaded_formatted": "1.0 KB",
            "directories_created": 1,
        }

        assert result == expected

    def test_print_summary(self, capsys):
        """Test printing summary"""
        stats = SyncStats()
        stats.files_checked = 10
        stats.files_downloaded = 5
        stats.files_skipped = 3
        stats.files_failed = 2
        stats.bytes_downloaded = 2048
        stats.directories_created = 1

        stats.print_summary()

        captured = capsys.readouterr()
        output = captured.out

        assert "=== Sync Summary ===" in output
        assert "Files checked: 10" in output
        assert "Files downloaded: 5" in output
        assert "Files skipped: 3" in output
        assert "Files failed: 2" in output
        assert "Data transferred: 2.0 KB" in output
        assert "Directories created: 1" in output
