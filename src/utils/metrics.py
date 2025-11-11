"""Metrics and monitoring utilities for tracking scraper performance."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ScraperMetrics:
    """Tracks metrics for scraper performance."""

    def __init__(self):
        """Initialize metrics tracker."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

        # Counters
        self.products_scraped: int = 0
        self.products_failed: int = 0
        self.creators_scraped: int = 0
        self.creators_failed: int = 0
        self.categories_scraped: int = 0
        self.categories_failed: int = 0

        # Timing
        self.total_requests: int = 0
        self.total_wait_time: float = 0.0
        self.total_retries: int = 0

        # Errors
        self.errors_by_type: Dict[str, int] = {}
        self.errors_by_url: Dict[str, int] = {}

    def start(self) -> None:
        """Start tracking metrics."""
        self.start_time = time.time()
        logger.info("metrics_tracking_started")

    def stop(self) -> None:
        """Stop tracking metrics."""
        self.end_time = time.time()
        logger.info("metrics_tracking_stopped")

    def record_product_scraped(self) -> None:
        """Record successful product scrape."""
        self.products_scraped += 1

    def record_product_failed(
        self, error_type: Optional[str] = None, url: Optional[str] = None
    ) -> None:
        """Record failed product scrape.

        Args:
            error_type: Type of error
            url: URL that failed
        """
        self.products_failed += 1
        if error_type:
            self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
        if url:
            self.errors_by_url[url] = self.errors_by_url.get(url, 0) + 1

    def record_creator_scraped(self) -> None:
        """Record successful creator scrape."""
        self.creators_scraped += 1

    def record_creator_failed(
        self, error_type: Optional[str] = None, url: Optional[str] = None
    ) -> None:
        """Record failed creator scrape.

        Args:
            error_type: Type of error
            url: URL that failed
        """
        self.creators_failed += 1
        if error_type:
            self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
        if url:
            self.errors_by_url[url] = self.errors_by_url.get(url, 0) + 1

    def record_category_scraped(self) -> None:
        """Record successful category scrape."""
        self.categories_scraped += 1

    def record_category_failed(
        self, error_type: Optional[str] = None, url: Optional[str] = None
    ) -> None:
        """Record failed category scrape.

        Args:
            error_type: Type of error
            url: URL that failed
        """
        self.categories_failed += 1
        if error_type:
            self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
        if url:
            self.errors_by_url[url] = self.errors_by_url.get(url, 0) + 1

    def record_request(self, wait_time: float = 0.0) -> None:
        """Record an HTTP request.

        Args:
            wait_time: Time spent waiting (rate limiting)
        """
        self.total_requests += 1
        self.total_wait_time += wait_time

    def record_retry(self) -> None:
        """Record a retry attempt."""
        self.total_retries += 1

    def get_duration(self) -> float:
        """Get total duration in seconds.

        Returns:
            Duration in seconds, or 0 if not started
        """
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    def get_success_rate(self) -> float:
        """Calculate overall success rate.

        Returns:
            Success rate as a float between 0 and 1
        """
        total_attempts = self.products_scraped + self.products_failed
        if total_attempts == 0:
            return 0.0
        return self.products_scraped / total_attempts

    def get_products_per_second(self) -> float:
        """Calculate products scraped per second.

        Returns:
            Products per second, or 0 if no products scraped
        """
        duration = self.get_duration()
        if duration == 0:
            return 0.0
        return self.products_scraped / duration

    def get_average_wait_time(self) -> float:
        """Get average wait time per request.

        Returns:
            Average wait time in seconds
        """
        if self.total_requests == 0:
            return 0.0
        return self.total_wait_time / self.total_requests

    def get_summary(self) -> Dict:
        """Get summary of all metrics.

        Returns:
            Dictionary with all metrics
        """
        duration = self.get_duration()
        total_products = self.products_scraped + self.products_failed
        total_creators = self.creators_scraped + self.creators_failed
        total_categories = self.categories_scraped + self.categories_failed

        return {
            "duration_seconds": duration,
            "duration_formatted": self._format_duration(duration),
            "start_time": (
                datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None
            ),
            "end_time": (
                datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None
            ),
            "products": {
                "scraped": self.products_scraped,
                "failed": self.products_failed,
                "total": total_products,
                "success_rate": self.get_success_rate(),
                "per_second": self.get_products_per_second(),
            },
            "creators": {
                "scraped": self.creators_scraped,
                "failed": self.creators_failed,
                "total": total_creators,
            },
            "categories": {
                "scraped": self.categories_scraped,
                "failed": self.categories_failed,
                "total": total_categories,
            },
            "requests": {
                "total": self.total_requests,
                "total_wait_time": self.total_wait_time,
                "average_wait_time": self.get_average_wait_time(),
            },
            "retries": {
                "total": self.total_retries,
            },
            "errors": {
                "by_type": self.errors_by_type,
                "total_unique_urls_failed": len(self.errors_by_url),
            },
        }

    def log_summary(self) -> None:
        """Log summary of metrics and save to metrics.log file."""
        summary = self.get_summary()
        logger.info("scraper_metrics_summary", **summary)

        # Save to metrics.log file for monitoring
        try:
            metrics_file = Path(settings.data_dir) / "metrics.log"
            metrics_file.parent.mkdir(parents=True, exist_ok=True)

            # Append metrics entry with timestamp
            metrics_entry = {"timestamp": datetime.now().isoformat(), **summary}

            with open(metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metrics_entry, ensure_ascii=False) + "\n")

            logger.debug("metrics_saved_to_file", file=str(metrics_file))
        except Exception as e:
            logger.warning("metrics_file_save_error", error=str(e))

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            minutes = (seconds % 3600) / 60
            return f"{int(hours)}h {int(minutes)}m"


# Global metrics instance
_metrics: Optional[ScraperMetrics] = None


def get_metrics() -> ScraperMetrics:
    """Get or create global metrics instance.

    Returns:
        ScraperMetrics instance
    """
    global _metrics
    if _metrics is None:
        _metrics = ScraperMetrics()
    return _metrics
