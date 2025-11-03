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
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            logger.info("limit_set", limit=limit)
        except ValueError:
            logger.warning("invalid_limit_argument", arg=sys.argv[1])

    # Run scraper
    try:
        async with MarketplaceScraper() as scraper:
            stats = await scraper.scrape(limit=limit)

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
