"""Main marketplace scraper orchestrator."""

import asyncio
from typing import List, Optional

import httpx
from tqdm.asyncio import tqdm

from src.config.settings import settings
from src.parsers.product_parser import ProductParser
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
        self.product_parser = ProductParser()
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

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def scrape_product(self, url: str, skip_if_processed: bool = True) -> bool:
        """Scrape a single product.

        Args:
            url: Product URL
            skip_if_processed: Skip if already processed (checkpoint)

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
                # TODO: Parse creator data when creator_parser is implemented
                # if creator_data:
                #     creator = self.creator_parser.parse(...)
                #     product.creator = creator

            # Save product
            success = await self.storage.save_product_json(product)
            if success:
                self.stats["products_scraped"] += 1
                self.metrics.record_product_scraped()
                # Mark as processed in checkpoint
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
        self, urls: List[str], limit: Optional[int] = None, skip_processed: bool = True
    ) -> None:
        """Scrape multiple products with concurrency limit.

        Args:
            urls: List of product URLs
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

        if limit:
            urls = urls[:limit] if limit else urls

        if not urls:
            logger.info("no_urls_to_scrape", reason="all_processed_or_limit_reached")
            return

        logger.info("starting_batch_scrape", total=len(urls), limit=limit)

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(limit)

        async def scrape_with_semaphore(url: str):
            async with semaphore:
                return await self.scrape_product(url, skip_if_processed=skip_processed)

        # Scrape with progress bar
        tasks = [scrape_with_semaphore(url) for url in urls]
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

    async def scrape(self, limit: Optional[int] = None, resume: bool = True) -> dict:
        """Main scraping method.

        Args:
            limit: Limit number of products to scrape (None for all)
            resume: Resume from checkpoint if available

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
            product_urls = self.sitemap_scraper.filter_urls_by_type(
                sitemap_data, settings.get_product_types()
            )

        if not product_urls:
            logger.warning("no_products_found")
            return self.stats

        logger.info("product_urls_found", count=len(product_urls))

        # Apply limit if specified
        if limit:
            product_urls = product_urls[:limit]
            logger.info("applying_limit", limit=limit, remaining=len(product_urls))

        # Scrape products
        await self.scrape_products_batch(product_urls, settings.max_concurrent_requests, skip_processed=resume)

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

