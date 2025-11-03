#!/usr/bin/env python3
"""Script to setup database schema for storing scraped data (optional)."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def setup_postgresql():
    """Setup PostgreSQL database schema."""
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError

        if not settings.database_url:
            logger.error("database_url_not_configured")
            print("ERROR: DATABASE_URL not configured in .env file")
            return False

        engine = create_engine(settings.database_url)

        # Create tables schema
        schema_sql = """
        -- Products table
        CREATE TABLE IF NOT EXISTS products (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(500) NOT NULL,
            type VARCHAR(50) NOT NULL,
            category VARCHAR(255),
            url TEXT NOT NULL UNIQUE,
            price DECIMAL(10, 2),
            currency VARCHAR(10) DEFAULT 'USD',
            is_free BOOLEAN DEFAULT FALSE,
            description TEXT,
            short_description TEXT,
            creator_username VARCHAR(255),
            creator_name VARCHAR(255),
            creator_url TEXT,
            views_raw VARCHAR(50),
            views_normalized INTEGER,
            pages_raw VARCHAR(50),
            pages_normalized INTEGER,
            users_raw VARCHAR(50),
            users_normalized INTEGER,
            installs_raw VARCHAR(50),
            installs_normalized INTEGER,
            vectors_raw VARCHAR(50),
            vectors_normalized INTEGER,
            published_date_raw VARCHAR(100),
            published_date_normalized TIMESTAMP,
            last_updated_raw VARCHAR(100),
            last_updated_normalized TIMESTAMP,
            version VARCHAR(50),
            features_list TEXT,
            is_responsive BOOLEAN,
            has_animations BOOLEAN,
            cms_integration BOOLEAN,
            pages_count INTEGER,
            thumbnail_url TEXT,
            screenshots_count INTEGER,
            average_rating DECIMAL(3, 2),
            total_reviews INTEGER,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Creators table
        CREATE TABLE IF NOT EXISTS creators (
            username VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255),
            profile_url TEXT NOT NULL UNIQUE,
            avatar_url TEXT,
            bio TEXT,
            website TEXT,
            social_media JSONB,
            total_products INTEGER DEFAULT 0,
            templates_count INTEGER DEFAULT 0,
            components_count INTEGER DEFAULT 0,
            vectors_count INTEGER DEFAULT 0,
            plugins_count INTEGER DEFAULT 0,
            total_sales INTEGER,
            average_rating DECIMAL(3, 2),
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Reviews table
        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,
            product_id VARCHAR(255) REFERENCES products(id) ON DELETE CASCADE,
            author VARCHAR(255) NOT NULL,
            author_url TEXT,
            rating DECIMAL(3, 2) NOT NULL,
            content TEXT NOT NULL,
            date TIMESTAMP,
            attachments JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Categories table
        CREATE TABLE IF NOT EXISTS categories (
            slug VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            url TEXT NOT NULL UNIQUE,
            description TEXT,
            product_count INTEGER,
            product_types JSONB,
            parent_category VARCHAR(255),
            subcategories JSONB,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_products_type ON products(type);
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
        CREATE INDEX IF NOT EXISTS idx_products_creator ON products(creator_username);
        CREATE INDEX IF NOT EXISTS idx_products_scraped_at ON products(scraped_at);
        CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);
        CREATE INDEX IF NOT EXISTS idx_creators_scraped_at ON creators(scraped_at);
        """
        with engine.connect() as conn:
            conn.execute(text(schema_sql))
            conn.commit()

        logger.info("database_schema_created")
        print("✓ Database schema created successfully!")
        return True

    except ImportError:
        logger.error("sqlalchemy_not_installed")
        print("ERROR: sqlalchemy and psycopg2-binary not installed")
        print("Install with: pip install sqlalchemy psycopg2-binary")
        return False
    except SQLAlchemyError as e:
        logger.error("database_setup_error", error=str(e))
        print(f"ERROR: Database setup failed: {e}")
        return False
    except Exception as e:
        logger.error("unexpected_error", error=str(e))
        print(f"ERROR: Unexpected error: {e}")
        return False


def setup_mongodb():
    """Setup MongoDB collections (optional, if using MongoDB)."""
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure

        if not settings.database_url:
            logger.error("database_url_not_configured")
            print("ERROR: DATABASE_URL not configured in .env file")
            return False

        client = MongoClient(settings.database_url)
        db = client.get_database()

        # MongoDB doesn't require explicit schema, but we can create indexes
        db.products.create_index("id", unique=True)
        db.products.create_index("type")
        db.products.create_index("category")
        db.products.create_index("creator_username")
        db.products.create_index("scraped_at")

        db.creators.create_index("username", unique=True)
        db.creators.create_index("scraped_at")

        db.reviews.create_index("product_id")
        db.reviews.create_index("author")

        db.categories.create_index("slug", unique=True)
        db.categories.create_index("name")

        logger.info("mongodb_indexes_created")
        print("✓ MongoDB indexes created successfully!")
        return True

    except ImportError:
        logger.error("pymongo_not_installed")
        print("ERROR: pymongo not installed")
        print("Install with: pip install pymongo")
        return False
    except ConnectionFailure as e:
        logger.error("mongodb_connection_failed", error=str(e))
        print(f"ERROR: MongoDB connection failed: {e}")
        return False
    except Exception as e:
        logger.error("unexpected_error", error=str(e))
        print(f"ERROR: Unexpected error: {e}")
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Setup database schema for scraper")
    parser.add_argument(
        "--db-type",
        type=str,
        choices=["postgresql", "mongodb"],
        default="postgresql",
        help="Database type (default: postgresql)",
    )

    args = parser.parse_args()

    if args.db_type == "postgresql":
        success = setup_postgresql()
    elif args.db_type == "mongodb":
        success = setup_mongodb()
    else:
        print(f"ERROR: Unsupported database type: {args.db_type}")
        success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

