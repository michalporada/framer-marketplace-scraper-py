"""Main marketplace scraper orchestrator."""

import asyncio
from typing import Any, Dict, List, Optional

import httpx
from tqdm.asyncio import tqdm

from src.config.settings import settings
from src.parsers.category_parser import CategoryParser
from src.parsers.creator_parser import CreatorParser
from src.parsers.product_parser import ProductParser
from src.scrapers.category_scraper import CategoryScraper
from src.scrapers.creator_scraper import CreatorScraper
from src.scrapers.product_scraper import ProductScraper
from src.scrapers.sitemap_scraper import SitemapScraper
from src.storage.database import DatabaseStorage
from src.storage.file_storage import FileStorage
from src.utils.checkpoint import CheckpointManager
from src.utils.logger import get_logger
from src.utils.metrics import get_metrics

logger = get_logger(__name__)


class MarketplaceScraper:
    """Main orchestrator for scraping Framer Marketplace."""

    def __init__(self):
        """Initialize marketplace scraper."""
        self.sitemap_scraper: Optional[SitemapScraper] = None
        self.product_scraper: Optional[ProductScraper] = None
        self.creator_scraper: Optional[CreatorScraper] = None
        self.category_scraper: Optional[CategoryScraper] = None
        self.product_parser = ProductParser()
        self.creator_parser = CreatorParser()
        self.category_parser = CategoryParser()
        self.storage = FileStorage()
        self.db_storage = DatabaseStorage()
        self.checkpoint_manager = CheckpointManager()
        self.metrics = get_metrics()
        self.client: Optional[httpx.AsyncClient] = None

        # Statistics (for backward compatibility)
        self.stats = {
            "products_scraped": 0,
            "products_failed": 0,
            "creators_scraped": 0,
            "creators_failed": 0,
            "categories_scraped": 0,
            "categories_failed": 0,
        }

        # Deduplication tracking
        self.seen_product_ids: set = set()
        self.seen_product_urls: set = set()
        self.seen_creator_ids: set = set()
        self.duplicate_count: int = 0

    async def __aenter__(self):
        """Async context manager entry."""
        # Set explicit timeouts: connect, read, write, pool
        # This ensures requests are properly cancelled if they exceed timeout
        timeout = httpx.Timeout(
            connect=5.0,  # Connection timeout: 5s
            read=settings.timeout,  # Read timeout: 12s (from settings)
            write=5.0,  # Write timeout: 5s
            pool=5.0,  # Pool timeout: 5s
        )
        from src.utils.user_agents import get_random_user_agent

        # Use realistic browser headers to avoid bot detection
        user_agent = get_random_user_agent()
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                # Only request gzip/deflate - httpx auto-decompresses these, but NOT Brotli (br)
                "Accept-Encoding": "gzip, deflate",
                "Referer": settings.marketplace_url,
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Upgrade-Insecure-Requests": "1",
            },
            follow_redirects=True,
        )

        self.sitemap_scraper = SitemapScraper(self.client)
        self.product_scraper = ProductScraper(self.client)
        self.creator_scraper = CreatorScraper(self.client)
        self.category_scraper = CategoryScraper(self.client)

        # Initialize refresh lock
        self.refresh_lock = asyncio.Lock()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def scrape_product(
        self,
        url: str,
        skip_if_processed: bool = True,
        save_checkpoint_immediately: bool = True,
    ) -> bool:
        """Scrape a single product.

        Args:
            url: Product URL
            skip_if_processed: Skip if already processed (checkpoint)
            save_checkpoint_immediately: If False, checkpoint is saved in batch (for performance)

        Returns:
            True if successful, False otherwise
        """
        # Check checkpoint if enabled
        if skip_if_processed and settings.checkpoint_enabled:
            if self.checkpoint_manager.is_processed(url):
                logger.debug("product_already_processed", url=url)
                return True

        try:
            # Scrape product page
            product_data = await self.product_scraper.scrape(url)
            if product_data is None:
                self.stats["products_failed"] += 1
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_failed(url)
                return False

            # Parse HTML
            product = self.product_parser.parse(
                product_data["html"],
                product_data["url"],
                product_data["type"],
            )
            if product is None:
                self.stats["products_failed"] += 1
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_failed(url)
                return False

            # Scrape creator if available
            if product.creator and product.creator.profile_url:
                creator_data = await self.creator_scraper.scrape(product.creator.profile_url)
                if creator_data:
                    # Parse creator HTML to get full creator data (including avatar)
                    creator = self.creator_parser.parse(creator_data["html"], creator_data["url"])
                    if creator:
                        # Save creator as separate file (only once per creator)
                        await self.storage.save_creator_json(creator)
                        # Save creator to database
                        await self.db_storage.save_creator_db(creator)
                        self.stats["creators_scraped"] = self.stats.get("creators_scraped", 0) + 1

                        # Update product.creator with full data (merge to preserve avatar from product page if available)
                        if not product.creator.avatar_url:
                            product.creator.avatar_url = creator.avatar_url
                        if not product.creator.name:
                            product.creator.name = creator.name
                        if not product.creator.bio:
                            product.creator.bio = creator.bio
                        if not product.creator.website:
                            product.creator.website = creator.website
                        if creator.social_media:
                            product.creator.social_media = creator.social_media
                        if creator.stats:
                            product.creator.stats = creator.stats

            # Track seen URLs for refresh sitemap deduplication
            # Main deduplication happens in filter_urls_by_type, but we still track
            # for refresh sitemap which may add new URLs during scraping
            is_duplicate = False
            if product.url in self.seen_product_urls:
                logger.warning("duplicate_product_url", product_id=product.id, url=url)
                is_duplicate = True
                self.duplicate_count += 1
            else:
                self.seen_product_urls.add(product.url)
                self.seen_product_ids.add(product.id)

            # Log record count before save
            logger.debug(
                "product_before_save",
                product_id=product.id,
                total_scraped=self.stats["products_scraped"],
                total_failed=self.stats["products_failed"],
            )

            # Save product
            success = await self.storage.save_product_json(product)

            # Save product to database (duplicates already filtered in filter_urls_by_type)
            # Only skip if this is a duplicate from refresh sitemap
            if not is_duplicate:
                await self.db_storage.save_product_db(product)
            else:
                logger.warning("db_write_skipped_duplicate", product_id=product.id)

            if success:
                self.stats["products_scraped"] += 1
                self.metrics.record_product_scraped()
                # Mark as processed in checkpoint
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_processed(url, save_immediately=save_checkpoint_immediately)
                logger.info(
                    "product_scraped",
                    product_id=product.id,
                    name=product.name,
                    type=product.type,
                )
            else:
                self.stats["products_failed"] += 1
                self.metrics.record_product_failed()
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_failed(url)

            return success

        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                "product_scrape_exception",
                url=url,
                error=str(e),
                error_type=error_type,
            )
            self.stats["products_failed"] += 1
            self.metrics.record_product_failed(error_type=error_type, url=url)
            if settings.checkpoint_enabled:
                self.checkpoint_manager.add_failed(url)
            return False

    async def _get_sitemap_with_initial_retry(self) -> tuple[Dict[str, Any], bool, float]:
        """Get sitemap with initial retry attempts before falling back to cache.

        Retry sequence: Fibonacci sequence in seconds (0s, 1s, 1s, 2s, 3s, 5s, 8s, 13s, 21s, 34s, 55s, 89s, 144s, 233s, 377s)
        Total max wait: ~16.4 minutes (986 seconds) before using cache.

        Returns:
            Tuple of (sitemap_data, cache_used, cache_age_hours)
        """
        retry_delays = [
            0,
            1,
            1,
            2,
            3,
            5,
            8,
            13,
            21,
            34,
            55,
            89,
            144,
            233,
            377,
        ]  # Fibonacci sequence in seconds
        total_attempts = len(retry_delays)

        total_max_wait = sum(retry_delays)
        total_max_wait_minutes = round(total_max_wait / 60, 2)
        logger.info(
            "sitemap_initial_retry_start",
            total_attempts=total_attempts,
            max_wait_seconds=total_max_wait,
            max_wait_minutes=total_max_wait_minutes,
            message=f"Starting sitemap fetch with {total_attempts} retry attempts (max wait: {total_max_wait}s / {total_max_wait_minutes} minutes)",
        )

        for attempt_num, delay_seconds in enumerate(retry_delays, 1):
            # Wait before retry (except first attempt)
            if delay_seconds > 0:
                # Format wait time: show seconds for < 60s, minutes for >= 60s
                if delay_seconds < 60:
                    wait_display = f"{delay_seconds}s"
                else:
                    wait_display = f"{delay_seconds}s ({round(delay_seconds / 60, 1)}min)"

                logger.info(
                    "sitemap_retry_wait",
                    attempt=attempt_num,
                    total=total_attempts,
                    wait_seconds=delay_seconds,
                    wait_minutes=round(delay_seconds / 60, 2) if delay_seconds >= 60 else 0,
                    message=f"Waiting {wait_display} before retry attempt {attempt_num}/{total_attempts}",
                )
                await asyncio.sleep(delay_seconds)

            try:
                logger.info(
                    "sitemap_retry_attempt",
                    attempt=attempt_num,
                    total=total_attempts,
                    message=f"Attempt {attempt_num}/{total_attempts}: Trying to fetch fresh sitemap",
                )

                # Try to get fresh sitemap (this will use cache if upstream fails)
                xml_content, cache_used, cache_age_hours = await self.sitemap_scraper.get_sitemap()

                # If we got fresh sitemap (not from cache), parse and return
                if xml_content and not cache_used:
                    total_wait = sum(retry_delays[:attempt_num])
                    total_wait_minutes = round(total_wait / 60, 2)
                    logger.info(
                        "sitemap_fetch_success_after_retry",
                        attempt=attempt_num,
                        total_wait_seconds=total_wait,
                        total_wait_minutes=total_wait_minutes,
                        message=f"✅ Successfully fetched fresh sitemap on attempt {attempt_num}/{total_attempts} (waited {total_wait}s / {total_wait_minutes} minutes total)",
                    )
                    # Parse and return
                    sitemap_data = self.sitemap_scraper.parse_sitemap(xml_content)
                    return (sitemap_data, False, 0.0)

                # If we got cached sitemap, it means upstream is still failing
                # Continue to next retry attempt
                if xml_content and cache_used:
                    logger.warning(
                        "sitemap_retry_still_cache",
                        attempt=attempt_num,
                        total=total_attempts,
                        cache_age_hours=cache_age_hours,
                        message=f"Attempt {attempt_num}/{total_attempts} still returned cached sitemap ({cache_age_hours}h old) - will retry",
                    )
                    continue

                # If no content, continue to next retry
                logger.warning(
                    "sitemap_retry_no_content",
                    attempt=attempt_num,
                    total=total_attempts,
                    message=f"Attempt {attempt_num}/{total_attempts} returned no content - will retry",
                )
                continue

            except httpx.HTTPStatusError as e:
                # For 5xx errors, get_sitemap might return cache or raise
                # If it raises, it's a real 5xx - log and continue retry
                if 500 <= e.response.status_code < 600:
                    logger.warning(
                        "sitemap_retry_5xx",
                        attempt=attempt_num,
                        total=total_attempts,
                        status_code=e.response.status_code,
                        message=f"Attempt {attempt_num}/{total_attempts} got 5xx error ({e.response.status_code}) - will retry",
                    )
                    continue
                else:
                    logger.warning(
                        "sitemap_retry_http_error",
                        attempt=attempt_num,
                        total=total_attempts,
                        status_code=e.response.status_code,
                        message=f"Attempt {attempt_num}/{total_attempts} got HTTP error ({e.response.status_code}) - will retry",
                    )
                    continue
            except Exception as e:
                logger.warning(
                    "sitemap_retry_error",
                    attempt=attempt_num,
                    total=total_attempts,
                    error=str(e),
                    error_type=type(e).__name__,
                    message=f"Attempt {attempt_num}/{total_attempts} failed with error - will retry",
                )
                continue

        # All retry attempts failed - fall back to cache
        total_wait = sum(retry_delays)
        total_wait_minutes = round(total_wait / 60, 2)
        logger.warning(
            "sitemap_all_retries_failed",
            total_attempts=total_attempts,
            total_wait_seconds=total_wait,
            total_wait_minutes=total_wait_minutes,
            message=f"All {total_attempts} retry attempts failed (waited {total_wait}s / {total_wait_minutes} minutes total) - falling back to cached sitemap",
        )

        # Try to get cached sitemap (this should work as get_sitemap falls back to cache)
        try:
            xml_content, cache_used, cache_age_hours = await self.sitemap_scraper.get_sitemap()
            if xml_content:
                sitemap_data = self.sitemap_scraper.parse_sitemap(xml_content)
                logger.info(
                    "sitemap_using_cache_after_retries",
                    cache_age_hours=cache_age_hours,
                    message=f"Using cached sitemap ({cache_age_hours}h old) after all retry attempts failed",
                )
                return (sitemap_data, True, cache_age_hours)
        except Exception as e:
            logger.error(
                "sitemap_cache_fallback_failed",
                error=str(e),
                error_type=type(e).__name__,
                message="Failed to get cached sitemap after all retries - this is a critical error",
            )
            raise

        # If we get here, we have no sitemap at all
        logger.error(
            "sitemap_completely_failed",
            message="All retry attempts failed and no cache available - cannot proceed",
        )
        raise ValueError("Failed to get sitemap after all retry attempts and cache fallback")

    async def _scrape_new_products_background(self, new_urls: List[str]) -> None:
        """Scrape new products found during sitemap refresh in background.

        Args:
            new_urls: List of new product URLs to scrape
        """
        if not new_urls:
            return

        logger.info(
            "scraping_new_products_background",
            count=len(new_urls),
            message=f"Scraping {len(new_urls)} new products found during sitemap refresh (background task)",
        )

        # Scrape new URLs without refresh (to avoid infinite loop)
        # Use same concurrency limit as main batch
        limit = settings.max_concurrent_requests

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(limit)

        async def scrape_with_semaphore(url: str):
            async with semaphore:
                return await self.scrape_product(url, skip_if_processed=True)

        # Scrape new products
        tasks = [scrape_with_semaphore(url) for url in new_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r and not isinstance(r, Exception))
        failed_count = len(new_urls) - success_count

        logger.info(
            "new_products_background_completed",
            total=len(new_urls),
            success=success_count,
            failed=failed_count,
            message=f"Background scraping of new products completed: {success_count} success, {failed_count} failed",
        )

    async def _attempt_sitemap_refresh(self, milestone: float) -> None:
        """Attempt to refresh sitemap at milestone if stale cache was used.

        Args:
            milestone: Progress milestone (0.25, 0.5, 0.75, 1.0)
        """
        if not self.sitemap_scraper or not self.types_to_scrape:
            return

        # Skip if we already have fresh sitemap (optimization)
        if self.fresh_sitemap_obtained:
            return

        # Use lock to ensure only one refresh attempt at a time (prevents race condition)
        if not self.refresh_lock:
            return

        async with self.refresh_lock:
            # Double-check after acquiring lock (another task might have succeeded)
            if self.fresh_sitemap_obtained:
                return

            try:
                logger.info(
                    "attempting_sitemap_refresh",
                    milestone=f"{milestone * 100:.0f}%",
                    message=f"Attempting to refresh sitemap at {milestone * 100:.0f}% progress",
                )

                # Try to fetch fresh sitemap
                xml_content, cache_used, cache_age_hours = await self.sitemap_scraper.get_sitemap()

                if xml_content and not cache_used:
                    # Successfully fetched fresh sitemap!
                    self.fresh_sitemap_obtained = True  # Stop further attempts
                    logger.info(
                        "sitemap_refresh_success",
                        milestone=f"{milestone * 100:.0f}%",
                        message=f"✅ Successfully refreshed sitemap at {milestone * 100:.0f}% - checking for new products. No further refresh attempts will be made.",
                    )

                    # Parse fresh sitemap
                    fresh_sitemap_data = self.sitemap_scraper.parse_sitemap(xml_content)
                    fresh_urls = self.sitemap_scraper.filter_urls_by_type(
                        fresh_sitemap_data, self.types_to_scrape
                    )

                    # Find new URLs that weren't in original list
                    new_urls = [url for url in fresh_urls if url not in self.seen_product_urls]

                    if new_urls:
                        logger.info(
                            "new_products_found_in_refresh",
                            milestone=f"{milestone * 100:.0f}%",
                            count=len(new_urls),
                            message=f"Found {len(new_urls)} new products in refreshed sitemap - will be scraped immediately in background",
                        )
                        # Scrape new products immediately in background (non-blocking)
                        asyncio.create_task(self._scrape_new_products_background(new_urls))
                    else:
                        logger.info(
                            "no_new_products_in_refresh",
                            milestone=f"{milestone * 100:.0f}%",
                            message="Refreshed sitemap but no new products found",
                        )
                elif xml_content and cache_used:
                    logger.warning(
                        "sitemap_refresh_still_cache",
                        milestone=f"{milestone * 100:.0f}%",
                        cache_age_hours=cache_age_hours,
                        message=f"Refresh attempt at {milestone * 100:.0f}% still returned cached sitemap ({cache_age_hours}h old)",
                    )
                else:
                    logger.warning(
                        "sitemap_refresh_failed",
                        milestone=f"{milestone * 100:.0f}%",
                        message=f"Failed to refresh sitemap at {milestone * 100:.0f}% - continuing with original list",
                    )
            except Exception as e:
                logger.warning(
                    "sitemap_refresh_error",
                    milestone=f"{milestone * 100:.0f}%",
                    error=str(e),
                    error_type=type(e).__name__,
                    message=f"Error refreshing sitemap at {milestone * 100:.0f}% - continuing",
                )

    async def scrape_products_batch(
        self,
        urls: List[str],
        limit: Optional[int] = None,
        skip_processed: bool = True,
        used_stale_cache: bool = False,
    ) -> None:
        """Scrape multiple products with concurrency limit.

        Args:
            urls: List of product URLs
            limit: Maximum number of concurrent requests (defaults to settings)
            skip_processed: Skip URLs that are already processed (checkpoint)
            used_stale_cache: If True, attempt to refresh sitemap at milestones (25%, 50%, 75%, 100%)
        """
        if limit is None:
            limit = settings.max_concurrent_requests

        # Filter out already processed URLs if checkpoint enabled
        if skip_processed and settings.checkpoint_enabled:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            original_count = len(urls)
            urls = [url for url in urls if url not in checkpoint["processed_urls"]]
            if original_count > len(urls):
                logger.info(
                    "skipping_processed_urls",
                    skipped=original_count - len(urls),
                    remaining=len(urls),
                )

        if not urls:
            logger.info("no_urls_to_scrape", reason="all_processed_or_limit_reached")
            return

        logger.info("starting_batch_scrape", total=len(urls), concurrency_limit=limit)

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(limit)

        # Track milestones for sitemap refresh (only if used stale cache)
        refresh_milestones = [0.25, 0.5, 0.75, 1.0] if used_stale_cache else []
        refresh_attempted_at = set()

        # Batch checkpoint saving: save every 50 products for better performance
        checkpoint_batch_size = 50
        last_checkpoint_save = 0

        async def scrape_with_semaphore(url: str, index: int, total: int):
            nonlocal last_checkpoint_save
            async with semaphore:
                current_progress = (index + 1) / total

                # Log progress every 50 products or at milestones (10%, 25%, 50%, 75%, 90%)
                if index % 50 == 0 or index in [
                    int(total * 0.1),
                    int(total * 0.25),
                    int(total * 0.5),
                    int(total * 0.75),
                    int(total * 0.9),
                ]:
                    logger.info(
                        "scraping_progress",
                        current=index + 1,
                        total=total,
                        percentage=round(current_progress * 100, 2),
                    )

                # Attempt to refresh sitemap at milestones if used stale cache
                # Skip if we already have fresh sitemap (optimization)
                if used_stale_cache and refresh_milestones and not self.fresh_sitemap_obtained:
                    for milestone in refresh_milestones:
                        if current_progress >= milestone and milestone not in refresh_attempted_at:
                            refresh_attempted_at.add(milestone)
                            await self._attempt_sitemap_refresh(milestone)

                # Use batch checkpoint saving for better performance
                result = await self.scrape_product(
                    url,
                    skip_if_processed=skip_processed,
                    save_checkpoint_immediately=False,
                )

                # Save checkpoint periodically (every 50 products) for resume capability
                if (
                    settings.checkpoint_enabled
                    and (index + 1) - last_checkpoint_save >= checkpoint_batch_size
                ):
                    checkpoint = self.checkpoint_manager.load_checkpoint()
                    self.checkpoint_manager.save_checkpoint(
                        checkpoint["processed_urls"],
                        checkpoint["failed_urls"],
                        self.stats,
                    )
                    last_checkpoint_save = index + 1
                    logger.debug(
                        "checkpoint_saved_batch",
                        processed_count=len(checkpoint["processed_urls"]),
                        index=index + 1,
                    )

                return result

        # Scrape with progress bar
        tasks = [scrape_with_semaphore(url, i, len(urls)) for i, url in enumerate(urls)]
        results = await tqdm.gather(*tasks, desc="Scraping products")

        success_count = sum(1 for r in results if r)

        # Save final checkpoint with stats
        if settings.checkpoint_enabled:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            self.checkpoint_manager.save_checkpoint(
                checkpoint["processed_urls"],
                checkpoint["failed_urls"],
                self.stats,
            )

        logger.info(
            "batch_scrape_completed",
            total=len(urls),
            success=success_count,
            failed=len(urls) - success_count,
        )

    async def scrape(
        self,
        limit: Optional[int] = None,
        resume: bool = True,
        product_types: Optional[List[str]] = None,
    ) -> dict:
        """Main scraping method.

        Args:
            limit: Limit number of products to scrape (None for all)
            resume: Resume from checkpoint if available
            product_types: List of product types to scrape (None uses settings)

        Returns:
            Dictionary with scraping statistics

        Raises:
            TimeoutError: If global scraping timeout is exceeded
        """
        import asyncio
        import time

        # Start metrics tracking
        self.metrics.start()
        start_time = time.time()
        logger.info("marketplace_scraping_started", global_timeout=settings.global_scraping_timeout)

        # Check for existing checkpoint
        if resume and settings.checkpoint_enabled:
            resume_info = self.checkpoint_manager.get_resume_info()
            if resume_info["has_checkpoint"]:
                logger.info(
                    "checkpoint_found",
                    processed=resume_info["processed_count"],
                    failed=resume_info["failed_count"],
                    timestamp=resume_info["timestamp"],
                )

        # Get product URLs from sitemap with initial retry attempts
        async with self.sitemap_scraper:
            try:
                (
                    sitemap_data,
                    cache_used,
                    cache_age_hours,
                ) = await self._get_sitemap_with_initial_retry()
            except httpx.HTTPStatusError as e:
                # If marketplace sitemap returns 5xx, abort scraper
                if 500 <= e.response.status_code < 600:
                    logger.error(
                        "upstream_unavailable",
                        url=str(e.request.url),
                        status_code=e.response.status_code,
                        message="Marketplace sitemap returned 5xx - aborting scraper",
                    )
                    self.metrics.stop()
                    raise  # Propagate to main() for exit code handling
                else:
                    # Other HTTP errors - continue but log warning
                    logger.warning(
                        "sitemap_fetch_error",
                        url=str(e.request.url),
                        status_code=e.response.status_code,
                    )
                    sitemap_data = {
                        "products": {},
                        "categories": [],
                        "profiles": [],
                        "help_articles": [],
                    }
                    cache_used = False
                    cache_age_hours = 0.0

            # Use provided product types or fall back to settings
            types_to_scrape = (
                product_types if product_types is not None else settings.get_product_types()
            )
            product_urls = self.sitemap_scraper.filter_urls_by_type(sitemap_data, types_to_scrape)

        if not product_urls:
            logger.warning("no_products_found")
            return self.stats

        # Validate minimum URLs threshold
        if len(product_urls) < settings.min_urls_threshold:
            logger.error(
                "insufficient_urls",
                found=len(product_urls),
                required=settings.min_urls_threshold,
                message=f"Found only {len(product_urls)} URLs, minimum {settings.min_urls_threshold} required - aborting scraper",
            )
            self.metrics.stop()
            raise ValueError(
                f"Insufficient URLs: found {len(product_urls)}, required {settings.min_urls_threshold}"
            )

        logger.info("product_urls_found", count=len(product_urls))

        # Apply limit if specified
        if limit:
            product_urls = product_urls[:limit]
            logger.info("applying_limit", limit=limit, remaining=len(product_urls))

        # Store types for potential sitemap refresh
        self.types_to_scrape = types_to_scrape

        # Determine if we used stale cache (cache_used and cache_age > 6h)
        used_stale_cache = cache_used and cache_age_hours > 6.0
        if used_stale_cache:
            # Reset flags for this scraping session
            self.fresh_sitemap_obtained = False
            logger.info(
                "stale_cache_detected",
                cache_age_hours=cache_age_hours,
                message=f"Using stale cache ({cache_age_hours}h old) - will attempt sitemap refresh at 25%, 50%, 75%, 100% progress (will stop after first success)",
            )

        # Scrape products with global timeout (if enabled)
        try:
            scrape_task = self.scrape_products_batch(
                product_urls,
                settings.max_concurrent_requests,
                skip_processed=resume,
                used_stale_cache=used_stale_cache,
            )

            # Only apply timeout if it's enabled (timeout > 0)
            if settings.global_scraping_timeout and settings.global_scraping_timeout > 0:
                await asyncio.wait_for(scrape_task, timeout=settings.global_scraping_timeout)
            else:
                # No timeout - let it run indefinitely
                await scrape_task
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(
                "global_scraping_timeout",
                elapsed=round(elapsed, 2),
                timeout=settings.global_scraping_timeout,
                message=f"Scraping exceeded global timeout of {settings.global_scraping_timeout}s after {elapsed:.2f}s",
            )
            self.metrics.stop()
            raise TimeoutError(
                f"Scraping exceeded global timeout of {settings.global_scraping_timeout}s"
            )

        # Check elapsed time
        elapsed = time.time() - start_time
        if (
            settings.global_scraping_timeout > 0
            and elapsed > settings.global_scraping_timeout * 0.8
        ):  # Warn if > 80% of timeout
            logger.warning(
                "scraping_approaching_timeout",
                elapsed=round(elapsed, 2),
                timeout=settings.global_scraping_timeout,
                percentage=round((elapsed / settings.global_scraping_timeout) * 100, 1),
            )

        # Stop metrics tracking
        self.metrics.stop()

        # Update stats from metrics
        self.stats["products_scraped"] = self.metrics.products_scraped
        self.stats["products_failed"] = self.metrics.products_failed
        self.stats["creators_scraped"] = self.metrics.creators_scraped
        self.stats["creators_failed"] = self.metrics.creators_failed

        # Log metrics summary
        self.metrics.log_summary()

        # Log duplicate count
        if self.duplicate_count > 0:
            logger.warning(
                "duplicates_found",
                count=self.duplicate_count,
                message=f"Found {self.duplicate_count} duplicate products - DB writes were skipped for duplicates",
            )

        logger.info(
            "marketplace_scraping_completed",
            stats=self.stats,
            duplicates=self.duplicate_count,
        )

        return self.stats

    async def scrape_creator(self, url: str, skip_if_processed: bool = True) -> bool:
        """Scrape a single creator profile.

        Args:
            url: Creator profile URL
            skip_if_processed: Skip if already processed (checkpoint)

        Returns:
            True if successful, False otherwise
        """
        # Check checkpoint if enabled
        if skip_if_processed and settings.checkpoint_enabled:
            if self.checkpoint_manager.is_processed(url):
                logger.debug("creator_already_processed", url=url)
                return True

        try:
            # Scrape creator profile
            creator_data = await self.creator_scraper.scrape(url)
            if not creator_data:
                self.stats["creators_failed"] += 1
                self.metrics.record_product_failed(url=url)  # Reuse metrics for now
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_failed(url)
                return False

            # Parse creator HTML
            creator = self.creator_parser.parse(creator_data["html"], creator_data["url"])
            if not creator:
                self.stats["creators_failed"] += 1
                self.metrics.record_product_failed(url=url)
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_failed(url)
                return False

            # Deduplication check for creators
            is_duplicate_creator = False
            if creator.username in self.seen_creator_ids:
                logger.warning("duplicate_creator_id", username=creator.username, url=url)
                is_duplicate_creator = True
            else:
                self.seen_creator_ids.add(creator.username)

            # Save creator
            success = await self.storage.save_creator_json(creator)

            # Save creator to database only if not duplicate
            if not is_duplicate_creator:
                await self.db_storage.save_creator_db(creator)
            else:
                logger.warning("db_write_skipped_duplicate_creator", username=creator.username)

            if success:
                self.stats["creators_scraped"] += 1
                self.metrics.record_product_scraped()  # Reuse metrics for now
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_processed(url)
                logger.info(
                    "creator_scraped",
                    username=creator.username,
                    name=creator.name,
                )
            else:
                self.stats["creators_failed"] += 1
                self.metrics.record_product_failed(url=url)
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_failed(url)

            return success

        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                "creator_scrape_exception",
                url=url,
                error=str(e),
                error_type=error_type,
            )
            self.stats["creators_failed"] += 1
            self.metrics.record_product_failed(error_type=error_type, url=url)
            if settings.checkpoint_enabled:
                self.checkpoint_manager.add_failed(url)
            return False

    async def scrape_creators_batch(
        self, urls: List[str], limit: Optional[int] = None, skip_processed: bool = True
    ) -> None:
        """Scrape multiple creators with concurrency limit.

        Args:
            urls: List of creator profile URLs
            limit: Maximum number of concurrent requests (defaults to settings)
            skip_processed: Skip URLs that are already processed (checkpoint)
        """
        if limit is None:
            limit = settings.max_concurrent_requests

        # Filter out already processed URLs if checkpoint enabled
        if skip_processed and settings.checkpoint_enabled:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            original_count = len(urls)
            urls = [url for url in urls if url not in checkpoint["processed_urls"]]
            if original_count > len(urls):
                logger.info(
                    "skipping_processed_urls",
                    skipped=original_count - len(urls),
                    remaining=len(urls),
                )

        if not urls:
            logger.info("no_urls_to_scrape", reason="all_processed_or_limit_reached")
            return

        logger.info("starting_creators_batch_scrape", total=len(urls), concurrency_limit=limit)

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(limit)

        async def scrape_with_semaphore(url: str, index: int, total: int):
            async with semaphore:
                # Log progress every 50 creators or at milestones
                if index % 50 == 0 or index in [
                    int(total * 0.1),
                    int(total * 0.25),
                    int(total * 0.5),
                    int(total * 0.75),
                    int(total * 0.9),
                ]:
                    logger.info(
                        "scraping_creators_progress",
                        current=index + 1,
                        total=total,
                        percentage=round((index + 1) / total * 100, 2),
                    )
                return await self.scrape_creator(url, skip_if_processed=skip_processed)

        # Scrape with progress bar
        tasks = [scrape_with_semaphore(url, i, len(urls)) for i, url in enumerate(urls)]
        results = await tqdm.gather(*tasks, desc="Scraping creators")

        success_count = sum(1 for r in results if r)

        # Save final checkpoint with stats
        if settings.checkpoint_enabled:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            self.checkpoint_manager.save_checkpoint(
                checkpoint["processed_urls"],
                checkpoint["failed_urls"],
                self.stats,
            )

        logger.info(
            "creators_batch_scrape_completed",
            total=len(urls),
            success=success_count,
            failed=len(urls) - success_count,
        )

    async def scrape_creators_only(self, limit: Optional[int] = None, resume: bool = True) -> dict:
        """Scrape only creators from sitemap.

        Args:
            limit: Limit number of creators to scrape (None for all)
            resume: Resume from checkpoint if available

        Returns:
            Dictionary with scraping statistics
        """
        # Start metrics tracking
        self.metrics.start()
        logger.info("creators_scraping_started")

        # Check for existing checkpoint
        if resume and settings.checkpoint_enabled:
            resume_info = self.checkpoint_manager.get_resume_info()
            if resume_info["has_checkpoint"]:
                logger.info(
                    "checkpoint_found",
                    processed=resume_info["processed_count"],
                    failed=resume_info["failed_count"],
                    timestamp=resume_info["timestamp"],
                )

        # Get creator profile URLs from sitemap
        async with self.sitemap_scraper:
            try:
                sitemap_data, _, _ = await self.sitemap_scraper.scrape()
            except httpx.HTTPStatusError as e:
                # If marketplace sitemap returns 5xx, abort scraper
                if 500 <= e.response.status_code < 600:
                    logger.error(
                        "upstream_unavailable",
                        url=str(e.request.url),
                        status_code=e.response.status_code,
                        message="Marketplace sitemap returned 5xx - aborting scraper",
                    )
                    self.metrics.stop()
                    raise  # Propagate to main() for exit code handling
                else:
                    # Other HTTP errors - continue but log warning
                    logger.warning(
                        "sitemap_fetch_error",
                        url=str(e.request.url),
                        status_code=e.response.status_code,
                    )
                    sitemap_data = {
                        "products": {},
                        "categories": [],
                        "profiles": [],
                        "help_articles": [],
                    }
            creator_urls = sitemap_data.get("profiles", [])

        if not creator_urls:
            logger.warning("no_creators_found")
            return self.stats

        logger.info("creator_urls_found", count=len(creator_urls))

        # Apply limit if specified
        if limit:
            creator_urls = creator_urls[:limit]
            logger.info("applying_limit", limit=limit, remaining=len(creator_urls))

        # Scrape creators
        await self.scrape_creators_batch(
            creator_urls, settings.max_concurrent_requests, skip_processed=resume
        )

        # Stop metrics tracking
        self.metrics.stop()

        # Update stats from metrics (reuse for compatibility)
        self.stats["creators_scraped"] = self.metrics.products_scraped
        self.stats["creators_failed"] = self.metrics.products_failed

        # Log metrics summary
        self.metrics.log_summary()

        logger.info(
            "creators_scraping_completed",
            creators_scraped=self.stats["creators_scraped"],
            creators_failed=self.stats["creators_failed"],
        )

        return self.stats

    async def scrape_category(self, url: str, skip_if_processed: bool = True) -> bool:
        """Scrape a single category page.

        Args:
            url: Category URL
            skip_if_processed: Skip if already processed (checkpoint)

        Returns:
            True if successful, False otherwise
        """
        # Check checkpoint if enabled
        if skip_if_processed and settings.checkpoint_enabled:
            if self.checkpoint_manager.is_processed(url):
                logger.debug("category_already_processed", url=url)
                return True

        try:
            # Scrape category page
            html = await self.category_scraper.scrape_category(url)
            if not html:
                self.stats["categories_failed"] += 1
                self.metrics.record_product_failed(url=url)  # Reuse metrics for now
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_failed(url)
                return False

            # Parse category HTML
            category = self.category_parser.parse(html, url)
            if not category:
                self.stats["categories_failed"] += 1
                self.metrics.record_product_failed(url=url)
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_failed(url)
                return False

            # Save category
            success = await self.storage.save_category_json(category)
            # Save category to database
            await self.db_storage.save_category_db(category)
            if success:
                self.stats["categories_scraped"] += 1
                self.metrics.record_product_scraped()  # Reuse metrics for now
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_processed(url)
                logger.info(
                    "category_scraped",
                    slug=category.slug,
                    name=category.name,
                )
            else:
                self.stats["categories_failed"] += 1
                self.metrics.record_product_failed(url=url)
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_failed(url)

            return success

        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                "category_scrape_exception",
                url=url,
                error=str(e),
                error_type=error_type,
            )
            self.stats["categories_failed"] += 1
            self.metrics.record_product_failed(error_type=error_type, url=url)
            if settings.checkpoint_enabled:
                self.checkpoint_manager.add_failed(url)
            return False

    async def scrape_categories_batch(
        self, urls: List[str], limit: Optional[int] = None, skip_processed: bool = True
    ) -> None:
        """Scrape multiple categories with concurrency limit.

        Args:
            urls: List of category URLs
            limit: Maximum number of concurrent requests (defaults to settings)
            skip_processed: Skip URLs that are already processed (checkpoint)
        """
        if limit is None:
            limit = settings.max_concurrent_requests

        # Filter out already processed URLs if checkpoint enabled
        if skip_processed and settings.checkpoint_enabled:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            original_count = len(urls)
            urls = [url for url in urls if url not in checkpoint["processed_urls"]]
            if original_count > len(urls):
                logger.info(
                    "skipping_processed_urls",
                    skipped=original_count - len(urls),
                    remaining=len(urls),
                )

        if not urls:
            logger.info("no_urls_to_scrape", reason="all_processed_or_limit_reached")
            return

        logger.info("starting_categories_batch_scrape", total=len(urls), concurrency_limit=limit)

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(limit)

        async def scrape_with_semaphore(url: str, index: int, total: int):
            async with semaphore:
                # Log progress every 50 categories or at milestones
                if index % 50 == 0 or index in [
                    int(total * 0.1),
                    int(total * 0.25),
                    int(total * 0.5),
                    int(total * 0.75),
                    int(total * 0.9),
                ]:
                    logger.info(
                        "scraping_categories_progress",
                        current=index + 1,
                        total=total,
                        percentage=round((index + 1) / total * 100, 2),
                    )
                return await self.scrape_category(url, skip_if_processed=skip_processed)

        # Scrape with progress bar
        tasks = [scrape_with_semaphore(url, i, len(urls)) for i, url in enumerate(urls)]
        results = await tqdm.gather(*tasks, desc="Scraping categories")

        success_count = sum(1 for r in results if r)

        # Save final checkpoint with stats
        if settings.checkpoint_enabled:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            self.checkpoint_manager.save_checkpoint(
                checkpoint["processed_urls"],
                checkpoint["failed_urls"],
                self.stats,
            )

        logger.info(
            "categories_batch_scrape_completed",
            total=len(urls),
            success=success_count,
            failed=len(urls) - success_count,
        )

    async def scrape_categories_only(
        self, limit: Optional[int] = None, resume: bool = True
    ) -> dict:
        """Scrape only categories from sitemap.

        Args:
            limit: Limit number of categories to scrape (None for all)
            resume: Resume from checkpoint if available

        Returns:
            Dictionary with scraping statistics
        """
        # Start metrics tracking
        self.metrics.start()
        logger.info("categories_scraping_started")

        # Check for existing checkpoint
        if resume and settings.checkpoint_enabled:
            resume_info = self.checkpoint_manager.get_resume_info()
            if resume_info["has_checkpoint"]:
                logger.info(
                    "checkpoint_found",
                    processed=resume_info["processed_count"],
                    failed=resume_info["failed_count"],
                    timestamp=resume_info["timestamp"],
                )

        # Get category URLs from sitemap
        async with self.sitemap_scraper:
            try:
                sitemap_data, _, _ = await self.sitemap_scraper.scrape()
            except httpx.HTTPStatusError as e:
                # If marketplace sitemap returns 5xx, abort scraper
                if 500 <= e.response.status_code < 600:
                    logger.error(
                        "upstream_unavailable",
                        url=str(e.request.url),
                        status_code=e.response.status_code,
                        message="Marketplace sitemap returned 5xx - aborting scraper",
                    )
                    self.metrics.stop()
                    raise  # Propagate to main() for exit code handling
                else:
                    # Other HTTP errors - continue but log warning
                    logger.warning(
                        "sitemap_fetch_error",
                        url=str(e.request.url),
                        status_code=e.response.status_code,
                    )
                    sitemap_data = {
                        "products": {},
                        "categories": [],
                        "profiles": [],
                        "help_articles": [],
                    }
            category_urls = sitemap_data.get("categories", [])

        if not category_urls:
            logger.warning("no_categories_found")
            return self.stats

        logger.info("category_urls_found", count=len(category_urls))

        # Apply limit if specified
        if limit:
            category_urls = category_urls[:limit]
            logger.info("applying_limit", limit=limit, remaining=len(category_urls))

        # Scrape categories
        await self.scrape_categories_batch(
            category_urls, settings.max_concurrent_requests, skip_processed=resume
        )

        # Stop metrics tracking
        self.metrics.stop()

        # Update stats from metrics (reuse for compatibility)
        self.stats["categories_scraped"] = self.metrics.products_scraped
        self.stats["categories_failed"] = self.metrics.products_failed

        # Log metrics summary
        self.metrics.log_summary()

        logger.info(
            "categories_scraping_completed",
            categories_scraped=self.stats["categories_scraped"],
            categories_failed=self.stats["categories_failed"],
        )

        return self.stats
