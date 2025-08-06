"""Unit tests for progress_tracker.py module"""

import time
from unittest.mock import Mock, patch

import pytest

from gitbridge.progress_tracker import ProgressTracker


class TestProgressTracker:
    """Test cases for ProgressTracker class"""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method"""
        pass

    def test_init_with_progress_bar(self) -> None:
        """Test initialization with progress bar"""
        with patch("gitbridge.progress_tracker.tqdm") as mock_tqdm:
            mock_progress_bar = Mock()
            mock_tqdm.return_value = mock_progress_bar

            tracker = ProgressTracker(total_files=100, show_progress=True, desc="Testing")

            assert tracker.show_progress is True
            assert tracker.total_files == 100
            assert tracker.progress_bar == mock_progress_bar
            assert tracker.stats.files_checked == 0

            mock_tqdm.assert_called_once_with(
                total=100,
                desc="Testing",
                unit="file",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
            )

    def test_init_without_progress_bar(self) -> None:
        """Test initialization without progress bar"""
        tracker = ProgressTracker(total_files=0, show_progress=False)

        assert tracker.show_progress is False
        assert tracker.total_files == 0
        assert tracker.progress_bar is None

    def test_init_no_progress_bar_zero_files(self) -> None:
        """Test initialization with zero files doesn't create progress bar"""
        tracker = ProgressTracker(total_files=0, show_progress=True)

        assert tracker.show_progress is True
        assert tracker.total_files == 0
        assert tracker.progress_bar is None

    def test_update_progress_downloaded(self) -> None:
        """Test updating progress for downloaded file"""
        with patch("gitbridge.progress_tracker.tqdm") as mock_tqdm:
            mock_progress_bar = Mock()
            mock_tqdm.return_value = mock_progress_bar

            tracker = ProgressTracker(total_files=100, show_progress=True)

            tracker.update_progress("file.txt", downloaded=True, size=1024)

            assert tracker.stats.files_checked == 1
            assert tracker.stats.files_downloaded == 1
            assert tracker.stats.bytes_downloaded == 1024
            assert tracker.stats.files_skipped == 0
            assert tracker.stats.files_failed == 0

            mock_progress_bar.update.assert_called_once_with(1)
            mock_progress_bar.set_postfix_str.assert_called_once_with("Downloaded: file.txt")

    def test_update_progress_skipped(self) -> None:
        """Test updating progress for skipped file"""
        with patch("gitbridge.progress_tracker.tqdm") as mock_tqdm:
            mock_progress_bar = Mock()
            mock_tqdm.return_value = mock_progress_bar

            tracker = ProgressTracker(total_files=100, show_progress=True)

            tracker.update_progress("file.txt", skipped=True)

            assert tracker.stats.files_checked == 1
            assert tracker.stats.files_downloaded == 0
            assert tracker.stats.files_skipped == 1
            assert tracker.stats.files_failed == 0

            mock_progress_bar.set_postfix_str.assert_called_once_with("Skipped: file.txt")

    def test_update_progress_failed(self) -> None:
        """Test updating progress for failed file"""
        with patch("gitbridge.progress_tracker.tqdm") as mock_tqdm:
            mock_progress_bar = Mock()
            mock_tqdm.return_value = mock_progress_bar

            tracker = ProgressTracker(total_files=100, show_progress=True)

            tracker.update_progress("file.txt", failed=True)

            assert tracker.stats.files_checked == 1
            assert tracker.stats.files_downloaded == 0
            assert tracker.stats.files_skipped == 0
            assert tracker.stats.files_failed == 1

            mock_progress_bar.set_postfix_str.assert_called_once_with("Failed: file.txt")

    def test_update_progress_no_progress_bar(self) -> None:
        """Test updating progress without progress bar"""
        tracker = ProgressTracker(total_files=100, show_progress=False)

        tracker.update_progress("file.txt", downloaded=True, size=1024)

        assert tracker.stats.files_checked == 1
        assert tracker.stats.files_downloaded == 1
        assert tracker.stats.bytes_downloaded == 1024

    def test_set_total_files(self) -> None:
        """Test setting total files"""
        with patch("gitbridge.progress_tracker.tqdm") as mock_tqdm:
            mock_progress_bar = Mock()
            mock_tqdm.return_value = mock_progress_bar

            tracker = ProgressTracker(total_files=50, show_progress=True)
            tracker.set_total_files(100)

            assert tracker.total_files == 100
            assert mock_progress_bar.total == 100
            mock_progress_bar.refresh.assert_called_once()

    def test_update_postfix(self) -> None:
        """Test updating progress bar postfix"""
        with patch("gitbridge.progress_tracker.tqdm") as mock_tqdm:
            mock_progress_bar = Mock()
            mock_tqdm.return_value = mock_progress_bar

            tracker = ProgressTracker(total_files=100, show_progress=True)
            tracker.update_postfix(custom="value", another=42)

            mock_progress_bar.set_postfix.assert_called_once_with(custom="value", another=42)

    def test_set_description(self) -> None:
        """Test setting progress bar description"""
        with patch("gitbridge.progress_tracker.tqdm") as mock_tqdm:
            mock_progress_bar = Mock()
            mock_tqdm.return_value = mock_progress_bar

            tracker = ProgressTracker(total_files=100, show_progress=True)
            tracker.set_description("New description")

            mock_progress_bar.set_description.assert_called_once_with("New description")

    def test_close(self) -> None:
        """Test closing progress tracker"""
        with patch("gitbridge.progress_tracker.tqdm") as mock_tqdm:
            mock_progress_bar = Mock()
            mock_tqdm.return_value = mock_progress_bar

            tracker = ProgressTracker(total_files=100, show_progress=True)
            tracker.close()

            mock_progress_bar.close.assert_called_once()
            assert tracker.progress_bar is None

    def test_get_elapsed_time(self) -> None:
        """Test getting elapsed time"""
        tracker = ProgressTracker(total_files=100, show_progress=False)

        # Wait a small amount of time
        time.sleep(0.01)

        elapsed = tracker.get_elapsed_time()
        assert elapsed > 0

    def test_get_download_rate(self) -> None:
        """Test getting download rate"""
        tracker = ProgressTracker(total_files=100, show_progress=False)

        # Simulate some downloads
        tracker.stats.bytes_downloaded = 1024
        time.sleep(0.01)  # Ensure some time passes

        rate = tracker.get_download_rate()
        assert rate > 0

    def test_get_download_rate_no_time(self) -> None:
        """Test getting download rate with no elapsed time"""
        with patch.object(ProgressTracker, "get_elapsed_time", return_value=0):
            tracker = ProgressTracker(total_files=100, show_progress=False)
            tracker.stats.bytes_downloaded = 1024

            rate = tracker.get_download_rate()
            assert rate == 0.0

    def test_get_file_rate(self) -> None:
        """Test getting file processing rate"""
        tracker = ProgressTracker(total_files=100, show_progress=False)

        # Simulate some file processing
        tracker.stats.files_checked = 10
        time.sleep(0.01)  # Ensure some time passes

        rate = tracker.get_file_rate()
        assert rate > 0

    def test_print_summary_basic(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test printing basic summary"""
        tracker = ProgressTracker(total_files=100, show_progress=False)

        # Simulate some activity
        tracker.stats.files_checked = 10
        tracker.stats.files_downloaded = 8
        tracker.stats.files_skipped = 1
        tracker.stats.files_failed = 1
        tracker.stats.bytes_downloaded = 1024

        time.sleep(0.01)  # Ensure some time passes

        tracker.print_summary()

        captured = capsys.readouterr()
        assert "SYNCHRONIZATION SUMMARY" in captured.out
        assert "Files checked:    10" in captured.out
        assert "Files downloaded: 8" in captured.out
        assert "Files skipped:    1" in captured.out
        assert "Files failed:     1" in captured.out
        assert "Data downloaded:" in captured.out
        assert "Success rate:     90.0%" in captured.out

    def test_print_summary_with_rate_limit(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test printing summary with rate limit info"""
        tracker = ProgressTracker(total_files=100, show_progress=False)

        rate_limit_info = {"rate": {"remaining": 4500, "limit": 5000, "reset": 1234567890}}

        tracker.print_summary(show_rate_limit=True, rate_limit_info=rate_limit_info)

        captured = capsys.readouterr()
        assert "Rate limit:       4500/5000" in captured.out

    def test_get_stats_dict(self) -> None:
        """Test getting statistics as dictionary"""
        tracker = ProgressTracker(total_files=100, show_progress=False)

        # Simulate some activity
        tracker.stats.files_checked = 10
        tracker.stats.files_downloaded = 8
        tracker.stats.files_skipped = 1
        tracker.stats.files_failed = 1
        tracker.stats.bytes_downloaded = 1024

        time.sleep(0.01)  # Ensure some time passes

        stats = tracker.get_stats_dict()

        assert stats["files_checked"] == 10
        assert stats["files_downloaded"] == 8
        assert stats["files_skipped"] == 1
        assert stats["files_failed"] == 1
        assert stats["bytes_downloaded"] == 1024
        assert stats["elapsed_time"] > 0
        assert stats["success_rate"] == 90.0  # (8 + 1) / 10 * 100

    def test_should_throttle(self) -> None:
        """Test throttling check"""
        tracker = ProgressTracker(total_files=100, show_progress=False)

        # Test normal cases
        assert tracker.should_throttle(50, throttle_interval=100) is False
        assert tracker.should_throttle(99, throttle_interval=100) is False
        assert tracker.should_throttle(100, throttle_interval=100) is True
        assert tracker.should_throttle(200, throttle_interval=100) is True

        # Test zero case
        assert tracker.should_throttle(0, throttle_interval=100) is False

    @patch("gitbridge.progress_tracker.time.sleep")
    def test_log_throttle_pause(self, mock_sleep: Mock) -> None:
        """Test logging throttle pause"""
        with patch("gitbridge.progress_tracker.tqdm") as mock_tqdm:
            mock_progress_bar = Mock()
            mock_tqdm.return_value = mock_progress_bar

            tracker = ProgressTracker(total_files=100, show_progress=True)
            tracker.log_throttle_pause(0.5)

            mock_progress_bar.set_postfix_str.assert_called_once_with("Throttling...")
            mock_sleep.assert_called_once_with(0.5)
