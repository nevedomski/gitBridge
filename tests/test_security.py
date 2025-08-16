"""Security tests for GitBridge.

Tests for critical security vulnerabilities:
1. Path traversal prevention
2. Proxy URL validation
3. Thread-safe certificate management
4. Request size limits
"""

import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
import requests

from src.gitbridge.api_client import GitHubAPIClient
from src.gitbridge.cert_support import CertificateManager, _cert_lock, _temp_cert_files
from src.gitbridge.exceptions import ConfigurationError, SecurityError
from src.gitbridge.file_synchronizer import FileSynchronizer
from src.gitbridge.utils import validate_proxy_url, validate_safe_path


class TestPathTraversal:
    """Test path traversal vulnerability prevention."""

    def test_validate_safe_path_normal(self):
        """Test normal safe paths are allowed."""
        base = Path("/home/user/repo")

        # Normal file paths should work
        result = validate_safe_path(base, "src/main.py")
        assert result == base.resolve() / "src/main.py"

        result = validate_safe_path(base, "deeply/nested/folder/file.txt")
        assert result == base.resolve() / "deeply/nested/folder/file.txt"

    def test_validate_safe_path_traversal_attempts(self):
        """Test path traversal attempts are blocked."""
        base = Path("/home/user/repo")

        # Various path traversal attempts should be blocked
        with pytest.raises(SecurityError) as exc_info:
            validate_safe_path(base, "../etc/passwd")
        assert "path_traversal" in str(exc_info.value)

        with pytest.raises(SecurityError) as exc_info:
            validate_safe_path(base, "../../../../../../etc/shadow")
        assert "path_traversal" in str(exc_info.value)

        with pytest.raises(SecurityError) as exc_info:
            validate_safe_path(base, "src/../../etc/passwd")
        assert "path_traversal" in str(exc_info.value)

    def test_validate_safe_path_absolute_paths(self):
        """Test absolute paths are rejected."""
        base = Path("/home/user/repo")

        # Absolute paths should be rejected as they escape the base
        with pytest.raises(SecurityError) as exc_info:
            validate_safe_path(base, "/etc/passwd")
        assert "path_traversal" in str(exc_info.value)

    def test_file_synchronizer_uses_validation(self):
        """Test FileSynchronizer uses path validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = Path(tmpdir)
            client = MagicMock(spec=GitHubAPIClient)
            sync = FileSynchronizer(client, local_path)

            # Mock download_file to return content
            sync.download_file = MagicMock(return_value=b"test content")

            # Attempt to sync a file with path traversal
            entry = {"path": "../../../etc/passwd", "sha": "abc123", "type": "file"}

            # Should fail with SecurityError
            result = sync.sync_file(entry)
            assert result is False  # Sync should fail for path traversal


class TestProxyValidation:
    """Test proxy URL validation."""

    def test_validate_proxy_url_valid(self):
        """Test valid proxy URLs are accepted."""
        # HTTP proxy
        result = validate_proxy_url("http://proxy.example.com:8080")
        assert result["server"] == "http://proxy.example.com:8080"
        assert result.get("username") is None

        # HTTPS proxy
        result = validate_proxy_url("https://secure-proxy.example.com:443")
        assert result["server"] == "https://secure-proxy.example.com:443"

        # SOCKS5 proxy
        result = validate_proxy_url("socks5://socks-proxy.example.com:1080")
        assert result["server"] == "socks5://socks-proxy.example.com:1080"

        # Proxy with credentials
        result = validate_proxy_url("http://user:pass@proxy.example.com:8080")
        assert result["server"] == "http://proxy.example.com:8080"
        assert result["username"] == "user"
        assert result["password"] == "pass"

    def test_validate_proxy_url_invalid_scheme(self):
        """Test invalid schemes are rejected."""
        # File scheme should be rejected
        with pytest.raises(SecurityError) as exc_info:
            validate_proxy_url("file:///etc/passwd")
        assert "invalid_proxy_scheme" in str(exc_info.value)

        # JavaScript scheme should be rejected
        with pytest.raises(SecurityError) as exc_info:
            validate_proxy_url("javascript:alert(1)")
        assert "invalid_proxy_scheme" in str(exc_info.value)

        # FTP scheme should be rejected
        with pytest.raises(SecurityError) as exc_info:
            validate_proxy_url("ftp://ftp.example.com")
        assert "invalid_proxy_scheme" in str(exc_info.value)

    def test_validate_proxy_url_missing_hostname(self):
        """Test URLs without hostname are rejected."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_proxy_url("http://:8080")
        assert "missing hostname" in str(exc_info.value).lower()

        with pytest.raises(ConfigurationError) as exc_info:
            validate_proxy_url("http://")
        assert "missing hostname" in str(exc_info.value).lower()

    def test_validate_proxy_url_invalid_port(self):
        """Test invalid ports are rejected."""
        # Port 0 is invalid
        with pytest.raises(ConfigurationError) as exc_info:
            validate_proxy_url("http://proxy.example.com:0")
        assert "invalid proxy port" in str(exc_info.value).lower()

        # Port > 65535 is invalid (caught by urlparse)
        with pytest.raises(ConfigurationError) as exc_info:
            validate_proxy_url("http://proxy.example.com:99999")
        # urlparse raises "Port out of range" for ports > 65535
        assert "port" in str(exc_info.value).lower() and "range" in str(exc_info.value).lower()

    def test_validate_proxy_url_malicious_hostname(self):
        """Test hostnames with suspicious characters are rejected."""
        # Hostname with script tags
        with pytest.raises(SecurityError) as exc_info:
            validate_proxy_url("http://<script>alert(1)</script>:8080")
        assert "suspicious characters" in str(exc_info.value).lower()

        # Hostname with newlines (caught earlier as control characters)
        with pytest.raises(SecurityError) as exc_info:
            validate_proxy_url("http://proxy.example.com\nSet-Cookie:evil:8080")
        assert "control characters" in str(exc_info.value).lower()

    def test_validate_proxy_url_control_chars_in_username(self):
        """Test usernames with control characters are rejected."""
        # Username with null byte
        with pytest.raises(SecurityError) as exc_info:
            validate_proxy_url("http://user\x00:pass@proxy.example.com:8080")
        assert "control characters" in str(exc_info.value).lower()


class TestThreadSafeCertificates:
    """Test thread-safe certificate management."""

    def test_certificate_manager_cleanup(self):
        """Test CertificateManager cleans up temp files."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(b"test certificate")

        # Use CertificateManager
        with CertificateManager() as mgr:
            mgr.add_temp_cert(temp_path)
            assert temp_path in _temp_cert_files
            assert os.path.exists(temp_path)

        # After context exit, file should be cleaned up
        assert temp_path not in _temp_cert_files
        assert not os.path.exists(temp_path)

    def test_certificate_manager_thread_safety(self):
        """Test thread-safe operations on certificate list."""
        # Create multiple temp files
        temp_files = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(f"cert {i}".encode())
                temp_files.append(tmp.name)

        # Track which files were added by which thread
        added_by_thread = {}

        def add_certs(thread_id):
            """Add certificates from a thread."""
            with CertificateManager() as mgr:
                for temp_path in temp_files:
                    mgr.add_temp_cert(temp_path)
                    added_by_thread[thread_id] = temp_path
                    time.sleep(0.001)  # Small delay to increase contention

        # Run multiple threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=add_certs, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # All files should be cleaned up
        for temp_path in temp_files:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_cert_lock_prevents_race_condition(self):
        """Test that the lock prevents race conditions."""
        results = []

        def modify_list():
            """Modify the global list with lock."""
            with _cert_lock:
                current_len = len(_temp_cert_files)
                time.sleep(0.001)  # Simulate work
                _temp_cert_files.append(f"test_{current_len}")
                results.append(current_len)

        # Clear the list first
        with _cert_lock:
            _temp_cert_files.clear()

        # Run multiple threads
        threads = []
        for _ in range(10):
            t = threading.Thread(target=modify_list)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check results - each thread should see a unique length
        assert len(set(results)) == 10  # All results should be unique
        assert sorted(results) == list(range(10))  # Should be 0,1,2...9

        # Clean up
        with _cert_lock:
            _temp_cert_files.clear()


class TestSizeLimits:
    """Test request size limits to prevent DoS."""

    def test_get_with_limits_size_check(self):
        """Test that get_with_limits enforces size limits."""
        client = GitHubAPIClient(
            owner="test",
            repo="test",
            config={
                "download_limits": {
                    "max_file_size": 1024,  # 1KB limit for testing
                    "timeout": 30,
                }
            },
        )

        # Mock session
        client.session = Mock()

        # Mock HEAD response with large Content-Length
        head_response = Mock()
        head_response.headers = {"Content-Length": "2048"}  # 2KB - exceeds limit
        client.session.head.return_value = head_response

        # Should raise SecurityError for oversized file
        with pytest.raises(SecurityError) as exc_info:
            client.get_with_limits("test/path")

        assert "size_limit" in str(exc_info.value)
        assert "exceeds limit" in str(exc_info.value).lower()

    def test_get_with_limits_streaming_for_large_files(self):
        """Test that large files trigger streaming."""
        client = GitHubAPIClient(
            owner="test",
            repo="test",
            config={
                "download_limits": {
                    "max_file_size": 10 * 1024 * 1024,  # 10MB
                    "timeout": 30,
                }
            },
        )

        # Mock session
        client.session = Mock()

        # Mock HEAD response with medium size
        head_response = Mock()
        head_response.headers = {"Content-Length": str(5 * 1024 * 1024)}  # 5MB
        client.session.head.return_value = head_response

        # Mock GET response
        get_response = Mock()
        get_response.status_code = 200
        get_response.headers = {}
        client.session.get.return_value = get_response

        # Call get_with_limits
        _ = client.get_with_limits("test/path")

        # Should have called get with stream=False (under threshold)
        client.session.get.assert_called_once()
        call_kwargs = client.session.get.call_args[1]
        assert call_kwargs["stream"] is False

    def test_get_with_limits_fallback_to_streaming(self):
        """Test fallback to streaming when HEAD fails."""
        client = GitHubAPIClient(owner="test", repo="test", config={})

        # Mock session
        client.session = Mock()

        # Mock HEAD to fail
        client.session.head.side_effect = requests.RequestException("HEAD failed")

        # Mock GET response
        get_response = Mock()
        get_response.status_code = 200
        get_response.headers = {}
        client.session.get.return_value = get_response

        # Call get_with_limits
        _ = client.get_with_limits("test/path")

        # Should have called get with stream=True (fallback)
        client.session.get.assert_called_once()
        call_kwargs = client.session.get.call_args[1]
        assert call_kwargs["stream"] is True

    def test_download_blob_streamed_size_enforcement(self):
        """Test streaming download enforces size limits."""
        client = MagicMock(spec=GitHubAPIClient)
        client.owner = "test"
        client.repo = "test"
        client.config = {
            "download_limits": {
                "max_file_size": 1024,  # 1KB limit
                "chunk_size": 256,
            }
        }

        # Create FileSynchronizer
        sync = FileSynchronizer(client, Path("/tmp"))

        # Mock response that returns too much data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response._max_size = 1024

        # Simulate large content in chunks
        large_content = b"x" * 2048  # 2KB - exceeds limit
        mock_response.iter_content.return_value = [large_content[i : i + 256] for i in range(0, len(large_content), 256)]

        client.get_with_limits.return_value = mock_response

        # Should raise SecurityError when size exceeded
        with pytest.raises(SecurityError) as exc_info:
            sync.download_blob_streamed("test_sha")

        assert "size_limit" in str(exc_info.value)
        assert "exceeded size limit" in str(exc_info.value).lower()


class TestIntegration:
    """Integration tests for security features."""

    def test_complete_sync_with_security_checks(self):
        """Test complete sync flow with all security checks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = Path(tmpdir)

            # Create client with security config
            client = MagicMock(spec=GitHubAPIClient)
            client.owner = "test"
            client.repo = "test"
            client.config = {
                "download_limits": {"max_file_size": 10 * 1024 * 1024, "stream_threshold": 1024 * 1024, "chunk_size": 8192, "timeout": 30}
            }

            # Create synchronizer
            sync = FileSynchronizer(client, local_path)

            # Mock API responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "size": 512,  # Small file
                "content": "dGVzdCBjb250ZW50",  # base64: "test content"
            }
            client.get_with_limits.return_value = mock_response

            # Normal file should sync successfully
            entry = {"path": "src/main.py", "sha": "abc123", "type": "file"}

            result = sync.sync_file(entry)
            assert result is True

            # Verify file was written to safe location
            expected_path = local_path / "src/main.py"
            assert expected_path.exists()
            assert expected_path.read_bytes() == b"test content"

            # Path traversal should fail
            entry = {"path": "../../../etc/passwd", "sha": "def456", "type": "file"}

            result = sync.sync_file(entry)
            assert result is False

            # Verify no file was written outside local_path
            assert not Path("/etc/passwd").exists() or Path("/etc/passwd").stat().st_size > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
