"""Creator parser for extracting data from creator profile HTML pages."""

import re
from typing import Optional

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
                # Remove "Creator" suffix if present
                name = re.sub(r"\s+Creator\s*$", "", name, flags=re.IGNORECASE)

            if not name:
                # Try meta og:title
                og_title = soup.find("meta", property="og:title")
                if og_title:
                    name = og_title.get("content", "").strip()
                    # Remove common suffixes
                    name = re.sub(r"\s*[-|]\s*Framer.*$", "", name, flags=re.IGNORECASE)
                    # Remove "Creator" suffix if present
                    name = re.sub(r"\s+Creator\s*$", "", name, flags=re.IGNORECASE)

            # Extract avatar
            avatar_url = None
            # Try og:image
            og_image = soup.find("meta", property="og:image")
            if og_image:
                avatar_url = og_image.get("content", "")
                if avatar_url:
                    # Decode Next.js Image URL if needed
                    avatar_url = self._product_parser.decode_nextjs_image_url(avatar_url)

            if not avatar_url:
                # Try img with alt containing username or "avatar"
                img = soup.find("img", alt=re.compile(r"avatar|profile", re.I))
                if img:
                    avatar_url = img.get("src") or img.get("data-src")
                    if avatar_url:
                        # Decode Next.js Image URL if needed
                        avatar_url = self._product_parser.decode_nextjs_image_url(avatar_url)

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

            # Extract social media links
            social_media = {}
            for link in links:
                href = link.get("href", "")
                text = link.get_text().strip().lower()

                # Twitter/X
                if "twitter.com" in href.lower() or "x.com" in href.lower():
                    social_media["twitter"] = href
                # LinkedIn
                elif "linkedin.com" in href.lower():
                    social_media["linkedin"] = href
                # Instagram
                elif "instagram.com" in href.lower():
                    social_media["instagram"] = href
                # GitHub
                elif "github.com" in href.lower():
                    social_media["github"] = href
                # Dribbble
                elif "dribbble.com" in href.lower():
                    social_media["dribbble"] = href
                # Behance
                elif "behance.net" in href.lower():
                    social_media["behance"] = href

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

        # Extract average rating if available
        # Look for rating text or stars
        rating_text = soup.find(string=re.compile(r"rating|stars?", re.I))
        if rating_text:
            # Try to extract numeric rating
            rating_match = re.search(r"([\d.]+)\s*(?:stars?|rating)", rating_text, re.IGNORECASE)
            if rating_match:
                try:
                    stats_dict["average_rating"] = float(rating_match.group(1))
                except ValueError:
                    pass

        return CreatorStats(**stats_dict)
