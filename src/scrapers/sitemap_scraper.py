"""Sitemap scraper for extracting product URLs from sitemap.xml."""

import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx

from src.config.settings import settings
from src.utils.logger import get_logger
from src.utils.retry import retry_async
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

    async def fetch_sitemap(self, url: str) -> Optional[bytes]:
        """Fetch sitemap XML content.

        Args:
            url: URL to sitemap.xml

        Returns:
            Sitemap XML content or None if failed
        """
        try:
            logger.info("fetching_sitemap", url=url)
            response = await self.client.get(url)
            response.raise_for_status()
            logger.info("sitemap_fetched", url=url, status_code=response.status_code)
            return response.content
        except httpx.HTTPStatusError as e:
            logger.warning("sitemap_fetch_failed", url=url, status_code=e.response.status_code)
            return None
        except Exception as e:
            logger.error("sitemap_fetch_error", url=url, error=str(e))
            return None

    async def get_sitemap(self) -> Optional[bytes]:
        """Get sitemap with fallback mechanism.

        Tries marketplace sitemap first, then falls back to main sitemap.

        Returns:
            Sitemap XML content or None if both fail
        """
        # Try marketplace sitemap first
        content = await self.fetch_sitemap(settings.sitemap_url)
        if content:
            return content

        # Fallback to main sitemap
        logger.info("falling_back_to_main_sitemap", url=settings.main_sitemap_url)
        content = await self.fetch_sitemap(settings.main_sitemap_url)
        if content:
            return content

        logger.error("both_sitemaps_failed")
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
                if "/@" in url or url.startswith("https://www.framer.com/@") or url.startswith(
                    "http://www.framer.com/@"
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
                if (
                    "/marketplace/vectors/" in url
                    and url.endswith("/")
                    and "/category/" not in url
                ):
                    result["products"]["vectors"].append(url)
                    continue

                # Plugins (nowy typ)
                if (
                    "/marketplace/plugins/" in url
                    and url.endswith("/")
                    and "/category/" not in url
                ):
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
        """
        # Get sitemap content
        xml_content = await self.get_sitemap()
        if xml_content is None:
            logger.error("sitemap_fetch_failed_all_attempts")
            return {"products": {}, "categories": [], "profiles": [], "help_articles": []}

        # Parse sitemap
        parsed = self.parse_sitemap(xml_content)
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

