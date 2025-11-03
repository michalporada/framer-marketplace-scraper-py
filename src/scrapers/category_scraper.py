"""Category scraper for fetching category pages."""

from typing import Optional

import httpx

from src.config.settings import settings
from src.utils.logger import get_logger
from src.utils.retry import retry_on_network_error
from src.utils.user_agents import get_random_user_agent

logger = get_logger(__name__)


class CategoryScraper:
    """Scraper for category pages."""

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """Initialize category scraper.

        Args:
            client: Optional httpx.AsyncClient instance
        """
        self.client = client
        self.timeout = settings.timeout

    async def scrape_category(self, category_url: str) -> Optional[str]:
        """Scrape a category page.

        Args:
            category_url: Category URL (e.g., /marketplace/category/templates/)

        Returns:
            HTML content or None if failed
        """
        # Make full URL if needed
        if category_url.startswith("/"):
            full_url = f"{settings.base_url}{category_url}"
        else:
            full_url = category_url

        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        try:
            if self.client:
                response = await self.client.get(full_url, headers=headers, timeout=self.timeout)
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.get(full_url, headers=headers, timeout=self.timeout)

            response.raise_for_status()
            logger.info("category_scraped", url=category_url, status_code=response.status_code)
            return response.text

        except httpx.HTTPError as e:
            logger.error("category_scrape_error", url=category_url, error=str(e))
            return None

    @retry_on_network_error(max_retries=3)
    async def scrape_category_with_retry(self, category_url: str) -> Optional[str]:
        """Scrape a category page with retry logic.

        Args:
            category_url: Category URL

        Returns:
            HTML content or None if failed
        """
        return await self.scrape_category(category_url)

