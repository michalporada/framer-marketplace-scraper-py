"""Sitemap scraper for extracting product URLs from sitemap.xml."""

import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

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
        """Fetch sitemap XML content with retry.

        Args:
            url: URL to sitemap.xml

        Returns:
            Sitemap XML content or None if failed
        """
        async def _fetch():
            logger.info("fetching_sitemap", url=url)
            response = await self.client.get(url)
            response.raise_for_status()
            logger.info("sitemap_fetched", url=url, status_code=response.status_code)
            return response.content
        
        try:
            content = await retry_async(_fetch)
            return content
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

    def parse_sitemap(self, xml_content: bytes) -> Dict[str, Any]:
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

            result: Dict[str, Any] = {
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

                # User profiles (everything starting with @)
                if (
                    "/@" in url
                    or url.startswith("https://www.framer.com/@")
                    or url.startswith("http://www.framer.com/@")
                ):
                    result["profiles"].append(url)
                    continue

                # Categories
                if "/marketplace/category/" in url:
                    result["categories"].append(url)
                    continue

                # Products - distinguish types
                # Templates: /marketplace/templates/{name}/ (ends with /, doesn't contain /category/)
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

                # Plugins (new type)
                if "/marketplace/plugins/" in url and url.endswith("/") and "/category/" not in url:
                    result["products"]["plugins"].append(url)
                    continue

                # Help pages related to marketplace
                if "/help/articles/" in url and "marketplace" in url.lower():
                    result["help_articles"].append(url)
                    continue

            # Convert defaultdict to regular dict
            result["products"] = dict(result["products"])

            total_products = (
                len(result["products"].get("templates", []))
                + len(result["products"].get("components", []))
                + len(result["products"].get("vectors", []))
                + len(result["products"].get("plugins", []))
            )
            logger.info(
                "sitemap_parsed",
                templates=len(result["products"].get("templates", [])),
                components=len(result["products"].get("components", [])),
                vectors=len(result["products"].get("vectors", [])),
                plugins=len(result["products"].get("plugins", [])),
                total_products=total_products,
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
        self, parsed_sitemap: Dict[str, Any], product_types: Optional[List[str]] = None
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
        urls = self.filter_urls_by_type(parsed, product_types)
        
        # Fallback: If no products found in sitemap, try scraping from marketplace pages
        if not urls:
            logger.warning("no_products_in_sitemap_fallback_to_marketplace_pages")
            urls = await self._scrape_product_urls_from_marketplace_pages(product_types)
        else:
            # Supplement: Use fallback to find additional products not in sitemap
            # This helps catch products that might be missing from sitemap
            logger.info("sitemap_products_found_supplementing_with_marketplace_pages", count=len(urls))
            fallback_urls = await self._scrape_product_urls_from_marketplace_pages(product_types)
            # Merge, keeping sitemap URLs as primary
            sitemap_urls_set = set(urls)
            for fallback_url in fallback_urls:
                if fallback_url not in sitemap_urls_set:
                    urls.append(fallback_url)
                    logger.debug("fallback_product_not_in_sitemap", url=fallback_url)
            
            if len(fallback_urls) > 0:
                logger.info(
                    "supplemented_with_fallback",
                    sitemap_count=len(sitemap_urls_set),
                    fallback_count=len(fallback_urls),
                    total_count=len(urls),
                    new_products_found=len(urls) - len(sitemap_urls_set),
                )
        
        return urls
    
    async def _scrape_product_urls_from_marketplace_pages(
        self, product_types: Optional[List[str]] = None
    ) -> List[str]:
        """Fallback: Scrape product URLs from marketplace via categories.
        
        This method is used when sitemap doesn't contain products (e.g., 502 error).
        It scrapes categories first, then extracts all products from each category.
        This is more reliable than pagination since Framer uses infinite scroll.
        
        Args:
            product_types: List of product types to scrape
            
        Returns:
            List of product URLs
        """
        if product_types is None:
            product_types = settings.get_product_types()
        
        product_urls = []
        seen_urls = set()
        
        # Map product types to marketplace URLs
        type_to_url = {
            "template": "https://www.framer.com/marketplace/templates/",
            "component": "https://www.framer.com/marketplace/components/",
            "vector": "https://www.framer.com/marketplace/vectors/",
            "plugin": "https://www.framer.com/marketplace/plugins/",
        }
        
        async def find_categories(marketplace_url: str, product_type: str) -> List[str]:
            """Find all category URLs from marketplace page."""
            category_urls = []
            try:
                async def _fetch():
                    response = await self.client.get(marketplace_url)
                    response.raise_for_status()
                    return response.text
                
                html = await retry_async(_fetch)
                soup = BeautifulSoup(html, "lxml")
                
                # Find category links - pattern: /marketplace/{type}s/category/{slug}/
                category_pattern = rf"/marketplace/{product_type}s/category/[^/]+/"
                category_links = soup.find_all("a", href=re.compile(category_pattern))
                
                for link in category_links:
                    href = link.get("href", "")
                    if href:
                        if href.startswith("/"):
                            full_url = f"https://www.framer.com{href}"
                        else:
                            full_url = href
                        if full_url not in category_urls:
                            category_urls.append(full_url)
                
                logger.info(
                    "fallback_categories_found",
                    type=product_type,
                    count=len(category_urls),
                )
                
            except Exception as e:
                logger.warning(
                    "fallback_category_discovery_failed",
                    url=marketplace_url,
                    type=product_type,
                    error=str(e),
                )
            
            return category_urls
        
        async def scrape_category_page(category_url: str, product_type: str) -> List[str]:
            """Scrape all products from a category page.
            
            Uses multiple strategies:
            1. Extract from __NEXT_DATA__ JSON (most complete - includes all products)
            2. Extract from HTML product cards (fallback)
            3. Extract from all links matching pattern (fallback)
            """
            page_urls = []
            try:
                async def _fetch():
                    response = await self.client.get(category_url)
                    response.raise_for_status()
                    return response.text
                
                html = await retry_async(_fetch)
                
                # Strategy 1: Try to extract from __NEXT_DATA__ JSON (Next.js embeds data here)
                # This is more reliable and gets ALL products, not just first page
                next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
                if next_data_match:
                    try:
                        next_data = json.loads(next_data_match.group(1))
                        # Navigate through Next.js data structure to find products
                        # Structure varies, so we try multiple paths
                        def extract_products_from_data(data, path=""):
                            """Recursively search for product URLs in JSON data."""
                            found_urls = []
                            if isinstance(data, dict):
                                for key, value in data.items():
                                    # Look for product URLs in various keys
                                    if isinstance(value, str) and f"/marketplace/{product_type}s/" in value:
                                        if "/category/" not in value and value not in seen_urls:
                                            if value.startswith("/"):
                                                full_url = f"https://www.framer.com{value}"
                                            else:
                                                full_url = value
                                            if f"/marketplace/{product_type}s/" in full_url:
                                                found_urls.append(full_url)
                                                seen_urls.add(full_url)
                                    elif isinstance(value, (dict, list)):
                                        found_urls.extend(extract_products_from_data(value, f"{path}.{key}"))
                            elif isinstance(data, list):
                                for item in data:
                                    found_urls.extend(extract_products_from_data(item, path))
                            return found_urls
                        
                        json_urls = extract_products_from_data(next_data)
                        if json_urls:
                            page_urls.extend(json_urls)
                            logger.debug(
                                "fallback_extracted_from_json",
                                url=category_url,
                                type=product_type,
                                count=len(json_urls),
                            )
                    except (json.JSONDecodeError, Exception) as e:
                        logger.debug(
                            "fallback_json_extraction_failed",
                            url=category_url,
                            error=str(e),
                        )
                
                # Strategy 2: Extract from HTML product cards (fallback if JSON fails)
                if not page_urls:
                    soup = BeautifulSoup(html, "lxml")
                    product_cards = soup.select("div.card-module-scss-module__P62yvW__card")
                    for card in product_cards:
                        link = card.find("a", href=re.compile(rf"/marketplace/{product_type}s/[^/]+/"))
                        if link:
                            href = link.get("href", "")
                            if href and href not in seen_urls:
                                if href.startswith("/"):
                                    full_url = f"https://www.framer.com{href}"
                                else:
                                    full_url = href
                                
                                if f"/marketplace/{product_type}s/" in full_url and "/category/" not in full_url:
                                    page_urls.append(full_url)
                                    seen_urls.add(full_url)
                
                # Strategy 3: Find all links matching product pattern (last resort)
                if not page_urls:
                    soup = BeautifulSoup(html, "lxml")
                    all_links = soup.find_all("a", href=re.compile(rf"/marketplace/{product_type}s/[^/]+/"))
                    for link in all_links:
                        href = link.get("href", "")
                        if href and href not in seen_urls:
                            if "/category/" in href:
                                continue
                            
                            if href.startswith("/"):
                                full_url = f"https://www.framer.com{href}"
                            else:
                                full_url = href
                            
                            match = re.search(rf"/marketplace/{product_type}s/([^/]+)/", full_url)
                            if match:
                                product_id = match.group(1)
                                if product_id not in ["category", product_type + "s", "templates", "components", "vectors", "plugins"]:
                                    page_urls.append(full_url)
                                    seen_urls.add(full_url)
                
            except Exception as e:
                logger.warning(
                    "fallback_category_scraping_failed",
                    url=category_url,
                    type=product_type,
                    error=str(e),
                )
            
            return page_urls
        
        for product_type in product_types:
            marketplace_url = type_to_url.get(product_type)
            if not marketplace_url:
                continue
            
            logger.info("fallback_scraping_via_categories", url=marketplace_url, type=product_type)
            
            # Step 1: Find all categories
            category_urls = await find_categories(marketplace_url, product_type)
            
            # Step 2: Scrape products from each category
            if category_urls:
                for category_url in category_urls:
                    category_products = await scrape_category_page(category_url, product_type)
                    if category_products:
                        product_urls.extend(category_products)
                        logger.debug(
                            "fallback_category_scraped",
                            type=product_type,
                            category_url=category_url,
                            products_found=len(category_products),
                            total=len(product_urls),
                        )
            else:
                # Fallback: If no categories found, scrape main page (limited products)
                logger.warning("fallback_no_categories_found", type=product_type, note="Scraping main page only")
                main_page_products = await scrape_category_page(marketplace_url, product_type)
                product_urls.extend(main_page_products)
            
            logger.info(
                "fallback_products_found",
                type=product_type,
                count=len([url for url in product_urls if f"/{product_type}s/" in url]),
                categories_scraped=len(category_urls),
            )
        
        logger.info("fallback_total_products_found", count=len(product_urls))
        return product_urls
