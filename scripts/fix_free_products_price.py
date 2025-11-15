"""Script to fix products that have price but should be free.

This script:
1. Finds products with price != NULL and is_free = FALSE (potentially incorrect)
2. Re-scrapes them with the improved parser
3. Updates database with correct price/is_free values
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from src.config.settings import settings
from src.parsers.product_parser import ProductParser
from src.scrapers.product_scraper import ProductScraper
from src.storage.database import DatabaseStorage
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def fix_free_products_price(limit: Optional[int] = None):
    """Fix products that have price but should be free.
    
    Args:
        limit: Optional limit on number of products to process
    """
    if not settings.database_url:
        print("ERROR: DATABASE_URL not configured")
        return False

    try:
        engine = create_engine(
            settings.database_url,
            poolclass=NullPool,
            connect_args={"connect_timeout": 10},
        )

        # Find products with price != NULL and is_free = FALSE
        # These might be incorrectly marked as paid when they're actually free
        with engine.connect() as conn:
            select_query = text("""
                SELECT id, name, url, price, is_free, type
                FROM products
                WHERE price IS NOT NULL
                AND is_free = FALSE
                ORDER BY type, name
            """)
            result = conn.execute(select_query)
            products = result.fetchall()

            if not products:
                print("No products to fix (all products have correct price data)")
                return True

            # Apply limit if specified
            if limit and limit > 0:
                products = products[:limit]
                print(f"Limited to first {limit} products (use --limit N to change)")

            print(f"Found {len(products)} products with price that need verification")
            print("These products will be re-scraped with improved parser to check if they're actually free\n")

            # Initialize storage (no async initialization needed)
            storage = DatabaseStorage()
            
            if not storage.is_available():
                print("ERROR: Database not available")
                return False

            fixed_count = 0
            failed_count = 0
            unchanged_count = 0

            # Initialize parser
            parser = ProductParser()

            async with ProductScraper() as scraper:
                for idx, (product_id, name, url, price, is_free, product_type) in enumerate(products, 1):
                    print(f"[{idx}/{len(products)}] Checking: {name} ({product_id})")
                    print(f"  Current: price={price}, is_free={is_free}")
                    print(f"  URL: {url}")

                    try:
                        # Scrape product page
                        product_data = await scraper.scrape(url)
                        if not product_data:
                            print(f"  ⚠️  Failed to scrape product page")
                            failed_count += 1
                            continue

                        # Parse HTML with improved parser
                        product = parser.parse(
                            product_data["html"],
                            product_data["url"],
                            product_data["type"],
                        )

                        if not product:
                            print(f"  ⚠️  Failed to scrape product")
                            failed_count += 1
                            continue

                        # Check if price changed
                        new_price = product.price
                        new_is_free = product.is_free

                        if new_price == price and new_is_free == is_free:
                            print(f"  ✓ No change needed (price={new_price}, is_free={new_is_free})")
                            unchanged_count += 1
                        else:
                            print(f"  🔧 Fixing: price={price}→{new_price}, is_free={is_free}→{new_is_free}")

                            # Save to database (will update price and is_free)
                            success = await storage.save_product_db(product)
                            if success:
                                print(f"  ✓ Updated in database")
                                fixed_count += 1
                            else:
                                print(f"  ✗ Failed to update database")
                                failed_count += 1

                    except Exception as e:
                        print(f"  ✗ Error: {type(e).__name__}: {str(e)}")
                        failed_count += 1
                        logger.error(
                            "fix_product_error",
                            product_id=product_id,
                            error=str(e),
                            error_type=type(e).__name__,
                        )

                    print()  # Empty line for readability

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total products checked: {len(products)}")
        print(f"✓ Fixed: {fixed_count}")
        print(f"✓ Unchanged: {unchanged_count}")
        print(f"✗ Failed: {failed_count}")
        print("=" * 60)

        return True

    except SQLAlchemyError as e:
        print(f"ERROR: Database error: {str(e)}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function."""
    print("=" * 60)
    print("Fix Free Products Price")
    print("=" * 60)
    print()
    print("This script will:")
    print("1. Find products with price != NULL and is_free = FALSE")
    print("2. Re-scrape them with improved parser")
    print("3. Update database if price/is_free changed")
    print()
    print("The improved parser now correctly detects 'Free' in button text")
    print("and avoids picking prices from 'More from' sections.")
    print()

    # Check for --yes flag
    auto_confirm = "--yes" in sys.argv or "-y" in sys.argv
    
    # Check for limit
    limit = None
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            try:
                limit = int(sys.argv[idx + 1])
            except ValueError:
                pass
    
    if not auto_confirm:
        # Ask for confirmation
        try:
            response = input("Continue? (y/N): ").strip().lower()
            if response != "y":
                print("Cancelled.")
                return 0
        except EOFError:
            print("No input available. Use --yes flag for non-interactive mode.")
            return 1
    else:
        print("Auto-confirmed (--yes flag used)")

    print()
    success = await fix_free_products_price(limit=limit)

    if success:
        print("\n✅ Script completed successfully!")
        print("\nNote: Next full scrape will automatically fix all remaining cases")
        print("      thanks to the improved parser.")
        return 0
    else:
        print("\n❌ Script failed!")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))

