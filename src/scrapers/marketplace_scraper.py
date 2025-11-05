"""Main marketplace scraper orchestrator."""

import asyncio
from typing import List, Optional

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

    async def __aenter__(self):
        """Async context manager entry."""
        timeout = httpx.Timeout(settings.timeout)
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
        )

        self.sitemap_scraper = SitemapScraper(self.client)
        self.product_scraper = ProductScraper(self.client)
        self.creator_scraper = CreatorScraper(self.client)
        self.category_scraper = CategoryScraper(self.client)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def scrape_product(self, url: str, skip_if_processed: bool = False) -> bool:
        """Scrape a single product.

        Args:
            url: Product URL
            skip_if_processed: Skip if already processed (default: False - always update)

        Returns:
            True if successful, False otherwise
            
        Note:
            By default, we always scrape products to update views, prices, stats, etc.
            Checkpoint is only used for tracking failures, not for skipping updates.
            This ensures we always have the latest data (views, prices, positions, etc.).
        """
        # Always scrape products to update views, prices, stats, etc.
        # Only skip if explicitly requested (for testing or partial updates)
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

            # Get category positions for each category (only for templates)
            if product.type == "template" and product.categories:
                for category in product.categories:
                    # Convert category name to URL slug (lowercase, replace spaces with hyphens, etc.)
                    # Category names from product page might be "Non-profit" but URL needs "non-profit"
                    category_slug = category.lower().replace(" ", "-").replace("&", "").strip()
                    
                    # Build category URL - try both formats (redirects to /marketplace/templates/category/{category}/)
                    category_urls = [
                        f"/marketplace/category/{category_slug}/",
                        f"/marketplace/templates/category/{category_slug}/",
                    ]
                    category_html = None
                    for category_url in category_urls:
                        category_html = await self.category_scraper.scrape_category(category_url)
                        if category_html:
                            break
                    
                    if category_html:
                        # Find product position in category
                        position = self.category_parser.find_product_position(category_html, str(product.url))
                        if position:
                            product.category_positions[category] = position
                            logger.info(
                                "category_position_found",
                                product_id=product.id,
                                category=category,
                                position=position,
                            )
                        else:
                            logger.debug(
                                "category_position_not_found",
                                product_id=product.id,
                                category=category,
                            )

            # Save product (always overwrites to update views, prices, stats, etc.)
            success = await self.storage.save_product_json(product)
            if success:
                self.stats["products_scraped"] += 1
                self.metrics.record_product_scraped()
                # Mark as processed in checkpoint (for tracking, not for skipping)
                # We always update products to track changes in views, prices, etc.
                if settings.checkpoint_enabled:
                    self.checkpoint_manager.add_processed(url)
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

    async def scrape_products_batch(
        self, urls: List[str], limit: Optional[int] = None, skip_processed: bool = False
    ) -> None:
        """Scrape multiple products with concurrency limit.

        Args:
            urls: List of product URLs
            limit: Maximum number of concurrent requests (defaults to settings)
            skip_processed: Skip URLs that are already processed (default: False - always update)
            
        Note:
            By default, we always scrape all products to update views, prices, stats, etc.
            Set skip_processed=True only if you want to skip already processed URLs.
        """
        if limit is None:
            limit = settings.max_concurrent_requests

        # Always scrape all products to update views, prices, stats, etc.
        # Only skip if explicitly requested (for testing or partial updates)
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
        else:
            logger.debug(
                "updating_all_products",
                total=len(urls),
                note="All products will be updated with latest data (views, prices, stats, etc.)",
            )

        if not urls:
            logger.info("no_urls_to_scrape", reason="all_processed_or_limit_reached")
            return

        logger.info("starting_batch_scrape", total=len(urls), concurrency_limit=limit)

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(limit)

        async def scrape_with_semaphore(url: str, index: int, total: int):
            async with semaphore:
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
                        percentage=round((index + 1) / total * 100, 2),
                    )
                # Always update products (skip_if_processed=False) to get latest views, prices, etc.
                return await self.scrape_product(url, skip_if_processed=False)

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
        skip_processed: bool = True,
    ) -> dict:
        """Main scraping method.

        Args:
            limit: Limit number of products to scrape (None for all)
            resume: Resume from checkpoint if available
            product_types: List of product types to scrape (None uses settings)

        Returns:
            Dictionary with scraping statistics
        """
        # Start metrics tracking
        self.metrics.start()
        logger.info("marketplace_scraping_started")

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

        # Get product URLs from sitemap
        async with self.sitemap_scraper:
            sitemap_data = await self.sitemap_scraper.scrape()
            # Use provided product types or fall back to settings
            types_to_scrape = (
                product_types if product_types is not None else settings.get_product_types()
            )
            product_urls = self.sitemap_scraper.filter_urls_by_type(sitemap_data, types_to_scrape)

        if not product_urls:
            logger.warning("no_products_found")
            return self.stats

        logger.info("product_urls_found", count=len(product_urls))

        # Apply limit if specified
        if limit:
            product_urls = product_urls[:limit]
            logger.info("applying_limit", limit=limit, remaining=len(product_urls))

        # Scrape products - always update all to track changes in views, prices, stats, etc.
        # skip_processed is only used for force_rescrape flag (which forces full rescrape)
        # By default, we always update all products
        await self.scrape_products_batch(
            product_urls, settings.max_concurrent_requests, skip_processed=False
        )

        # Retry failed URLs at the end
        if settings.checkpoint_enabled:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            failed_urls = list(checkpoint.get("failed_urls", []))
            if failed_urls:
                logger.info(
                    "retrying_failed_urls",
                    count=len(failed_urls),
                    note="Retrying previously failed URLs at the end of scraping",
                )
                # Retry failed URLs with lower concurrency to avoid overwhelming the server
                retry_limit = min(settings.max_concurrent_requests, 3)  # Max 3 concurrent for retries
                await self.scrape_products_batch(
                    failed_urls, retry_limit, skip_processed=False
                )
                
                # Check which URLs were successfully processed after retry
                checkpoint_after_retry = self.checkpoint_manager.load_checkpoint()
                processed_after_retry = checkpoint_after_retry.get("processed_urls", [])
                if not isinstance(processed_after_retry, set):
                    processed_after_retry = set(processed_after_retry)
                
                # Remove successfully retried URLs from failed list
                successful_retries = []
                for url in failed_urls:
                    if url in processed_after_retry:
                        successful_retries.append(url)
                        self.checkpoint_manager.remove_failed(url)
                
                if successful_retries:
                    logger.info(
                        "retry_success",
                        retried=len(failed_urls),
                        successful=len(successful_retries),
                        still_failed=len(failed_urls) - len(successful_retries),
                    )
                else:
                    logger.warning(
                        "retry_no_success",
                        retried=len(failed_urls),
                        note="All retries failed, URLs remain in failed list",
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

        logger.info(
            "marketplace_scraping_completed",
            stats=self.stats,
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

            # Save creator
            success = await self.storage.save_creator_json(creator)
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
            sitemap_data = await self.sitemap_scraper.scrape()
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
            sitemap_data = await self.sitemap_scraper.scrape()
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
