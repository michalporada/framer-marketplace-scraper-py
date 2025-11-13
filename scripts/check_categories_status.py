"""Check how many products have categories filled in production database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from src.config.settings import settings


def check_categories_status():
    """Check status of categories column in production."""
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
            # Check total products
            total_query = text("SELECT COUNT(*) FROM products")
            total_result = conn.execute(total_query)
            total = total_result.scalar()

            # Check products with categories
            with_categories_query = text("""
                SELECT COUNT(*) 
                FROM products 
                WHERE categories IS NOT NULL AND categories != 'null'::jsonb
            """)
            with_categories_result = conn.execute(with_categories_query)
            with_categories = with_categories_result.scalar()

            # Check products without categories
            without_categories = total - with_categories

            print(f"Total products: {total}")
            print(f"Products with categories: {with_categories}")
            print(f"Products without categories: {without_categories}")
            print(f"Coverage: {(with_categories/total*100):.1f}%" if total > 0 else "N/A")

            return True

    except SQLAlchemyError as e:
        print(f"ERROR: Database query failed: {str(e)}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    success = check_categories_status()
    sys.exit(0 if success else 1)

