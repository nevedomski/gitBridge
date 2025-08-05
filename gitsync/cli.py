"""Command-line interface for GitSync"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from .api_sync import GitHubAPISync
from .config import Config

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
def sync(
    repo: Optional[str],
    local: Optional[str],
    ref: Optional[str],
    token: Optional[str],
    config: Optional[str],
    method: str,
    no_progress: bool,
    verbose: bool,
    no_ssl_verify: bool,
):
    """Synchronize a GitHub repository to local directory."""

    # Load configuration
    cfg = Config(config)

    # Override with command-line options
    if repo:
        cfg.set("repository.url", repo)
    if local:
        # Expand path before setting
        import os
        expanded_path = os.path.expanduser(local)
        expanded_path = os.path.expandvars(expanded_path)
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
    if not cfg.validate():
        click.echo("Configuration validation failed", err=True)
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
    
    # Log SSL configuration in verbose mode
    if verbose and ca_bundle:
        click.echo(f"Using CA bundle: {ca_bundle}")
    elif verbose and not verify_ssl:
        click.echo("WARNING: SSL verification disabled")

    # Perform sync based on method
    if method == "api":
        syncer = GitHubAPISync(repo_url, local_path, token, verify_ssl=verify_ssl, ca_bundle=ca_bundle)
        success = syncer.sync(ref=ref, show_progress=not no_progress)
    else:
        click.echo("Browser method not yet implemented", err=True)
        sys.exit(1)

    if success:
        click.echo("✓ Sync completed successfully")
    else:
        click.echo("✗ Sync failed", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", help="Configuration file path", type=click.Path())
@click.option("--repo", "-r", help="GitHub repository URL")
@click.option("--local", "-l", help="Local directory path")
@click.option("--token", "-t", help="GitHub personal access token")
def status(config: Optional[str], repo: Optional[str], local: Optional[str], token: Optional[str]):
    """Check sync status and repository information."""

    # Load configuration
    cfg = Config(config)

    # Override with command-line options
    if repo:
        cfg.set("repository.url", repo)
    if local:
        # Expand path before setting
        import os
        expanded_path = os.path.expanduser(local)
        expanded_path = os.path.expandvars(expanded_path)
        cfg.set("local.path", expanded_path)
    if token:
        cfg.set("auth.token", token)

    # Setup logging
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

    # Create syncer
    syncer = GitHubAPISync(repo_url, local_path, token)

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
            except:
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
def init(output: str, repo: str, local: str, ref: str, token: Optional[str], method: str):
    """Create a new configuration file."""

    # Create configuration
    cfg = Config()

    # Set values
    cfg.set("repository.url", repo)
    cfg.set("repository.ref", ref)
    # Expand path before setting
    import os
    expanded_path = os.path.expanduser(local)
    expanded_path = os.path.expandvars(expanded_path)
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

    if cfg.validate():
        click.echo("✓ Configuration is valid")

        # Display configuration
        click.echo("\nConfiguration:")
        click.echo(yaml.dump(cfg.to_dict(), default_flow_style=False, sort_keys=False))
    else:
        click.echo("✗ Configuration is invalid", err=True)
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
