"""Update products without categories using main category as fallback."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from src.config.settings import settings


def update_missing_categories():
    """Update products without categories using main category."""
    if not settings.database_url:
        print("ERROR: DATABASE_URL not configured")
        return False

    try:
        engine = create_engine(
            settings.database_url,
            poolclass=NullPool,
            connect_args={"connect_timeout": 10},
        )

        with engine.connect() as conn:
            # Get products without categories but with main category
            select_query = text("""
                SELECT id, category
                FROM products
                WHERE (categories IS NULL OR categories = 'null'::jsonb)
                AND category IS NOT NULL
            """)
            result = conn.execute(select_query)
            products = result.fetchall()

            if not products:
                print("No products to update")
                return True

            print(f"Found {len(products)} products to update")

            updated_count = 0
            failed_count = 0

            for product_id, category in products:
                try:
                    # Use main category as single-item list
                    categories_json = json.dumps([category])
                    
                    update_query = text("""
                        UPDATE products 
                        SET categories = CAST(:categories AS jsonb)
                        WHERE id = :id
                    """)
                    
                    with engine.begin() as conn_update:
                        result = conn_update.execute(update_query, {
                            "id": product_id,
                            "categories": categories_json
                        })
                        if result.rowcount > 0:
                            updated_count += 1
                            
                except Exception as e:
                    failed_count += 1
                    if failed_count <= 5:
                        print(f"Warning: Failed to update product {product_id}: {str(e)}")
                    continue

            print(f"Successfully updated {updated_count} products with categories")
            if failed_count > 0:
                print(f"Failed to update {failed_count} products")
            
            return True

    except SQLAlchemyError as e:
        print(f"ERROR: Database update failed: {str(e)}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    success = update_missing_categories()
    sys.exit(0 if success else 1)

