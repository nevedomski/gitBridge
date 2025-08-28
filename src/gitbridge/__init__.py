"""GitBridge - GitHub Repository Synchronization Tool"""

__version__ = "0.1.0"

# Main facade class - primary interface for users
# Component classes - for advanced users who need fine-grained control
from .api_client import GitHubAPIClient
from .api_sync import GitHubAPISync

# Browser sync fallback - import only if available
try:
    from .browser_sync import GitHubBrowserSync

    _BROWSER_SYNC_AVAILABLE = True
except ImportError:
    _BROWSER_SYNC_AVAILABLE = False
    GitHubBrowserSync = None  # type: ignore

# Configuration and utilities
from .config import Config
from .file_synchronizer import FileSynchronizer
from .progress_tracker import ProgressTracker
from .repository_manager import RepositoryManager
from .utils import SyncStats, parse_github_url

__all__ = [
    # Main interface
    "GitHubAPISync",
    # Components
    "GitHubAPIClient",
    "RepositoryManager",
    "FileSynchronizer",
    "ProgressTracker",
    # Configuration and utilities
    "Config",
    "parse_github_url",
    "SyncStats",
]

# Add GitHubBrowserSync to __all__ only if available
if _BROWSER_SYNC_AVAILABLE:
    __all__.append("GitHubBrowserSync")
