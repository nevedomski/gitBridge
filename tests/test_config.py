"""Unit tests for config.py module"""

import logging
import os
from unittest.mock import patch

import pytest
import yaml

from gitbridge.config import DEFAULT_CONFIG, Config
from gitbridge.exceptions import ConfigurationError


class TestConfig:
    """Test cases for Config class"""

    def test_init_without_config_file(self):
        """Test Config initialization without config file"""
        import copy

        with patch("gitbridge.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            config = Config()

        assert config.config_file is None
        # Use deepcopy to match the implementation
        expected = copy.deepcopy(DEFAULT_CONFIG)
        assert config.config == expected

    def test_init_with_config_file(self, temp_dir):
        """Test Config initialization with config file"""
        config_file = os.path.join(temp_dir, "test_config.yaml")
        test_config = {"repository": {"url": "https://github.com/test/repo"}}

        with open(config_file, "w") as f:
            yaml.dump(test_config, f)

        with patch("gitbridge.config.load_dotenv"):
            config = Config(config_file)

        assert config.config_file == config_file
        assert config.get("repository.url") == "https://github.com/test/repo"

    def test_init_calls_load_env(self):
        """Test that initialization calls load_env"""
        with (
            patch("gitbridge.config.load_dotenv") as mock_load_dotenv,
            patch.object(Config, "load_env") as mock_load_env,
            patch.dict(os.environ, {}, clear=True),
        ):
            Config()

            mock_load_dotenv.assert_called_once()
            mock_load_env.assert_called_once()

    def test_default_config_values(self):
        """Test default configuration values"""
        with (
            patch("gitbridge.config.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
            patch("gitbridge.config.Path.exists", return_value=False),
        ):
            config = Config()

        assert config.get("repository.url") is None
        assert config.get("repository.ref") == "main"
        assert config.get("local.path") is None
        assert config.get("auth.token") is None
        assert config.get("sync.method") == "api"
        assert config.get("sync.incremental") is True
        assert config.get("sync.verify_ssl") is True
        assert config.get("logging.level") == "INFO"
        assert config.get("logging.file") is None


class TestConfigLoadFile:
    """Test cases for Config.load_file method"""

    def test_load_file_success(self, temp_dir):
        """Test successful file loading"""
        config_file = os.path.join(temp_dir, "test_config.yaml")
        test_config = {
            "repository": {"url": "https://github.com/test/repo", "ref": "develop"},
            "local": {"path": "/tmp/test"},
            "auth": {"token": "test_token"},
        }

        with open(config_file, "w") as f:
            yaml.dump(test_config, f)

        with patch("gitbridge.config.load_dotenv"):
            config = Config()
            config.load_file(config_file)

        assert config.get("repository.url") == "https://github.com/test/repo"
        assert config.get("repository.ref") == "develop"
        assert config.get("local.path") == "/tmp/test"
        assert config.get("auth.token") == "test_token"

    def test_load_file_nonexistent(self):
        """Test loading non-existent file"""
        with patch("gitbridge.config.load_dotenv"), patch("gitbridge.config.logger") as mock_logger:
            config = Config()
            config.load_file("/nonexistent/config.yaml")

            mock_logger.warning.assert_called_once()
            assert "Configuration file not found" in mock_logger.warning.call_args[0][0]

    def test_load_file_empty_file(self, temp_dir):
        """Test loading empty YAML file"""
        config_file = os.path.join(temp_dir, "empty_config.yaml")
        with open(config_file, "w") as f:
            f.write("")

        with patch("gitbridge.config.load_dotenv"):
            config = Config()
            original_config = config.config.copy()
            config.load_file(config_file)

        # Config should remain unchanged for empty file
        assert config.config == original_config

    def test_load_file_invalid_yaml(self, temp_dir):
        """Test loading invalid YAML file raises ConfigurationError"""
        config_file = os.path.join(temp_dir, "invalid_config.yaml")
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [")

        with patch("gitbridge.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            config = Config()
            with pytest.raises(ConfigurationError, match="Invalid YAML syntax"):
                config.load_file(config_file)

    def test_load_file_deep_merge(self, temp_dir):
        """Test deep merging of configuration"""
        config_file = os.path.join(temp_dir, "merge_config.yaml")
        test_config = {"repository": {"url": "https://github.com/test/repo"}, "sync": {"method": "browser"}}

        with open(config_file, "w") as f:
            yaml.dump(test_config, f)

        with patch("gitbridge.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            config = Config()
            config.load_file(config_file)

        # New values should be merged
        assert config.get("repository.url") == "https://github.com/test/repo"
        assert config.get("sync.method") == "browser"
        # Existing values should remain
        assert config.get("repository.ref") == "main"
        assert config.get("sync.incremental") is True

    def test_load_file_permission_error(self, temp_dir):
        """Test loading file with permission error raises ConfigurationError"""
        config_file = os.path.join(temp_dir, "restricted_config.yaml")

        with (
            patch("gitbridge.config.Path.exists", return_value=True),
            patch("builtins.open", side_effect=PermissionError("Permission denied")),
            patch("gitbridge.config.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
        ):
            config = Config()
            with pytest.raises(ConfigurationError, match="Failed to read configuration file"):
                config.load_file(config_file)


class TestConfigLoadEnv:
    """Test cases for Config.load_env method"""

    def test_load_env_github_repo_url(self):
        """Test loading GITHUB_REPO_URL environment variable"""
        with (
            patch.dict(os.environ, {"GITHUB_REPO_URL": "https://github.com/env/repo"}, clear=True),
            patch("gitbridge.config.load_dotenv"),
        ):
            config = Config()
            assert config.get("repository.url") == "https://github.com/env/repo"

    def test_load_env_github_ref(self):
        """Test loading GITHUB_REF environment variable"""
        with patch.dict(os.environ, {"GITHUB_REF": "develop"}, clear=True), patch("gitbridge.config.load_dotenv"):
            config = Config()
            assert config.get("repository.ref") == "develop"

    def test_load_env_github_ref_normalization(self):
        """Test GITHUB_REF normalization for GitHub Actions format"""
        # Test refs/heads/ format
        with patch.dict(os.environ, {"GITHUB_REF": "refs/heads/main"}, clear=True), patch("gitbridge.config.load_dotenv"):
            config = Config()
            assert config.get("repository.ref") == "main"

        # Test refs/tags/ format
        with patch.dict(os.environ, {"GITHUB_REF": "refs/tags/v1.0.0"}, clear=True), patch("gitbridge.config.load_dotenv"):
            config = Config()
            assert config.get("repository.ref") == "v1.0.0"

        # Test plain branch name (no normalization needed)
        with patch.dict(os.environ, {"GITHUB_REF": "feature-branch"}, clear=True), patch("gitbridge.config.load_dotenv"):
            config = Config()
            assert config.get("repository.ref") == "feature-branch"

    def test_load_env_local_path(self):
        """Test loading GITBRIDGE_LOCAL_PATH environment variable"""
        with (
            patch.dict(os.environ, {"GITBRIDGE_LOCAL_PATH": "/env/path"}, clear=True),
            patch("gitbridge.config.load_dotenv"),
        ):
            config = Config()
            assert config.get("local.path") == "/env/path"

    def test_load_env_github_token(self):
        """Test loading GITHUB_TOKEN environment variable"""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"}, clear=True), patch("gitbridge.config.load_dotenv"):
            config = Config()
            assert config.get("auth.token") == "env_token"

    def test_load_env_sync_method(self):
        """Test loading GITBRIDGE_METHOD environment variable"""
        with patch.dict(os.environ, {"GITBRIDGE_METHOD": "browser"}, clear=True), patch("gitbridge.config.load_dotenv"):
            config = Config()
            assert config.get("sync.method") == "browser"

    def test_load_env_incremental_true(self):
        """Test loading GITBRIDGE_INCREMENTAL environment variable (true values)"""
        for value in ["true", "1", "yes"]:
            with (
                patch.dict(os.environ, {"GITBRIDGE_INCREMENTAL": value}, clear=True),
                patch("gitbridge.config.load_dotenv"),
            ):
                config = Config()
                assert config.get("sync.incremental") is True

    def test_load_env_incremental_false(self):
        """Test loading GITBRIDGE_INCREMENTAL environment variable (false values)"""
        for value in ["false", "0", "no", "other"]:
            with (
                patch.dict(os.environ, {"GITBRIDGE_INCREMENTAL": value}, clear=True),
                patch("gitbridge.config.load_dotenv"),
            ):
                config = Config()
                assert config.get("sync.incremental") is False

    def test_load_env_log_level(self):
        """Test loading GITBRIDGE_LOG_LEVEL environment variable"""
        with (
            patch.dict(os.environ, {"GITBRIDGE_LOG_LEVEL": "DEBUG"}, clear=True),
            patch("gitbridge.config.load_dotenv"),
        ):
            config = Config()
            assert config.get("logging.level") == "DEBUG"

    def test_load_env_log_file(self):
        """Test loading GITBRIDGE_LOG_FILE environment variable"""
        with (
            patch.dict(os.environ, {"GITBRIDGE_LOG_FILE": "/tmp/gitbridge.log"}, clear=True),
            patch("gitbridge.config.load_dotenv"),
        ):
            config = Config()
            assert config.get("logging.file") == "/tmp/gitbridge.log"

    def test_load_env_multiple_variables(self):
        """Test loading multiple environment variables"""
        env_vars = {
            "GITHUB_REPO_URL": "https://github.com/multi/repo",
            "GITHUB_REF": "feature-branch",
            "GITBRIDGE_LOCAL_PATH": "/multi/path",
            "GITHUB_TOKEN": "multi_token",
            "GITBRIDGE_METHOD": "browser",
            "GITBRIDGE_INCREMENTAL": "false",
            "GITBRIDGE_LOG_LEVEL": "WARNING",
            "GITBRIDGE_LOG_FILE": "/multi/log.txt",
        }

        with patch.dict(os.environ, env_vars, clear=True), patch("gitbridge.config.load_dotenv"):
            config = Config()
            assert config.get("repository.url") == "https://github.com/multi/repo"
            assert config.get("repository.ref") == "feature-branch"
            assert config.get("local.path") == "/multi/path"
            assert config.get("auth.token") == "multi_token"
            assert config.get("sync.method") == "browser"
            assert config.get("sync.incremental") is False
            assert config.get("logging.level") == "WARNING"
            assert config.get("logging.file") == "/multi/log.txt"


class TestConfigDeepMerge:
    """Test cases for Config._deep_merge method"""

    def test_deep_merge_simple(self):
        """Test simple deep merge"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        target = {"a": {"b": 1, "c": 2}}
        source = {"a": {"b": 10, "d": 3}}

        config._deep_merge(target, source)

        assert target == {"a": {"b": 10, "c": 2, "d": 3}}

    def test_deep_merge_new_keys(self):
        """Test deep merge with new keys"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        target = {"existing": {"key": "value"}}
        source = {"new": {"key": "new_value"}}

        config._deep_merge(target, source)

        assert target == {"existing": {"key": "value"}, "new": {"key": "new_value"}}

    def test_deep_merge_overwrite_non_dict(self):
        """Test deep merge overwrites non-dict values"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        target = {"key": "old_value"}
        source = {"key": "new_value"}

        config._deep_merge(target, source)

        assert target == {"key": "new_value"}

    def test_deep_merge_nested(self):
        """Test deep merge with nested dictionaries"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        target = {"level1": {"level2": {"level3": "old"}}}
        source = {"level1": {"level2": {"level3": "new", "extra": "value"}}}

        config._deep_merge(target, source)

        assert target == {"level1": {"level2": {"level3": "new", "extra": "value"}}}


class TestConfigGet:
    """Test cases for Config.get method"""

    def test_get_existing_key(self):
        """Test getting existing configuration key"""
        with patch("gitbridge.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            config = Config()

        assert config.get("repository.ref") == "main"
        assert config.get("sync.method") == "api"

    def test_get_nonexistent_key(self):
        """Test getting non-existent key returns default"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "default") == "default"

    def test_get_nested_key(self):
        """Test getting nested configuration key"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        config.config = {"level1": {"level2": {"level3": "value"}}}
        assert config.get("level1.level2.level3") == "value"

    def test_get_partial_path(self):
        """Test getting partial path returns dict"""
        with patch("gitbridge.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            config = Config()

        result = config.get("repository")
        assert isinstance(result, dict)
        assert result["ref"] == "main"

    def test_get_path_expansion_local_path(self):
        """Test path expansion for local.path"""
        with (
            patch("gitbridge.config.load_dotenv"),
            patch("os.path.expanduser", return_value="/home/user/expanded"),
            patch("os.path.expandvars", return_value="/home/user/expanded"),
        ):
            config = Config()
            config.config["local"]["path"] = "~/test/path"

            result = config.get("local.path")
            assert result == "/home/user/expanded"

    def test_get_path_expansion_non_local_path(self):
        """Test no path expansion for non-local.path keys"""
        with (
            patch("gitbridge.config.load_dotenv"),
            patch("os.path.expanduser") as mock_expand_user,
            patch("os.path.expandvars") as mock_expand_vars,
        ):
            config = Config()
            config.config["other"] = {"path": "~/test/path"}

            result = config.get("other.path")
            assert result == "~/test/path"
            mock_expand_user.assert_not_called()
            mock_expand_vars.assert_not_called()

    def test_get_path_expansion_none_value(self):
        """Test path expansion with None value"""
        with patch("gitbridge.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            config = Config()

        result = config.get("local.path")
        assert result is None

    def test_get_invalid_key_format(self):
        """Test getting key with invalid format"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        config.config = {"key": "not_dict"}
        assert config.get("key.subkey") is None


class TestConfigSet:
    """Test cases for Config.set method"""

    def test_set_simple_key(self):
        """Test setting simple configuration key"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        config.set("repository.url", "https://github.com/test/repo")
        assert config.get("repository.url") == "https://github.com/test/repo"

    def test_set_nested_key(self):
        """Test setting nested configuration key"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        config.set("new.nested.key", "value")
        assert config.get("new.nested.key") == "value"

    def test_set_creates_intermediate_dicts(self):
        """Test setting creates intermediate dictionaries"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        config.set("a.b.c.d", "deep_value")
        assert config.get("a.b.c.d") == "deep_value"
        assert isinstance(config.config["a"], dict)
        assert isinstance(config.config["a"]["b"], dict)
        assert isinstance(config.config["a"]["b"]["c"], dict)

    def test_set_overwrites_existing(self):
        """Test setting overwrites existing values"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        config.set("repository.ref", "develop")
        assert config.get("repository.ref") == "develop"


class TestConfigValidate:
    """Test cases for Config.validate method"""

    def test_validate_valid_config(self):
        """Test validation with valid configuration"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        config.set("repository.url", "https://github.com/test/repo")
        config.set("local.path", "/tmp/test")

        assert config.validate() is True

    def test_validate_missing_repository_url(self):
        """Test validation fails with missing repository URL"""
        with patch("gitbridge.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            config = Config()
            config.set("local.path", "/tmp/test")

            with pytest.raises(ConfigurationError, match="Repository URL is required"):
                config.validate()

    def test_validate_missing_local_path(self):
        """Test validation fails with missing local path"""
        with patch("gitbridge.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            config = Config()
            config.set("repository.url", "https://github.com/test/repo")

            with pytest.raises(ConfigurationError, match="Local path is required"):
                config.validate()

    def test_validate_invalid_sync_method(self):
        """Test validation fails with invalid sync method"""
        with patch("gitbridge.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            config = Config()
            config.set("repository.url", "https://github.com/test/repo")
            config.set("local.path", "/tmp/test")
            config.set("sync.method", "invalid")

            with pytest.raises(ConfigurationError, match="Invalid sync method: invalid"):
                config.validate()

    def test_validate_valid_sync_methods(self):
        """Test validation passes with valid sync methods"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()
            config.set("repository.url", "https://github.com/test/repo")
            config.set("local.path", "/tmp/test")

            for method in ["api", "browser"]:
                config.set("sync.method", method)
                assert config.validate() is True

    def test_validate_invalid_log_level(self):
        """Test validation fails with invalid log level"""
        with patch("gitbridge.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            config = Config()
            config.set("repository.url", "https://github.com/test/repo")
            config.set("local.path", "/tmp/test")
            config.set("logging.level", "INVALID")

            with pytest.raises(ConfigurationError, match="Invalid log level: INVALID"):
                config.validate()

    def test_validate_valid_log_levels(self):
        """Test validation passes with valid log levels"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()
            config.set("repository.url", "https://github.com/test/repo")
            config.set("local.path", "/tmp/test")

            for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                config.set("logging.level", level)
                assert config.validate() is True


class TestConfigSave:
    """Test cases for Config.save method"""

    def test_save_with_file_path(self, temp_dir):
        """Test saving configuration to specified file"""
        config_file = os.path.join(temp_dir, "save_config.yaml")

        with patch("gitbridge.config.load_dotenv"):
            config = Config()
            config.set("repository.url", "https://github.com/save/repo")
            config.save(config_file)

        # Verify file was created and contains correct data
        assert os.path.exists(config_file)
        with open(config_file) as f:
            saved_config = yaml.safe_load(f)
        assert saved_config["repository"]["url"] == "https://github.com/save/repo"

    def test_save_with_existing_config_file(self, temp_dir):
        """Test saving configuration using existing config file path"""
        config_file = os.path.join(temp_dir, "existing_config.yaml")

        with patch("gitbridge.config.load_dotenv"):
            config = Config(config_file)
            config.set("repository.url", "https://github.com/existing/repo")
            config.save()

        # Verify file was created and contains correct data
        assert os.path.exists(config_file)
        with open(config_file) as f:
            saved_config = yaml.safe_load(f)
        assert saved_config["repository"]["url"] == "https://github.com/existing/repo"

    def test_save_without_file_path(self):
        """Test saving configuration without file path raises error"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

            with pytest.raises(ValueError, match="No configuration file specified"):
                config.save()

    def test_save_creates_parent_directories(self, temp_dir):
        """Test saving configuration creates parent directories"""
        config_file = os.path.join(temp_dir, "nested", "dir", "config.yaml")

        with patch("gitbridge.config.load_dotenv"):
            config = Config()
            config.set("repository.url", "https://github.com/nested/repo")
            config.save(config_file)

        # Verify file and directories were created
        assert os.path.exists(config_file)
        with open(config_file) as f:
            saved_config = yaml.safe_load(f)
        assert saved_config["repository"]["url"] == "https://github.com/nested/repo"

    def test_save_logs_success(self, temp_dir):
        """Test saving configuration logs success message"""
        config_file = os.path.join(temp_dir, "log_config.yaml")

        with patch("gitbridge.config.load_dotenv"), patch("gitbridge.config.logger") as mock_logger:
            config = Config()
            config.save(config_file)

            mock_logger.info.assert_called_with(f"Saved configuration to {config_file}")


class TestConfigToDict:
    """Test cases for Config.to_dict method"""

    def test_to_dict_returns_copy(self):
        """Test to_dict returns a copy of configuration"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        config_dict = config.to_dict()
        config_dict["new_key"] = "new_value"

        # Original config should not be modified
        assert "new_key" not in config.config

    def test_to_dict_structure(self):
        """Test to_dict returns correct structure"""
        with patch("gitbridge.config.load_dotenv"):
            config = Config()

        config_dict = config.to_dict()

        # Should contain all default sections
        assert "repository" in config_dict
        assert "local" in config_dict
        assert "auth" in config_dict
        assert "sync" in config_dict
        assert "logging" in config_dict


class TestConfigSetupLogging:
    """Test cases for Config.setup_logging method"""

    def test_setup_logging_default_level(self):
        """Test setup logging with default level"""
        with (
            patch("gitbridge.config.load_dotenv"),
            patch("logging.basicConfig") as mock_basic_config,
            patch("logging.StreamHandler"),
            patch.dict(os.environ, {}, clear=True),
        ):
            config = Config()
            config.setup_logging()

            mock_basic_config.assert_called_once()
            args, kwargs = mock_basic_config.call_args
            assert kwargs["level"] == logging.INFO
            assert kwargs["force"] is True
            assert len(kwargs["handlers"]) == 1

    def test_setup_logging_custom_level(self):
        """Test setup logging with custom level"""
        with (
            patch("gitbridge.config.load_dotenv"),
            patch("logging.basicConfig") as mock_basic_config,
            patch.dict(os.environ, {}, clear=True),
        ):
            config = Config()
            config.set("logging.level", "DEBUG")
            config.setup_logging()

            mock_basic_config.assert_called_once()
            args, kwargs = mock_basic_config.call_args
            assert kwargs["level"] == logging.DEBUG

    def test_setup_logging_with_file(self, temp_dir):
        """Test setup logging with file handler"""
        log_file = os.path.join(temp_dir, "test.log")

        with (
            patch("gitbridge.config.load_dotenv"),
            patch("logging.basicConfig") as mock_basic_config,
            patch("logging.FileHandler") as mock_file_handler,
            patch.dict(os.environ, {}, clear=True),
        ):
            config = Config()
            config.set("logging.file", log_file)
            config.setup_logging()

            mock_basic_config.assert_called_once()
            args, kwargs = mock_basic_config.call_args
            assert len(kwargs["handlers"]) == 2  # Console + File handlers
            mock_file_handler.assert_called_once_with(log_file)

    def test_setup_logging_format(self):
        """Test setup logging uses correct format"""
        with (
            patch("gitbridge.config.load_dotenv"),
            patch("logging.basicConfig"),
            patch("logging.StreamHandler"),
            patch("logging.Formatter") as mock_formatter,
            patch.dict(os.environ, {}, clear=True),
        ):
            config = Config()
            config.setup_logging()

            # Check that formatter was created with correct format
            expected_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            mock_formatter.assert_called_with(expected_format)


class TestConfigFileHandling:
    """Test cases for Config file handling edge cases"""

    def test_config_file_with_unicode(self, temp_dir):
        """Test loading configuration file with unicode characters"""
        config_file = os.path.join(temp_dir, "unicode_config.yaml")
        test_config = {"repository": {"url": "https://github.com/tëst/repö"}, "local": {"path": "/tëst/päth"}}

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(test_config, f, allow_unicode=True)

        with patch("gitbridge.config.load_dotenv"):
            config = Config(config_file)

        assert config.get("repository.url") == "https://github.com/tëst/repö"
        assert config.get("local.path") == "/tëst/päth"

    def test_config_file_with_comments(self, temp_dir):
        """Test loading configuration file with YAML comments"""
        config_file = os.path.join(temp_dir, "commented_config.yaml")
        yaml_content = """
# Repository configuration
repository:
  url: https://github.com/test/repo  # Main repository
  ref: main  # Default branch

# Local settings
local:
  path: /tmp/test
"""

        with open(config_file, "w") as f:
            f.write(yaml_content)

        with patch("gitbridge.config.load_dotenv"):
            config = Config(config_file)

        assert config.get("repository.url") == "https://github.com/test/repo"
        assert config.get("repository.ref") == "main"
        assert config.get("local.path") == "/tmp/test"

    def test_config_file_complex_structure(self, temp_dir):
        """Test loading configuration file with complex nested structure"""
        config_file = os.path.join(temp_dir, "complex_config.yaml")
        test_config = {
            "repository": {
                "url": "https://github.com/complex/repo",
                "ref": "main",
                "options": {"recursive": True, "depth": 10, "filters": ["*.py", "*.md"]},
            },
            "sync": {"method": "api", "retries": 3, "timeout": 30, "advanced": {"parallel": True, "chunk_size": 1024}},
        }

        with open(config_file, "w") as f:
            yaml.dump(test_config, f)

        with patch("gitbridge.config.load_dotenv"):
            config = Config(config_file)

        assert config.get("repository.options.recursive") is True
        assert config.get("repository.options.filters") == ["*.py", "*.md"]
        assert config.get("sync.advanced.parallel") is True
        assert config.get("sync.advanced.chunk_size") == 1024


class TestConfigIntegration:
    """Integration test cases for Config class"""

    def test_full_config_workflow(self, temp_dir):
        """Test complete configuration workflow"""
        config_file = os.path.join(temp_dir, "workflow_config.yaml")

        # Create initial config
        with patch("gitbridge.config.load_dotenv"):
            config = Config()
            config.set("repository.url", "https://github.com/workflow/repo")
            config.set("local.path", "/tmp/workflow")
            config.set("auth.token", "workflow_token")
            config.save(config_file)

        # Load config from file
        with patch("gitbridge.config.load_dotenv"):
            loaded_config = Config(config_file)

        # Verify loaded values
        assert loaded_config.get("repository.url") == "https://github.com/workflow/repo"
        assert loaded_config.get("local.path") == "/tmp/workflow"
        assert loaded_config.get("auth.token") == "workflow_token"

        # Validate configuration
        assert loaded_config.validate() is True

        # Test to_dict
        config_dict = loaded_config.to_dict()
        assert config_dict["repository"]["url"] == "https://github.com/workflow/repo"

    def test_file_and_env_precedence(self, temp_dir):
        """Test that environment variables override file configuration"""
        config_file = os.path.join(temp_dir, "precedence_config.yaml")
        file_config = {"repository": {"url": "https://github.com/file/repo"}, "auth": {"token": "file_token"}}

        with open(config_file, "w") as f:
            yaml.dump(file_config, f)

        env_vars = {"GITHUB_REPO_URL": "https://github.com/env/repo", "GITHUB_TOKEN": "env_token"}

        with patch.dict(os.environ, env_vars, clear=True), patch("gitbridge.config.load_dotenv"):
            config = Config(config_file)

        # Environment variables should override file values
        assert config.get("repository.url") == "https://github.com/env/repo"
        assert config.get("auth.token") == "env_token"

    def test_config_error_recovery(self, temp_dir):
        """Test configuration handles errors by raising ConfigurationError"""
        # Test with corrupted file raises error on construction
        config_file = os.path.join(temp_dir, "corrupted_config.yaml")
        with open(config_file, "w") as f:
            f.write("corrupted: yaml: [invalid")

        with patch("gitbridge.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            # Should raise ConfigurationError when loading invalid file
            with pytest.raises(ConfigurationError, match="Invalid YAML syntax"):
                Config(config_file)

            # Should work fine without the corrupted file
            config = Config()
            assert config.get("repository.ref") == "main"
            assert config.get("sync.method") == "api"

            # Should be able to set and validate
            config.set("repository.url", "https://github.com/recovery/repo")
            config.set("local.path", "/tmp/recovery")
            assert config.validate() is True
