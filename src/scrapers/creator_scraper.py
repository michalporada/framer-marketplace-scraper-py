"""Creator scraper for fetching user profile pages."""

import re
from typing import Optional

import httpx

from src.config.settings import settings
from src.utils.logger import get_logger
from src.utils.rate_limiter import get_rate_limiter
from src.utils.retry import retry_async
from src.utils.user_agents import get_random_user_agent

logger = get_logger(__name__)


class CreatorScraper:
    """Scraper for creator/user profile pages."""

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """Initialize creator scraper.

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

    def extract_username_from_url(self, url: str) -> Optional[str]:
        """Extract username from profile URL.

        Args:
            url: Profile URL (e.g., https://www.framer.com/@ev-studio/ or /@-790ivi/)

        Returns:
            Username (without @) or None
        """
        # Pattern: /@{username}/ or https://.../@{username}/
        pattern = r"/@([^/]+)/?"
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None

    def normalize_profile_url(self, url: str) -> str:
        """Normalize profile URL to full URL format.

        Args:
            url: Profile URL (may be relative or absolute, or HttpUrl object)

        Returns:
            Normalized full URL
        """
        # Convert HttpUrl to string if needed
        url_str = str(url)

        if url_str.startswith("http"):
            return url_str.rstrip("/")
        elif url_str.startswith("/@"):
            return f"{settings.base_url}{url_str}".rstrip("/")
        elif url_str.startswith("@"):
            return f"{settings.base_url}/{url_str}".rstrip("/")
        else:
            return f"{settings.base_url}/@{url_str}".rstrip("/")

    async def fetch_profile_page(self, url: str) -> Optional[str]:
        """Fetch profile page HTML with retry and rate limiting.

        Args:
            url: Profile URL (may be relative like /@username/ or full URL)

        Returns:
            HTML content or None if failed
        """
        try:
            # Normalize URL
            normalized_url = self.normalize_profile_url(url)

            # Rate limiting
            await self.rate_limiter.acquire()

            # Retry logic with exponential backoff
            async def _fetch():
                logger.debug("fetching_profile", url=normalized_url)
                response = await self.client.get(normalized_url)
                response.raise_for_status()
                logger.debug(
                    "profile_fetched", url=normalized_url, status_code=response.status_code
                )
                return response.text

            html_content = await retry_async(_fetch)
            return html_content

        except httpx.HTTPStatusError as e:
            logger.warning(
                "profile_fetch_failed",
                url=url,
                status_code=e.response.status_code,
            )
            return None
        except Exception as e:
            logger.error("profile_fetch_error", url=url, error=str(e), error_type=type(e).__name__)
            return None

    async def scrape(self, url: str) -> Optional[dict]:
        """Scrape a creator profile page.

        Args:
            url: Profile URL (may be relative like /@username/ or full URL)

        Returns:
            Dictionary with:
            - url: Normalized profile URL
            - html: HTML content
            - username: Extracted username
            or None if failed
        """
        normalized_url = self.normalize_profile_url(url)
        html = await self.fetch_profile_page(normalized_url)
        if html is None:
            return None

        username = self.extract_username_from_url(normalized_url)

        return {
            "url": normalized_url,
            "html": html,
            "username": username,
        }
