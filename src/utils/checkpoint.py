"""Checkpoint system for resuming scraping after interruption."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Set

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CheckpointManager:
    """Manages checkpoint state for resume capability."""

    def __init__(self, checkpoint_file: Optional[str] = None):
        """Initialize checkpoint manager.

        Args:
            checkpoint_file: Path to checkpoint file (defaults to settings.checkpoint_file)
        """
        self.checkpoint_file = Path(checkpoint_file or settings.checkpoint_file)
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

    def load_checkpoint(self) -> dict:
        """Load checkpoint data from file.

        Returns:
            Dictionary with checkpoint data:
            - processed_urls: Set of already processed URLs
            - failed_urls: Set of URLs that failed
            - stats: Statistics from last run
            - timestamp: Last checkpoint timestamp
        """
        if not self.checkpoint_file.exists():
            logger.info("checkpoint_not_found", file=str(self.checkpoint_file))
            return {
                "processed_urls": [],
                "failed_urls": [],
                "stats": {},
                "timestamp": None,
            }

        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert lists back to sets for faster lookups
                processed = data.get("processed_urls", [])
                failed = data.get("failed_urls", [])
                return {
                    "processed_urls": set(processed) if isinstance(processed, list) else processed,
                    "failed_urls": set(failed) if isinstance(failed, list) else failed,
                    "stats": data.get("stats", {}),
                    "timestamp": data.get("timestamp"),
                }
        except Exception as e:
            logger.warning("checkpoint_load_error", file=str(self.checkpoint_file), error=str(e))
            return {
                "processed_urls": [],
                "failed_urls": [],
                "stats": {},
                "timestamp": None,
            }

    def save_checkpoint(
        self,
        processed_urls: Set[str],
        failed_urls: Optional[Set[str]] = None,
        stats: Optional[dict] = None,
    ) -> None:
        """Save checkpoint data to file.

        Args:
            processed_urls: Set of successfully processed URLs
            failed_urls: Set of URLs that failed (optional)
            stats: Statistics dictionary (optional)
        """
        if not settings.checkpoint_enabled:
            return

        try:
            checkpoint_data = {
                "processed_urls": sorted(list(processed_urls)),  # Sort for consistency
                "failed_urls": sorted(list(failed_urls or [])),
                "stats": stats or {},
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Write to temporary file first, then rename (atomic operation)
            temp_file = self.checkpoint_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

            temp_file.replace(self.checkpoint_file)
            logger.debug(
                "checkpoint_saved", file=str(self.checkpoint_file), count=len(processed_urls)
            )

        except Exception as e:
            logger.error("checkpoint_save_error", file=str(self.checkpoint_file), error=str(e))

    def is_processed(self, url: str) -> bool:
        """Check if URL has been processed.

        Args:
            url: URL to check

        Returns:
            True if URL is in processed set
        """
        checkpoint = self.load_checkpoint()
        processed = checkpoint["processed_urls"]
        # Ensure it's a set for membership check
        if not isinstance(processed, set):
            processed = set(processed) if processed else set()
        return url in processed

    def add_processed(self, url: str) -> None:
        """Add URL to processed set and save checkpoint.

        Args:
            url: URL that was successfully processed
        """
        checkpoint = self.load_checkpoint()
        # Ensure processed_urls is a set
        processed = checkpoint["processed_urls"]
        if not isinstance(processed, set):
            processed = set(processed) if processed else set()
        processed.add(url)
        checkpoint["processed_urls"] = processed

        self.save_checkpoint(
            checkpoint["processed_urls"],
            checkpoint["failed_urls"],
            checkpoint["stats"],
        )

    def add_failed(self, url: str) -> None:
        """Add URL to failed set and save checkpoint.

        Args:
            url: URL that failed to process
        """
        checkpoint = self.load_checkpoint()
        # Ensure failed_urls is a set
        failed = checkpoint["failed_urls"]
        if not isinstance(failed, set):
            failed = set(failed) if failed else set()
        failed.add(url)
        # Remove from processed if it was there (in case of retry failure)
        processed = checkpoint["processed_urls"]
        if not isinstance(processed, set):
            processed = set(processed) if processed else set()
        processed.discard(url)  # Remove if exists
        checkpoint["failed_urls"] = failed
        checkpoint["processed_urls"] = processed

        self.save_checkpoint(
            checkpoint["processed_urls"],
            checkpoint["failed_urls"],
            checkpoint["stats"],
        )

    def remove_failed(self, url: str) -> None:
        """Remove URL from failed set (after successful retry).

        Args:
            url: URL that was successfully processed after retry
        """
        checkpoint = self.load_checkpoint()
        failed = checkpoint["failed_urls"]
        if not isinstance(failed, set):
            failed = set(failed) if failed else set()
        failed.discard(url)
        checkpoint["failed_urls"] = failed

        self.save_checkpoint(
            checkpoint["processed_urls"],
            checkpoint["failed_urls"],
            checkpoint["stats"],
        )

    def clear_checkpoint(self) -> None:
        """Clear checkpoint file."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            logger.info("checkpoint_cleared", file=str(self.checkpoint_file))

    def get_resume_info(self) -> dict:
        """Get information about checkpoint for resume.

        Returns:
            Dictionary with resume information
        """
        checkpoint = self.load_checkpoint()
        return {
            "has_checkpoint": len(checkpoint["processed_urls"]) > 0,
            "processed_count": len(checkpoint["processed_urls"]),
            "failed_count": len(checkpoint["failed_urls"]),
            "timestamp": checkpoint["timestamp"],
        }
