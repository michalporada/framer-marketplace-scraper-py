"""Main entry point for the Framer Marketplace scraper."""

import asyncio
import sys

import httpx

from src.config.settings import settings
from src.scrapers.marketplace_scraper import MarketplaceScraper
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def check_robots_txt() -> bool:
    """Check robots.txt to ensure scraping is allowed.

    Returns:
        True if allowed, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(settings.robots_url)
            if response.status_code == 200:
                robots_content = response.text.lower()
                # Check if marketplace is disallowed
                # Note: robots.txt might disallow specific paths, but not the main marketplace
                # Check for explicit disallow of /marketplace (not just /marketplace/search)
                lines = robots_content.split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("disallow:"):
                        path = line.replace("disallow:", "").strip()
                        # Check if /marketplace is explicitly disallowed (not just search)
                        if path == "/marketplace" or path == "/marketplace/":
                            logger.warning("robots_txt_disallows_marketplace")
                            return False
                        # Allow /marketplace/search to be disallowed (it's in documentation)

                logger.info("robots_txt_check_passed")
                return True
    except Exception as e:
        logger.warning("robots_txt_check_failed", error=str(e))
        # Continue anyway, but log warning
        return True


async def main():
    """Main scraping function."""
    logger.info("scraper_started", version="0.1.0")

    # Check robots.txt
    if not await check_robots_txt():
        logger.error("robots_txt_disallows_scraping")
        sys.exit(1)

    # Parse command line arguments
    limit = None
    creators_only = False
    categories_only = False
    product_types = None  # List of product types to scrape
    force_rescrape = False  # Force scraping even if already processed

    if len(sys.argv) > 1:
        # Check for --creators-only flag
        if "--creators-only" in sys.argv or "-c" in sys.argv:
            creators_only = True
            sys.argv = [arg for arg in sys.argv if arg not in ["--creators-only", "-c"]]

        # Check for --categories-only flag
        if "--categories-only" in sys.argv or "-cat" in sys.argv:
            categories_only = True
            sys.argv = [arg for arg in sys.argv if arg not in ["--categories-only", "-cat"]]

        # Check for --force-rescrape flag
        if "--force-rescrape" in sys.argv or "--force" in sys.argv:
            force_rescrape = True
            sys.argv = [arg for arg in sys.argv if arg not in ["--force-rescrape", "--force"]]

        # Check for product type flags
        if "--templates-only" in sys.argv or "--template-only" in sys.argv:
            product_types = ["template"]
            sys.argv = [
                arg for arg in sys.argv if arg not in ["--templates-only", "--template-only"]
            ]
        elif "--components-only" in sys.argv or "--component-only" in sys.argv:
            product_types = ["component"]
            sys.argv = [
                arg for arg in sys.argv if arg not in ["--components-only", "--component-only"]
            ]
        elif "--vectors-only" in sys.argv or "--vector-only" in sys.argv:
            product_types = ["vector"]
            sys.argv = [arg for arg in sys.argv if arg not in ["--vectors-only", "--vector-only"]]
        elif "--plugins-only" in sys.argv or "--plugin-only" in sys.argv:
            product_types = ["plugin"]
            sys.argv = [arg for arg in sys.argv if arg not in ["--plugins-only", "--plugin-only"]]

        # Check for limit argument
        if len(sys.argv) > 1:
            try:
                limit = int(sys.argv[1])
                logger.info("limit_set", limit=limit)
            except ValueError:
                logger.warning("invalid_limit_argument", arg=sys.argv[1])

    # Run scraper
    try:
        async with MarketplaceScraper() as scraper:
            if creators_only:
                logger.info("scraping_creators_only")
                stats = await scraper.scrape_creators_only(limit=limit)
            elif categories_only:
                logger.info("scraping_categories_only")
                stats = await scraper.scrape_categories_only(limit=limit)
            else:
                if product_types:
                    logger.info("scraping_product_types", types=product_types)
                stats = await scraper.scrape(
                    limit=limit, 
                    product_types=product_types, 
                    skip_processed=not force_rescrape
                )

            if creators_only:
                logger.info(
                    "scraping_completed",
                    creators_scraped=stats["creators_scraped"],
                    creators_failed=stats["creators_failed"],
                )
            elif categories_only:
                logger.info(
                    "scraping_completed",
                    categories_scraped=stats["categories_scraped"],
                    categories_failed=stats["categories_failed"],
                )
            else:
                logger.info(
                    "scraping_completed",
                    products_scraped=stats["products_scraped"],
                    products_failed=stats["products_failed"],
                    creators_scraped=stats["creators_scraped"],
                    creators_failed=stats["creators_failed"],
                )

            # Log final metrics summary
            from src.utils.metrics import get_metrics

            metrics = get_metrics()
            metrics.log_summary()

            # Export to CSV if configured
            if settings.output_format in ["csv", "both"]:
                logger.info("exporting_to_csv")
                storage = scraper.storage
                storage.export_products_to_csv()

    except KeyboardInterrupt:
        logger.info("scraping_interrupted_by_user")
        sys.exit(1)
    except Exception as e:
        logger.error(
            "scraping_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        sys.exit(1)

    logger.info("scraper_finished")


if __name__ == "__main__":
    asyncio.run(main())
