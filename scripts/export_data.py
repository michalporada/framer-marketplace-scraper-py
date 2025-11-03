#!/usr/bin/env python3
"""Script to export scraped data to CSV format."""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_products_from_directory(data_dir: Path, product_type: Optional[str] = None) -> List[dict]:
    """Load all product JSON files from directory.

    Args:
        data_dir: Directory containing product JSON files
        product_type: Filter by product type (template/component/vector/plugin) or None for all

    Returns:
        List of product dictionaries
    """
    products = []
    product_types = ["templates", "components", "vectors", "plugins"] if not product_type else [product_type]

    for ptype in product_types:
        type_dir = data_dir / "products" / ptype
        if not type_dir.exists():
            continue

        for json_file in type_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    product = json.load(f)
                    products.append(product)
            except Exception as e:
                logger.warning("failed_to_load_product", file=str(json_file), error=str(e))

    return products


def flatten_product(product: dict) -> dict:
    """Flatten nested product structure for CSV export.

    Args:
        product: Product dictionary

    Returns:
        Flattened dictionary
    """
    flattened = {
        "id": product.get("id"),
        "name": product.get("name"),
        "type": product.get("type"),
        "category": product.get("category"),
        "url": product.get("url"),
        "price": product.get("price"),
        "currency": product.get("currency"),
        "is_free": product.get("is_free"),
        "description": product.get("description"),
        "short_description": product.get("short_description"),
    }

    # Flatten creator
    creator = product.get("creator")
    if creator:
        flattened["creator_username"] = creator.get("username")
        flattened["creator_name"] = creator.get("name")
        flattened["creator_url"] = creator.get("profile_url")

    # Flatten stats
    stats = product.get("stats", {})
    if stats:
        # Views
        views = stats.get("views")
        if views:
            flattened["views_raw"] = views.get("raw")
            flattened["views_normalized"] = views.get("normalized")

        # Pages (templates)
        pages = stats.get("pages")
        if pages:
            flattened["pages_raw"] = pages.get("raw")
            flattened["pages_normalized"] = pages.get("normalized")

        # Users (plugins, vectors)
        users = stats.get("users")
        if users:
            flattened["users_raw"] = users.get("raw")
            flattened["users_normalized"] = users.get("normalized")

        # Installs (components)
        installs = stats.get("installs")
        if installs:
            flattened["installs_raw"] = installs.get("raw")
            flattened["installs_normalized"] = installs.get("normalized")

        # Vectors (vectors only)
        vectors = stats.get("vectors")
        if vectors:
            flattened["vectors_raw"] = vectors.get("raw")
            flattened["vectors_normalized"] = vectors.get("normalized")

    # Flatten metadata
    metadata = product.get("metadata", {})
    if metadata:
        published_date = metadata.get("published_date")
        if published_date:
            flattened["published_date_raw"] = published_date.get("raw")
            flattened["published_date_normalized"] = published_date.get("normalized")

        last_updated = metadata.get("last_updated")
        if last_updated:
            flattened["last_updated_raw"] = last_updated.get("raw")
            flattened["last_updated_normalized"] = last_updated.get("normalized")

        flattened["version"] = metadata.get("version")

    # Flatten features
    features = product.get("features", {})
    if features:
        flattened["features_list"] = ", ".join(features.get("features", []))
        flattened["is_responsive"] = features.get("is_responsive")
        flattened["has_animations"] = features.get("has_animations")
        flattened["cms_integration"] = features.get("cms_integration")
        flattened["pages_count"] = features.get("pages_count")

    # Media
    media = product.get("media", {})
    if media:
        flattened["thumbnail_url"] = media.get("thumbnail")
        flattened["screenshots_count"] = len(media.get("screenshots", []))

    # Reviews
    reviews = product.get("reviews", {})
    if reviews:
        flattened["average_rating"] = reviews.get("average_rating")
        flattened["total_reviews"] = reviews.get("total_reviews")

    flattened["scraped_at"] = product.get("scraped_at")

    return flattened


def export_to_csv(
    output_file: Path,
    data_dir: Optional[Path] = None,
    product_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> None:
    """Export products to CSV file.

    Args:
        output_file: Output CSV file path
        data_dir: Directory containing product data (defaults to settings.data_dir)
        product_type: Filter by product type or None for all
        limit: Limit number of products to export
    """
    if data_dir is None:
        data_dir = settings.data_path

    logger.info("export_started", output_file=str(output_file), data_dir=str(data_dir))

    # Load products
    products = load_products_from_directory(data_dir, product_type)

    if limit:
        products = products[:limit]

    if not products:
        logger.warning("no_products_found")
        return

    logger.info("products_loaded", count=len(products))

    # Flatten products
    flattened_products = [flatten_product(p) for p in products]

    # Create DataFrame
    df = pd.DataFrame(flattened_products)

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Export to CSV
    df.to_csv(output_file, index=False, encoding="utf-8")

    logger.info("export_completed", output_file=str(output_file), rows=len(df))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Export scraped data to CSV")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="data/exports/products.csv",
        help="Output CSV file path (default: data/exports/products.csv)",
    )
    parser.add_argument(
        "-d",
        "--data-dir",
        type=str,
        default=None,
        help="Data directory (defaults to settings.data_dir)",
    )
    parser.add_argument(
        "-t",
        "--type",
        type=str,
        choices=["template", "component", "vector", "plugin"],
        default=None,
        help="Filter by product type",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=None,
        help="Limit number of products to export",
    )

    args = parser.parse_args()

    output_file = Path(args.output)
    data_dir = Path(args.data_dir) if args.data_dir else None

    export_to_csv(output_file, data_dir, args.type, args.limit)


if __name__ == "__main__":
    main()

