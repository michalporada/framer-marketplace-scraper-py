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
            url: Category URL (e.g., /marketplace/category/templates/ or /marketplace/templates/category/non-profit/)

        Returns:
            Category slug or None
        """
        # Try format: /marketplace/templates/category/{slug}/
        match = re.search(
            r"/marketplace/(?:templates|components|vectors|plugins)/category/([^/]+)/?", url
        )
        if match:
            return match.group(1)
        # Try format: /marketplace/category/{slug}/
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

    def find_product_position(self, html: str, product_url: str) -> Optional[int]:
        """Find product position in category page listing.

        Products are ordered left-to-right, top-to-bottom (grid layout).
        Position is 1-indexed (first product = 1).

        Note: Currently only used for templates.

        Args:
            html: HTML content of category page
            product_url: Product URL to find (e.g., /marketplace/templates/healing/)

        Returns:
            Position (1-indexed) or None if not found
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            # Extract product ID from URL for matching
            # Format: /marketplace/{type}/{product_id}/
            product_id_match = re.search(
                r"/marketplace/(?:templates|components|vectors|plugins)/([^/]+)/?", product_url
            )
            if not product_id_match:
                logger.warning("product_id_not_found_in_url", url=product_url)
                return None

            product_id = product_id_match.group(1)

            # Find all product cards/links in order (left-to-right, top-to-bottom)
            # Try multiple selectors for product cards
            product_links = []
            seen_product_ids = set()

            # Method 1: Find product cards by CSS selector (most reliable for grid layout)
            product_cards = soup.select("div.card-module-scss-module__P62yvW__card")

            # Process cards in document order (preserves left-to-right, top-to-bottom)
            for card in product_cards:
                # Find link within card - try multiple approaches
                link = card.find(
                    "a", href=re.compile(r"/marketplace/(?:templates|components|vectors|plugins)/")
                )

                # If no direct link, try to find any link in the card
                if not link:
                    all_links = card.find_all("a")
                    for a_link in all_links:
                        href = a_link.get("href", "")
                        if re.search(
                            r"/marketplace/(?:templates|components|vectors|plugins)/", href
                        ):
                            link = a_link
                            break

                if link:
                    href = link.get("href", "")
                    # Extract product ID from href
                    link_match = re.search(
                        r"/marketplace/(?:templates|components|vectors|plugins)/([^/]+)/?", href
                    )
                    if link_match:
                        link_product_id = link_match.group(1)
                        # Skip navigation links
                        if link_product_id not in [
                            "category",
                            "templates",
                            "components",
                            "vectors",
                            "plugins",
                        ]:
                            # Only add if not already in list (avoid duplicates)
                            if link_product_id not in seen_product_ids:
                                seen_product_ids.add(link_product_id)
                                product_links.append(
                                    {"id": link_product_id, "url": href, "element": card}
                                )

            # Method 2: If no cards found, try to find all product links in document order
            if not product_links:
                all_links = soup.find_all(
                    "a",
                    href=re.compile(
                        r"/marketplace/(?:templates|components|vectors|plugins)/[^/]+/"
                    ),
                )
                for link in all_links:
                    href = link.get("href", "")
                    link_match = re.search(
                        r"/marketplace/(?:templates|components|vectors|plugins)/([^/]+)/?", href
                    )
                    if link_match:
                        link_product_id = link_match.group(1)
                        # Skip navigation links
                        if link_product_id not in [
                            "category",
                            "templates",
                            "components",
                            "vectors",
                            "plugins",
                        ]:
                            if link_product_id not in seen_product_ids:
                                seen_product_ids.add(link_product_id)
                                product_links.append(
                                    {"id": link_product_id, "url": href, "element": link}
                                )

            # Find position of our product
            for idx, product_link in enumerate(product_links, start=1):
                if product_link["id"] == product_id:
                    logger.debug(
                        "product_position_found",
                        product_id=product_id,
                        category_url=html[:100] if len(html) > 100 else html,
                        position=idx,
                        total_products=len(product_links),
                    )
                    return idx

            logger.warning(
                "product_not_found_in_category",
                product_id=product_id,
                total_products_found=len(product_links),
            )
            return None

        except Exception as e:
            logger.error(
                "find_product_position_error",
                product_url=product_url,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None
