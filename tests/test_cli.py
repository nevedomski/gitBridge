"""Unit tests for cli.py module"""

import sys
import tempfile
from unittest.mock import Mock, mock_open, patch

from click.testing import CliRunner

# Mock browser_sync module before importing CLI to avoid Playwright dependency
mock_browser_sync = Mock()
mock_browser_sync.GitHubBrowserSync = Mock()
sys.modules["gitsync.browser_sync"] = mock_browser_sync

from gitsync.cli import cli, init, main, status, sync, validate  # noqa: E402


class TestCLIGroup:
    """Test cases for the main CLI group"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.runner = CliRunner()

    def test_cli_group_help(self):
        """Test CLI group shows help correctly"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "GitSync - Synchronize GitHub repositories" in result.output
        assert "Commands:" in result.output
        assert "init" in result.output
        assert "sync" in result.output
        assert "status" in result.output
        assert "validate" in result.output

    def test_cli_version(self):
        """Test CLI version option"""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        # Version output varies by Click version, just check it doesn't crash

    def test_main_function(self):
        """Test main entry point function"""
        with patch("gitsync.cli.cli") as mock_cli:
            main()
            mock_cli.assert_called_once()


class TestInitCommand:
    """Test cases for the init command"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    @patch("gitsync.cli.Config")
    def test_init_basic(self, mock_config_class):
        """Test basic init command functionality"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                init,
                [
                    "--repo",
                    "https://github.com/owner/repo",
                    "--local",
                    "/home/user/local",
                    "--output",
                    "test_config.yaml",
                ],
            )

        assert result.exit_code == 0
        assert "Configuration saved to test_config.yaml" in result.output
        assert "Example usage:" in result.output
        assert "gitsync sync --config test_config.yaml" in result.output

        # Verify Config calls
        mock_config_class.assert_called_once()
        mock_config.set.assert_any_call("repository.url", "https://github.com/owner/repo")
        mock_config.set.assert_any_call("repository.ref", "main")
        mock_config.set.assert_any_call("local.path", "/home/user/local")
        mock_config.set.assert_any_call("sync.method", "api")
        mock_config.save.assert_called_once_with("test_config.yaml")

    @patch("gitsync.cli.Config")
    def test_init_with_token(self, mock_config_class):
        """Test init command with token"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                init,
                [
                    "--repo",
                    "https://github.com/owner/repo",
                    "--local",
                    "/home/user/local",
                    "--token",
                    "ghp_test123",
                    "--ref",
                    "develop",
                    "--method",
                    "browser",
                    "--output",
                    "config.yaml",
                ],
            )

        assert result.exit_code == 0
        mock_config.set.assert_any_call("auth.token", "ghp_test123")
        mock_config.set.assert_any_call("repository.ref", "develop")
        mock_config.set.assert_any_call("sync.method", "browser")

    @patch("gitsync.cli.Config")
    def test_init_without_token_shows_note(self, mock_config_class):
        """Test init command without token shows environment variable note"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                init, ["--repo", "https://github.com/owner/repo", "--local", "/home/user/local"]
            )

        assert result.exit_code == 0
        assert "No token provided" in result.output
        assert "GITHUB_TOKEN environment variable" in result.output

    @patch("gitsync.cli.Config")
    @patch("os.path.expanduser")
    @patch("os.path.expandvars")
    def test_init_path_expansion(self, mock_expandvars, mock_expanduser, mock_config_class):
        """Test init command expands paths correctly"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_expanduser.return_value = "/home/user/local"
        mock_expandvars.return_value = "/home/user/local"

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(init, ["--repo", "https://github.com/owner/repo", "--local", "~/local"])

        assert result.exit_code == 0
        mock_expanduser.assert_called_with("~/local")
        mock_expandvars.assert_called_with("/home/user/local")
        mock_config.set.assert_any_call("local.path", "/home/user/local")

    def test_init_prompts_for_required_fields(self):
        """Test init command prompts for required repository and local path"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(init, input="https://github.com/owner/repo\n/home/user/local\n")

        # Should not crash due to missing required fields when prompted
        assert "GitHub repository URL" in result.output


class TestSyncCommand:
    """Test cases for the sync command"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.runner = CliRunner()

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_sync_api_method_success(self, mock_config_class, mock_api_sync_class):
        """Test sync command with API method - success case"""
        # Setup mocks
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "main",
            "auth.token": "ghp_test123",
            "sync.method": "api",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.sync.return_value = True

        result = self.runner.invoke(
            sync, ["--repo", "https://github.com/owner/repo", "--local", "/home/user/local", "--token", "ghp_test123"]
        )

        assert result.exit_code == 0
        assert "✓ Sync completed successfully" in result.output
        mock_syncer.sync.assert_called_once_with(ref="main", show_progress=True)

    @patch("gitsync.cli.GitHubBrowserSync")
    @patch("gitsync.cli.Config")
    def test_sync_browser_method_success(self, mock_config_class, mock_browser_sync_class):
        """Test sync command with browser method - success case"""
        # Setup mocks
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "main",
            "auth.token": "ghp_test123",
            "sync.method": "browser",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_browser_sync_class.return_value = mock_syncer
        mock_syncer.sync.return_value = True

        result = self.runner.invoke(sync, ["--method", "browser"])

        assert result.exit_code == 0
        assert "✓ Sync completed successfully" in result.output
        mock_syncer.sync.assert_called_once_with(ref="main", show_progress=True)

    @patch("gitsync.cli.Config")
    def test_sync_validation_failure(self, mock_config_class):
        """Test sync command with configuration validation failure"""
        from gitsync.exceptions import ConfigurationError

        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.validate.side_effect = ConfigurationError("Repository URL is required", "repository.url")

        result = self.runner.invoke(sync)

        assert result.exit_code == 1
        assert "Configuration validation failed" in result.output
        assert "Repository URL is required" in result.output

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_sync_failure(self, mock_config_class, mock_api_sync_class):
        """Test sync command with sync failure"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "main",
            "auth.token": "ghp_test123",
            "sync.method": "api",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.sync.return_value = False

        result = self.runner.invoke(sync)

        assert result.exit_code == 1
        assert "✗ Sync failed" in result.output

    @patch("gitsync.cli.Config")
    def test_sync_unknown_method(self, mock_config_class):
        """Test sync command with unknown sync method"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "main",
            "auth.token": "ghp_test123",
            "sync.method": "unknown",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        result = self.runner.invoke(sync)

        assert result.exit_code == 1
        assert "Unknown sync method: unknown" in result.output

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_sync_with_config_file(self, mock_config_class, mock_api_sync_class):
        """Test sync command with configuration file"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "main",
            "auth.token": "ghp_test123",
            "sync.method": "api",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.sync.return_value = True

        result = self.runner.invoke(sync, ["--config", "test_config.yaml"])

        assert result.exit_code == 0
        mock_config_class.assert_called_once_with("test_config.yaml")

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_sync_verbose_mode(self, mock_config_class, mock_api_sync_class):
        """Test sync command with verbose mode"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "main",
            "auth.token": "ghp_test123",
            "sync.method": "api",
            "sync.verify_ssl": True,
            "sync.ca_bundle": "/path/to/ca.pem",
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.sync.return_value = True

        result = self.runner.invoke(sync, ["--verbose"])

        assert result.exit_code == 0
        mock_config.set.assert_any_call("logging.level", "DEBUG")
        mock_config.setup_logging.assert_called_once()
        assert "Using CA bundle: /path/to/ca.pem" in result.output

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_sync_no_ssl_verify(self, mock_config_class, mock_api_sync_class):
        """Test sync command with SSL verification disabled"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "main",
            "auth.token": "ghp_test123",
            "sync.method": "api",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.sync.return_value = True

        result = self.runner.invoke(sync, ["--no-ssl-verify", "--verbose"])

        assert result.exit_code == 0
        assert "WARNING: SSL verification disabled" in result.output
        mock_api_sync_class.assert_called_once()
        args, kwargs = mock_api_sync_class.call_args
        assert kwargs["verify_ssl"] is False
        assert kwargs["ca_bundle"] is None

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_sync_with_all_options(self, mock_config_class, mock_api_sync_class):
        """Test sync command with all command-line options"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "develop",
            "auth.token": "ghp_test123",
            "sync.method": "api",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": True,
            "sync.auto_cert": True,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.sync.return_value = True

        result = self.runner.invoke(
            sync,
            [
                "--repo",
                "https://github.com/owner/repo",
                "--local",
                "/home/user/local",
                "--ref",
                "develop",
                "--token",
                "ghp_test123",
                "--method",
                "api",
                "--no-progress",
                "--verbose",
                "--auto-proxy",
                "--auto-cert",
            ],
        )

        assert result.exit_code == 0
        mock_syncer.sync.assert_called_once_with(ref="develop", show_progress=False)

        # Verify GitHubAPISync was called with correct parameters
        mock_api_sync_class.assert_called_once()
        args, kwargs = mock_api_sync_class.call_args
        assert kwargs["auto_proxy"] is True
        assert kwargs["auto_cert"] is True

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    @patch("os.path.expanduser")
    @patch("os.path.expandvars")
    def test_sync_path_expansion(self, mock_expandvars, mock_expanduser, mock_config_class, mock_api_sync_class):
        """Test sync command expands paths correctly"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "main",
            "auth.token": "ghp_test123",
            "sync.method": "api",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)
        mock_expanduser.return_value = "/home/user/local"
        mock_expandvars.return_value = "/home/user/local"

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.sync.return_value = True

        result = self.runner.invoke(sync, ["--repo", "https://github.com/owner/repo", "--local", "~/local"])

        assert result.exit_code == 0
        mock_expanduser.assert_called_with("~/local")
        mock_expandvars.assert_called_with("/home/user/local")
        mock_config.set.assert_any_call("local.path", "/home/user/local")


class TestStatusCommand:
    """Test cases for the status command"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.runner = CliRunner()

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    @patch("pathlib.Path.exists")
    def test_status_success(self, mock_path_exists, mock_config_class, mock_api_sync_class):
        """Test status command with successful connection"""
        # Setup mocks
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "auth.token": "ghp_test123",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.test_connection.return_value = True
        mock_syncer.get_rate_limit.return_value = {"rate": {"remaining": 4500, "limit": 5000}}

        mock_path_exists.return_value = True

        result = self.runner.invoke(
            status, ["--repo", "https://github.com/owner/repo", "--local", "/home/user/local", "--token", "ghp_test123"]
        )

        assert result.exit_code == 0
        assert "Repository: https://github.com/owner/repo" in result.output
        assert "Local path: /home/user/local" in result.output
        assert "✓ API connection successful" in result.output
        assert "API rate limit: 4500/5000 requests remaining" in result.output
        assert "✓ Local directory exists" in result.output

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_status_missing_repo_url(self, mock_config_class, mock_api_sync_class):
        """Test status command with missing repository URL"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": None,
            "local.path": "/home/user/local",
        }.get(key, default)

        result = self.runner.invoke(status)

        assert result.exit_code == 1
        assert "Repository URL is required" in result.output

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_status_missing_local_path(self, mock_config_class, mock_api_sync_class):
        """Test status command with missing local path"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": None,
        }.get(key, default)

        result = self.runner.invoke(status)

        assert result.exit_code == 1
        assert "Local path is required" in result.output

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_status_connection_failure(self, mock_config_class, mock_api_sync_class):
        """Test status command with connection failure"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "auth.token": "ghp_test123",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.test_connection.return_value = False

        result = self.runner.invoke(status)

        assert result.exit_code == 0  # Status command doesn't exit with error code
        assert "✗ API connection failed" in result.output

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    @patch("pathlib.Path.exists")
    def test_status_local_directory_missing(self, mock_path_exists, mock_config_class, mock_api_sync_class):
        """Test status command when local directory doesn't exist"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "auth.token": "ghp_test123",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.test_connection.return_value = True
        mock_syncer.get_rate_limit.return_value = None

        mock_path_exists.return_value = False

        result = self.runner.invoke(status)

        assert result.exit_code == 0
        assert "✗ Local directory does not exist" in result.output

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data='{"file1.txt": "hash1", "file2.txt": "hash2"}')
    def test_status_with_hash_cache(self, mock_file_open, mock_path_exists, mock_config_class, mock_api_sync_class):
        """Test status command with hash cache file present"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "auth.token": "ghp_test123",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.test_connection.return_value = True
        mock_syncer.get_rate_limit.return_value = None

        mock_path_exists.return_value = True

        result = self.runner.invoke(status)

        assert result.exit_code == 0
        assert "✓ Incremental sync data found" in result.output
        assert "Tracked files: 2" in result.output

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    @patch("pathlib.Path.exists")
    @patch("builtins.open", side_effect=Exception("JSON error"))
    def test_status_hash_cache_read_error(
        self, mock_file_open, mock_path_exists, mock_config_class, mock_api_sync_class
    ):
        """Test status command when hash cache file exists but can't be read"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "auth.token": "ghp_test123",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.test_connection.return_value = True
        mock_syncer.get_rate_limit.return_value = None

        mock_path_exists.return_value = True

        result = self.runner.invoke(status)

        assert result.exit_code == 0
        assert "✓ Incremental sync data found" in result.output
        # Should not show tracked files count due to error

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_status_verbose_mode(self, mock_config_class, mock_api_sync_class):
        """Test status command with verbose mode"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "auth.token": "ghp_test123",
            "sync.verify_ssl": True,
            "sync.ca_bundle": "/path/to/ca.pem",
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.test_connection.return_value = True
        mock_syncer.get_rate_limit.return_value = None

        result = self.runner.invoke(status, ["--verbose"])

        assert result.exit_code == 0
        mock_config.set.assert_any_call("logging.level", "DEBUG")
        mock_config.setup_logging.assert_called_once()
        assert "Using CA bundle: /path/to/ca.pem" in result.output

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_status_no_ssl_verify_verbose(self, mock_config_class, mock_api_sync_class):
        """Test status command with SSL verification disabled in verbose mode"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "auth.token": "ghp_test123",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.test_connection.return_value = True
        mock_syncer.get_rate_limit.return_value = None

        result = self.runner.invoke(status, ["--no-ssl-verify", "--verbose"])

        assert result.exit_code == 0
        assert "WARNING: SSL verification disabled" in result.output

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    @patch("os.path.expanduser")
    @patch("os.path.expandvars")
    def test_status_path_expansion(self, mock_expandvars, mock_expanduser, mock_config_class, mock_api_sync_class):
        """Test status command expands paths correctly"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "auth.token": "ghp_test123",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_expanduser.return_value = "/home/user/local"
        mock_expandvars.return_value = "/home/user/local"

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.test_connection.return_value = True
        mock_syncer.get_rate_limit.return_value = None

        result = self.runner.invoke(status, ["--repo", "https://github.com/owner/repo", "--local", "~/local"])

        assert result.exit_code == 0
        mock_expanduser.assert_called_with("~/local")
        mock_expandvars.assert_called_with("/home/user/local")
        mock_config.set.assert_any_call("local.path", "/home/user/local")


class TestValidateCommand:
    """Test cases for the validate command"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.runner = CliRunner()

    @patch("gitsync.cli.Config")
    @patch("gitsync.cli.yaml.dump")
    def test_validate_success(self, mock_yaml_dump, mock_config_class):
        """Test validate command with valid configuration"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes
        mock_config.to_dict.return_value = {"repository": {"url": "https://github.com/owner/repo"}}
        mock_yaml_dump.return_value = "repository:\n  url: https://github.com/owner/repo\n"

        with self.runner.isolated_filesystem():
            # Create a temporary config file
            with open("test_config.yaml", "w") as f:
                f.write("repository:\n  url: https://github.com/owner/repo\n")

            result = self.runner.invoke(validate, ["test_config.yaml"])

        assert result.exit_code == 0
        assert "Validating test_config.yaml..." in result.output
        assert "✓ Configuration is valid" in result.output
        assert "Configuration:" in result.output
        mock_config_class.assert_called_once_with("test_config.yaml")
        mock_config.validate.assert_called_once()

    @patch("gitsync.cli.Config")
    def test_validate_failure(self, mock_config_class):
        """Test validate command with invalid configuration"""
        from gitsync.exceptions import ConfigurationError

        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.validate.side_effect = ConfigurationError("Repository URL is required", "repository.url")

        with self.runner.isolated_filesystem():
            # Create a temporary config file
            with open("invalid_config.yaml", "w") as f:
                f.write("invalid: config\n")

            result = self.runner.invoke(validate, ["invalid_config.yaml"])

        assert result.exit_code == 1
        assert "✗ Configuration is invalid" in result.output

    def test_validate_nonexistent_file(self):
        """Test validate command with non-existent file"""
        result = self.runner.invoke(validate, ["nonexistent.yaml"])

        assert result.exit_code == 2  # Click error for file not found
        assert "does not exist" in result.output


class TestErrorConditions:
    """Test cases for error conditions and edge cases"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.runner = CliRunner()

    @patch("gitsync.cli.Config")
    def test_config_file_loading_error(self, mock_config_class):
        """Test handling of configuration file loading errors"""
        mock_config_class.side_effect = Exception("Config loading failed")

        result = self.runner.invoke(sync, ["--config", "broken_config.yaml"])

        # Should not crash, but may exit with error
        assert "Config loading failed" in str(result.exception) or result.exit_code != 0

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_syncer_initialization_error(self, mock_config_class, mock_api_sync_class):
        """Test handling of syncer initialization errors"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "main",
            "auth.token": "ghp_test123",
            "sync.method": "api",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_api_sync_class.side_effect = Exception("Syncer init failed")

        result = self.runner.invoke(sync)

        # Exception is properly handled by Click, resulting in an exit code of 1
        assert result.exit_code == 1
        # The exception should be raised and captured by Click
        assert result.exception is not None

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_sync_method_exception(self, mock_config_class, mock_api_sync_class):
        """Test handling of exceptions in sync method"""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes
        mock_config.get.side_effect = lambda key, default=None: {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "main",
            "auth.token": "ghp_test123",
            "sync.method": "api",
            "sync.verify_ssl": True,
            "sync.ca_bundle": None,
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }.get(key, default)

        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.sync.side_effect = Exception("Sync failed")

        result = self.runner.invoke(sync)

        # Exception is properly handled by Click, resulting in an exit code of 1
        assert result.exit_code == 1
        # The exception should be raised and captured by Click
        assert result.exception is not None


class TestIntegrationScenarios:
    """Test cases for integration scenarios"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.runner = CliRunner()

    @patch("gitsync.cli.GitHubAPISync")
    @patch("gitsync.cli.Config")
    def test_full_sync_workflow_api(self, mock_config_class, mock_api_sync_class):
        """Test complete sync workflow using API method"""
        # Mock configuration
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes

        # Mock config values for different stages
        config_values = {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "develop",
            "auth.token": "ghp_test123",
            "sync.method": "api",
            "sync.verify_ssl": False,
            "sync.ca_bundle": None,
            "sync.auto_proxy": True,
            "sync.auto_cert": True,
        }
        mock_config.get.side_effect = lambda key, default=None: config_values.get(key, default)

        # Mock successful sync
        mock_syncer = Mock()
        mock_api_sync_class.return_value = mock_syncer
        mock_syncer.sync.return_value = True

        result = self.runner.invoke(
            sync,
            [
                "--repo",
                "https://github.com/owner/repo",
                "--local",
                "/home/user/local",
                "--ref",
                "develop",
                "--token",
                "ghp_test123",
                "--method",
                "api",
                "--no-ssl-verify",
                "--auto-proxy",
                "--auto-cert",
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        assert "✓ Sync completed successfully" in result.output
        assert "WARNING: SSL verification disabled" in result.output

        # Verify all configuration overrides were applied
        expected_calls = [
            ("repository.url", "https://github.com/owner/repo"),
            ("local.path", "/home/user/local"),
            ("repository.ref", "develop"),
            ("auth.token", "ghp_test123"),
            ("sync.method", "api"),
            ("logging.level", "DEBUG"),
        ]

        for key, value in expected_calls:
            mock_config.set.assert_any_call(key, value)

        # Verify syncer was called with correct parameters
        mock_api_sync_class.assert_called_once()
        args, kwargs = mock_api_sync_class.call_args
        assert args[0] == "https://github.com/owner/repo"
        assert args[1] == "/home/user/local"
        assert args[2] == "ghp_test123"
        assert kwargs["verify_ssl"] is False
        assert kwargs["ca_bundle"] is None
        assert kwargs["auto_proxy"] is True
        assert kwargs["auto_cert"] is True

    @patch("gitsync.cli.GitHubBrowserSync")
    @patch("gitsync.cli.Config")
    def test_full_sync_workflow_browser(self, mock_config_class, mock_browser_sync_class):
        """Test complete sync workflow using browser method"""
        # Mock configuration
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        # No exception means validation passes

        config_values = {
            "repository.url": "https://github.com/owner/repo",
            "local.path": "/home/user/local",
            "repository.ref": "main",
            "auth.token": None,
            "sync.method": "browser",
            "sync.verify_ssl": True,
            "sync.ca_bundle": "/custom/ca.pem",
            "sync.auto_proxy": False,
            "sync.auto_cert": False,
        }
        mock_config.get.side_effect = lambda key, default=None: config_values.get(key, default)

        # Mock successful sync
        mock_syncer = Mock()
        mock_browser_sync_class.return_value = mock_syncer
        mock_syncer.sync.return_value = True

        result = self.runner.invoke(sync, ["--method", "browser", "--no-progress", "--verbose"])

        assert result.exit_code == 0
        assert "✓ Sync completed successfully" in result.output
        assert "Using CA bundle: /custom/ca.pem" in result.output

        # Verify browser syncer was used
        mock_browser_sync_class.assert_called_once()
        mock_syncer.sync.assert_called_once_with(ref="main", show_progress=False)
