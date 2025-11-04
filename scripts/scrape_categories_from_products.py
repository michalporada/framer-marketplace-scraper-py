#!/usr/bin/env python3
"""Script to scrape categories extracted from scraped products."""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Set

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.marketplace_scraper import MarketplaceScraper
from src.utils.logger import get_logger

logger = get_logger(__name__)


def extract_categories_from_products() -> Set[str]:
    """Extract all unique categories from scraped products.
    
    Returns:
        Set of category names
    """
    categories = set()
    product_types = ['templates', 'components', 'vectors', 'plugins']
    data_dir = Path('data/products')
    
    for product_type in product_types:
        product_dir = data_dir / product_type
        if not product_dir.exists():
            continue
        
        for json_file in product_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    product = json.load(f)
                    if 'categories' in product and product['categories']:
                        categories.update(product['categories'])
            except Exception as e:
                logger.debug("failed_to_read_product", file=str(json_file), error=str(e))
                continue
    
    return categories


def category_name_to_urls(category_name: str) -> List[str]:
    """Convert category name to possible category URLs.
    
    Args:
        category_name: Category name (e.g., "Non-profit")
        
    Returns:
        List of possible category URLs to try
    """
    # Convert to slug format
    slug = category_name.lower().replace(" ", "-").replace("&", "").strip()
    
    # Generate URLs for different product types
    urls = []
    for product_type in ['templates', 'components', 'vectors', 'plugins']:
        urls.append(f"/marketplace/{product_type}/category/{slug}/")
    
    # Also try generic category URL
    urls.append(f"/marketplace/category/{slug}/")
    
    return urls


async def scrape_categories_from_products():
    """Scrape categories extracted from scraped products."""
    # Extract categories from products
    logger.info("extracting_categories_from_products")
    categories = extract_categories_from_products()
    
    if not categories:
        logger.warning("no_categories_found_in_products")
        return
    
    logger.info("categories_extracted", count=len(categories))
    
    # Convert category names to URLs
    category_urls = []
    for category in categories:
        urls = category_name_to_urls(category)
        # Use the templates category URL as primary (most common)
        category_urls.append(urls[0])  # templates/category/{slug}/
    
    logger.info("category_urls_generated", count=len(category_urls))
    
    # Scrape categories
    async with MarketplaceScraper() as scraper:
        logger.info("starting_category_scrape", count=len(category_urls))
        await scraper.scrape_categories_batch(
            category_urls, 
            limit=5, 
            skip_processed=False
        )
        
        logger.info("category_scraping_completed", 
                   categories_scraped=len(category_urls))


if __name__ == "__main__":
    asyncio.run(scrape_categories_from_products())

