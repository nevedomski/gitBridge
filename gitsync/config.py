"""Configuration handling for GitSync"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

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

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = DEFAULT_CONFIG.copy()

        # Load environment variables
        load_dotenv()

        # Load configuration
        if config_file:
            self.load_file(config_file)

        # Override with environment variables
        self.load_env()

    def load_file(self, config_file: str) -> None:
        """Load configuration from YAML file."""
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

        except Exception as e:
            logger.error(f"Failed to load configuration file: {e}")

    def load_env(self) -> None:
        """Load configuration from environment variables."""
        # Repository settings
        if os.getenv("GITHUB_REPO_URL"):
            self.config["repository"]["url"] = os.getenv("GITHUB_REPO_URL")

        if os.getenv("GITHUB_REF"):
            self.config["repository"]["ref"] = os.getenv("GITHUB_REF")

        # Local path
        if os.getenv("GITSYNC_LOCAL_PATH"):
            self.config["local"]["path"] = os.getenv("GITSYNC_LOCAL_PATH")

        # Authentication
        if os.getenv("GITHUB_TOKEN"):
            self.config["auth"]["token"] = os.getenv("GITHUB_TOKEN")

        # Sync settings
        if os.getenv("GITSYNC_METHOD"):
            self.config["sync"]["method"] = os.getenv("GITSYNC_METHOD")

        if os.getenv("GITSYNC_INCREMENTAL"):
            self.config["sync"]["incremental"] = os.getenv("GITSYNC_INCREMENTAL").lower() in ("true", "1", "yes")

        # Logging
        if os.getenv("GITSYNC_LOG_LEVEL"):
            self.config["logging"]["level"] = os.getenv("GITSYNC_LOG_LEVEL")

        if os.getenv("GITSYNC_LOG_FILE"):
            self.config["logging"]["file"] = os.getenv("GITSYNC_LOG_FILE")

    def _deep_merge(self, target: Dict, source: Dict) -> None:
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
            value = os.path.expanduser(value)
            value = os.path.expandvars(value)

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
            True if valid, False otherwise
        """
        # Check required fields
        if not self.get("repository.url"):
            logger.error("Repository URL is required")
            return False

        if not self.get("local.path"):
            logger.error("Local path is required")
            return False

        # Validate sync method
        method = self.get("sync.method", "api")
        if method not in ["api", "browser"]:
            logger.error(f"Invalid sync method: {method}")
            return False

        # Validate log level
        log_level = self.get("logging.level", "INFO")
        if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger.error(f"Invalid log level: {log_level}")
            return False

        return True

    def save(self, config_file: Optional[str] = None) -> None:
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

    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self.config.copy()

    def setup_logging(self) -> None:
        """Set up logging based on configuration."""
        log_level = getattr(logging, self.get("logging.level", "INFO"))
        log_file = self.get("logging.file")

        # Configure logging format
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Configure handlers
        handlers = []

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
