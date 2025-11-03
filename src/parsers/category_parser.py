"""Category parser for extracting data from category HTML pages."""

import re
from typing import Optional

from bs4 import BeautifulSoup

from src.config.settings import settings
from src.models.category import Category
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CategoryParser:
    """Parser for category HTML pages."""

    def __init__(self):
        """Initialize category parser."""

    def extract_category_slug_from_url(self, url: str) -> Optional[str]:
        """Extract category slug from URL.

        Args:
            url: Category URL (e.g., /marketplace/category/templates/)

        Returns:
            Category slug or None
        """
        match = re.search(r"/marketplace/category/([^/]+)/?", url)
        if match:
            return match.group(1)
        return None

    def parse(self, html: str, url: str) -> Optional[Category]:
        """Parse category HTML and extract data.

        Args:
            html: HTML content of category page
            url: Category URL

        Returns:
            Category model or None if parsing failed
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            # Extract category slug from URL
            slug = self.extract_category_slug_from_url(url)
            if not slug:
                logger.warning("category_slug_not_found", url=url)
                return None

            # Make full URL
            if url.startswith("/"):
                full_url = f"{settings.base_url}{url}"
            else:
                full_url = url

            # Extract category name
            name = None
            # Try h1 for category name
            h1 = soup.find("h1")
            if h1:
                name = h1.get_text().strip()

            if not name:
                # Try meta og:title
                og_title = soup.find("meta", property="og:title")
                if og_title:
                    name = og_title.get("content", "").strip()
                    # Remove common suffixes
                    name = re.sub(r"\s*[-|]\s*Framer.*$", "", name, flags=re.IGNORECASE)

            if not name:
                # Use slug as fallback, capitalize it
                name = slug.replace("-", " ").title()

            # Extract description
            description = None
            # Try meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "").strip()

            if not description:
                # Try og:description
                og_desc = soup.find("meta", property="og:description")
                if og_desc:
                    description = og_desc.get("content", "").strip()

            # Extract product count
            product_count = None
            # Look for product count text
            text_content = soup.get_text()
            count_match = re.search(r"(\d+)\s*(?:products?|items?)", text_content, re.IGNORECASE)
            if count_match:
                try:
                    product_count = int(count_match.group(1))
                except ValueError:
                    pass

            # Count products from product cards if not found in text
            if product_count is None:
                product_cards = soup.select("div.card-module-scss-module__P62yvW__card")
                if product_cards:
                    product_count = len(product_cards)

            # Extract product types in this category
            product_types = []
            # Look for product type indicators in URL or page
            url_lower = url.lower()
            if "template" in url_lower or "template" in name.lower():
                product_types.append("template")
            if "component" in url_lower or "component" in name.lower():
                product_types.append("component")
            if "vector" in url_lower or "vector" in name.lower():
                product_types.append("vector")
            if "plugin" in url_lower or "plugin" in name.lower():
                product_types.append("plugin")

            # If no types found, try to infer from product cards
            if not product_types:
                product_links = soup.find_all(
                    "a", href=re.compile(r"/marketplace/(templates|components|vectors|plugins)/")
                )
                found_types = set()
                for link in product_links:
                    href = link.get("href", "")
                    if "/marketplace/templates/" in href:
                        found_types.add("template")
                    elif "/marketplace/components/" in href:
                        found_types.add("component")
                    elif "/marketplace/vectors/" in href:
                        found_types.add("vector")
                    elif "/marketplace/plugins/" in href:
                        found_types.add("plugin")
                product_types = list(found_types)

            # Extract subcategories (if available)
            subcategories = []
            # Look for subcategory links
            subcategory_links = soup.find_all("a", href=re.compile(r"/marketplace/category/[^/]+/"))
            for link in subcategory_links:
                href = link.get("href", "")
                sub_slug = self.extract_category_slug_from_url(href)
                if sub_slug and sub_slug != slug:
                    subcategories.append(sub_slug)

            # Extract parent category (if available)
            parent_category = None
            # Look for breadcrumbs or parent category links
            breadcrumbs = soup.find_all(["nav", "ol"], class_=re.compile(r"breadcrumb", re.I))
            for breadcrumb in breadcrumbs:
                links = breadcrumb.find_all("a", href=re.compile(r"/marketplace/category/"))
                if len(links) > 1:
                    # Last link before current is parent
                    parent_link = links[-2] if len(links) >= 2 else None
                    if parent_link:
                        parent_slug = self.extract_category_slug_from_url(
                            parent_link.get("href", "")
                        )
                        if parent_slug:
                            parent_category = parent_slug

            # Create Category model
            category = Category(
                name=name,
                slug=slug,
                url=full_url,
                description=description,
                product_count=product_count,
                product_types=product_types if product_types else [],
                parent_category=parent_category,
                subcategories=subcategories,
            )

            logger.info("category_parsed", slug=slug, name=name, product_count=product_count)
            return category

        except Exception as e:
            logger.error(
                "category_parse_error",
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None
