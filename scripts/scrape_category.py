#!/usr/bin/env python3
"""Script to scrape products from a specific category."""

import asyncio
import sys
import os
from pathlib import Path
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

from src.scrapers.category_scraper import CategoryScraper
from src.scrapers.marketplace_scraper import MarketplaceScraper
from src.parsers.category_parser import CategoryParser
from src.utils.logger import get_logger

logger = get_logger(__name__)


def extract_product_urls_from_category(html: str, category_url: str) -> List[str]:
    """Extract all product URLs from category page.
    
    Args:
        html: HTML content of category page
        category_url: Category URL
        
    Returns:
        List of product URLs
    """
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html, "lxml")
    product_urls = []
    seen_ids = set()
    
    # Find all product links
    links = soup.find_all("a", href=re.compile(r"/marketplace/templates/[^/]+/"))
    for link in links:
        href = link.get("href", "")
        # Extract product ID
        match = re.search(r"/marketplace/templates/([^/]+)/?", href)
        if match:
            product_id = match.group(1)
            if product_id not in seen_ids and product_id not in ["category", "templates"]:
                seen_ids.add(product_id)
                # Make full URL
                if href.startswith("/"):
                    full_url = f"https://www.framer.com{href}"
                else:
                    full_url = href
                product_urls.append(full_url)
    
    return product_urls


async def scrape_category(category_url: str):
    """Scrape all products from a category.
    
    Args:
        category_url: Category URL (e.g., https://www.framer.com/marketplace/templates/category/non-profit/)
    """
    async with httpx.AsyncClient() as client:
        category_scraper = CategoryScraper(client)
        category_parser = CategoryParser()
        
        # Scrape category page
        logger.info("scraping_category", url=category_url)
        html = await category_scraper.scrape_category(category_url)
        
        if not html:
            logger.error("failed_to_scrape_category", url=category_url)
            return
        
        # Parse category
        category = category_parser.parse(html, category_url)
        if category:
            logger.info("category_parsed", name=category.name, slug=category.slug, product_count=category.product_count)
        
        # Extract product URLs
        product_urls = extract_product_urls_from_category(html, category_url)
        logger.info("products_found_in_category", count=len(product_urls), category_url=category_url)
        
        if not product_urls:
            logger.warning("no_products_found", category_url=category_url)
            return
        
        # Scrape products
        async with MarketplaceScraper() as scraper:
            logger.info("starting_product_scrape", count=len(product_urls))
            await scraper.scrape_products_batch(product_urls, limit=5, skip_processed=False)
            
            logger.info("category_scraping_completed", 
                       category=category.name if category else category_url,
                       products_scraped=len(product_urls))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/scrape_category.py <category_url>")
        print("Example: python scripts/scrape_category.py https://www.framer.com/marketplace/templates/category/non-profit/")
        sys.exit(1)
    
    category_url = sys.argv[1]
    asyncio.run(scrape_category(category_url))

