"""Script to update categories column in products table from JSON files."""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from src.config.settings import settings


def load_all_products_from_json(base_path: Path, product_type=None):
    """Load all products from JSON files."""
    products = []
    product_type_map = {
        "template": "templates",
        "component": "components",
        "vector": "vectors",
        "plugin": "plugins",
    }

    if product_type:
        subdirs = [product_type_map.get(product_type, "templates")]
    else:
        subdirs = product_type_map.values()

    for subdir in subdirs:
        products_dir = base_path / "products" / subdir
        if products_dir.exists():
            for json_file in products_dir.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        products.append(json.load(f))
                except (json.JSONDecodeError, IOError):
                    continue

    return products


def update_categories_from_json():
    """Update categories column in products table from JSON files."""
    if not settings.database_url:
        print("ERROR: DATABASE_URL not configured")
        return False

    # Check if JSON files exist
    data_path = Path(settings.data_path)
    if not data_path.exists():
        print(f"WARNING: Data path does not exist: {data_path}")
        print("Skipping update - will be populated on next scrape")
        return True

    try:
        engine = create_engine(
            settings.database_url,
            poolclass=NullPool,
            connect_args={"connect_timeout": 10},
        )

        # Load all products from JSON
        print("Loading products from JSON files...")
        products = load_all_products_from_json(data_path)
        
        if not products:
            print("No products found in JSON files")
            return True

        print(f"Found {len(products)} products in JSON files")

        # Update products in database (each in separate transaction to avoid rollback)
        updated_count = 0
        failed_count = 0
        
        for product in products:
            product_id = product.get("id")
            if not product_id:
                continue

            # Get categories from JSON
            categories_list = product.get("categories", [])
            if not categories_list and product.get("category"):
                categories_list = [product.get("category")]

            if not categories_list:
                continue

            # Update categories in database (separate transaction for each)
            try:
                categories_json = json.dumps(categories_list)
                update_query = text("""
                    UPDATE products 
                    SET categories = CAST(:categories AS jsonb)
                    WHERE id = :id
                """)
                
                with engine.begin() as conn:
                    result = conn.execute(update_query, {
                        "id": product_id,
                        "categories": categories_json
                    })
                    if result.rowcount > 0:
                        updated_count += 1
                        
            except Exception as e:
                failed_count += 1
                if failed_count <= 10:  # Show first 10 errors
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
    success = update_categories_from_json()
    sys.exit(0 if success else 1)

