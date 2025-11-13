"""Migration script to add categories JSONB column to products table."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from src.config.settings import settings


def add_categories_column():
    """Add categories JSONB column to products table if it doesn't exist."""
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
            # Check if column already exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='products' AND column_name='categories'
            """)
            result = conn.execute(check_query)
            if result.fetchone():
                print("Column 'categories' already exists, skipping migration")
                conn.commit()
                return True

            # Add categories column
            alter_query = text("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS categories JSONB
            """)
            conn.execute(alter_query)
            conn.commit()
            print("Successfully added 'categories' column to products table")

            # Create index for better query performance
            index_query = text("""
                CREATE INDEX IF NOT EXISTS idx_products_categories 
                ON products USING GIN (categories)
            """)
            conn.execute(index_query)
            conn.commit()
            print("Successfully created GIN index on categories column")

            return True

    except SQLAlchemyError as e:
        print(f"ERROR: Database migration failed: {str(e)}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    success = add_categories_column()
    sys.exit(0 if success else 1)

