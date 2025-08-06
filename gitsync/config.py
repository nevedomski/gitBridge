"""Configuration handling for GitSync"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "repository": {
        "url": None,
        "ref": "main",  # branch, tag, or commit SHA
    },
    "local": {
        "path": None,
    },
    "auth": {
        "token": None,
    },
    "sync": {
        "method": "api",  # 'api' or 'browser'
        "incremental": True,
        "verify_ssl": True,
    },
    "logging": {
        "level": "INFO",
        "file": None,
    },
}


class Config:
    """GitSync configuration handler."""

    def __init__(self, config_file: str | None = None):
        """Initialize configuration.

        Args:
            config_file: Path to configuration file
        """
        import copy

        self.config_file = config_file
        self.config: dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)

        # Load environment variables
        load_dotenv()

        # Load configuration
        if config_file:
            self.load_file(config_file)

        # Override with environment variables
        self.load_env()

    def load_file(self, config_file: str) -> None:
        """Load configuration from YAML file.

        Raises:
            ConfigurationError: If configuration file cannot be loaded or parsed
        """
        try:
            path = Path(config_file)
            if not path.exists():
                logger.warning(f"Configuration file not found: {config_file}")
                return

            with open(path) as f:
                file_config = yaml.safe_load(f) or {}

            # Deep merge configurations
            self._deep_merge(self.config, file_config)

            logger.info(f"Loaded configuration from {config_file}")

        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML syntax in configuration file: {e}", config_file=config_file, original_error=e
            ) from e
        except OSError as e:
            raise ConfigurationError(
                f"Failed to read configuration file: {e}", config_file=config_file, original_error=e
            ) from e
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration file: {e}", config_file=config_file, original_error=e
            ) from e

    def load_env(self) -> None:
        """Load configuration from environment variables."""
        # Repository settings
        github_repo_url = os.getenv("GITHUB_REPO_URL")
        if github_repo_url:
            self.config["repository"]["url"] = github_repo_url

        github_ref = os.getenv("GITHUB_REF")
        if github_ref:
            self.config["repository"]["ref"] = github_ref

        # Local path
        local_path = os.getenv("GITSYNC_LOCAL_PATH")
        if local_path:
            self.config["local"]["path"] = local_path

        # Authentication
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            self.config["auth"]["token"] = github_token

        # Sync settings
        sync_method = os.getenv("GITSYNC_METHOD")
        if sync_method:
            self.config["sync"]["method"] = sync_method

        incremental_env = os.getenv("GITSYNC_INCREMENTAL")
        if incremental_env:
            self.config["sync"]["incremental"] = incremental_env.lower() in ("true", "1", "yes")

        # Logging
        log_level = os.getenv("GITSYNC_LOG_LEVEL")
        if log_level:
            self.config["logging"]["level"] = log_level

        log_file = os.getenv("GITSYNC_LOG_FILE")
        if log_file:
            self.config["logging"]["file"] = log_file

    def _deep_merge(self, target: dict[str, Any], source: dict[str, Any]) -> None:
        """Deep merge source dictionary into target."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'repository.url')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        # Expand paths for local.path
        if key == "local.path" and value and isinstance(value, str):
            from .utils import expand_path

            value = expand_path(value)

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'repository.url')
            value: Value to set
        """
        keys = key.split(".")
        target = self.config

        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        target[keys[-1]] = value

    def validate(self) -> bool:
        """Validate configuration.

        Returns:
            True if valid

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Check required fields
        if not self.get("repository.url"):
            raise ConfigurationError(
                "Repository URL is required", config_file=self.config_file, invalid_key="repository.url"
            )

        if not self.get("local.path"):
            raise ConfigurationError("Local path is required", config_file=self.config_file, invalid_key="local.path")

        # Validate sync method
        method = self.get("sync.method", "api")
        if method not in ["api", "browser"]:
            raise ConfigurationError(
                f"Invalid sync method: {method}. Must be 'api' or 'browser'",
                config_file=self.config_file,
                invalid_key="sync.method",
            )

        # Validate log level
        log_level = self.get("logging.level", "INFO")
        if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ConfigurationError(
                f"Invalid log level: {log_level}. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL",
                config_file=self.config_file,
                invalid_key="logging.level",
            )

        return True

    def save(self, config_file: str | None = None) -> None:
        """Save configuration to file.

        Args:
            config_file: Path to save configuration (uses loaded file if not specified)
        """
        file_path = config_file or self.config_file
        if not file_path:
            raise ValueError("No configuration file specified")

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved configuration to {file_path}")

    def to_dict(self) -> dict[str, Any]:
        """Get configuration as dictionary."""
        return self.config.copy()

    def setup_logging(self) -> None:
        """Set up logging based on configuration."""
        log_level = getattr(logging, self.get("logging.level", "INFO"))
        log_file = self.get("logging.file")

        # Configure logging format
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Configure handlers
        handlers: list[logging.Handler] = []

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)

        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)

        # Configure root logger
        logging.basicConfig(level=log_level, handlers=handlers, force=True)
