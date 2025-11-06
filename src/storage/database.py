"""Database storage for saving scraped data to PostgreSQL/Supabase."""

from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from src.config.settings import settings
from src.models.category import Category
from src.models.creator import Creator
from src.models.product import Product
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseStorage:
    """Database storage for saving scraped data to PostgreSQL."""

    def __init__(self):
        """Initialize database storage."""
        self.database_url = settings.database_url
        if not self.database_url:
            logger.warning("database_url_not_configured", message="Database URL not configured, database storage disabled")
            self.engine = None
            return

        try:
            # Use NullPool for serverless environments (Railway, Vercel)
            self.engine = create_engine(
                self.database_url,
                poolclass=NullPool,
                connect_args={"connect_timeout": 10},
            )
            logger.info("database_connection_initialized")
        except Exception as e:
            logger.error("database_connection_failed", error=str(e), error_type=type(e).__name__)
            self.engine = None

    def is_available(self) -> bool:
        """Check if database storage is available.

        Returns:
            True if database is configured and available, False otherwise
        """
        return self.engine is not None

    async def save_product_db(self, product: Product) -> bool:
        """Save product to database.

        Args:
            product: Product model

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            # Extract normalized values
            views_raw = product.stats.views.raw if product.stats and product.stats.views else None
            views_normalized = (
                product.stats.views.normalized if product.stats and product.stats.views else None
            )
            pages_raw = product.stats.pages.raw if product.stats and product.stats.pages else None
            pages_normalized = (
                product.stats.pages.normalized if product.stats and product.stats.pages else None
            )
            users_raw = product.stats.users.raw if product.stats and product.stats.users else None
            users_normalized = (
                product.stats.users.normalized if product.stats and product.stats.users else None
            )
            installs_raw = (
                product.stats.installs.raw if product.stats and product.stats.installs else None
            )
            installs_normalized = (
                product.stats.installs.normalized
                if product.stats and product.stats.installs
                else None
            )
            vectors_raw = (
                product.stats.vectors.raw if product.stats and product.stats.vectors else None
            )
            vectors_normalized = (
                product.stats.vectors.normalized
                if product.stats and product.stats.vectors
                else None
            )

            published_date_raw = (
                product.metadata.published_date.raw
                if product.metadata and product.metadata.published_date
                else None
            )
            published_date_normalized = (
                product.metadata.published_date.normalized
                if product.metadata
                and product.metadata.published_date
                and product.metadata.published_date.normalized
                else None
            )
            if published_date_normalized:
                try:
                    published_date_normalized = datetime.fromisoformat(
                        published_date_normalized.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    published_date_normalized = None

            last_updated_raw = (
                product.metadata.last_updated.raw
                if product.metadata and product.metadata.last_updated
                else None
            )
            last_updated_normalized = (
                product.metadata.last_updated.normalized
                if product.metadata
                and product.metadata.last_updated
                and product.metadata.last_updated.normalized
                else None
            )
            if last_updated_normalized:
                try:
                    last_updated_normalized = datetime.fromisoformat(
                        last_updated_normalized.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    last_updated_normalized = None

            # Extract creator info
            creator_username = product.creator.username if product.creator else None
            creator_name = product.creator.name if product.creator else None
            creator_url = str(product.creator.profile_url) if product.creator else None

            # Extract features
            features_list = (
                ", ".join(product.features.features) if product.features and product.features.features else None
            )

            # Use INSERT ... ON CONFLICT to handle duplicates
            # We insert a new record with scraped_at timestamp for history tracking
            insert_sql = text("""
                INSERT INTO products (
                    id, name, type, category, url, price, currency, is_free,
                    description, short_description,
                    creator_username, creator_name, creator_url,
                    views_raw, views_normalized,
                    pages_raw, pages_normalized,
                    users_raw, users_normalized,
                    installs_raw, installs_normalized,
                    vectors_raw, vectors_normalized,
                    published_date_raw, published_date_normalized,
                    last_updated_raw, last_updated_normalized,
                    version, features_list,
                    is_responsive, has_animations, cms_integration,
                    pages_count, thumbnail_url, screenshots_count,
                    scraped_at, created_at, updated_at
                ) VALUES (
                    :id, :name, :type, :category, :url, :price, :currency, :is_free,
                    :description, :short_description,
                    :creator_username, :creator_name, :creator_url,
                    :views_raw, :views_normalized,
                    :pages_raw, :pages_normalized,
                    :users_raw, :users_normalized,
                    :installs_raw, :installs_normalized,
                    :vectors_raw, :vectors_normalized,
                    :published_date_raw, :published_date_normalized,
                    :last_updated_raw, :last_updated_normalized,
                    :version, :features_list,
                    :is_responsive, :has_animations, :cms_integration,
                    :pages_count, :thumbnail_url, :screenshots_count,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    type = EXCLUDED.type,
                    category = EXCLUDED.category,
                    url = EXCLUDED.url,
                    price = EXCLUDED.price,
                    currency = EXCLUDED.currency,
                    is_free = EXCLUDED.is_free,
                    description = EXCLUDED.description,
                    short_description = EXCLUDED.short_description,
                    creator_username = EXCLUDED.creator_username,
                    creator_name = EXCLUDED.creator_name,
                    creator_url = EXCLUDED.creator_url,
                    views_raw = EXCLUDED.views_raw,
                    views_normalized = EXCLUDED.views_normalized,
                    pages_raw = EXCLUDED.pages_raw,
                    pages_normalized = EXCLUDED.pages_normalized,
                    users_raw = EXCLUDED.users_raw,
                    users_normalized = EXCLUDED.users_normalized,
                    installs_raw = EXCLUDED.installs_raw,
                    installs_normalized = EXCLUDED.installs_normalized,
                    vectors_raw = EXCLUDED.vectors_raw,
                    vectors_normalized = EXCLUDED.vectors_normalized,
                    published_date_raw = EXCLUDED.published_date_raw,
                    published_date_normalized = EXCLUDED.published_date_normalized,
                    last_updated_raw = EXCLUDED.last_updated_raw,
                    last_updated_normalized = EXCLUDED.last_updated_normalized,
                    version = EXCLUDED.version,
                    features_list = EXCLUDED.features_list,
                    is_responsive = EXCLUDED.is_responsive,
                    has_animations = EXCLUDED.has_animations,
                    cms_integration = EXCLUDED.cms_integration,
                    pages_count = EXCLUDED.pages_count,
                    thumbnail_url = EXCLUDED.thumbnail_url,
                    screenshots_count = EXCLUDED.screenshots_count,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.engine.connect() as conn:
                conn.execute(
                    insert_sql,
                    {
                        "id": product.id,
                        "name": product.name,
                        "type": product.type,
                        "category": product.category,
                        "url": str(product.url),
                        "price": product.price,
                        "currency": product.currency,
                        "is_free": product.is_free,
                        "description": product.description,
                        "short_description": product.short_description,
                        "creator_username": creator_username,
                        "creator_name": creator_name,
                        "creator_url": creator_url,
                        "views_raw": views_raw,
                        "views_normalized": views_normalized,
                        "pages_raw": pages_raw,
                        "pages_normalized": pages_normalized,
                        "users_raw": users_raw,
                        "users_normalized": users_normalized,
                        "installs_raw": installs_raw,
                        "installs_normalized": installs_normalized,
                        "vectors_raw": vectors_raw,
                        "vectors_normalized": vectors_normalized,
                        "published_date_raw": published_date_raw,
                        "published_date_normalized": published_date_normalized,
                        "last_updated_raw": last_updated_raw,
                        "last_updated_normalized": last_updated_normalized,
                        "version": product.metadata.version if product.metadata else None,
                        "features_list": features_list,
                        "is_responsive": (
                            product.features.is_responsive if product.features else False
                        ),
                        "has_animations": (
                            product.features.has_animations if product.features else False
                        ),
                        "cms_integration": (
                            product.features.cms_integration if product.features else False
                        ),
                        "pages_count": (
                            product.features.pages_count if product.features else None
                        ),
                        "thumbnail_url": (
                            str(product.media.thumbnail) if product.media and product.media.thumbnail else None
                        ),
                        "screenshots_count": (
                            len(product.media.screenshots) if product.media and product.media.screenshots else 0
                        ),
                    },
                )
                conn.commit()

            logger.debug("product_saved_to_db", product_id=product.id)
            return True

        except SQLAlchemyError as e:
            logger.error(
                "product_db_save_error",
                product_id=product.id if product else "unknown",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False
        except Exception as e:
            logger.error(
                "product_db_save_unexpected_error",
                product_id=product.id if product else "unknown",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    async def save_creator_db(self, creator: Creator) -> bool:
        """Save creator to database.

        Args:
            creator: Creator model

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            # Convert social_media dict to JSON string for JSONB
            import json as json_lib

            social_media_json = json_lib.dumps(creator.social_media) if creator.social_media else None

            insert_sql = text("""
                INSERT INTO creators (
                    username, name, profile_url, avatar_url, bio, website,
                    social_media, total_products, templates_count, components_count,
                    vectors_count, plugins_count, total_sales,
                    scraped_at, created_at, updated_at
                ) VALUES (
                    :username, :name, :profile_url, :avatar_url, :bio, :website,
                    :social_media::jsonb, :total_products, :templates_count, :components_count,
                    :vectors_count, :plugins_count, :total_sales,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (username) DO UPDATE SET
                    name = EXCLUDED.name,
                    profile_url = EXCLUDED.profile_url,
                    avatar_url = EXCLUDED.avatar_url,
                    bio = EXCLUDED.bio,
                    website = EXCLUDED.website,
                    social_media = EXCLUDED.social_media::jsonb,
                    total_products = EXCLUDED.total_products,
                    templates_count = EXCLUDED.templates_count,
                    components_count = EXCLUDED.components_count,
                    vectors_count = EXCLUDED.vectors_count,
                    plugins_count = EXCLUDED.plugins_count,
                    total_sales = EXCLUDED.total_sales,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.engine.connect() as conn:
                conn.execute(
                    insert_sql,
                    {
                        "username": creator.username,
                        "name": creator.name,
                        "profile_url": str(creator.profile_url),
                        "avatar_url": str(creator.avatar_url) if creator.avatar_url else None,
                        "bio": creator.bio,
                        "website": str(creator.website) if creator.website else None,
                        "social_media": social_media_json,
                        "total_products": creator.stats.total_products,
                        "templates_count": creator.stats.templates_count,
                        "components_count": creator.stats.components_count,
                        "vectors_count": creator.stats.vectors_count,
                        "plugins_count": creator.stats.plugins_count,
                        "total_sales": creator.stats.total_sales,
                    },
                )
                conn.commit()

            logger.debug("creator_saved_to_db", username=creator.username)
            return True

        except SQLAlchemyError as e:
            logger.error(
                "creator_db_save_error",
                username=creator.username if creator else "unknown",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False
        except Exception as e:
            logger.error(
                "creator_db_save_unexpected_error",
                username=creator.username if creator else "unknown",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    async def save_category_db(self, category: Category) -> bool:
        """Save category to database.

        Args:
            category: Category model

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            import json as json_lib

            # Convert product_types and subcategories to JSON
            product_types_json = (
                json_lib.dumps(category.product_types) if category.product_types else None
            )
            subcategories_json = (
                json_lib.dumps(category.subcategories) if category.subcategories else None
            )

            insert_sql = text("""
                INSERT INTO categories (
                    slug, name, url, description, product_count,
                    product_types, parent_category, subcategories,
                    scraped_at, created_at, updated_at
                ) VALUES (
                    :slug, :name, :url, :description, :product_count,
                    :product_types::jsonb, :parent_category, :subcategories::jsonb,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (slug) DO UPDATE SET
                    name = EXCLUDED.name,
                    url = EXCLUDED.url,
                    description = EXCLUDED.description,
                    product_count = EXCLUDED.product_count,
                    product_types = EXCLUDED.product_types::jsonb,
                    parent_category = EXCLUDED.parent_category,
                    subcategories = EXCLUDED.subcategories::jsonb,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.engine.connect() as conn:
                conn.execute(
                    insert_sql,
                    {
                        "slug": category.slug,
                        "name": category.name,
                        "url": str(category.url),
                        "description": category.description,
                        "product_count": category.product_count,
                        "product_types": product_types_json,
                        "parent_category": category.parent_category,
                        "subcategories": subcategories_json,
                    },
                )
                conn.commit()

            logger.debug("category_saved_to_db", slug=category.slug)
            return True

        except SQLAlchemyError as e:
            logger.error(
                "category_db_save_error",
                slug=category.slug if category else "unknown",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False
        except Exception as e:
            logger.error(
                "category_db_save_unexpected_error",
                slug=category.slug if category else "unknown",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

