"""Creator parser for extracting data from creator profile HTML pages."""

import re
from typing import Optional
from urllib.parse import unquote

from bs4 import BeautifulSoup

from src.config.settings import settings
from src.models.creator import Creator, CreatorStats
from src.utils.logger import get_logger
from src.parsers.product_parser import ProductParser

logger = get_logger(__name__)


class CreatorParser:
    """Parser for creator profile HTML pages."""

    def __init__(self):
        """Initialize creator parser."""
        self.selectors = settings.get_selectors()
        # Use ProductParser for image URL decoding
        self._product_parser = ProductParser()

    def extract_username_from_url(self, url: str) -> Optional[str]:
        """Extract username from profile URL.

        Args:
            url: Creator profile URL (e.g., /@ev-studio/ or /@-790ivi/)

        Returns:
            Username (without @) or None
        """
        # Match /@username/ or https://www.framer.com/@username/
        match = re.search(r"/@([^/]+)/?", url)
        if match:
            return match.group(1)
        return None

    def parse(self, html: str, url: str) -> Optional[Creator]:
        """Parse creator profile HTML and extract data.

        Args:
            html: HTML content of creator profile page
            url: Creator profile URL

        Returns:
            Creator model or None if parsing failed
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            # Extract username from URL
            username = self.extract_username_from_url(url)
            if not username:
                logger.warning("creator_username_not_found", url=url)
                return None

            # Make full profile URL
            if url.startswith("/"):
                profile_url = f"{settings.base_url}{url}"
            else:
                profile_url = url

            # Extract display name
            name = None
            # Try h1 or h2 for display name
            h1 = soup.find("h1")
            if h1:
                name = h1.get_text().strip()
                # Remove "Creator" suffix if present (with or without space before it)
                name = re.sub(r"Creator\s*$", "", name, flags=re.IGNORECASE)

            if not name:
                # Try meta og:title
                og_title = soup.find("meta", property="og:title")
                if og_title:
                    name = og_title.get("content", "").strip()
                    # Remove common suffixes
                    name = re.sub(r"\s*[-|]\s*Framer.*$", "", name, flags=re.IGNORECASE)
                    # Remove "Creator" suffix if present (with or without space before it)
                    name = re.sub(r"Creator\s*$", "", name, flags=re.IGNORECASE)

            # Extract avatar - prioritize JSON data, then HTML images
            avatar_url = None

            # First, try to extract from JSON data in script tags (Next.js data)
            script_tags = soup.find_all("script")
            for script in script_tags:
                script_content = script.string
                if not script_content:
                    continue

                # Look for creator data in Next.js JSON structure
                # Pattern: "creator":{...} with avatar field
                if '"creator"' in script_content and '"avatar"' in script_content:
                    try:
                        # Try to find the avatar URL in the creator object
                        # Look for "avatar":"https://..." pattern
                        avatar_match = re.search(
                            r'"avatar"\s*:\s*"(https?://[^"]+)"', script_content
                        )
                        if avatar_match:
                            potential_url = avatar_match.group(1)
                            # Check if it's not a placeholder API URL
                            if "api/og/creator" not in potential_url:
                                avatar_url = potential_url
                                break
                    except Exception:
                        pass

            # If not found in JSON, try to find avatar image in sidebar
            if not avatar_url:
                # Look for avatar in sidebar (most reliable location)
                sidebar = soup.find("div", class_=re.compile(r"sidebar", re.I))
                if sidebar:
                    avatar_container = sidebar.find("div", class_=re.compile(r"avatar", re.I))
                    if avatar_container:
                        img = avatar_container.find("img")
                        if img:
                            # Try srcSet first (Next.js optimized images)
                            srcset = img.get("srcSet") or img.get("srcset")
                            if srcset:
                                # Extract first URL from srcSet
                                srcset_urls = re.findall(r"url=([^&\s]+)", srcset)
                                if srcset_urls:
                                    avatar_url = self._product_parser.decode_nextjs_image_url(
                                        unquote(srcset_urls[0])
                                    )
                            if not avatar_url:
                                avatar_src = img.get("src") or img.get("data-src")
                                if avatar_src:
                                    avatar_url = self._product_parser.decode_nextjs_image_url(
                                        avatar_src
                                    )

            # Fallback: try og:image but only if it's not a placeholder
            if not avatar_url:
                og_image = soup.find("meta", property="og:image")
                if og_image:
                    og_url = og_image.get("content", "")
                    # Skip placeholder API URLs
                    if og_url and "api/og/creator" not in og_url:
                        avatar_url = self._product_parser.decode_nextjs_image_url(og_url)

            # Final fallback: look for any img with alt containing username
            if not avatar_url:
                img = soup.find("img", alt=re.compile(r"avatar|profile|%s" % username, re.I))
                if img:
                    avatar_src = img.get("src") or img.get("data-src")
                    if avatar_src:
                        avatar_url = self._product_parser.decode_nextjs_image_url(avatar_src)

            # Extract bio
            bio = None
            # Try meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                bio = meta_desc.get("content", "").strip()

            if not bio:
                # Try og:description
                og_desc = soup.find("meta", property="og:description")
                if og_desc:
                    bio = og_desc.get("content", "").strip()

            # Look for bio in page content
            if not bio:
                # Try to find paragraphs with bio-like content
                paragraphs = soup.find_all("p")
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and len(text) > 20 and len(text) < 500:  # Reasonable bio length
                        bio = text
                        break

            # Extract website
            website = None
            # Look for website links
            links = soup.find_all("a", href=True)
            for link in links:
                href = link.get("href", "")
                text = link.get_text().strip()
                # Check if it's an external website link
                if href.startswith("http") and not href.startswith(settings.base_url):
                    # Check if it's not a social media link
                    if not any(
                        social in href.lower()
                        for social in ["twitter.com", "linkedin.com", "instagram.com", "github.com"]
                    ):
                        website = href
                        break

            # Extract social media links - prioritize JSON data, then HTML links
            social_media = {}

            # First, try to extract from JSON data in script tags (Next.js data)
            script_tags = soup.find_all("script")
            for script in script_tags:
                script_content = script.string
                if not script_content:
                    continue

                # Look for creator data with socials array
                # Pattern: "creator":{...,"socials":[...]} or "socials":[...]
                if '"socials"' in script_content:
                    try:
                        # Try to find socials array in creator object
                        # Pattern: "socials":["url1","url2",...]
                        socials_match = re.search(
                            r'"socials"\s*:\s*\[(.*?)\]', script_content, re.DOTALL
                        )
                        if socials_match:
                            socials_content = socials_match.group(1)
                            # Extract URLs from the array (handle both string and object formats)
                            urls = re.findall(r'"(https?://[^"]+)"', socials_content)
                            for url in urls:
                                url_lower = url.lower()
                                # Skip if it's Framer's own social links
                                if "/framer" in url_lower or "/company/framer" in url_lower:
                                    continue

                                if "twitter.com" in url_lower or "x.com" in url_lower:
                                    if "twitter" not in social_media:
                                        social_media["twitter"] = url
                                elif "linkedin.com" in url_lower:
                                    if "linkedin" not in social_media:
                                        social_media["linkedin"] = url
                                elif "instagram.com" in url_lower:
                                    if "instagram" not in social_media:
                                        social_media["instagram"] = url
                                elif "github.com" in url_lower:
                                    if "github" not in social_media:
                                        social_media["github"] = url
                                elif "dribbble.com" in url_lower:
                                    if "dribbble" not in social_media:
                                        social_media["dribbble"] = url
                                elif "behance.net" in url_lower:
                                    if "behance" not in social_media:
                                        social_media["behance"] = url
                                elif "youtube.com" in url_lower:
                                    if "youtube" not in social_media:
                                        social_media["youtube"] = url
                            if social_media:
                                break  # Found socials, no need to continue
                    except Exception:
                        pass

            # Fallback: try to find social media links in HTML (only if not already found)
            if not social_media:
                # Look for links in sidebar section (not in footer)
                sidebar = soup.find("div", class_=re.compile(r"sidebar", re.I))
                sidebar_links = sidebar.find_all("a", href=True) if sidebar else []

                # Only check links that are NOT in footer (to avoid Framer's own social links)
                for link in sidebar_links if sidebar_links else links:
                    href = link.get("href", "")
                    if not href:
                        continue

                    # Skip links that are clearly Framer's own links
                    href_lower = href.lower()
                    if "framer.com" in href_lower and "/company/" in href_lower:
                        continue

                    # Check if it's a social media link
                    if "twitter.com" in href_lower or "x.com" in href_lower:
                        # Only add if it's not Framer's own account
                        if "/framer" not in href_lower and "/framer/" not in href_lower:
                            social_media["twitter"] = href
                    elif "linkedin.com" in href_lower:
                        # Only add if it's not Framer's company page
                        if "/company/framer" not in href_lower:
                            social_media["linkedin"] = href
                    elif "instagram.com" in href_lower:
                        # Only add if it's not Framer's own account
                        if "/framer" not in href_lower and "/framer/" not in href_lower:
                            social_media["instagram"] = href
                    elif "github.com" in href_lower:
                        social_media["github"] = href
                    elif "dribbble.com" in href_lower:
                        social_media["dribbble"] = href
                    elif "behance.net" in href_lower:
                        social_media["behance"] = href
                    elif "youtube.com" in href_lower:
                        social_media["youtube"] = href

            # Extract statistics
            stats = self._extract_statistics(soup, username)

            # Create Creator model
            creator = Creator(
                username=username,
                name=name,
                profile_url=profile_url,
                avatar_url=avatar_url,
                bio=bio,
                website=website,
                social_media=social_media,
                stats=stats,
            )

            logger.info("creator_parsed", username=username, name=name)
            return creator

        except Exception as e:
            logger.error(
                "creator_parse_error",
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def _extract_statistics(self, soup: BeautifulSoup, username: str) -> CreatorStats:
        """Extract creator statistics from profile page.

        Args:
            soup: BeautifulSoup object
            username: Creator username

        Returns:
            CreatorStats model
        """
        stats_dict = {
            "total_products": 0,
            "templates_count": 0,
            "components_count": 0,
            "vectors_count": 0,
            "plugins_count": 0,
        }

        # Find all product cards on the profile page
        # Use the same selectors as product list
        product_cards = soup.select("div.card-module-scss-module__P62yvW__card")
        if not product_cards:
            # Try alternative selectors
            product_cards = soup.select('a[href^="/marketplace/"]')

        # Count products by type
        for card in product_cards:
            # Try to find link to product
            link = card.find(
                "a", href=re.compile(r"/marketplace/(templates|components|vectors|plugins)/")
            )
            if link:
                href = link.get("href", "")
                # Determine product type from URL
                if "/marketplace/templates/" in href:
                    stats_dict["templates_count"] += 1
                elif "/marketplace/components/" in href:
                    stats_dict["components_count"] += 1
                elif "/marketplace/vectors/" in href:
                    stats_dict["vectors_count"] += 1
                elif "/marketplace/plugins/" in href:
                    stats_dict["plugins_count"] += 1

        # Calculate total
        stats_dict["total_products"] = (
            stats_dict["templates_count"]
            + stats_dict["components_count"]
            + stats_dict["vectors_count"]
            + stats_dict["plugins_count"]
        )

        # Try to find "See All" link to determine if there are more products
        see_all_link = soup.find("a", string=re.compile(r"See All|View All", re.I))
        if see_all_link:
            # If "See All" exists, there might be more products than visible
            # We can't determine exact count, but we know there are at least the visible ones
            pass

        return CreatorStats(**stats_dict)
