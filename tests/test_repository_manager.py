"""Unit tests for repository_manager.py module"""

from unittest.mock import Mock

from gitsync.api_client import GitHubAPIClient
from gitsync.repository_manager import RepositoryManager


class TestRepositoryManager:
    """Test cases for RepositoryManager class"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.mock_client = Mock(spec=GitHubAPIClient)
        self.mock_client.owner = "test_owner"
        self.mock_client.repo = "test_repo"
        self.manager = RepositoryManager(self.mock_client)

    def test_init(self):
        """Test initialization"""
        assert self.manager.client == self.mock_client
        assert self.manager.owner == "test_owner"
        assert self.manager.repo == "test_repo"

    def test_resolve_ref_full_sha_success(self):
        """Test resolving full SHA reference"""
        sha = "a" * 40  # 40-character SHA
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_client.get.return_value = mock_response

        result = self.manager.resolve_ref(sha)

        assert result == sha
        self.mock_client.get.assert_called_once_with(f"repos/test_owner/test_repo/git/commits/{sha}")

    def test_resolve_ref_full_sha_not_found(self):
        """Test resolving full SHA reference that doesn't exist"""
        sha = "a" * 40  # 40-character SHA
        mock_response = Mock()
        mock_response.status_code = 404
        self.mock_client.get.return_value = mock_response

        result = self.manager.resolve_ref(sha)

        assert result is None

    def test_resolve_ref_branch_success(self):
        """Test resolving branch reference"""
        branch = "main"
        commit_sha = "b" * 40

        # Mock just the branch call since "main" is not 40 chars (won't match full SHA)
        branch_response = Mock(status_code=200)
        branch_response.json.return_value = {"object": {"sha": commit_sha}}
        self.mock_client.get.return_value = branch_response

        result = self.manager.resolve_ref(branch)

        assert result == commit_sha

    def test_resolve_ref_tag_direct_commit(self):
        """Test resolving tag that points directly to commit"""
        tag = "v1.0.0"
        commit_sha = "c" * 40

        # Mock the response sequence: branch fails, tag succeeds
        responses = []
        responses.append(Mock(status_code=404))  # Branch
        # Tag response
        tag_response = Mock(status_code=200)
        tag_response.json.return_value = {"object": {"type": "commit", "sha": commit_sha}}
        responses.append(tag_response)

        self.mock_client.get.side_effect = responses

        result = self.manager.resolve_ref(tag)

        assert result == commit_sha

    def test_resolve_ref_annotated_tag(self):
        """Test resolving annotated tag"""
        tag = "v1.0.0"
        tag_sha = "d" * 40
        commit_sha = "e" * 40

        # Mock the response sequence: branch fails, tag succeeds, tag object succeeds
        responses = []
        responses.append(Mock(status_code=404))  # Branch
        # Tag reference response
        tag_ref_response = Mock(status_code=200)
        tag_ref_response.json.return_value = {"object": {"type": "tag", "sha": tag_sha}}
        responses.append(tag_ref_response)
        # Tag object response
        tag_obj_response = Mock(status_code=200)
        tag_obj_response.json.return_value = {"object": {"sha": commit_sha}}
        responses.append(tag_obj_response)

        self.mock_client.get.side_effect = responses

        result = self.manager.resolve_ref(tag)

        assert result == commit_sha

    def test_resolve_ref_short_sha(self):
        """Test resolving short SHA reference"""
        short_sha = "abcdef0"
        full_sha = "abcdef0123456789abcdef0123456789abcdef01"

        # Mock the response sequence: branch fails, tag fails, commits API succeeds
        responses = []
        responses.append(Mock(status_code=404))  # Branch
        responses.append(Mock(status_code=404))  # Tag
        # Commits response
        commits_response = Mock(status_code=200)
        commits_response.json.return_value = [{"sha": full_sha}]
        responses.append(commits_response)

        self.mock_client.get.side_effect = responses

        result = self.manager.resolve_ref(short_sha)

        assert result == full_sha

    def test_resolve_ref_not_found(self):
        """Test resolving non-existent reference"""
        ref = "nonexistent"

        # Mock all methods to return 404
        mock_response = Mock(status_code=404)
        self.mock_client.get.return_value = mock_response

        result = self.manager.resolve_ref(ref)

        assert result is None

    def test_get_repository_tree_success(self):
        """Test successful repository tree retrieval"""
        ref = "main"
        commit_sha = "f" * 40
        expected_tree = [
            {"path": "file1.txt", "sha": "abc123", "type": "blob"},
            {"path": "dir1/file2.txt", "sha": "def456", "type": "blob"},
        ]

        # Mock resolve_ref and tree API
        self.manager.resolve_ref = Mock(return_value=commit_sha)

        tree_response = Mock(status_code=200)
        tree_response.json.return_value = {"tree": expected_tree}
        self.mock_client.get.return_value = tree_response

        result = self.manager.get_repository_tree(ref, recursive=True)

        assert result == expected_tree
        self.manager.resolve_ref.assert_called_once_with(ref)
        self.mock_client.get.assert_called_once_with(
            f"repos/test_owner/test_repo/git/trees/{commit_sha}", params={"recursive": "1"}
        )

    def test_get_repository_tree_fallback_to_master(self):
        """Test repository tree fallback from main to master"""
        ref = "main"
        commit_sha = "g" * 40
        expected_tree = [{"path": "file1.txt", "sha": "abc123", "type": "blob"}]

        # Mock resolve_ref to fail for main, succeed for master
        def resolve_ref_side_effect(r):
            if r == "main":
                return None
            elif r == "master":
                return commit_sha
            return None

        self.manager.resolve_ref = Mock(side_effect=resolve_ref_side_effect)

        # Mock recursive call result
        self.manager.get_repository_tree = Mock()

        def get_tree_side_effect(r, recursive=True):
            if r == "master":
                return expected_tree
            # This is the actual call being tested
            return self.manager.__class__.get_repository_tree(self.manager, r, recursive)

        # We need to test this differently since it's a recursive call
        # Let's mock the client response instead
        tree_response = Mock(status_code=200)
        tree_response.json.return_value = {"tree": expected_tree}
        self.mock_client.get.return_value = tree_response

        # Create a fresh manager to avoid mocking conflicts
        manager = RepositoryManager(self.mock_client)
        manager.resolve_ref = Mock(side_effect=resolve_ref_side_effect)

        result = manager.get_repository_tree(ref, recursive=True)

        assert result == expected_tree

    def test_get_repository_tree_ref_not_found(self):
        """Test repository tree with non-existent reference"""
        ref = "nonexistent"

        self.manager.resolve_ref = Mock(return_value=None)

        result = self.manager.get_repository_tree(ref)

        assert result is None

    def test_get_repository_tree_non_recursive(self):
        """Test repository tree retrieval without recursion"""
        ref = "main"
        commit_sha = "h" * 40

        self.manager.resolve_ref = Mock(return_value=commit_sha)

        tree_response = Mock(status_code=200)
        tree_response.json.return_value = {"tree": []}
        self.mock_client.get.return_value = tree_response

        self.manager.get_repository_tree(ref, recursive=False)

        self.mock_client.get.assert_called_once_with(f"repos/test_owner/test_repo/git/trees/{commit_sha}", params={})

    def test_get_default_branch_success(self):
        """Test getting default branch"""
        expected_branch = "main"
        repo_info = {"default_branch": expected_branch}

        self.mock_client.get_repository_info.return_value = repo_info

        result = self.manager.get_default_branch()

        assert result == expected_branch

    def test_get_default_branch_failure(self):
        """Test getting default branch with API failure"""
        self.mock_client.get_repository_info.side_effect = Exception("API error")

        result = self.manager.get_default_branch()

        assert result is None

    def test_list_branches_success(self):
        """Test listing repository branches"""
        expected_branches = [
            {"name": "main", "commit": {"sha": "abc123"}},
            {"name": "develop", "commit": {"sha": "def456"}},
        ]

        branches_response = Mock(status_code=200)
        branches_response.json.return_value = expected_branches
        self.mock_client.get.return_value = branches_response

        result = self.manager.list_branches()

        assert result == expected_branches

    def test_list_branches_failure(self):
        """Test listing branches with API failure"""
        self.mock_client.get.side_effect = Exception("API error")

        result = self.manager.list_branches()

        assert result == []

    def test_list_tags_success(self):
        """Test listing repository tags"""
        expected_tags = [
            {"name": "v1.0.0", "commit": {"sha": "abc123"}},
            {"name": "v0.9.0", "commit": {"sha": "def456"}},
        ]

        tags_response = Mock(status_code=200)
        tags_response.json.return_value = expected_tags
        self.mock_client.get.return_value = tags_response

        result = self.manager.list_tags()

        assert result == expected_tags

    def test_get_commit_info_success(self):
        """Test getting commit information"""
        sha = "abc123"
        full_sha = "abc1234567890abcdef1234567890abcdef123456"
        expected_commit = {"sha": full_sha, "commit": {"message": "Test commit"}, "author": {"name": "Test Author"}}

        self.manager.resolve_ref = Mock(return_value=full_sha)

        commit_response = Mock(status_code=200)
        commit_response.json.return_value = expected_commit
        self.mock_client.get.return_value = commit_response

        result = self.manager.get_commit_info(sha)

        assert result == expected_commit
        self.manager.resolve_ref.assert_called_once_with(sha)

    def test_get_commit_info_not_found(self):
        """Test getting commit information for non-existent commit"""
        sha = "nonexistent"

        self.manager.resolve_ref = Mock(return_value=None)

        result = self.manager.get_commit_info(sha)

        assert result is None

    def test_validate_ref_exists(self):
        """Test validating existing reference"""
        ref = "main"

        self.manager.resolve_ref = Mock(return_value="abc123")

        result = self.manager.validate_ref(ref)

        assert result is True

    def test_validate_ref_not_exists(self):
        """Test validating non-existent reference"""
        ref = "nonexistent"

        self.manager.resolve_ref = Mock(return_value=None)

        result = self.manager.validate_ref(ref)

        assert result is False
