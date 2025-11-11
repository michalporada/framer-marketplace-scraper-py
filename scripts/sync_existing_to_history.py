#!/usr/bin/env python3
"""Script to sync existing products from products table to product_history table."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import DatabaseStorage
from src.models.product import Product
from api.dependencies import get_db_engine
from sqlalchemy import text
from src.utils.logger import get_logger

logger = get_logger(__name__)


def db_row_to_product_dict(row: dict) -> dict:
    """Convert database row to product dict for Product model."""
    return {
        "id": row["id"],
        "name": row["name"],
        "type": row["type"],
        "category": row.get("category"),
        "url": row["url"],
        "price": row.get("price"),
        "currency": row.get("currency", "USD"),
        "is_free": row.get("is_free", False),
        "description": row.get("description"),
        "short_description": row.get("short_description"),
        "scraped_at": row.get("scraped_at"),
        # Stats
        "views_raw": row.get("views_raw"),
        "views_normalized": row.get("views_normalized"),
        "pages_raw": row.get("pages_raw"),
        "pages_normalized": row.get("pages_normalized"),
        "users_raw": row.get("users_raw"),
        "users_normalized": row.get("users_normalized"),
        "installs_raw": row.get("installs_raw"),
        "installs_normalized": row.get("installs_normalized"),
        "vectors_raw": row.get("vectors_raw"),
        "vectors_normalized": row.get("vectors_normalized"),
        # Metadata
        "published_date_raw": row.get("published_date_raw"),
        "published_date_normalized": row.get("published_date_normalized"),
        "last_updated_raw": row.get("last_updated_raw"),
        "last_updated_normalized": row.get("last_updated_normalized"),
        "version": row.get("version"),
        # Features
        "features_list": row.get("features_list"),
        "is_responsive": row.get("is_responsive", False),
        "has_animations": row.get("has_animations", False),
        "cms_integration": row.get("cms_integration", False),
        "pages_count": row.get("pages_count"),
        # Media
        "thumbnail_url": row.get("thumbnail_url"),
        "screenshots_count": row.get("screenshots_count"),
        # Creator
        "creator_username": row.get("creator_username"),
        "creator_name": row.get("creator_name"),
        "creator_url": row.get("creator_url"),
    }


async def sync_existing_products_to_history():
    """Sync all existing products from products table to product_history."""
    db_storage = DatabaseStorage()

    if not db_storage.is_available():
        logger.error("database_not_available")
        print("❌ Database not available")
        return False

    engine = get_db_engine()
    if not engine:
        logger.error("database_engine_not_available")
        print("❌ Database engine not available")
        return False

    # Get all products from products table
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM products ORDER BY scraped_at DESC"))
        products_rows = result.fetchall()
        products_count = len(products_rows)

    if products_count == 0:
        print("ℹ️  No products found in products table")
        return True

    print(f"📊 Found {products_count} products to sync to history")

    # Check how many are already in history
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(DISTINCT product_id) FROM product_history"))
        existing_count = result.fetchone()[0]

    print(f"📊 Products already in history: {existing_count}")
    print(f"📊 Products to sync: {products_count - existing_count}")

    # Ask for confirmation
    response = input("\n⚠️  This will add all products to history. Continue? (y/n): ")
    if response.lower() != "y":
        print("❌ Cancelled")
        return False

    # Convert rows to dicts
    products_dicts = [dict(row._mapping) for row in products_rows]

    # Load products from JSON files to get full Product models
    # (We need full models because history save uses _prepare_product_data)
    from src.storage.file_storage import FileStorage
    from src.models.product import (
        ProductStats,
        ProductMetadata,
        ProductFeatures,
        ProductMedia,
        NormalizedStatistic,
    )
    from src.models.creator import Creator
    from datetime import datetime

    file_storage = FileStorage()
    synced_count = 0
    failed_count = 0

    print("\n🔄 Syncing products to history...")

    for idx, product_dict in enumerate(products_dicts):
        try:
            # Try to load from JSON first (has full data)
            product_id = product_dict["id"]
            product_type = product_dict["type"]

            json_file = file_storage.get_product_dir(product_type) / f"{product_id}.json"

            if json_file.exists():
                import json

                with open(json_file, "r") as f:
                    json_data = json.load(f)

                # Create Product from JSON
                product = Product(**json_data)
            else:
                # Create Product from DB row (limited data)
                # This is a fallback - we'll create a minimal Product
                from pydantic import HttpUrl

                stats = ProductStats()
                if product_dict.get("views_raw") or product_dict.get("views_normalized"):
                    stats.views = NormalizedStatistic(
                        raw=product_dict.get("views_raw", ""),
                        normalized=product_dict.get("views_normalized"),
                    )
                if product_dict.get("pages_raw") or product_dict.get("pages_normalized"):
                    stats.pages = NormalizedStatistic(
                        raw=product_dict.get("pages_raw", ""),
                        normalized=product_dict.get("pages_normalized"),
                    )
                # ... add other stats similarly

                metadata = ProductMetadata()
                if product_dict.get("version"):
                    metadata.version = product_dict["version"]

                features = ProductFeatures()
                if product_dict.get("features_list"):
                    features.features = [
                        f.strip() for f in product_dict["features_list"].split(",") if f.strip()
                    ]
                features.is_responsive = product_dict.get("is_responsive", False)
                features.has_animations = product_dict.get("has_animations", False)
                features.cms_integration = product_dict.get("cms_integration", False)
                features.pages_count = product_dict.get("pages_count")

                media = ProductMedia()
                if product_dict.get("thumbnail_url"):
                    media.thumbnail = HttpUrl(product_dict["thumbnail_url"])

                creator = None
                if product_dict.get("creator_username"):
                    creator = Creator(
                        username=product_dict["creator_username"],
                        name=product_dict.get("creator_name"),
                        profile_url=HttpUrl(product_dict.get("creator_url", "")),
                    )

                scraped_at = product_dict.get("scraped_at")
                if isinstance(scraped_at, str):
                    try:
                        scraped_at = datetime.fromisoformat(scraped_at.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        scraped_at = datetime.utcnow()
                elif scraped_at is None:
                    scraped_at = datetime.utcnow()

                product = Product(
                    id=product_dict["id"],
                    name=product_dict["name"],
                    type=product_dict["type"],
                    category=product_dict.get("category"),
                    url=HttpUrl(product_dict["url"]),
                    price=product_dict.get("price"),
                    currency=product_dict.get("currency", "USD"),
                    is_free=product_dict.get("is_free", False),
                    description=product_dict.get("description"),
                    short_description=product_dict.get("short_description"),
                    creator=creator,
                    stats=stats,
                    metadata=metadata,
                    features=features,
                    media=media,
                    scraped_at=scraped_at,
                )

            # Save to history
            success = await db_storage.save_product_history_db(product)
            if success:
                synced_count += 1
                if synced_count % 100 == 0:
                    print(f"  ✅ Synced {synced_count}/{products_count} products...")
            else:
                failed_count += 1
                logger.warning("sync_failed", product_id=product_id)

        except Exception as e:
            failed_count += 1
            logger.error(
                "sync_error",
                product_id=product_dict.get("id", "unknown"),
                error=str(e),
                error_type=type(e).__name__,
            )

    print("\n✅ Sync completed!")
    print(f"   Synced: {synced_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Total: {products_count}")

    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM product_history"))
        history_count = result.fetchone()[0]
        print(f"\n📊 Total records in product_history: {history_count}")

    return True


if __name__ == "__main__":
    asyncio.run(sync_existing_products_to_history())
