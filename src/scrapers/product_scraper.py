"""Product scraper for fetching individual product pages."""

from typing import Optional
from urllib.parse import urlparse

import httpx

from src.config.settings import settings
from src.utils.logger import get_logger
from src.utils.rate_limiter import get_rate_limiter
from src.utils.retry import retry_async
from src.utils.user_agents import get_random_user_agent

logger = get_logger(__name__)


class ProductScraper:
    """Scraper for individual product pages."""

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """Initialize product scraper.

        Args:
            client: Optional httpx async client (will create one if not provided)
        """
        self.client = client
        self._should_close_client = client is None
        self.rate_limiter = get_rate_limiter()

    async def __aenter__(self):
        """Async context manager entry."""
        if self.client is None:
            timeout = httpx.Timeout(settings.timeout)
            self.client = httpx.AsyncClient(
                timeout=timeout,
                headers={"User-Agent": get_random_user_agent()},
                follow_redirects=True,
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._should_close_client and self.client:
            await self.client.aclose()

    def extract_product_type_from_url(self, url: str) -> Optional[str]:
        """Extract product type from URL.

        Args:
            url: Product URL

        Returns:
            Product type (template, component, vector, plugin) or None
        """
        url_lower = url.lower()
        if "/marketplace/templates/" in url_lower:
            return "template"
        elif "/marketplace/components/" in url_lower:
            return "component"
        elif "/marketplace/vectors/" in url_lower:
            return "vector"
        elif "/marketplace/plugins/" in url_lower:
            return "plugin"
        return None

    def extract_product_id_from_url(self, url: str) -> str:
        """Extract product ID/name from URL.

        Args:
            url: Product URL

        Returns:
            Product ID (last segment of URL)
        """
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        # Extract last segment (product name)
        segments = [s for s in path.split("/") if s]
        if segments:
            return segments[-1]
        return "unknown"

    async def fetch_product_page(self, url: str) -> Optional[str]:
        """Fetch product page HTML with retry and rate limiting.

        Args:
            url: Product URL

        Returns:
            HTML content or None if failed
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()

            # Retry logic with exponential backoff
            async def _fetch():
                logger.debug("fetching_product", url=url)
                response = await self.client.get(url)
                response.raise_for_status()
                logger.debug("product_fetched", url=url, status_code=response.status_code)
                return response.text

            html_content = await retry_async(_fetch)
            return html_content

        except httpx.HTTPStatusError as e:
            logger.warning(
                "product_fetch_failed",
                url=url,
                status_code=e.response.status_code,
            )
            return None
        except Exception as e:
            logger.error("product_fetch_error", url=url, error=str(e), error_type=type(e).__name__)
            return None

    async def scrape(self, url: str) -> Optional[dict]:
        """Scrape a product page.

        Args:
            url: Product URL

        Returns:
            Dictionary with:
            - url: Product URL
            - html: HTML content
            - type: Product type (template/component/vector/plugin)
            - id: Product ID
            or None if failed
        """
        html = await self.fetch_product_page(url)
        if html is None:
            return None

        product_type = self.extract_product_type_from_url(url)
        product_id = self.extract_product_id_from_url(url)

        return {
            "url": url,
            "html": html,
            "type": product_type,
            "id": product_id,
        }
