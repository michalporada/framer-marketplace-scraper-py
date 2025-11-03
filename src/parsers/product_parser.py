"""Product parser for extracting data from product HTML pages."""

import re
from typing import List, Optional
from urllib.parse import urlparse, parse_qs, unquote

from bs4 import BeautifulSoup

from src.config.settings import settings
from src.models.product import (
    Product,
    ProductStats,
    ProductMetadata,
    NormalizedDate,
    NormalizedStatistic,
)
from src.utils.logger import get_logger
from src.utils.normalizers import parse_relative_date, parse_statistic

logger = get_logger(__name__)


class ProductParser:
    """Parser for product HTML pages."""

    def __init__(self):
        """Initialize product parser."""
        self.selectors = settings.get_selectors()

    def decode_nextjs_image_url(self, url: str) -> Optional[str]:
        """Decode Next.js Image URL to original image URL.

        Args:
            url: Next.js Image URL (e.g., /creators-assets/_next/image/?url=...&w=...&q=100)

        Returns:
            Original image URL or None
        """
        try:
            parsed = urlparse(url)
            if "/_next/image" in parsed.path:
                query_params = parse_qs(parsed.query)
                if "url" in query_params:
                    encoded_url = query_params["url"][0]
                    decoded_url = unquote(encoded_url)
                    return decoded_url
            return url
        except Exception as e:
            logger.warning("image_url_decode_failed", url=url, error=str(e))
            return url

    def extract_price(self, price_text: str) -> tuple[Optional[float], bool]:
        """Extract price from text.

        Args:
            price_text: Price text (e.g., "$49", "Free")

        Returns:
            Tuple of (price, is_free)
        """
        if not price_text:
            return None, False

        price_text = price_text.strip().lower()
        if price_text == "free":
            return None, True

        # Extract number from price string
        match = re.search(r"[\d.]+", price_text.replace(",", ""))
        if match:
            try:
                price = float(match.group())
                return price, False
            except ValueError:
                pass

        return None, False

    def extract_creator_username(self, creator_url: str) -> Optional[str]:
        """Extract creator username from URL.

        Args:
            creator_url: Creator profile URL (e.g., /@ev-studio/)

        Returns:
            Username (without @) or None
        """
        match = re.search(r"/@([^/]+)/?", creator_url)
        if match:
            return match.group(1)
        return None

    def parse(self, html: str, url: str, product_type: Optional[str] = None) -> Optional[Product]:
        """Parse product HTML and extract data.

        Args:
            html: HTML content of product page
            url: Product URL
            product_type: Product type (template/component/vector/plugin) or None to extract from URL

        Returns:
            Product model or None if parsing failed
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            # Extract product ID from URL
            parsed_url = urlparse(url)
            path = parsed_url.path.rstrip("/")
            product_id = path.split("/")[-1] if path else "unknown"

            # Extract product type if not provided
            if product_type is None:
                url_lower = url.lower()
                if "/marketplace/templates/" in url_lower:
                    product_type = "template"
                elif "/marketplace/components/" in url_lower:
                    product_type = "component"
                elif "/marketplace/vectors/" in url_lower:
                    product_type = "vector"
                elif "/marketplace/plugins/" in url_lower:
                    product_type = "plugin"

            # Extract name and creator from title tag
            title_tag = soup.find("title")
            title_full = None
            if title_tag:
                title_full = title_tag.get_text().strip()

            # Try meta og:title if title tag not found
            if not title_full:
                og_title = soup.find("meta", property="og:title")
                if og_title:
                    title_full = og_title.get("content", "").strip()

            # Parse title to extract product name and creator name
            name, creator_name_from_title = self._parse_title_components(title_full)

            # Try h1 as fallback for product name
            if not name:
                h1 = soup.find("h1")
                if h1:
                    name = h1.get_text().strip()

            if not name:
                logger.warning("product_name_not_found", url=url)
                name = product_id

            # Extract price based on product type
            price = None
            is_free = False
            # Try button text (more reliable for product pages)
            price_button = soup.find(
                "button", string=re.compile(r"(Purchase|Preview|Open|Copy)", re.I)
            )
            if price_button:
                button_text = price_button.get_text().strip()
                # Check for free indicators
                if any(
                    free in button_text.lower()
                    for free in ["preview", "open in framer", "copy component", "copy vectors"]
                ):
                    is_free = True
                    price = None
                else:
                    # Extract price from button text (e.g., "Purchase for $49")
                    price_match = re.search(r"\$([\d.]+)", button_text)
                    if price_match:
                        price = float(price_match.group(1))
                        is_free = False

            # Fallback to span elements
            if price is None and not is_free:
                price_elem = soup.select_one('span:contains("$"), span:contains("Free")')
                if not price_elem:
                    for selector in [
                        '[class*="price"]',
                        '[class*="Price"]',
                        'span[class*="normalMeta"]',
                    ]:
                        price_elem = soup.select_one(selector)
                        if price_elem:
                            break

                if price_elem:
                    price_text = price_elem.get_text().strip()
                    price, is_free = self.extract_price(price_text)

            # Extract description
            description = None
            # Try meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "").strip()

            # Try og:description
            if not description:
                og_desc = soup.find("meta", property="og:description")
                if og_desc:
                    description = og_desc.get("content", "").strip()

            # Extract images
            thumbnail = None
            screenshots = []
            gallery = []

            # Try og:image for thumbnail
            og_image = soup.find("meta", property="og:image")
            if og_image:
                thumbnail_url = og_image.get("content", "")
                if thumbnail_url:
                    thumbnail_url = self.decode_nextjs_image_url(thumbnail_url)
                    thumbnail = thumbnail_url

            # Find all images
            images = soup.find_all("img")
            for img in images:
                src = img.get("src") or img.get("data-src")
                if not src:
                    continue

                # Skip icons and small images
                if any(skip in src.lower() for skip in ["icon", "logo", "avatar"]):
                    continue

                # Decode Next.js Image URLs
                decoded_src = self.decode_nextjs_image_url(src)
                if decoded_src not in gallery:
                    gallery.append(decoded_src)

            # Use first gallery image as thumbnail if not found
            if not thumbnail and gallery:
                thumbnail = gallery[0]

            # Screenshots are typically gallery images
            screenshots = gallery.copy()

            # Extract creator link
            creator_username = None
            creator_url = None
            creator_name = creator_name_from_title  # Use name from title as fallback
            creator_link = soup.select_one('a[href^="/@"]')
            if creator_link:
                creator_url = creator_link.get("href", "")
                creator_username = self.extract_creator_username(creator_url)
                # Make full URL
                if creator_url.startswith("/"):
                    creator_url = f"{settings.base_url}{creator_url}"
                # Try to get creator display name from link text
                creator_link_text = creator_link.get_text().strip()
                if creator_link_text:
                    creator_name = creator_link_text

            # Extract categories (all of them)
            categories = self._extract_categories(soup)
            category = (
                categories[0] if categories else None
            )  # Main category for backward compatibility

            # Extract statistics based on product type
            stats = self._extract_statistics(soup, product_type)

            # Extract metadata (dates, version)
            metadata = self._extract_metadata(soup, product_type)

            # Extract features based on product type
            features = self._extract_features(soup, product_type)

            # Create Product model
            product = Product(
                id=product_id,
                name=name,
                type=product_type or "unknown",
                category=category,
                categories=categories,
                url=url,
                price=price,
                is_free=is_free,
                description=description,
                stats=stats,
                metadata=metadata,
                features=features,
                media={
                    "thumbnail": thumbnail,
                    "screenshots": screenshots[:10],  # Limit screenshots
                    "gallery": gallery[:20],  # Limit gallery
                    "video_preview": None,  # TODO: Extract video if available
                },
            )

            # Add creator info if available
            if creator_username and creator_url:
                from src.models.creator import Creator

                product.creator = Creator(
                    username=creator_username,
                    name=creator_name,  # Use name from title or link text
                    profile_url=creator_url,
                )

            logger.info("product_parsed", product_id=product_id, name=name, type=product_type)
            return product

        except Exception as e:
            logger.error(
                "product_parse_error",
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def _extract_statistics(self, soup: BeautifulSoup, product_type: str) -> ProductStats:
        """Extract statistics based on product type.

        Args:
            soup: BeautifulSoup object
            product_type: Product type (template/component/vector/plugin)

        Returns:
            ProductStats model
        """
        stats_dict = {}

        # Find all text that might contain statistics
        # Look for patterns like "X Pages", "X Views", "X Users", "X Installs", "X Vectors"
        text_content = soup.get_text()

        # Templates: Pages + Views
        if product_type == "template":
            pages_match = re.search(r"(\d+)\s*Pages", text_content, re.IGNORECASE)
            if pages_match:
                pages_raw = pages_match.group(0)
                stats_dict["pages"] = NormalizedStatistic(**parse_statistic(pages_raw))

            views_match = re.search(r"([\d.,]+[Kk]?)\s*Views", text_content, re.IGNORECASE)
            if views_match:
                views_raw = views_match.group(0)
                stats_dict["views"] = NormalizedStatistic(**parse_statistic(views_raw))

        # Plugins: Version + Users
        elif product_type == "plugin":
            # Version is stored in metadata, not stats (extracted in _extract_metadata)

            users_match = re.search(r"([\d.,]+[Kk]?)\s*Users", text_content, re.IGNORECASE)
            if users_match:
                users_raw = users_match.group(0)
                stats_dict["users"] = NormalizedStatistic(**parse_statistic(users_raw))

        # Components: Installs
        elif product_type == "component":
            installs_match = re.search(r"([\d.,]+[Kk]?)\s*Installs", text_content, re.IGNORECASE)
            if installs_match:
                installs_raw = installs_match.group(0)
                stats_dict["installs"] = NormalizedStatistic(**parse_statistic(installs_raw))

        # Vectors: Users + Views + Vectors (count)
        elif product_type == "vector":
            users_match = re.search(r"([\d.,]+[Kk]?)\s*Users", text_content, re.IGNORECASE)
            if users_match:
                users_raw = users_match.group(0)
                stats_dict["users"] = NormalizedStatistic(**parse_statistic(users_raw))

            views_match = re.search(r"([\d.,]+[Kk]?)\s*Views", text_content, re.IGNORECASE)
            if views_match:
                views_raw = views_match.group(0)
                stats_dict["views"] = NormalizedStatistic(**parse_statistic(views_raw))

            vectors_match = re.search(r"([\d.,]+)\s*Vectors", text_content, re.IGNORECASE)
            if vectors_match:
                vectors_raw = vectors_match.group(0)
                stats_dict["vectors"] = NormalizedStatistic(**parse_statistic(vectors_raw))

        return ProductStats(**stats_dict)

    def _extract_metadata(self, soup: BeautifulSoup, product_type: str) -> ProductMetadata:
        """Extract metadata (dates, version) based on product type.

        Args:
            soup: BeautifulSoup object
            product_type: Product type (template/component/vector/plugin)

        Returns:
            ProductMetadata model
        """
        metadata_dict = {}

        # Extract published date ("X months ago", "Xmo ago", "Xw ago")
        text_content = soup.get_text()
        date_patterns = [
            r"(\d+\s*months?\s*ago)",
            r"(\d+mo\s*ago)",
            r"(\d+w\s*ago)",
            r"(\d+\s*weeks?\s*ago)",
            r"(\d+\s*days?\s*ago)",
        ]

        published_date_raw = None
        for pattern in date_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                published_date_raw = match.group(1)
                break

        if published_date_raw:
            date_data = parse_relative_date(published_date_raw)
            metadata_dict["published_date"] = NormalizedDate(**date_data)

        # Extract "Updated" date if available
        updated_match = re.search(
            r"Updated.*?(\d+\s*months?\s*ago|\d+mo\s*ago|\d+w\s*ago)", text_content, re.IGNORECASE
        )
        if updated_match:
            updated_raw = updated_match.group(1)
            date_data = parse_relative_date(updated_raw)
            metadata_dict["last_updated"] = NormalizedDate(**date_data)

        # Extract version (for plugins)
        if product_type == "plugin":
            version_match = re.search(r"Version\s+(\d+)", text_content, re.IGNORECASE)
            if version_match:
                metadata_dict["version"] = version_match.group(1)

        return ProductMetadata(**metadata_dict)

    def _extract_features(self, soup: BeautifulSoup, product_type: str):
        """Extract features based on product type.

        Args:
            soup: BeautifulSoup object
            product_type: Product type (template/component/vector/plugin)

        Returns:
            ProductFeatures model
        """
        from src.models.product import ProductFeatures

        features_list = []
        pages_count = None
        pages_list = []

        # Templates: Features, Pages, "What's Included", "What makes different"
        if product_type == "template":
            # Find Features section - look for h2/h3 heading with "Features"
            features_section = None
            # Try h2 first
            for heading in soup.find_all(["h2", "h3", "h4"]):
                if heading.get_text().strip().lower() == "features":
                    features_section = heading
                    break

            # If not found, try finding by text
            if not features_section:
                features_section = soup.find(string=re.compile(r"^Features$", re.I))
                if features_section:
                    features_section = features_section.find_parent()

            if features_section:
                # Find parent container (usually a section or div after heading)
                features_parent = features_section.find_next_sibling()
                if not features_parent:
                    features_parent = features_section.find_parent()

                if features_parent:
                    # Find all feature links/spans - they're usually in links with class "contentSidebarItem"
                    # or spans with text-label class
                    feature_tags = features_parent.find_all(["a", "span", "div", "li"])
                    for tag in feature_tags:
                        text = tag.get_text().strip()
                        # Filter: feature tags are usually short, not empty, and not "Features"
                        if text and len(text) < 100 and text.lower() != "features":
                            # Skip if it's a navigation link or section header
                            if not any(
                                skip in text.lower()
                                for skip in [
                                    "see all",
                                    "more from",
                                    "related",
                                    "categories",
                                    "pages",
                                    "support",
                                ]
                            ):
                                if text not in features_list:
                                    features_list.append(text)

            # Extract pages count
            pages_match = re.search(r"(\d+)\s*Pages", soup.get_text(), re.IGNORECASE)
            if pages_match:
                pages_count = int(pages_match.group(1))

            # Extract pages list (if available)
            # Method 1: Look for "Pages" heading (h6, h2, h3, etc.) and find sibling elements
            pages_heading = None
            for heading in soup.find_all(["h6", "h2", "h3", "h4"]):
                heading_text = heading.get_text().strip()
                if heading_text.lower() == "pages":
                    pages_heading = heading
                    break

            if pages_heading:
                # Find parent section that contains the heading
                section = pages_heading.find_parent(["section", "div"])
                if section:
                    # Find all links/spans/divs in the section (pages are usually in links or spans)
                    page_elements = section.find_all(
                        ["a", "span", "div"], class_=re.compile(r"text-label|contentSidebarItem")
                    )
                    for elem in page_elements:
                        page_text = elem.get_text().strip()
                        if page_text and len(page_text) < 100:
                            # Skip if it's just "Pages" label or navigation
                            if page_text.lower() not in [
                                "pages",
                                "see all",
                                "more from",
                                "related",
                            ]:
                                if page_text not in pages_list:
                                    pages_list.append(page_text)

            # Method 2: Fallback - find by text "Pages" and get siblings
            if not pages_list:
                pages_section = soup.find(string=re.compile(r"^Pages$", re.I))
                if pages_section:
                    pages_parent = pages_section.find_parent()
                    if pages_parent:
                        page_items = pages_parent.find_all(["li", "span", "div", "a"])
                        for item in page_items:
                            page_text = item.get_text().strip()
                            if page_text and len(page_text) < 100:
                                # Skip if it's just "Pages" label or navigation
                                if page_text.lower() not in [
                                    "pages",
                                    "see all",
                                    "more from",
                                    "related",
                                ]:
                                    if page_text not in pages_list:
                                        pages_list.append(page_text)

        # Plugins: "About this Plugin" (no Features section)
        elif product_type == "plugin":
            # Plugins typically don't have features list
            pass

        # Components: "About this Component" (may have features)
        elif product_type == "component":
            # Components may have some features/tags
            features_section = soup.find(string=re.compile(r"Features|About", re.I))
            if features_section:
                features_parent = features_section.find_parent()
                if features_parent:
                    feature_tags = features_parent.find_all(["span", "div", "li"])
                    for tag in feature_tags:
                        text = tag.get_text().strip()
                        if text and len(text) < 50:
                            features_list.append(text)

        # Vectors: "About these Vectors" (no Features section)
        elif product_type == "vector":
            # Vectors typically don't have features list
            pass

        # Infer features from text
        text_lower = soup.get_text().lower()
        is_responsive = any(term in text_lower for term in ["responsive", "mobile"])
        has_animations = any(term in text_lower for term in ["animation", "animate", "effects"])
        cms_integration = any(term in text_lower for term in ["cms", "contentful", "prismic"])

        return ProductFeatures(
            features=features_list[:20],  # Limit features
            pages_count=pages_count,
            pages_list=pages_list,
            is_responsive=is_responsive,
            has_animations=has_animations,
            cms_integration=cms_integration,
        )

    def _parse_title_components(self, title: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Parse title tag to extract product name and creator name.

        Format: "{ProductName}: {Subtitle} by {CreatorName} — Framer Marketplace"
        Example: "1936Redcliff: Responsive Real Estate Website Template by NutsDev — Framer Marketplace"

        Args:
            title: Full title text from <title> tag

        Returns:
            Tuple of (product_name, creator_name) or (None, None) if parsing fails
        """
        if not title:
            return None, None

        product_name = None
        creator_name = None

        # Remove common suffix
        title_clean = re.sub(r"\s*[-|—]\s*Framer.*$", "", title, flags=re.IGNORECASE).strip()

        # Extract product name (before first colon)
        if ":" in title_clean:
            product_name = title_clean.split(":")[0].strip()

        # Extract creator name (between "by" and end or "—")
        # Pattern: "... by CreatorName —" or "... by CreatorName"
        by_match = re.search(r"\s+by\s+([^—]+?)(?:\s*—|$)", title_clean, re.IGNORECASE)
        if by_match:
            creator_name = by_match.group(1).strip()

        # If no colon, try to extract product name from beginning
        if not product_name:
            # If there's "by", take everything before it
            if creator_name:
                by_index = title_clean.lower().find(" by ")
                if by_index > 0:
                    product_name = title_clean[:by_index].strip()
            else:
                # No creator found, use first part
                product_name = title_clean.split()[0] if title_clean else None

        return product_name, creator_name

    def _extract_categories(self, soup: BeautifulSoup) -> List[str]:
        """Extract all categories from product page.

        Categories are typically found in a "Categories" section.
        Example from Omicorn: "SaaS", "Agency", "Landing Page", "Modern", "Animated", "Minimal", "Gradient", "Professional"

        Args:
            soup: BeautifulSoup object

        Returns:
            List of all category names
        """
        categories = []

        # Method 1: Look for "Categories" heading (h6, h2, h3, etc.) and find sibling elements
        categories_heading = None
        for heading in soup.find_all(["h6", "h2", "h3", "h4"]):
            heading_text = heading.get_text().strip()
            if heading_text.lower() == "categories":
                categories_heading = heading
                break

        if categories_heading:
            # Find parent section that contains the heading
            section = categories_heading.find_parent(["section", "div"])
            if section:
                # Find all links in the section (categories are usually links)
                category_links = section.find_all(
                    "a", href=re.compile(r"/category/|/marketplace/category/")
                )
                for link in category_links:
                    category_text = link.get_text().strip()
                    if category_text and category_text.lower() != "categories":
                        categories.append(category_text)

                # Also check spans/divs with text-label class (common pattern)
                if not categories:
                    category_elements = section.find_all(
                        ["span", "div"], class_=re.compile(r"text-label|contentSidebarItem")
                    )
                    for elem in category_elements:
                        category_text = elem.get_text().strip()
                        if category_text and len(category_text) < 100:
                            if category_text.lower() not in ["categories", "see all"]:
                                categories.append(category_text)

        # Method 2: Fallback - find by text "Categories" and get siblings
        if not categories:
            categories_section = soup.find(string=re.compile(r"^Categories$", re.I))
            if categories_section:
                categories_parent = categories_section.find_parent()
                if categories_parent:
                    # Find all links or spans that might be categories
                    category_elements = categories_parent.find_all(["a", "span", "div"])
                    for elem in category_elements:
                        category_text = elem.get_text().strip()
                        # Filter out non-category text
                        if category_text and len(category_text) < 100:
                            # Skip if it's just "Categories" label or navigation
                            if category_text.lower() not in [
                                "categories",
                                "see all",
                                "more from",
                                "related",
                            ]:
                                categories.append(category_text)

        # Method 3: Find all category links on the page (href contains /category/)
        category_links = soup.find_all("a", href=re.compile(r"/category/|/marketplace/category/"))
        for link in category_links:
            category_text = link.get_text().strip()
            if category_text and category_text not in categories:
                # Additional check - make sure it's not a navigation link
                if category_text.lower() not in ["see all", "categories"]:
                    categories.append(category_text)

        # Remove duplicates while preserving order
        seen = set()
        unique_categories = []
        for cat in categories:
            cat_lower = cat.lower().strip()
            if cat_lower and cat_lower not in seen and len(cat) > 0:
                seen.add(cat_lower)
                unique_categories.append(cat)

        return unique_categories
