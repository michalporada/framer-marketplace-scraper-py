"""File storage for saving scraped data to JSON and CSV files."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
import pandas as pd

from src.config.settings import settings
from src.models.product import Product
from src.models.creator import Creator
from src.models.category import Category
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FileStorage:
    """File storage for saving scraped data."""

    def __init__(self):
        """Initialize file storage."""
        self.data_dir = settings.data_path
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.data_dir / "products" / "templates").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "products" / "components").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "products" / "vectors").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "products" / "plugins").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "creators").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "categories").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "exports").mkdir(parents=True, exist_ok=True)

    def get_product_dir(self, product_type: str) -> Path:
        """Get directory path for product type.

        Args:
            product_type: Product type (template, component, vector, plugin)

        Returns:
            Path to product directory
        """
        product_type_map = {
            "template": "templates",
            "component": "components",
            "vector": "vectors",
            "plugin": "plugins",
        }
        subdir = product_type_map.get(product_type, "products")
        return self.data_dir / "products" / subdir

    async def save_product_json(self, product: Product) -> bool:
        """Save product to JSON file.

        Args:
            product: Product model

        Returns:
            True if successful, False otherwise
        """
        try:
            product_dir = self.get_product_dir(product.type)
            filename = f"{product.id}.json"
            filepath = product_dir / filename

            # Convert to dict
            product_dict = product.model_dump(mode="json")

            # Save asynchronously
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(product_dict, indent=2, ensure_ascii=False, default=str))

            logger.debug("product_saved", product_id=product.id, filepath=str(filepath))
            return True

        except Exception as e:
            logger.error(
                "product_save_error",
                product_id=product.id if product else "unknown",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    async def save_creator_json(self, creator: Creator) -> bool:
        """Save creator to JSON file.

        Args:
            creator: Creator model

        Returns:
            True if successful, False otherwise
        """
        try:
            filename = f"{creator.username}.json"
            filepath = self.data_dir / "creators" / filename

            # Convert to dict
            creator_dict = creator.model_dump(mode="json")

            # Save asynchronously
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(creator_dict, indent=2, ensure_ascii=False, default=str))

            logger.debug("creator_saved", username=creator.username, filepath=str(filepath))
            return True

        except Exception as e:
            logger.error(
                "creator_save_error",
                username=creator.username if creator else "unknown",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    async def save_category_json(self, category: Category) -> bool:
        """Save category to JSON file.

        Args:
            category: Category model

        Returns:
            True if successful, False otherwise
        """
        try:
            filename = f"{category.slug}.json"
            filepath = self.data_dir / "categories" / filename

            # Convert to dict
            category_dict = category.model_dump(mode="json")

            # Save asynchronously
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(category_dict, indent=2, ensure_ascii=False, default=str))

            logger.debug("category_saved", slug=category.slug, filepath=str(filepath))
            return True

        except Exception as e:
            logger.error(
                "category_save_error",
                slug=category.slug if category else "unknown",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    def export_products_to_csv(
        self, product_type: Optional[str] = None, output_file: Optional[str] = None
    ) -> bool:
        """Export products to CSV file.

        Args:
            product_type: Product type to export (None for all types)
            output_file: Output CSV file path (None for auto-generated)

        Returns:
            True if successful, False otherwise
        """
        try:
            products = []

            # Load all products
            if product_type:
                product_dir = self.get_product_dir(product_type)
                dirs_to_search = [product_dir]
            else:
                dirs_to_search = [
                    self.data_dir / "products" / "templates",
                    self.data_dir / "products" / "components",
                    self.data_dir / "products" / "vectors",
                    self.data_dir / "products" / "plugins",
                ]

            for product_dir in dirs_to_search:
                if not product_dir.exists():
                    continue

                for json_file in product_dir.glob("*.json"):
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            product_data = json.load(f)
                            products.append(product_data)
                    except Exception as e:
                        logger.warning("product_load_error", file=str(json_file), error=str(e))

            if not products:
                logger.warning("no_products_to_export")
                return False

            # Flatten product data for CSV
            flattened_products = []
            for product in products:
                flattened = {
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "type": product.get("type"),
                    "url": product.get("url"),
                    "price": product.get("price"),
                    "currency": product.get("currency"),
                    "is_free": product.get("is_free"),
                    "description": product.get("description"),
                    "short_description": product.get("short_description"),
                    "category": product.get("category"),
                    # Stats
                    "views": product.get("stats", {}).get("views", 0),
                    "remixes": product.get("stats", {}).get("remixes", 0),
                    "previews": product.get("stats", {}).get("previews", 0),
                    "sales": product.get("stats", {}).get("sales"),
                    # Creator
                    "creator_username": product.get("creator", {}).get("username"),
                    "creator_name": product.get("creator", {}).get("name"),
                    "creator_url": product.get("creator", {}).get("profile_url"),
                    # Metadata
                    "published_date": product.get("metadata", {}).get("published_date"),
                    "last_updated": product.get("metadata", {}).get("last_updated"),
                    "scraped_at": product.get("scraped_at"),
                }
                flattened_products.append(flattened)

            # Create DataFrame
            df = pd.DataFrame(flattened_products)

            # Generate output filename
            if output_file is None:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                type_suffix = f"_{product_type}" if product_type else ""
                output_file = self.data_dir / "exports" / f"products{type_suffix}_{timestamp}.csv"

            # Save CSV
            df.to_csv(output_file, index=False, encoding="utf-8")
            logger.info(
                "products_exported",
                count=len(flattened_products),
                filepath=str(output_file),
            )
            return True

        except Exception as e:
            logger.error("csv_export_error", error=str(e), error_type=type(e).__name__)
            return False

    def export_creators_to_csv(self, output_file: Optional[str] = None) -> bool:
        """Export creators to CSV file.

        Args:
            output_file: Output CSV file path (None for auto-generated)

        Returns:
            True if successful, False otherwise
        """
        try:
            creators = []
            creators_dir = self.data_dir / "creators"

            if not creators_dir.exists():
                logger.warning("no_creators_to_export")
                return False

            for json_file in creators_dir.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        creator_data = json.load(f)
                        creators.append(creator_data)
                except Exception as e:
                    logger.warning("creator_load_error", file=str(json_file), error=str(e))

            if not creators:
                logger.warning("no_creators_to_export")
                return False

            # Flatten creator data for CSV
            flattened_creators = []
            for creator in creators:
                flattened = {
                    "username": creator.get("username"),
                    "name": creator.get("name"),
                    "profile_url": creator.get("profile_url"),
                    "avatar_url": creator.get("avatar_url"),
                    "bio": creator.get("bio"),
                    "website": creator.get("website"),
                    # Stats
                    "total_products": creator.get("stats", {}).get("total_products", 0),
                    "templates_count": creator.get("stats", {}).get("templates_count", 0),
                    "components_count": creator.get("stats", {}).get("components_count", 0),
                    "vectors_count": creator.get("stats", {}).get("vectors_count", 0),
                    "plugins_count": creator.get("stats", {}).get("plugins_count", 0),
                    "total_sales": creator.get("stats", {}).get("total_sales"),
                }
                flattened_creators.append(flattened)

            # Create DataFrame
            df = pd.DataFrame(flattened_creators)

            # Generate output filename
            if output_file is None:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                output_file = self.data_dir / "exports" / f"creators_{timestamp}.csv"

            # Save CSV
            df.to_csv(output_file, index=False, encoding="utf-8")
            logger.info(
                "creators_exported", count=len(flattened_creators), filepath=str(output_file)
            )
            return True

        except Exception as e:
            logger.error("csv_export_error", error=str(e), error_type=type(e).__name__)
            return False
