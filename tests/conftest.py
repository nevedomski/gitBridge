"""Test configuration and fixtures for gitSync tests"""

import shutil
import tempfile
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_response():
    """Create a mock HTTP response"""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {}
    response.text = ""
    return response


@pytest.fixture
def sample_tree_data():
    """Sample GitHub API tree response data"""
    return {
        "tree": [
            {"path": "README.md", "type": "blob", "sha": "readme_sha123", "size": 1024},
            {"path": "src/main.py", "type": "blob", "sha": "main_sha456", "size": 2048},
            {"path": "src", "type": "tree", "sha": "src_tree_sha", "size": 0},
            {"path": "tests/test_main.py", "type": "blob", "sha": "test_sha789", "size": 512},
        ]
    }


@pytest.fixture
def sample_file_content():
    """Sample file content for testing"""
    return b"# Sample File\n\nThis is test content for the file."


@pytest.fixture
def github_api_urls():
    """Common GitHub API URLs for testing"""
    return {
        "repo": "https://api.github.com/repos/owner/repo",
        "rate_limit": "https://api.github.com/rate_limit",
        "tree": "https://api.github.com/repos/owner/repo/git/trees",
        "contents": "https://api.github.com/repos/owner/repo/contents",
        "blobs": "https://api.github.com/repos/owner/repo/git/blobs",
        "commits": "https://api.github.com/repos/owner/repo/git/commits",
        "refs_heads": "https://api.github.com/repos/owner/repo/git/ref/heads",
        "refs_tags": "https://api.github.com/repos/owner/repo/git/ref/tags",
    }
