"""Sitemap scraper for extracting product URLs from sitemap.xml."""

import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from src.config.settings import settings
from src.utils.logger import get_logger
from src.utils.user_agents import get_random_user_agent

logger = get_logger(__name__)


class SitemapScraper:
    """Scraper for sitemap.xml files."""

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """Initialize sitemap scraper.

        Args:
            client: Optional httpx async client (will create one if not provided)
        """
        self.client = client
        self._should_close_client = client is None

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

    async def fetch_sitemap(self, url: str, retry_on_502: bool = True) -> Optional[bytes]:
        """Fetch sitemap XML content with retry logic for 502 errors.

        Args:
            url: URL to sitemap.xml
            retry_on_502: Whether to retry on 502 Bad Gateway errors (default: True)

        Returns:
            Sitemap XML content or None if failed

        Raises:
            httpx.HTTPStatusError: If marketplace sitemap returns 5xx error (after retries)
        """
        from src.utils.retry import retry_async

        async def _fetch():
            logger.info("fetching_sitemap", url=url)
            response = await self.client.get(url)
            response.raise_for_status()
            logger.info("sitemap_fetched", url=url, status_code=response.status_code)
            return response.content

        try:
            # For marketplace sitemap, retry on 502 errors (temporary Framer issues)
            if retry_on_502 and "marketplace" in url:
                try:
                    # Retry with exponential backoff + jitter (uses settings.max_retries)
                    # retry_async catches all exceptions by default, including HTTPStatusError
                    content = await retry_async(
                        _fetch,
                        max_retries=settings.max_retries,
                        initial_wait=settings.retry_initial_wait,
                        max_wait=settings.retry_max_wait,
                    )
                    return content
                except httpx.HTTPStatusError as e:
                    # If marketplace sitemap returns 5xx after retries, fail immediately
                    if 500 <= e.response.status_code < 600:
                        logger.error(
                            "sitemap_fetch_failed_5xx",
                            url=url,
                            status_code=e.response.status_code,
                            message="Marketplace sitemap returned 5xx error - aborting scraper run",
                        )
                        raise  # Re-raise to abort scraper
                    else:
                        logger.warning(
                            "sitemap_fetch_failed_after_retries",
                            url=url,
                            status_code=e.response.status_code,
                        )
                        return None
                except Exception as e:
                    logger.warning(
                        "sitemap_fetch_failed_after_retries",
                        url=url,
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    return None
            else:
                # For other sitemaps, no retry
                return await _fetch()
        except httpx.HTTPStatusError as e:
            # Re-raise 5xx errors for marketplace sitemap (they should be handled upstream)
            if 500 <= e.response.status_code < 600 and "marketplace" in url:
                raise
            logger.warning("sitemap_fetch_failed", url=url, status_code=e.response.status_code)
            return None
        except Exception as e:
            logger.error("sitemap_fetch_error", url=url, error=str(e))
            return None

    def _load_cached_sitemap(self) -> Optional[bytes]:
        """Load cached sitemap if available and not expired.

        Returns:
            Cached sitemap content or None if cache is missing/expired
        """
        if not settings.sitemap_cache_enabled:
            return None

        cache_path = Path(settings.sitemap_cache_file)
        if not cache_path.exists():
            return None

        # Check cache age
        cache_age = time.time() - cache_path.stat().st_mtime
        if cache_age > settings.sitemap_cache_max_age:
            logger.debug(
                "sitemap_cache_expired",
                age=round(cache_age, 2),
                max_age=settings.sitemap_cache_max_age,
            )
            return None

        try:
            with open(cache_path, "rb") as f:
                content = f.read()
            logger.info("sitemap_cache_loaded", cache_age=round(cache_age, 2), size=len(content))
            return content
        except Exception as e:
            logger.warning("sitemap_cache_load_error", error=str(e))
            return None

    def _save_cached_sitemap(self, content: bytes) -> None:
        """Save sitemap to cache.

        Args:
            content: Sitemap XML content
        """
        if not settings.sitemap_cache_enabled:
            return

        try:
            cache_path = Path(settings.sitemap_cache_file)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "wb") as f:
                f.write(content)
            logger.info("sitemap_cache_saved", path=str(cache_path), size=len(content))
        except Exception as e:
            logger.warning("sitemap_cache_save_error", error=str(e))

    async def get_sitemap(self) -> Optional[bytes]:
        """Get marketplace sitemap with cache support.

        Tries marketplace sitemap first. If upstream fails (non-5xx), uses cache.
        If marketplace sitemap returns 5xx, raises exception to abort scraper.

        Returns:
            Sitemap XML content or None if failed (non-5xx errors)

        Raises:
            httpx.HTTPStatusError: If marketplace sitemap returns 5xx error
        """
        # Try marketplace sitemap first
        try:
            content = await self.fetch_sitemap(settings.sitemap_url)
            if content:
                # Save to cache on success
                self._save_cached_sitemap(content)
                return content
        except httpx.HTTPStatusError as e:
            # For 5xx errors, don't use cache - fail immediately
            if 500 <= e.response.status_code < 600:
                raise
            # For other HTTP errors, try cache
            logger.warning("sitemap_fetch_failed_trying_cache", status_code=e.response.status_code)
        except Exception as e:
            logger.warning("sitemap_fetch_error_trying_cache", error=str(e))

        # If fetch failed (non-5xx), try cache
        cached_content = self._load_cached_sitemap()
        if cached_content:
            logger.info(
                "using_cached_sitemap", message="Using cached sitemap due to upstream failure"
            )
            return cached_content

        logger.error("marketplace_sitemap_failed_no_cache", url=settings.sitemap_url)
        return None

    def parse_sitemap(self, xml_content: bytes) -> Dict[str, List[str]]:
        """Parse sitemap XML and extract URLs by type.

        Args:
            xml_content: Sitemap XML content

        Returns:
            Dictionary with categorized URLs:
            {
                'products': {
                    'templates': [...],
                    'components': [...],
                    'vectors': [...],
                    'plugins': [...]
                },
                'categories': [...],
                'profiles': [...],
                'help_articles': [...]
            }
        """
        try:
            root = ET.fromstring(xml_content)
            namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            result: Dict[str, any] = {
                "products": defaultdict(list),
                "categories": [],
                "profiles": [],
                "help_articles": [],
            }

            for url_elem in root.findall(".//sitemap:url", namespace):
                loc_elem = url_elem.find("sitemap:loc", namespace)
                if loc_elem is None:
                    continue

                url = loc_elem.text
                if not url:
                    continue

                # Profile użytkowników (wszystko zaczynające się od @)
                if (
                    "/@" in url
                    or url.startswith("https://www.framer.com/@")
                    or url.startswith("http://www.framer.com/@")
                ):
                    result["profiles"].append(url)
                    continue

                # Kategorie
                if "/marketplace/category/" in url:
                    result["categories"].append(url)
                    continue

                # Produkty - rozróżnij typy
                # Templates: /marketplace/templates/{nazwa}/ (kończy się na /, nie zawiera /category/)
                if (
                    "/marketplace/templates/" in url
                    and url.endswith("/")
                    and "/category/" not in url
                ):
                    result["products"]["templates"].append(url)
                    continue

                # Components
                if (
                    "/marketplace/components/" in url
                    and url.endswith("/")
                    and "/category/" not in url
                ):
                    result["products"]["components"].append(url)
                    continue

                # Vectors
                if "/marketplace/vectors/" in url and url.endswith("/") and "/category/" not in url:
                    result["products"]["vectors"].append(url)
                    continue

                # Plugins (nowy typ)
                if "/marketplace/plugins/" in url and url.endswith("/") and "/category/" not in url:
                    result["products"]["plugins"].append(url)
                    continue

                # Strony pomocowe związane z marketplace
                if "/help/articles/" in url and "marketplace" in url.lower():
                    result["help_articles"].append(url)
                    continue

            # Convert defaultdict to regular dict
            result["products"] = dict(result["products"])

            logger.info(
                "sitemap_parsed",
                templates=len(result["products"].get("templates", [])),
                components=len(result["products"].get("components", [])),
                vectors=len(result["products"].get("vectors", [])),
                plugins=len(result["products"].get("plugins", [])),
                categories=len(result["categories"]),
                profiles=len(result["profiles"]),
                help_articles=len(result["help_articles"]),
            )

            return result

        except ET.ParseError as e:
            logger.error("sitemap_parse_error", error=str(e))
            return {"products": {}, "categories": [], "profiles": [], "help_articles": []}
        except Exception as e:
            logger.error("sitemap_parse_exception", error=str(e), error_type=type(e).__name__)
            return {"products": {}, "categories": [], "profiles": [], "help_articles": []}

    def filter_urls_by_type(
        self, parsed_sitemap: Dict[str, any], product_types: Optional[List[str]] = None
    ) -> List[str]:
        """Filter product URLs by type.

        Args:
            parsed_sitemap: Parsed sitemap dictionary
            product_types: List of product types to include (defaults to settings)

        Returns:
            List of product URLs matching the specified types
        """
        if product_types is None:
            product_types = settings.get_product_types()

        urls = []
        products = parsed_sitemap.get("products", {})

        # Handle both dict and defaultdict formats
        if isinstance(products, dict):
            for product_type in product_types:
                # Map product type to plural form used in sitemap
                type_key_map = {
                    "template": "templates",
                    "component": "components",
                    "vector": "vectors",
                    "plugin": "plugins",
                }
                type_key = type_key_map.get(product_type, product_type)

                if type_key in products:
                    type_urls = products[type_key]
                    if isinstance(type_urls, list):
                        urls.extend(type_urls)
                    elif isinstance(type_urls, str):
                        urls.append(type_urls)

        logger.info("urls_filtered", count=len(urls), types=product_types)
        return urls

    async def scrape(self) -> Dict[str, List[str]]:
        """Main method to scrape sitemap.

        Returns:
            Dictionary with categorized URLs

        Raises:
            httpx.HTTPStatusError: If marketplace sitemap returns 5xx error
            ValueError: If sitemap parsing fails or returns empty/invalid data
        """
        # Get sitemap content
        # This may raise HTTPStatusError for 5xx errors (no fallback)
        xml_content = await self.get_sitemap()
        if xml_content is None:
            logger.error("sitemap_fetch_failed_all_attempts")
            return {"products": {}, "categories": [], "profiles": [], "help_articles": []}

        # Parse sitemap
        parsed = self.parse_sitemap(xml_content)

        # Verify sitemap parsing was successful
        total_urls = (
            sum(len(urls) for urls in parsed.get("products", {}).values())
            + len(parsed.get("categories", []))
            + len(parsed.get("profiles", []))
            + len(parsed.get("help_articles", []))
        )

        if total_urls == 0:
            logger.error(
                "sitemap_parse_verification_failed",
                message="Sitemap parsed but contains no URLs - aborting scraper",
            )
            raise ValueError("Sitemap parsing returned empty result - no URLs found")

        logger.info(
            "sitemap_parse_verified",
            total_urls=total_urls,
            products=sum(len(urls) for urls in parsed.get("products", {}).values()),
            categories=len(parsed.get("categories", [])),
            profiles=len(parsed.get("profiles", [])),
        )

        return parsed

    async def get_product_urls(self, product_types: Optional[List[str]] = None) -> List[str]:
        """Get filtered list of product URLs.

        Args:
            product_types: List of product types to include

        Returns:
            List of product URLs
        """
        parsed = await self.scrape()
        return self.filter_urls_by_type(parsed, product_types)
