"""Command-line interface for GitSync"""

import logging
import sys
from pathlib import Path

import click
import yaml

from .api_sync import GitHubAPISync
from .browser_sync import GitHubBrowserSync
from .config import Config
from .exceptions import (
    AuthenticationError,
    BrowserError,
    ConfigurationError,
    FileSystemError,
    GitSyncError,
    NetworkError,
    RateLimitError,
    RepositoryNotFoundError,
)

logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def cli():
    """GitSync - Synchronize GitHub repositories when git access is blocked."""
    pass


@cli.command()
@click.option("--repo", "-r", help="GitHub repository URL", required=False)
@click.option("--local", "-l", help="Local directory path", required=False)
@click.option("--ref", help="Branch, tag, or commit SHA to sync")
@click.option("--token", "-t", help="GitHub personal access token", envvar="GITHUB_TOKEN")
@click.option("--config", "-c", help="Configuration file path", type=click.Path())
@click.option("--method", type=click.Choice(["api", "browser"]), default="api", help="Sync method")
@click.option("--no-progress", is_flag=True, help="Disable progress bar")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--no-ssl-verify", is_flag=True, help="Disable SSL verification (use with caution)")
@click.option("--auto-proxy", is_flag=True, help="Auto-detect proxy from Windows/Chrome PAC")
@click.option("--auto-cert", is_flag=True, help="Auto-detect certificates from Windows certificate store")
def sync(
    repo: str | None,
    local: str | None,
    ref: str | None,
    token: str | None,
    config: str | None,
    method: str,
    no_progress: bool,
    verbose: bool,
    no_ssl_verify: bool,
    auto_proxy: bool,
    auto_cert: bool,
):
    """Synchronize a GitHub repository to local directory."""

    # Load configuration
    cfg = Config(config)

    # Override with command-line options
    if repo:
        cfg.set("repository.url", repo)
    if local:
        # Expand path before setting
        from .utils import expand_path

        expanded_path = expand_path(local)
        cfg.set("local.path", expanded_path)
    if ref:
        cfg.set("repository.ref", ref)
    if token:
        cfg.set("auth.token", token)
    if method:
        cfg.set("sync.method", method)

    # Set up logging
    if verbose:
        cfg.set("logging.level", "DEBUG")
    cfg.setup_logging()

    # Validate configuration
    try:
        cfg.validate()
    except ConfigurationError as e:
        click.echo(f"Configuration validation failed: {e}", err=True)
        if verbose:
            click.echo(f"Error details: {e.get_context()}", err=True)
        sys.exit(1)

    # Get configuration values
    repo_url = cfg.get("repository.url")
    local_path = cfg.get("local.path")
    ref = cfg.get("repository.ref", "main")
    token = cfg.get("auth.token")
    method = cfg.get("sync.method", "api")

    # Handle SSL verification
    if no_ssl_verify:
        verify_ssl = False
        ca_bundle = None
    else:
        verify_ssl = cfg.get("sync.verify_ssl", True)
        ca_bundle = cfg.get("sync.ca_bundle")

    # Handle auto proxy detection
    if not auto_proxy:
        auto_proxy = cfg.get("sync.auto_proxy", False)

    # Handle auto certificate detection
    if not auto_cert:
        auto_cert = cfg.get("sync.auto_cert", False)

    # Log SSL configuration in verbose mode
    if verbose and ca_bundle:
        click.echo(f"Using CA bundle: {ca_bundle}")
    elif verbose and not verify_ssl:
        click.echo("WARNING: SSL verification disabled")

    # Perform sync based on method
    try:
        if method == "api":
            syncer = GitHubAPISync(
                repo_url,
                local_path,
                token,
                verify_ssl=verify_ssl,
                ca_bundle=ca_bundle,
                auto_proxy=auto_proxy,
                auto_cert=auto_cert,
            )
            success = syncer.sync(ref=ref, show_progress=not no_progress)
        elif method == "browser":
            syncer = GitHubBrowserSync(
                repo_url,
                local_path,
                token,
                verify_ssl=verify_ssl,
                ca_bundle=ca_bundle,
                auto_proxy=auto_proxy,
                auto_cert=auto_cert,
            )
            success = syncer.sync(ref=ref, show_progress=not no_progress)
        else:
            click.echo(f"Unknown sync method: {method}", err=True)
            sys.exit(1)

        if success:
            click.echo("✓ Sync completed successfully")
        else:
            click.echo("✗ Sync failed", err=True)
            sys.exit(1)

    except AuthenticationError as e:
        click.echo(f"✗ Authentication failed: {e}", err=True)
        if not e.details.get("token_provided"):
            click.echo("Hint: Provide a GitHub token with --token or GITHUB_TOKEN environment variable", err=True)
        if verbose:
            click.echo(f"Error details: {e.get_context()}", err=True)
        sys.exit(1)
    except RepositoryNotFoundError as e:
        click.echo(f"✗ Repository not found: {e}", err=True)
        if e.details.get("is_private"):
            click.echo("Hint: This might be a private repository. Check your token permissions.", err=True)
        if verbose:
            click.echo(f"Error details: {e.get_context()}", err=True)
        sys.exit(1)
    except RateLimitError as e:
        click.echo(f"✗ Rate limit exceeded: {e}", err=True)
        if e.details.get("reset_time"):
            import time

            reset_time = time.strftime("%H:%M:%S", time.localtime(e.details["reset_time"]))
            click.echo(f"Rate limit resets at: {reset_time}", err=True)
        click.echo("Hint: Wait for rate limit to reset or use a GitHub token for higher limits", err=True)
        if verbose:
            click.echo(f"Error details: {e.get_context()}", err=True)
        sys.exit(1)
    except NetworkError as e:
        click.echo(f"✗ Network error: {e}", err=True)
        if e.details.get("status_code"):
            click.echo(f"HTTP Status: {e.details['status_code']}", err=True)
        click.echo("Hint: Check your internet connection and proxy settings", err=True)
        if verbose:
            click.echo(f"Error details: {e.get_context()}", err=True)
        sys.exit(1)
    except BrowserError as e:
        click.echo(f"✗ Browser automation error: {e}", err=True)
        click.echo("Hint: Try using --method api instead of browser automation", err=True)
        if verbose:
            click.echo(f"Error details: {e.get_context()}", err=True)
        sys.exit(1)
    except FileSystemError as e:
        click.echo(f"✗ File system error: {e}", err=True)
        click.echo("Hint: Check directory permissions and available disk space", err=True)
        if verbose:
            click.echo(f"Error details: {e.get_context()}", err=True)
        sys.exit(1)
    except GitSyncError as e:
        click.echo(f"✗ Sync error: {e}", err=True)
        if verbose:
            click.echo(f"Error details: {e.get_context()}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        if verbose:
            import traceback

            click.echo("Full traceback:", err=True)
            click.echo(traceback.format_exc(), err=True)
        click.echo("This is an unexpected error. Please report it as a bug.", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", help="Configuration file path", type=click.Path())
@click.option("--repo", "-r", help="GitHub repository URL")
@click.option("--local", "-l", help="Local directory path")
@click.option("--token", "-t", help="GitHub personal access token")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--no-ssl-verify", is_flag=True, help="Disable SSL verification (use with caution)")
@click.option("--auto-proxy", is_flag=True, help="Auto-detect proxy from Windows/Chrome PAC")
@click.option("--auto-cert", is_flag=True, help="Auto-detect certificates from Windows certificate store")
def status(
    config: str | None,
    repo: str | None,
    local: str | None,
    token: str | None,
    verbose: bool,
    no_ssl_verify: bool,
    auto_proxy: bool,
    auto_cert: bool,
):
    """Check sync status and repository information."""

    # Load configuration
    cfg = Config(config)

    # Override with command-line options
    if repo:
        cfg.set("repository.url", repo)
    if local:
        # Expand path before setting
        from .utils import expand_path

        expanded_path = expand_path(local)
        cfg.set("local.path", expanded_path)
    if token:
        cfg.set("auth.token", token)

    # Set up logging
    if verbose:
        cfg.set("logging.level", "DEBUG")
    cfg.setup_logging()

    # Validate required fields
    repo_url = cfg.get("repository.url")
    local_path = cfg.get("local.path")

    if not repo_url:
        click.echo("Repository URL is required", err=True)
        sys.exit(1)

    if not local_path:
        click.echo("Local path is required", err=True)
        sys.exit(1)

    token = cfg.get("auth.token")

    # Handle SSL verification
    if no_ssl_verify:
        verify_ssl = False
        ca_bundle = None
    else:
        verify_ssl = cfg.get("sync.verify_ssl", True)
        ca_bundle = cfg.get("sync.ca_bundle")

    # Handle auto proxy detection
    if not auto_proxy:
        auto_proxy = cfg.get("sync.auto_proxy", False)

    # Handle auto certificate detection
    if not auto_cert:
        auto_cert = cfg.get("sync.auto_cert", False)

    # Log SSL configuration in verbose mode
    if verbose and ca_bundle:
        click.echo(f"Using CA bundle: {ca_bundle}")
    elif verbose and not verify_ssl:
        click.echo("WARNING: SSL verification disabled")

    # Create syncer with SSL and proxy configuration
    syncer = GitHubAPISync(
        repo_url,
        local_path,
        token,
        verify_ssl=verify_ssl,
        ca_bundle=ca_bundle,
        auto_proxy=auto_proxy,
        auto_cert=auto_cert,
    )

    click.echo(f"Repository: {repo_url}")
    click.echo(f"Local path: {local_path}")

    # Test connection
    if syncer.test_connection():
        click.echo("✓ API connection successful")

        # Get rate limit
        rate_limit = syncer.get_rate_limit()
        if rate_limit:
            core = rate_limit.get("rate", {})
            remaining = core.get("remaining", "unknown")
            limit = core.get("limit", "unknown")
            click.echo(f"API rate limit: {remaining}/{limit} requests remaining")
    else:
        click.echo("✗ API connection failed", err=True)

    # Check local directory
    local_dir = Path(local_path)
    if local_dir.exists():
        click.echo("✓ Local directory exists")

        # Check for hash cache
        hash_cache = local_dir / ".gitsync" / "file_hashes.json"
        if hash_cache.exists():
            click.echo("✓ Incremental sync data found")

            # Count tracked files
            try:
                import json

                with open(hash_cache) as f:
                    hashes = json.load(f)
                click.echo(f"  Tracked files: {len(hashes)}")
            except (OSError, json.JSONDecodeError):
                pass
    else:
        click.echo("✗ Local directory does not exist")


@cli.command()
@click.option("--output", "-o", default="config.yaml", help="Output configuration file")
@click.option("--repo", "-r", prompt="GitHub repository URL", help="GitHub repository URL")
@click.option("--local", "-l", prompt="Local directory path", help="Local directory path")
@click.option("--ref", help="Branch, tag, or commit SHA to sync", default="main")
@click.option("--token", "-t", help="GitHub personal access token")
@click.option("--method", type=click.Choice(["api", "browser"]), default="api", help="Sync method")
def init(output: str, repo: str, local: str, ref: str, token: str | None, method: str):
    """Create a new configuration file."""

    # Create configuration
    cfg = Config()

    # Set values
    cfg.set("repository.url", repo)
    cfg.set("repository.ref", ref)
    # Expand path before setting
    from .utils import expand_path

    expanded_path = expand_path(local)
    cfg.set("local.path", expanded_path)
    cfg.set("sync.method", method)

    if token:
        cfg.set("auth.token", token)

    # Save configuration
    cfg.save(output)

    click.echo(f"✓ Configuration saved to {output}")

    # Show example usage
    click.echo("\nExample usage:")
    click.echo(f"  gitsync sync --config {output}")

    if not token:
        click.echo("\nNote: No token provided. You may need to set GITHUB_TOKEN environment variable")
        click.echo("or add it to the configuration file for private repositories.")


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
def validate(config_file: str):
    """Validate a configuration file."""

    cfg = Config(config_file)

    click.echo(f"Validating {config_file}...")

    try:
        cfg.validate()
        click.echo("✓ Configuration is valid")

        # Display configuration
        click.echo("\nConfiguration:")
        click.echo(yaml.dump(cfg.to_dict(), default_flow_style=False, sort_keys=False))
    except ConfigurationError as e:
        click.echo(f"✗ Configuration is invalid: {e}", err=True)
        click.echo(f"Error details: {e.get_context()}", err=True)
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
