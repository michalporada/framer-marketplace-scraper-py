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
            # Set explicit timeouts: connect, read, write, pool
            # This ensures requests are properly cancelled if they exceed timeout
            timeout = httpx.Timeout(
                connect=5.0,  # Connection timeout: 5s
                read=settings.timeout,  # Read timeout: 12s (from settings)
                write=5.0,  # Write timeout: 5s
                pool=5.0,  # Pool timeout: 5s
            )
            # Use realistic browser headers to avoid bot detection
            user_agent = get_random_user_agent()
            self.client = httpx.AsyncClient(
                timeout=timeout,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "application/xml, text/xml, */*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    # Only request gzip/deflate - httpx auto-decompresses these, but NOT Brotli (br)
                    "Accept-Encoding": "gzip, deflate",
                    "Referer": settings.marketplace_url,
                    "Connection": "keep-alive",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Cache-Control": "max-age=0",
                },
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
            # Add small random delay before request to avoid hitting rate limits
            import asyncio
            import random

            await asyncio.sleep(random.uniform(0.5, 1.5))

            response = await self.client.get(url)
            response.raise_for_status()

            # Get content - httpx should auto-decompress, but verify
            content = response.content

            # Debug: log first 200 chars to diagnose parsing issues
            try:
                preview = content[:200].decode("utf-8", errors="replace")
                content_type = response.headers.get("content-type", "unknown")
                logger.debug(
                    "sitemap_content_preview",
                    preview=preview,
                    content_length=len(content),
                    content_type=content_type,
                    encoding=response.headers.get("content-encoding", "none"),
                )
            except Exception as e:
                logger.warning("sitemap_preview_failed", error=str(e))

            logger.info(
                "sitemap_fetched", url=url, status_code=response.status_code, size=len(content)
            )
            return content

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

    def _load_cached_sitemap(self, extended_max_age: bool = False) -> Optional[bytes]:
        """Load cached sitemap if available and not expired.

        Args:
            extended_max_age: If True, use extended max_age (for 502 errors)

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
        max_age = (
            settings.sitemap_cache_max_age_on_502
            if extended_max_age
            else settings.sitemap_cache_max_age
        )

        if cache_age > max_age:
            logger.debug(
                "sitemap_cache_expired",
                age=round(cache_age, 2),
                max_age=max_age,
                extended=extended_max_age,
            )
            return None

        try:
            with open(cache_path, "rb") as f:
                content = f.read()
            logger.info(
                "sitemap_cache_loaded",
                cache_age=round(cache_age, 2),
                size=len(content),
                extended=extended_max_age,
            )
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

    async def get_sitemap(self) -> tuple[Optional[bytes], bool, float]:
        """Get marketplace sitemap with cache support.

        Tries marketplace sitemap first. If upstream fails:
        - For 502 (CloudFront): Use cache even if expired (up to 24h)
        - For other 5xx: Fail immediately (origin server problem)
        - For other errors: Use cache if available

        Returns:
            Tuple of (sitemap XML content, cache_used: bool, cache_age_hours: float)
            - content: Sitemap XML content or None if failed (non-5xx errors)
            - cache_used: True if cache was used, False if fresh sitemap
            - cache_age_hours: Age of cache in hours (0.0 if fresh)

        Raises:
            httpx.HTTPStatusError: If marketplace sitemap returns 5xx error (except 502 with cache)
        """
        # Try marketplace sitemap first
        try:
            content = await self.fetch_sitemap(settings.sitemap_url)
            if content:
                # Save to cache on success
                self._save_cached_sitemap(content)
                logger.info(
                    "sitemap_fetched_fresh",
                    message="✅ Fresh sitemap fetched successfully - all products will be detected",
                    cache_used=False,
                )
                return (content, False, 0.0)
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code

            # Special handling for 502 (CloudFront problem, not origin)
            if status_code == 502 and settings.use_cache_on_502:
                logger.warning(
                    "sitemap_502_cloudfront_error",
                    url=settings.sitemap_url,
                    message="502 from CloudFront - checking cache freshness",
                )
                # Try to load cache with extended max_age for 502
                cached_content = self._load_cached_sitemap(extended_max_age=True)
                if cached_content:
                    # Check cache age to avoid missing new products
                    cache_path = Path(settings.sitemap_cache_file)
                    cache_age = time.time() - cache_path.stat().st_mtime
                    max_age_for_502 = settings.sitemap_cache_max_age_on_502

                    if cache_age > max_age_for_502:
                        if settings.fail_on_stale_cache_502:
                            logger.error(
                                "sitemap_502_stale_cache",
                                url=settings.sitemap_url,
                                cache_age_hours=round(cache_age / 3600, 2),
                                max_age_hours=round(max_age_for_502 / 3600, 2),
                                message=f"502 error and cache is stale ({round(cache_age / 3600, 2)}h old, max {round(max_age_for_502 / 3600, 2)}h). Failing to avoid missing new products added since cache was created.",
                            )
                            # Fail to avoid missing new products
                            raise
                        else:
                            # Use stale cache with strong warning - better than missing entire scrape
                            cache_age_hours = round(cache_age / 3600, 2)
                            logger.error(
                                "using_stale_cache_on_502",
                                url=settings.sitemap_url,
                                cache_age_hours=cache_age_hours,
                                max_age_hours=round(max_age_for_502 / 3600, 2),
                                message=f"🔴 WARNING: Using STALE cached sitemap ({cache_age_hours}h old) due to CloudFront 502 error. This is better than missing the entire scrape, but NEW PRODUCTS added in the last {cache_age_hours}h WILL BE MISSED. Product data for existing products will still be scraped fresh. Will attempt to refresh sitemap during scraping.",
                                cache_used=True,
                                new_products_may_be_missed=True,
                            )
                            return (cached_content, True, cache_age_hours)
                    else:
                        cache_age_hours = round(cache_age / 3600, 2)
                        logger.warning(
                            "using_cached_sitemap_on_502",
                            message=f"⚠️ Using cached sitemap ({cache_age_hours}h old) due to CloudFront 502 error. Product data will still be scraped fresh, but new products added in the last {cache_age_hours}h may be missed.",
                            cache_used=True,
                            cache_age_hours=cache_age_hours,
                        )
                        return (cached_content, True, cache_age_hours)
                else:
                    logger.error(
                        "sitemap_502_no_cache",
                        url=settings.sitemap_url,
                        message="502 error and no cache available - cannot proceed",
                    )
                    # For 502 without cache, treat as temporary error but still fail
                    raise

            # For other 5xx errors, don't use cache - fail immediately
            if 500 <= status_code < 600:
                raise
            # For other HTTP errors, try cache
            logger.warning("sitemap_fetch_failed_trying_cache", status_code=status_code)
        except Exception as e:
            logger.warning("sitemap_fetch_error_trying_cache", error=str(e))

        # If fetch failed (non-5xx), try cache
        cached_content = self._load_cached_sitemap()
        if cached_content:
            cache_path = Path(settings.sitemap_cache_file)
            cache_age = time.time() - cache_path.stat().st_mtime
            cache_age_hours = round(cache_age / 3600, 2)
            logger.warning(
                "using_cached_sitemap",
                message=f"⚠️ Using cached sitemap ({cache_age_hours}h old) due to upstream failure. Product data will still be scraped fresh, but new products may be missed if they were added after cache was created.",
                cache_used=True,
                cache_age_hours=cache_age_hours,
            )
            return (cached_content, True, cache_age_hours)

        logger.error("marketplace_sitemap_failed_no_cache", url=settings.sitemap_url)
        return (None, False, 0.0)

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
            # Ensure we have bytes, not string
            if isinstance(xml_content, str):
                xml_content = xml_content.encode("utf-8")

            # Try to decode and re-encode to ensure proper encoding
            try:
                # First try UTF-8
                decoded = xml_content.decode("utf-8")
            except UnicodeDecodeError:
                # Fallback to latin-1 (more permissive)
                logger.warning("sitemap_encoding_fallback", encoding="latin-1")
                decoded = xml_content.decode("latin-1", errors="replace")

            # Remove BOM if present
            if decoded.startswith("\ufeff"):
                decoded = decoded[1:]

            # Re-encode to UTF-8 for parsing
            xml_content = decoded.encode("utf-8")

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
            # Log more details about parsing error
            try:
                preview = xml_content[:500].decode("utf-8", errors="replace")
                logger.error(
                    "sitemap_parse_error",
                    error=str(e),
                    content_preview=preview,
                    content_length=len(xml_content),
                    message=f"Failed to parse sitemap XML: {str(e)}. First 500 chars: {preview}",
                )
            except Exception:
                logger.error(
                    "sitemap_parse_error",
                    error=str(e),
                    content_length=len(xml_content),
                    message=f"Failed to parse sitemap XML: {str(e)}",
                )
            return {"products": {}, "categories": [], "profiles": [], "help_articles": []}
        except Exception as e:
            logger.error("sitemap_parse_exception", error=str(e), error_type=type(e).__name__)
            return {"products": {}, "categories": [], "profiles": [], "help_articles": []}

    def filter_urls_by_type(
        self, parsed_sitemap: Dict[str, any], product_types: Optional[List[str]] = None
    ) -> List[str]:
        """Filter product URLs by type and remove duplicates.

        Args:
            parsed_sitemap: Parsed sitemap dictionary
            product_types: List of product types to include (defaults to settings)

        Returns:
            List of unique product URLs matching the specified types
        """
        from urllib.parse import urlparse

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

        # Deduplicate by product_id extracted from URL
        # Same product_id can appear in different paths (e.g., /templates/ripple/ and /components/tags/ripple/)
        seen_product_ids = set()
        unique_urls = []
        duplicates_removed = 0

        for url in urls:
            # Extract product_id from URL (last segment before trailing slash)
            parsed = urlparse(url)
            path = parsed.path.rstrip("/")
            segments = [s for s in path.split("/") if s]
            if segments:
                product_id = segments[-1]
                if product_id not in seen_product_ids:
                    seen_product_ids.add(product_id)
                    unique_urls.append(url)
                else:
                    duplicates_removed += 1

        if duplicates_removed > 0:
            logger.info(
                "duplicates_removed",
                count=duplicates_removed,
                total_before=len(urls),
                total_after=len(unique_urls),
            )

        logger.info("urls_filtered", count=len(unique_urls), types=product_types)
        return unique_urls

    async def scrape(self) -> tuple[Dict[str, List[str]], bool, float]:
        """Main method to scrape sitemap.

        Returns:
            Tuple of (parsed sitemap dict, cache_used: bool, cache_age_hours: float)

        Raises:
            httpx.HTTPStatusError: If marketplace sitemap returns 5xx error
            ValueError: If sitemap parsing fails or returns empty/invalid data
        """
        # Get sitemap content
        # This may raise HTTPStatusError for 5xx errors (no fallback)
        xml_content, cache_used, cache_age_hours = await self.get_sitemap()
        if xml_content is None:
            logger.error("sitemap_fetch_failed_all_attempts")
            return (
                {"products": {}, "categories": [], "profiles": [], "help_articles": []},
                False,
                0.0,
            )

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
            cache_used=cache_used,
            cache_age_hours=cache_age_hours,
        )

        return (parsed, cache_used, cache_age_hours)

    async def get_product_urls(self, product_types: Optional[List[str]] = None) -> List[str]:
        """Get filtered list of product URLs.

        Args:
            product_types: List of product types to include

        Returns:
            List of product URLs
        """
        parsed, _, _ = await self.scrape()
        return self.filter_urls_by_type(parsed, product_types)
