#!/usr/bin/env python3
"""Sync scraped data from JSON files to PostgreSQL database.

This script reads all products and creators from JSON files and imports them
into the Supabase database. It's safe to run multiple times (uses ON CONFLICT).
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.models.creator import Creator
from src.models.product import Product
from src.storage.database import DatabaseStorage
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_product_from_json(filepath: Path) -> Optional[Product]:
    """Load Product model from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        Product model or None if error
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Product(**data)
    except Exception as e:
        logger.warning("failed_to_load_product", filepath=str(filepath), error=str(e))
        return None


def load_creator_from_json(filepath: Path) -> Optional[Creator]:
    """Load Creator model from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        Creator model or None if error
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Creator(**data)
    except Exception as e:
        logger.warning("failed_to_load_creator", filepath=str(filepath), error=str(e))
        return None


async def sync_products(db_storage: DatabaseStorage, data_dir: Path) -> dict:
    """Sync all products from JSON files to database using batch inserts.

    Args:
        db_storage: DatabaseStorage instance
        data_dir: Path to data directory

    Returns:
        Dictionary with sync statistics
    """
    product_types = ["templates", "components", "vectors", "plugins"]
    stats = {"total": 0, "success": 0, "failed": 0, "skipped": 0}
    BATCH_SIZE = 100  # Number of products to insert in one batch

    for product_type in product_types:
        product_dir = data_dir / "products" / product_type
        if not product_dir.exists():
            logger.info("product_dir_not_found", product_type=product_type)
            continue

        json_files = list(product_dir.glob("*.json"))
        logger.info("syncing_products", product_type=product_type, count=len(json_files))

        # Collect products in batches
        batch = []
        for json_file in json_files:
            stats["total"] += 1
            product = load_product_from_json(json_file)

            if not product:
                stats["failed"] += 1
                continue

            batch.append(product)

            # Save batch when it reaches BATCH_SIZE
            if len(batch) >= BATCH_SIZE:
                saved_count = await db_storage.save_products_batch_db(batch)
                stats["success"] += saved_count
                if saved_count < len(batch):
                    stats["failed"] += len(batch) - saved_count
                
                if stats["success"] % 500 == 0:
                    logger.info("sync_progress", products_synced=stats["success"], total=stats["total"])
                
                batch = []

        # Save remaining products in batch
        if batch:
            saved_count = await db_storage.save_products_batch_db(batch)
            stats["success"] += saved_count
            if saved_count < len(batch):
                stats["failed"] += len(batch) - saved_count

    return stats


async def sync_creators(db_storage: DatabaseStorage, data_dir: Path) -> dict:
    """Sync all creators from JSON files to database using batch inserts.

    Args:
        db_storage: DatabaseStorage instance
        data_dir: Path to data directory

    Returns:
        Dictionary with sync statistics
    """
    creators_dir = data_dir / "creators"
    if not creators_dir.exists():
        logger.info("creators_dir_not_found")
        return {"total": 0, "success": 0, "failed": 0}

    json_files = list(creators_dir.glob("*.json"))
    logger.info("syncing_creators", count=len(json_files))

    stats = {"total": len(json_files), "success": 0, "failed": 0}
    BATCH_SIZE = 50  # Number of creators to insert in one batch

    # Collect creators in batches
    batch = []
    for json_file in json_files:
        creator = load_creator_from_json(json_file)

        if not creator:
            stats["failed"] += 1
            continue

        batch.append(creator)

        # Save batch when it reaches BATCH_SIZE
        if len(batch) >= BATCH_SIZE:
            saved_count = await db_storage.save_creators_batch_db(batch)
            stats["success"] += saved_count
            if saved_count < len(batch):
                stats["failed"] += len(batch) - saved_count
            
            if stats["success"] % 50 == 0:
                logger.info("sync_progress", creators_synced=stats["success"], total=stats["total"])
            
            batch = []

    # Save remaining creators in batch
    if batch:
        saved_count = await db_storage.save_creators_batch_db(batch)
        stats["success"] += saved_count
        if saved_count < len(batch):
            stats["failed"] += len(batch) - saved_count

    return stats


async def main():
    """Main sync function."""
    # Check if DATABASE_URL is configured
    if not settings.database_url:
        logger.error(
            "database_url_not_configured",
            message="DATABASE_URL not configured. Please set it in .env or environment variables.",
        )
        return

    # Initialize database storage
    db_storage = DatabaseStorage()
    if not db_storage.is_available():
        logger.error("database_not_available", message="Database connection failed. Check DATABASE_URL.")
        return

    logger.info("sync_started", database_url=settings.database_url[:30] + "...")

    # Get data directory
    data_dir = settings.data_path

    # Sync products
    logger.info("syncing_products_start")
    product_stats = await sync_products(db_storage, data_dir)
    logger.info(
        "products_sync_completed",
        total=product_stats["total"],
        success=product_stats["success"],
        failed=product_stats["failed"],
    )

    # Sync creators
    logger.info("syncing_creators_start")
    creator_stats = await sync_creators(db_storage, data_dir)
    logger.info(
        "creators_sync_completed",
        total=creator_stats["total"],
        success=creator_stats["success"],
        failed=creator_stats["failed"],
    )

    # Summary
    logger.info(
        "sync_completed",
        products=product_stats,
        creators=creator_stats,
        total_synced=product_stats["success"] + creator_stats["success"],
    )

    print("\n" + "=" * 60)
    print("SYNC SUMMARY")
    print("=" * 60)
    print(f"Products: {product_stats['success']}/{product_stats['total']} synced")
    print(f"Creators: {creator_stats['success']}/{creator_stats['total']} synced")
    print(f"Total: {product_stats['success'] + creator_stats['success']} items synced")
    if product_stats["failed"] > 0 or creator_stats["failed"] > 0:
        print(f"Failed: {product_stats['failed'] + creator_stats['failed']} items")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

