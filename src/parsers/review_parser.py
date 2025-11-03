"""Review parser for extracting review data from product HTML pages."""

import re
from typing import Optional
from datetime import datetime

from bs4 import BeautifulSoup

from src.models.review import Review
from src.utils.logger import get_logger
from src.utils.normalizers import parse_relative_date

logger = get_logger(__name__)


class ReviewParser:
    """Parser for product reviews."""

    def __init__(self):
        """Initialize review parser."""

    def parse_reviews(self, html: str, product_url: str) -> list[Review]:
        """Parse all reviews from product HTML page.

        Args:
            html: HTML content of product page
            product_url: Product URL

        Returns:
            List of Review models
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            reviews = []

            # Look for review sections
            # Reviews might be in different structures depending on Framer's implementation
            # Common patterns:
            # - Review cards/containers
            # - Review list items
            # - Structured data (JSON-LD)

            # Try to find review containers
            review_containers = soup.find_all(
                ["div", "article", "section"],
                class_=re.compile(r"review|rating|comment", re.I),
            )

            if not review_containers:
                # Try alternative selectors
                review_containers = soup.find_all("div", attrs={"data-review": True})

            for container in review_containers:
                review = self._parse_single_review(container, product_url)
                if review:
                    reviews.append(review)

            # If no structured reviews found, try to extract from text
            if not reviews:
                # Look for review-like text patterns
                reviews = self._extract_reviews_from_text(soup, product_url)

            logger.info("reviews_parsed", count=len(reviews), product_url=product_url)
            return reviews

        except Exception as e:
            logger.error(
                "review_parse_error",
                product_url=product_url,
                error=str(e),
                error_type=type(e).__name__,
            )
            return []

    def _parse_single_review(self, container, product_url: str) -> Optional[Review]:
        """Parse a single review from container element.

        Args:
            container: BeautifulSoup element containing review
            product_url: Product URL for context

        Returns:
            Review model or None
        """
        try:
            # Extract author
            author = None
            author_link = container.find("a", href=re.compile(r"/@"))
            if author_link:
                author = author_link.get_text().strip()
                author_url = author_link.get("href", "")
                if author_url.startswith("/"):
                    from src.config.settings import settings

                    author_url = f"{settings.base_url}{author_url}"
            else:
                # Try to find author name in text
                author_elem = container.find(
                    ["span", "div"], class_=re.compile(r"author|name", re.I)
                )
                if author_elem:
                    author = author_elem.get_text().strip()

            if not author:
                return None

            # Extract rating
            rating = None
            # Look for star rating
            stars = container.find_all(["span", "div"], class_=re.compile(r"star|rating", re.I))
            if stars:
                # Try to count filled stars
                filled_count = 0
                for star in stars:
                    if "filled" in star.get("class", []) or "active" in star.get("class", []):
                        filled_count += 1
                if filled_count > 0:
                    rating = float(filled_count)

            if rating is None:
                # Try to extract numeric rating from text
                rating_text = container.get_text()
                rating_match = re.search(
                    r"(\d+(?:\.\d+)?)\s*(?:out of|/)\s*5", rating_text, re.IGNORECASE
                )
                if rating_match:
                    rating = float(rating_match.group(1))
                else:
                    # Default to 0 if no rating found
                    rating = 0.0

            # Extract review content
            content = None
            # Look for review text
            content_elem = container.find(
                ["p", "div"], class_=re.compile(r"content|text|review", re.I)
            )
            if content_elem:
                content = content_elem.get_text().strip()
            else:
                # Try to get all text and clean it
                text = container.get_text()
                # Remove author and rating from text
                text = re.sub(rf"{re.escape(author)}", "", text, flags=re.IGNORECASE)
                text = re.sub(r"\d+(?:\.\d+)?\s*(?:out of|/)\s*5", "", text, flags=re.IGNORECASE)
                content = text.strip()

            if not content or len(content) < 10:
                return None

            # Extract date
            review_date = None
            date_elem = container.find(["span", "time"], class_=re.compile(r"date|time", re.I))
            if date_elem:
                date_text = date_elem.get_text().strip()
                # Try to parse relative date
                date_data = parse_relative_date(date_text)
                if date_data.get("normalized"):
                    try:
                        review_date = datetime.fromisoformat(
                            date_data["normalized"].replace("Z", "+00:00")
                        )
                    except Exception:
                        pass

            # Extract attachments (screenshots)
            attachments = []
            images = container.find_all("img")
            for img in images:
                src = img.get("src") or img.get("data-src")
                if src and "screenshot" in src.lower():
                    attachments.append(src)

            # Create Review model
            review = Review(
                author=author,
                author_url=author_url if author_link else None,
                rating=rating,
                content=content,
                date=review_date,
                attachments=attachments,
            )

            return review

        except Exception as e:
            logger.warning("single_review_parse_error", error=str(e))
            return None

    def _extract_reviews_from_text(self, soup: BeautifulSoup, product_url: str) -> list[Review]:
        """Extract reviews from unstructured text (fallback method).

        Args:
            soup: BeautifulSoup object
            product_url: Product URL

        Returns:
            List of Review models
        """
        reviews = []
        # This is a fallback method if structured reviews are not found
        # It might not be very reliable, but can extract some basic information
        # Implementation depends on actual HTML structure of Framer reviews
        return reviews
