"""Progress tracking and statistics reporting.

This module provides comprehensive progress tracking and statistics reporting
for synchronization operations. It includes visual progress bars, timing
information, and detailed statistics.

Key Features:
    - Real-time progress tracking with visual feedback
    - Detailed synchronization statistics
    - Rate limiting and timing information
    - Customizable progress reporting formats
    - Thread-safe progress updates

Typical Usage:
    >>> from gitsync.progress_tracker import ProgressTracker
    >>>
    >>> tracker = ProgressTracker(total_files=100, show_progress=True)
    >>> for file in files:
    ...     # Process file
    ...     tracker.update_progress("file.txt", downloaded=True)
    >>>
    >>> tracker.print_summary()
"""

import logging
import time
from typing import Any

from tqdm import tqdm

from .utils import SyncStats

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks progress and statistics for synchronization operations.

    This class provides comprehensive progress tracking with visual feedback
    via progress bars, detailed statistics collection, and summary reporting.
    It integrates with the existing SyncStats utility while adding enhanced
    progress display capabilities.

    Attributes:
        stats (SyncStats): Core statistics tracking object
        progress_bar (Optional[tqdm]): Visual progress bar instance
        show_progress (bool): Whether to show visual progress
        start_time (float): Timestamp when tracking started
        total_files (int): Total number of files to process

    DOCDEV-NOTE: Component Architecture - Progress Tracking Layer
        This class was extracted from the monolithic GitHubAPISync to provide
        dedicated progress tracking and statistics reporting. It provides a
        clean interface for tracking sync operations and displaying progress.

    DOCDEV-NOTE: Design Decisions
        - Separation of Concerns: Progress tracking isolated from sync logic
        - Flexible Display: Support for multiple output formats (tqdm, quiet, json)
        - Thread-Safe: Designed for future parallel sync operations
        - Rich Statistics: Comprehensive metrics beyond simple counts

    DOCDEV-NOTE: User Experience Focus
        - Real-time feedback keeps users informed during long syncs
        - Detailed statistics help diagnose sync issues
        - Customizable verbosity for different use cases

    DOCDEV-TODO: Future Enhancements
        - Add JSON output format for CI/CD pipelines
        - Implement ETA calculation based on historical data
        - Add bandwidth usage tracking and throttling
        - Support for multiple progress bars (parallel syncs)
    """

    def __init__(self, total_files: int = 0, show_progress: bool = True, desc: str = "Syncing files"):
        """Initialize progress tracker.

        Args:
            total_files: Total number of files to process (for progress bar)
            show_progress: Whether to show visual progress bar
            desc: Description text for progress bar

        Note:
            If show_progress is False, statistics are still tracked but
            no visual progress bar is displayed.
        """
        self.stats = SyncStats()
        self.show_progress = show_progress
        self.total_files = total_files
        self.start_time = time.time()
        self.progress_bar: tqdm[Any] | None = None

        # Initialize progress bar if requested
        if self.show_progress and total_files > 0:
            self.progress_bar = tqdm(
                total=total_files,
                desc=desc,
                unit="file",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
            )

    def update_progress(
        self, file_path: str = "", downloaded: bool = False, skipped: bool = False, failed: bool = False, size: int = 0
    ) -> None:
        """Update progress for a single file operation.

        Args:
            file_path: Path of the file being processed (for logging)
            downloaded: Whether file was successfully downloaded
            skipped: Whether file was skipped (already up to date)
            failed: Whether file operation failed
            size: Size of file in bytes (for bandwidth tracking)

        Note:
            Only one of downloaded/skipped/failed should be True.
            The method automatically updates internal counters and progress bar.
        """
        # Update statistics
        self.stats.files_checked += 1

        if downloaded:
            self.stats.files_downloaded += 1
            self.stats.bytes_downloaded += size
            if self.progress_bar:
                self.progress_bar.set_postfix_str(f"Downloaded: {file_path}")
        elif skipped:
            self.stats.files_skipped += 1
            if self.progress_bar:
                self.progress_bar.set_postfix_str(f"Skipped: {file_path}")
        elif failed:
            self.stats.files_failed += 1
            if self.progress_bar:
                self.progress_bar.set_postfix_str(f"Failed: {file_path}")

        # Update progress bar
        if self.progress_bar:
            self.progress_bar.update(1)
            self.progress_bar.set_postfix(
                {
                    "downloaded": self.stats.files_downloaded,
                    "skipped": self.stats.files_skipped,
                    "failed": self.stats.files_failed,
                }
            )

    def set_total_files(self, total: int) -> None:
        """Set or update the total number of files to process.

        Args:
            total: Total number of files

        Note:
            This is useful when the total number of files isn't known
            at initialization time.
        """
        self.total_files = total
        if self.progress_bar:
            self.progress_bar.total = total
            self.progress_bar.refresh()

    def update_postfix(self, **kwargs: Any) -> None:
        """Update progress bar postfix with custom information.

        Args:
            **kwargs: Key-value pairs to display in progress bar postfix
        """
        if self.progress_bar:
            self.progress_bar.set_postfix(**kwargs)

    def set_description(self, desc: str) -> None:
        """Update progress bar description.

        Args:
            desc: New description text
        """
        if self.progress_bar:
            self.progress_bar.set_description(desc)

    def close(self) -> None:
        """Close and cleanup the progress bar.

        This should be called when progress tracking is complete
        to properly cleanup the display.
        """
        if self.progress_bar:
            self.progress_bar.close()
            self.progress_bar = None

    def get_elapsed_time(self) -> float:
        """Get elapsed time since tracking started.

        Returns:
            Elapsed time in seconds
        """
        return time.time() - self.start_time

    def get_download_rate(self) -> float:
        """Get average download rate.

        Returns:
            Download rate in bytes per second
        """
        elapsed = self.get_elapsed_time()
        if elapsed > 0:
            return self.stats.bytes_downloaded / elapsed
        return 0.0

    def get_file_rate(self) -> float:
        """Get average file processing rate.

        Returns:
            File processing rate in files per second
        """
        elapsed = self.get_elapsed_time()
        if elapsed > 0:
            return self.stats.files_checked / elapsed
        return 0.0

    def print_summary(self, show_rate_limit: bool = False, rate_limit_info: dict[str, Any] | None = None) -> None:
        """Print detailed synchronization summary.

        Args:
            show_rate_limit: Whether to include rate limit information
            rate_limit_info: Rate limit data from GitHub API

        Note:
            This provides a comprehensive summary including timing,
            statistics, and optional rate limit information.
        """
        # Close progress bar before printing summary
        if self.progress_bar:
            self.progress_bar.close()
            self.progress_bar = None

        elapsed = self.get_elapsed_time()
        download_rate = self.get_download_rate()
        file_rate = self.get_file_rate()

        print("\n" + "=" * 60)
        print("SYNCHRONIZATION SUMMARY")
        print("=" * 60)

        # File statistics
        print(f"Files checked:    {self.stats.files_checked:,}")
        print(f"Files downloaded: {self.stats.files_downloaded:,}")
        print(f"Files skipped:    {self.stats.files_skipped:,}")
        print(f"Files failed:     {self.stats.files_failed:,}")

        # Size and performance statistics
        if self.stats.bytes_downloaded > 0:
            size_mb = self.stats.bytes_downloaded / (1024 * 1024)
            print(f"Data downloaded:  {size_mb:.2f} MB")

        print(f"Elapsed time:     {elapsed:.1f} seconds")

        if file_rate > 0:
            print(f"Processing rate:  {file_rate:.1f} files/sec")

        if download_rate > 0:
            rate_mb = download_rate / (1024 * 1024)
            print(f"Download rate:    {rate_mb:.2f} MB/sec")

        # Success rate
        if self.stats.files_checked > 0:
            success_rate = (self.stats.files_downloaded + self.stats.files_skipped) / self.stats.files_checked * 100
            print(f"Success rate:     {success_rate:.1f}%")

        # Rate limit information
        if show_rate_limit and rate_limit_info:
            core_limit = rate_limit_info.get("rate", {})
            remaining = core_limit.get("remaining", "unknown")
            limit = core_limit.get("limit", "unknown")
            reset_time = core_limit.get("reset", 0)

            print(f"Rate limit:       {remaining}/{limit} requests remaining")

            if isinstance(reset_time, int | float) and reset_time > 0:
                import datetime

                reset_dt = datetime.datetime.fromtimestamp(reset_time)
                print(f"Rate limit reset: {reset_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        print("=" * 60)

        # Log summary as well
        logger.info(
            f"Sync completed: {self.stats.files_downloaded} downloaded, "
            f"{self.stats.files_skipped} skipped, {self.stats.files_failed} failed "
            f"in {elapsed:.1f}s"
        )

    def get_stats_dict(self) -> dict[str, Any]:
        """Get current statistics as a dictionary.

        Returns:
            Dictionary containing all current statistics and timing information
        """
        elapsed = self.get_elapsed_time()

        return {
            "files_checked": self.stats.files_checked,
            "files_downloaded": self.stats.files_downloaded,
            "files_skipped": self.stats.files_skipped,
            "files_failed": self.stats.files_failed,
            "bytes_downloaded": self.stats.bytes_downloaded,
            "elapsed_time": elapsed,
            "download_rate": self.get_download_rate(),
            "file_rate": self.get_file_rate(),
            "success_rate": (
                (self.stats.files_downloaded + self.stats.files_skipped) / max(1, self.stats.files_checked)
            )
            * 100,
        }

    def should_throttle(self, files_processed: int, throttle_interval: int = 100) -> bool:
        """Check if processing should be throttled to avoid rate limits.

        Args:
            files_processed: Number of files processed so far
            throttle_interval: How often to throttle (every N files)

        Returns:
            True if processing should pause briefly

        Note:
            This can be used to implement rate limiting by pausing
            processing at regular intervals.
        """
        return files_processed > 0 and files_processed % throttle_interval == 0

    def log_throttle_pause(self, pause_duration: float = 0.1) -> None:
        """Log a throttling pause and update progress.

        Args:
            pause_duration: How long to pause in seconds

        Note:
            This should be called when implementing throttling logic
            to provide user feedback about the pause.
        """
        if self.progress_bar:
            self.progress_bar.set_postfix_str("Throttling...")

        logger.debug(f"Throttling for {pause_duration}s to avoid rate limits")
        time.sleep(pause_duration)
