"""API routes for products."""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.dependencies import execute_query, execute_query_one, get_db_engine
from api.cache import cached
from sqlalchemy import text
from src.config.settings import settings
from src.models.creator import Creator
from src.models.product import (
    NormalizedDate,
    NormalizedStatistic,
    Product,
    ProductFeatures,
    ProductMedia,
    ProductMetadata,
    ProductStats,
)

router = APIRouter(prefix="/api/products", tags=["products"])


def db_row_to_product(row: dict) -> Product:
    """Convert database row to Product model.

    Args:
        row: Database row as dict

    Returns:
        Product model
    """
    # Build stats
    stats = ProductStats()
    if row.get("views_raw") or row.get("views_normalized") is not None:
        stats.views = NormalizedStatistic(
            raw=row.get("views_raw", ""),
            normalized=row.get("views_normalized"),
        )
    if row.get("pages_raw") or row.get("pages_normalized") is not None:
        stats.pages = NormalizedStatistic(
            raw=row.get("pages_raw", ""),
            normalized=row.get("pages_normalized"),
        )
    if row.get("users_raw") or row.get("users_normalized") is not None:
        stats.users = NormalizedStatistic(
            raw=row.get("users_raw", ""),
            normalized=row.get("users_normalized"),
        )
    if row.get("installs_raw") or row.get("installs_normalized") is not None:
        stats.installs = NormalizedStatistic(
            raw=row.get("installs_raw", ""),
            normalized=row.get("installs_normalized"),
        )
    if row.get("vectors_raw") or row.get("vectors_normalized") is not None:
        stats.vectors = NormalizedStatistic(
            raw=row.get("vectors_raw", ""),
            normalized=row.get("vectors_normalized"),
        )

    # Build metadata
    metadata = ProductMetadata()
    if row.get("published_date_raw") or row.get("published_date_normalized"):
        published_date_normalized = None
        if row.get("published_date_normalized"):
            if isinstance(row["published_date_normalized"], datetime):
                published_date_normalized = row["published_date_normalized"].isoformat() + "Z"
            elif isinstance(row["published_date_normalized"], str):
                published_date_normalized = row["published_date_normalized"]
        metadata.published_date = NormalizedDate(
            raw=row.get("published_date_raw", ""),
            normalized=published_date_normalized,
        )
    if row.get("last_updated_raw") or row.get("last_updated_normalized"):
        last_updated_normalized = None
        if row.get("last_updated_normalized"):
            if isinstance(row["last_updated_normalized"], datetime):
                last_updated_normalized = row["last_updated_normalized"].isoformat() + "Z"
            elif isinstance(row["last_updated_normalized"], str):
                last_updated_normalized = row["last_updated_normalized"]
        metadata.last_updated = NormalizedDate(
            raw=row.get("last_updated_raw", ""),
            normalized=last_updated_normalized,
        )
    if row.get("version"):
        metadata.version = row["version"]

    # Build features
    features = ProductFeatures()
    if row.get("features_list"):
        try:
            features_list_str = str(row["features_list"]) if row["features_list"] else ""
            if features_list_str:
                features.features = [f.strip() for f in features_list_str.split(",") if f.strip()]
        except (AttributeError, TypeError):
            features.features = []
    features.is_responsive = row.get("is_responsive", False)
    features.has_animations = row.get("has_animations", False)
    features.cms_integration = row.get("cms_integration", False)
    features.pages_count = row.get("pages_count")

    # Build media
    media = ProductMedia()
    if row.get("thumbnail_url"):
        media.thumbnail = row["thumbnail_url"]
    # screenshots_count is stored in DB but not in ProductMedia model
    # We can calculate it from screenshots list if needed

    # Build creator
    creator = None
    if row.get("creator_username"):
        creator = Creator(
            username=row["creator_username"],
            name=row.get("creator_name"),
            profile_url=row.get("creator_url", ""),
        )

    # Build product
    product = Product(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        category=row.get("category"),
        url=row["url"],
        price=row.get("price"),
        currency=row.get("currency", "USD"),
        is_free=row.get("is_free", False),
        description=row.get("description"),
        short_description=row.get("short_description"),
        creator=creator,
        stats=stats,
        metadata=metadata,
        features=features,
        media=media,
    )

    # Set scraped_at if available
    if row.get("scraped_at"):
        if isinstance(row["scraped_at"], datetime):
            product.scraped_at = row["scraped_at"]
        elif isinstance(row["scraped_at"], str):
            try:
                product.scraped_at = datetime.fromisoformat(
                    row["scraped_at"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

    return product


class ProductListResponse(BaseModel):
    """Response model for product list."""

    data: List[Product]
    meta: dict = Field(
        default_factory=lambda: {
            "total": 0,
            "limit": 100,
            "offset": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )


class ProductResponse(BaseModel):
    """Response model for single product."""

    data: Product
    meta: dict = Field(default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"})


class ErrorResponse(BaseModel):
    """Error response model."""

    error: dict


class ViewsChange24hResponse(BaseModel):
    """Response model for 24h views change."""

    product_type: str
    total_views_change: int
    products_count: int
    products_with_changes: int
    meta: dict = Field(
        default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"}
    )


@router.get("/views-change-24h", response_model=ViewsChange24hResponse)
async def get_views_change_24h(
    product_type: str = Query(
        "template", description="Product type: template, component, vector, plugin"
    ),
):
    """Get total views change for all products of a given type in the last 24 hours.

    This endpoint compares the latest scrape with the scrape from 24 hours ago
    and calculates the total change in views.

    Args:
        product_type: Product type to analyze (default: template)

    Returns:
        ViewsChange24hResponse with total views change
    """
    # Validate product type
    if product_type not in ["template", "component", "vector", "plugin"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_PRODUCT_TYPE",
                    "message": (
                        "Invalid product type. Must be one of: template, component, vector, plugin"
                    ),
                    "details": {"type": product_type},
                }
            },
        )

    engine = get_db_engine()
    if not engine:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "DATABASE_NOT_AVAILABLE",
                    "message": "Database connection not available",
                    "details": {},
                }
            },
        )

    try:
        from sqlalchemy import text

        # Get current time and 24 hours ago
        now = datetime.utcnow()
        hours_24_ago = now - timedelta(hours=24)

        # Query to get latest views for each product
        # Uses DISTINCT ON to get the most recent scrape for each product
        # Prepared statement prevents SQL injection
        query_latest = text(
            """
            SELECT DISTINCT ON (product_id)
                product_id,
                views_normalized,
                scraped_at
            FROM product_history
            WHERE type = :product_type
                AND views_normalized IS NOT NULL
                AND scraped_at <= :now_time
            ORDER BY product_id, scraped_at DESC
        """
        )

        # Query to get views from 24 hours ago (or closest before that time)
        # Uses DISTINCT ON to get the most recent scrape before the 24h mark
        # Prepared statement prevents SQL injection
        query_24h_ago = text(
            """
            SELECT DISTINCT ON (product_id)
                product_id,
                views_normalized,
                scraped_at
            FROM product_history
            WHERE type = :product_type
                AND views_normalized IS NOT NULL
                AND scraped_at <= :hours_24_ago_time
            ORDER BY product_id, scraped_at DESC
        """
        )

        with engine.connect() as conn:
            # Get latest views
            result_latest = conn.execute(
                query_latest, {"product_type": product_type, "now_time": now}
            )
            latest_views = {row[0]: row[1] for row in result_latest if row[1] is not None}

            # Get views from 24h ago
            result_24h = conn.execute(
                query_24h_ago,
                {"product_type": product_type, "hours_24_ago_time": hours_24_ago},
            )
            views_24h_ago = {row[0]: row[1] for row in result_24h if row[1] is not None}

        # Calculate changes
        # Compare current views with views from 24h ago
        total_change = 0
        products_with_changes = 0
        products_count = len(latest_views)

        # For products that exist in both, calculate difference
        # For new products (didn't exist 24h ago), count all current views as change
        for product_id in latest_views:
            current_views = latest_views[product_id]
            old_views = views_24h_ago.get(product_id, 0)

            if current_views is not None and old_views is not None:
                # Product existed in both periods - calculate difference
                change = current_views - old_views
                total_change += change
                if change != 0:
                    products_with_changes += 1
            elif current_views is not None:
                # New product (didn't exist 24h ago) - all views are new
                total_change += current_views
                products_with_changes += 1

        return ViewsChange24hResponse(
            product_type=product_type,
            total_views_change=total_change,
            products_count=products_count,
            products_with_changes=products_with_changes,
            meta={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "period_start": hours_24_ago.isoformat() + "Z",
                "period_end": now.isoformat() + "Z",
            },
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating 24h views change: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to calculate views change: {str(e)}",
                    "details": {},
                }
            },
        )


class TopProductByViews(BaseModel):
    """Model for top product by views."""

    product_id: str
    name: str
    type: str
    creator_username: Optional[str] = None
    creator_name: Optional[str] = None
    views: int
    views_change: int = 0
    views_change_percent: float = 0.0
    is_free: bool = False
    price: Optional[float] = None


class TopProductsByViewsResponse(BaseModel):
    """Response model for top products by views."""

    data: List[TopProductByViews]
    meta: dict = Field(
        default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"}
    )


@router.get("/top-templates", response_model=TopProductsByViewsResponse)
@cached(ttl=300, cache_type="product")  # Cache for 5 minutes
async def get_top_templates(
    limit: int = Query(10, ge=1, le=100, description="Number of templates to return"),
    period_hours: int = Query(24, ge=1, le=168, description="Period in hours for % change (1-168, default: 24)"),
):
    """Get top templates by views with percentage change.

    This endpoint aggregates views_normalized from product_history for templates,
    calculates total views, and compares with period ago to calculate percentage change.

    Args:
        limit: Number of top templates to return (1-100, default: 10)
        period_hours: Period in hours to compare for % change (1-168, default: 24)

    Returns:
        TopProductsByViewsResponse with top templates sorted by views

    Raises:
        503: Database not available
    """
    return await _get_top_products_by_type("template", limit, period_hours)


@router.get("/top-components", response_model=TopProductsByViewsResponse)
@cached(ttl=300, cache_type="product")  # Cache for 5 minutes
async def get_top_components(
    limit: int = Query(10, ge=1, le=100, description="Number of components to return"),
    period_hours: int = Query(24, ge=1, le=168, description="Period in hours for % change (1-168, default: 24)"),
):
    """Get top components by views/installs with percentage change.

    This endpoint aggregates views_normalized from product_history for components,
    calculates total views, and compares with period ago to calculate percentage change.

    Args:
        limit: Number of top components to return (1-100, default: 10)
        period_hours: Period in hours to compare for % change (1-168, default: 24)

    Returns:
        TopProductsByViewsResponse with top components sorted by views

    Raises:
        503: Database not available
    """
    return await _get_top_products_by_type("component", limit, period_hours)


@router.get("/top-free-templates", response_model=TopProductsByViewsResponse)
@cached(ttl=300, cache_type="product")  # Cache for 5 minutes
async def get_top_free_templates(
    limit: int = Query(10, ge=1, le=100, description="Number of free templates to return"),
    period_hours: int = Query(24, ge=1, le=168, description="Period in hours for % change (1-168, default: 24)"),
):
    """Get top free templates by views with percentage change.

    This endpoint aggregates views_normalized from product_history for free templates,
    calculates total views, and compares with period ago to calculate percentage change.

    Args:
        limit: Number of top free templates to return (1-100, default: 10)
        period_hours: Period in hours to compare for % change (1-168, default: 24)

    Returns:
        TopProductsByViewsResponse with top free templates sorted by views

    Raises:
        503: Database not available
    """
    engine = get_db_engine()
    if not engine:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "DATABASE_NOT_AVAILABLE",
                    "message": "Database connection not available",
                    "details": {},
                }
            },
        )

    try:
        from sqlalchemy import text

        # Get current time and period ago
        now = datetime.utcnow()
        period_ago = now - timedelta(hours=period_hours)

        # Query to get latest views for free templates
        # First get latest views for each template, then join with products to filter by is_free
        query_latest = text(
            """
            WITH latest_views AS (
                SELECT DISTINCT ON (ph.product_id)
                    ph.product_id,
                    ph.name,
                    ph.creator_username,
                    ph.views_normalized
                FROM product_history ph
                INNER JOIN products p ON ph.product_id = p.id
                WHERE ph.type = 'template'
                    AND ph.views_normalized IS NOT NULL
                    AND p.is_free = true
                    AND ph.scraped_at <= :now_time
                ORDER BY ph.product_id, ph.scraped_at DESC
            )
            SELECT product_id, name, creator_username, views_normalized
            FROM latest_views
            ORDER BY views_normalized DESC
            LIMIT :limit
        """
        )

        # Query to get views from period ago (only for free templates)
        query_period_ago = text(
            """
            SELECT DISTINCT ON (ph.product_id)
                ph.product_id,
                ph.views_normalized
            FROM product_history ph
            INNER JOIN products p ON ph.product_id = p.id
            WHERE ph.type = 'template'
                AND ph.views_normalized IS NOT NULL
                AND p.is_free = true
                AND ph.scraped_at <= :period_ago_time
            ORDER BY ph.product_id, ph.scraped_at DESC
        """
        )

        with engine.connect() as conn:
            # Get latest views for top free templates
            result_latest = conn.execute(
                query_latest, {"now_time": now, "limit": limit}
            )
            latest_data = {}
            for row in result_latest:
                latest_data[row[0]] = {
                    "name": row[1],
                    "creator_username": row[2],
                    "views": int(row[3]) if row[3] else 0,
                }

            # Get views from period ago
            result_period = conn.execute(
                query_period_ago, {"period_ago_time": period_ago}
            )
            period_ago_data = {
                row[0]: int(row[1]) if row[1] else 0 for row in result_period
            }

        # Get product details (is_free, price) from products table
        product_ids = list(latest_data.keys())
        products_details = {}
        if product_ids:
            for product_id in product_ids:
                product_query = "SELECT id, is_free, price FROM products WHERE id = :product_id"
                product_row = execute_query_one(product_query, {"product_id": product_id})
                if product_row:
                    products_details[product_id] = {
                        "is_free": product_row.get("is_free", False),
                        "price": float(product_row.get("price")) if product_row.get("price") else None,
                    }

        # Get creator details
        creators_usernames = list(set([data["creator_username"] for data in latest_data.values() if data["creator_username"]]))
        creator_details = {}
        if creators_usernames:
            for username in creators_usernames:
                creator_query = "SELECT username, name FROM creators WHERE username = :username"
                creator_row = execute_query_one(creator_query, {"username": username})
                if creator_row:
                    creator_details[username] = creator_row.get("name")

        # Calculate changes and build response
        top_products = []
        for product_id, product_data in latest_data.items():
            current_views = product_data["views"]
            previous_views = period_ago_data.get(product_id, 0)

            # Calculate change
            views_change = current_views - previous_views
            views_change_percent = 0.0
            if previous_views > 0:
                views_change_percent = (views_change / previous_views) * 100

            product_info = products_details.get(product_id, {})
            creator_info = creator_details.get(product_data["creator_username"] or "", {})

            top_products.append(
                TopProductByViews(
                    product_id=product_id,
                    name=product_data["name"],
                    type="template",
                    creator_username=product_data["creator_username"],
                    creator_name=creator_info.get("name") if isinstance(creator_info, dict) else None,
                    views=current_views,
                    views_change=views_change,
                    views_change_percent=round(views_change_percent, 2),
                    is_free=product_info.get("is_free", True),  # Should always be True for free templates
                    price=product_info.get("price"),
                )
            )

        # Sort by views (should already be sorted, but ensure it)
        top_products.sort(key=lambda x: x.views, reverse=True)

        return TopProductsByViewsResponse(
            data=top_products,
            meta={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "period_hours": period_hours,
                "limit": limit,
            },
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"Error calculating top free templates: {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to calculate top free templates: {str(e)}",
                    "details": {},
                }
            },
        )


async def _get_top_products_by_type(
    product_type: str, limit: int, period_hours: int
) -> TopProductsByViewsResponse:
    """Helper function to get top products by type with percentage change.

    Args:
        product_type: Product type (template, component, vector, plugin)
        limit: Number of top products to return
        period_hours: Period in hours to compare for % change

    Returns:
        TopProductsByViewsResponse with top products sorted by views
    """
    engine = get_db_engine()
    if not engine:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "DATABASE_NOT_AVAILABLE",
                    "message": "Database connection not available",
                    "details": {},
                }
            },
        )

    try:
        from sqlalchemy import text

        # Get current time and period ago
        now = datetime.utcnow()
        period_ago = now - timedelta(hours=period_hours)

        # Query to get latest views for products
        # First get latest views for each product, then sort by views and limit
        query_latest = text(
            """
            WITH latest_views AS (
                SELECT DISTINCT ON (product_id)
                    product_id,
                    name,
                    creator_username,
                    views_normalized
                FROM product_history
                WHERE type = :product_type
                    AND views_normalized IS NOT NULL
                    AND scraped_at <= :now_time
                ORDER BY product_id, scraped_at DESC
            )
            SELECT product_id, name, creator_username, views_normalized
            FROM latest_views
            ORDER BY views_normalized DESC
            LIMIT :limit
        """
        )

        # Query to get views from period ago
        query_period_ago = text(
            """
            SELECT DISTINCT ON (product_id)
                product_id,
                views_normalized
            FROM product_history
            WHERE type = :product_type
                AND views_normalized IS NOT NULL
                AND scraped_at <= :period_ago_time
            ORDER BY product_id, scraped_at DESC
        """
        )

        with engine.connect() as conn:
            # Get latest views for top products
            result_latest = conn.execute(
                query_latest, {"product_type": product_type, "now_time": now, "limit": limit}
            )
            latest_data = {}
            for row in result_latest:
                latest_data[row[0]] = {
                    "name": row[1],
                    "creator_username": row[2],
                    "views": int(row[3]) if row[3] else 0,
                }

            # Get views from period ago
            result_period = conn.execute(
                query_period_ago, {"product_type": product_type, "period_ago_time": period_ago}
            )
            period_ago_data = {
                row[0]: int(row[1]) if row[1] else 0 for row in result_period
            }

        # Get product details (is_free, price) from products table
        product_ids = list(latest_data.keys())
        products_details = {}
        if product_ids:
            for product_id in product_ids:
                product_query = "SELECT id, is_free, price FROM products WHERE id = :product_id"
                product_row = execute_query_one(product_query, {"product_id": product_id})
                if product_row:
                    products_details[product_id] = {
                        "is_free": product_row.get("is_free", False),
                        "price": float(product_row.get("price")) if product_row.get("price") else None,
                    }

        # Get creator details
        creators_usernames = list(set([data["creator_username"] for data in latest_data.values() if data["creator_username"]]))
        creator_details = {}
        if creators_usernames:
            for username in creators_usernames:
                creator_query = "SELECT username, name FROM creators WHERE username = :username"
                creator_row = execute_query_one(creator_query, {"username": username})
                if creator_row:
                    creator_details[username] = creator_row.get("name")

        # Calculate changes and build response
        top_products = []
        for product_id, product_data in latest_data.items():
            current_views = product_data["views"]
            previous_views = period_ago_data.get(product_id, 0)

            # Calculate change
            views_change = current_views - previous_views
            views_change_percent = 0.0
            if previous_views > 0:
                views_change_percent = (views_change / previous_views) * 100

            product_info = products_details.get(product_id, {})
            creator_info = creator_details.get(product_data["creator_username"] or "", {})

            top_products.append(
                TopProductByViews(
                    product_id=product_id,
                    name=product_data["name"],
                    type=product_type,
                    creator_username=product_data["creator_username"],
                    creator_name=creator_info.get("name") if isinstance(creator_info, dict) else None,
                    views=current_views,
                    views_change=views_change,
                    views_change_percent=round(views_change_percent, 2),
                    is_free=product_info.get("is_free", False),
                    price=product_info.get("price"),
                )
            )

        # Sort by views (should already be sorted, but ensure it)
        top_products.sort(key=lambda x: x.views, reverse=True)

        return TopProductsByViewsResponse(
            data=top_products,
            meta={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "period_hours": period_hours,
                "limit": limit,
            },
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"Error calculating top templates: {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to calculate top templates: {str(e)}",
                    "details": {},
                }
            },
        )


@router.get("", response_model=ProductListResponse)
@cached(ttl=300, cache_type="product")  # Cache for 5 minutes
async def get_products(
    type: Optional[str] = Query(
        None, description="Product type: template, component, vector, plugin"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Number of products to return"),
    offset: int = Query(0, ge=0, description="Number of products to skip"),
    sort: str = Query(
        "created_at", description="Sort field: created_at, updated_at, views_normalized"
    ),
    order: str = Query("desc", description="Sort order: asc, desc"),
):
    """Get list of products.

    Args:
        type: Filter by product type
        limit: Number of products to return (1-1000)
        offset: Number of products to skip
        sort: Sort field
        order: Sort order (asc/desc)

    Returns:
        ProductListResponse with products and metadata
    """
    # Validate sort field
    valid_sorts = ["created_at", "updated_at", "scraped_at", "views_normalized", "name"]
    if sort not in valid_sorts:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Invalid sort field. Must be one of: {', '.join(valid_sorts)}",
                    "details": {"sort": sort},
                }
            },
        )

    # Validate order
    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid order. Must be 'asc' or 'desc'",
                    "details": {"order": order},
                }
            },
        )

    # Validate type
    if type and type not in ["template", "component", "vector", "plugin"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_PRODUCT_TYPE",
                    "message": (
                        "Invalid product type. Must be one of: template, component, vector, plugin"
                    ),
                    "details": {"type": type},
                }
            },
        )

    # Map sort field to database column (whitelist for security)
    sort_column_map = {
        "created_at": "created_at",
        "updated_at": "updated_at",
        "scraped_at": "scraped_at",
        "views_normalized": "views_normalized",
        "name": "name",
    }
    sort_column = sort_column_map.get(sort, "created_at")

    # Validate order (whitelist for security)
    order_upper = order.upper()
    if order_upper not in ["ASC", "DESC"]:
        order_upper = "DESC"

    # Build query with prepared statements
    params = {}
    where_clause = ""
    if type:
        # Use prepared statement parameter (validated, safe)
        where_clause = "WHERE type = :type"
        params["type"] = type

    # Get total count using prepared statement
    count_query = "SELECT COUNT(*) as total FROM products"
    if where_clause:
        count_query += " " + where_clause
    count_result = execute_query_one(count_query, params)
    total = count_result["total"] if count_result else 0

    # Build main query with prepared statements
    # Note: ORDER BY column name and LIMIT/OFFSET must use whitelist (cannot be parameterized)
    query = "SELECT * FROM products"
    if where_clause:
        query += " " + where_clause
    query += f" ORDER BY {sort_column} {order_upper}"
    query += " LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset

    rows = execute_query(query, params)
    if rows is None:
        # Log the query for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Database query failed. Query: {query[:200]}... Params: {params}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to fetch products from database",
                    "details": {"query_preview": query[:100]},
                }
            },
        )

    # Convert to Product models (rows is empty list if no results)
    products = []
    for row in rows:
        try:
            product = db_row_to_product(row)
            products.append(product)
        except Exception as e:
            # Log error but continue processing other products
            import logging

            log = logging.getLogger(__name__)
            log.error(f"Error converting product row to model: {type(e).__name__}: {str(e)}")
            continue

    return ProductListResponse(
        data=products,
        meta={
            "total": total,
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@router.get("/{product_id}", response_model=ProductResponse)
@cached(ttl=300, cache_type="product")  # Cache for 5 minutes
async def get_product(product_id: str):
    """Get single product by ID.

    Args:
        product_id: Product identifier

    Returns:
        ProductResponse with product data

    Raises:
        404: Product not found
    """
    query = "SELECT * FROM products WHERE id = :id"
    row = execute_query_one(query, {"id": product_id})

    if not row:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "PRODUCT_NOT_FOUND",
                    "message": f"Product with ID '{product_id}' not found",
                    "details": {"product_id": product_id},
                }
            },
        )

    product = db_row_to_product(row)

    return ProductResponse(
        data=product,
        meta={"timestamp": datetime.utcnow().isoformat() + "Z"},
    )


def load_product_from_json(product_id: str, base_path: Path) -> Optional[Dict]:
    """Load product data from JSON file in any scrape directory.

    Args:
        product_id: Product identifier
        base_path: Base path to search (e.g., data/ or data/scraped-data (2)/)

    Returns:
        Product data as dict or None if not found
    """
    product_type_map = {
        "template": "templates",
        "component": "components",
        "vector": "vectors",
        "plugin": "plugins",
    }

    # Try each product type directory
    for product_type, subdir in product_type_map.items():
        product_file = base_path / "products" / subdir / f"{product_id}.json"
        if product_file.exists():
            try:
                with open(product_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

    return None


def find_product_versions_from_db(product_id: str) -> List[Dict]:
    """Find all versions of a product from product_history table.

    Args:
        product_id: Product identifier

    Returns:
        List of product data dicts from database
    """
    engine = get_db_engine()
    if not engine:
        return []

    try:
        query = text(
            """
            SELECT 
                product_id, scraped_at,
                name, type, category, url, price, currency, is_free,
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
                pages_count, thumbnail_url, screenshots_count
            FROM product_history
            WHERE product_id = :product_id
            ORDER BY scraped_at DESC
        """
        )

        with engine.connect() as conn:
            result = conn.execute(query, {"product_id": product_id})
            rows = result.fetchall()

        versions = []
        for row in rows:
            row_dict = dict(row._mapping)

            # Convert to format expected by comparison logic
            version_dict = {
                "id": row_dict["product_id"],
                "scraped_at": (
                    row_dict["scraped_at"].isoformat() + "Z" if row_dict["scraped_at"] else None
                ),
                "source_path": "database",
                "name": row_dict["name"],
                "type": row_dict["type"],
                "category": row_dict.get("category"),
                "url": row_dict["url"],
                "price": float(row_dict["price"]) if row_dict.get("price") else None,
                "currency": row_dict.get("currency", "USD"),
                "is_free": row_dict.get("is_free", False),
                "description": row_dict.get("description"),
                "short_description": row_dict.get("short_description"),
                "stats": {},
                "metadata": {},
            }

            # Build stats
            stats = {}
            if row_dict.get("views_raw") or row_dict.get("views_normalized") is not None:
                stats["views"] = {
                    "raw": row_dict.get("views_raw", ""),
                    "normalized": row_dict.get("views_normalized"),
                }
            if row_dict.get("pages_raw") or row_dict.get("pages_normalized") is not None:
                stats["pages"] = {
                    "raw": row_dict.get("pages_raw", ""),
                    "normalized": row_dict.get("pages_normalized"),
                }
            if row_dict.get("users_raw") or row_dict.get("users_normalized") is not None:
                stats["users"] = {
                    "raw": row_dict.get("users_raw", ""),
                    "normalized": row_dict.get("users_normalized"),
                }
            if row_dict.get("installs_raw") or row_dict.get("installs_normalized") is not None:
                stats["installs"] = {
                    "raw": row_dict.get("installs_raw", ""),
                    "normalized": row_dict.get("installs_normalized"),
                }
            if row_dict.get("vectors_raw") or row_dict.get("vectors_normalized") is not None:
                stats["vectors"] = {
                    "raw": row_dict.get("vectors_raw", ""),
                    "normalized": row_dict.get("vectors_normalized"),
                }
            version_dict["stats"] = stats

            # Build metadata
            metadata = {}
            if row_dict.get("version"):
                metadata["version"] = row_dict["version"]
            if row_dict.get("published_date_raw") or row_dict.get("published_date_normalized"):
                published_date = {}
                if row_dict.get("published_date_raw"):
                    published_date["raw"] = row_dict["published_date_raw"]
                if row_dict.get("published_date_normalized"):
                    if isinstance(row_dict["published_date_normalized"], datetime):
                        published_date["normalized"] = (
                            row_dict["published_date_normalized"].isoformat() + "Z"
                        )
                    else:
                        published_date["normalized"] = row_dict["published_date_normalized"]
                metadata["published_date"] = published_date
            if row_dict.get("last_updated_raw") or row_dict.get("last_updated_normalized"):
                last_updated = {}
                if row_dict.get("last_updated_raw"):
                    last_updated["raw"] = row_dict["last_updated_raw"]
                if row_dict.get("last_updated_normalized"):
                    if isinstance(row_dict["last_updated_normalized"], datetime):
                        last_updated["normalized"] = (
                            row_dict["last_updated_normalized"].isoformat() + "Z"
                        )
                    else:
                        last_updated["normalized"] = row_dict["last_updated_normalized"]
                metadata["last_updated"] = last_updated
            version_dict["metadata"] = metadata

            # Build creator
            if row_dict.get("creator_username"):
                version_dict["creator"] = {
                    "username": row_dict["creator_username"],
                    "name": row_dict.get("creator_name"),
                    "profile_url": row_dict.get("creator_url"),
                }

            versions.append(version_dict)

        return versions

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching product versions from DB: {type(e).__name__}: {str(e)}")
        return []


def find_all_product_versions(product_id: str) -> List[Dict]:
    """Find all versions of a product from database and JSON files.

    Priority: Database (product_history) first, then JSON files as fallback.

    Args:
        product_id: Product identifier

    Returns:
        List of product data dicts, each with a 'source_path' key
    """
    versions = []

    # First, try database (product_history table)
    db_versions = find_product_versions_from_db(product_id)
    versions.extend(db_versions)

    # Then, check JSON files as fallback (for older scrapes not in DB)
    data_path = Path(settings.data_path)

    # Check main data directory
    main_data = load_product_from_json(product_id, data_path)
    if main_data:
        # Only add if not already in DB versions (avoid duplicates)
        if not any(v.get("scraped_at") == main_data.get("scraped_at") for v in db_versions):
            main_data["source_path"] = str(data_path)
            versions.append(main_data)

    # Check scraped-data (2) directory (legacy)
    scraped_data_2 = data_path.parent / "scraped-data (2)" / "data"
    if scraped_data_2.exists():
        version_2 = load_product_from_json(product_id, scraped_data_2)
        if version_2:
            # Only add if not already in versions
            if not any(v.get("scraped_at") == version_2.get("scraped_at") for v in versions):
                version_2["source_path"] = str(scraped_data_2)
                versions.append(version_2)

    # Check for dated scrape directories (scraped-data-YYYY-MM-DD)
    for scrape_dir in data_path.parent.glob("scraped-data-*"):
        if scrape_dir.is_dir():
            # Try both: direct structure and nested data/ structure
            scrape_data = scrape_dir / "data"
            if not scrape_data.exists():
                scrape_data = scrape_dir  # Direct structure

            if scrape_data.exists():
                version = load_product_from_json(product_id, scrape_data)
                if version:
                    # Only add if not already in versions
                    if not any(v.get("scraped_at") == version.get("scraped_at") for v in versions):
                        version["source_path"] = str(scrape_data)
                        versions.append(version)

    return versions


class ProductChange(BaseModel):
    """Model for a single field change."""

    field: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    change_type: str = Field(..., description="Type: added, removed, changed, unchanged")


class ProductChangesResponse(BaseModel):
    """Response model for product changes over time."""

    product_id: str
    versions: List[Dict] = Field(..., description="List of product versions found")
    changes: List[ProductChange] = Field(..., description="List of detected changes")
    meta: dict = Field(default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"})


@router.get("/{product_id}/changes", response_model=ProductChangesResponse)
@cached(ttl=600, cache_type="product")  # Cache for 10 minutes (changes don't update frequently)
async def get_product_changes(product_id: str):
    """Get changes in product data across different scrapes.

    This endpoint compares product data from different scrape runs to identify
    changes in statistics, metadata, and other fields.

    Args:
        product_id: Product identifier

    Returns:
        ProductChangesResponse with detected changes

    Raises:
        404: Product not found in any scrape
    """
    versions = find_all_product_versions(product_id)

    if not versions:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "PRODUCT_NOT_FOUND",
                    "message": f"Product with ID '{product_id}' not found in any scrape",
                    "details": {"product_id": product_id},
                }
            },
        )

    # Sort versions by scraped_at timestamp
    versions.sort(key=lambda v: v.get("scraped_at", ""), reverse=True)

    # Compare versions if we have multiple
    changes = []
    if len(versions) >= 2:
        old_version = versions[-1]  # Oldest
        new_version = versions[0]  # Newest

        # Compare stats
        old_stats = old_version.get("stats", {})
        new_stats = new_version.get("stats", {})

        stat_fields = ["views", "pages", "users", "installs", "vectors"]
        for field in stat_fields:
            old_val = None
            new_val = None

            if field in old_stats:
                old_stat = old_stats[field]
                if isinstance(old_stat, dict):
                    old_val = old_stat.get("normalized")
                else:
                    old_val = old_stat

            if field in new_stats:
                new_stat = new_stats[field]
                if isinstance(new_stat, dict):
                    new_val = new_stat.get("normalized")
                else:
                    new_val = new_stat

            if old_val != new_val:
                changes.append(
                    ProductChange(
                        field=f"stats.{field}",
                        old_value=old_val,
                        new_value=new_val,
                        change_type=(
                            "changed"
                            if old_val is not None and new_val is not None
                            else ("added" if new_val is not None else "removed")
                        ),
                    )
                )

        # Compare price
        old_price = old_version.get("price")
        new_price = new_version.get("price")
        if old_price != new_price:
            changes.append(
                ProductChange(
                    field="price",
                    old_value=old_price,
                    new_value=new_price,
                    change_type=(
                        "changed"
                        if old_price is not None and new_price is not None
                        else ("added" if new_price is not None else "removed")
                    ),
                )
            )

        # Compare metadata
        old_metadata = old_version.get("metadata", {})
        new_metadata = new_version.get("metadata", {})

        # Compare version
        old_version_str = old_metadata.get("version")
        new_version_str = new_metadata.get("version")
        if old_version_str != new_version_str:
            changes.append(
                ProductChange(
                    field="metadata.version",
                    old_value=old_version_str,
                    new_value=new_version_str,
                    change_type=(
                        "changed"
                        if old_version_str and new_version_str
                        else ("added" if new_version_str else "removed")
                    ),
                )
            )

        # Compare last_updated
        old_last_updated = old_metadata.get("last_updated", {})
        new_last_updated = new_metadata.get("last_updated", {})
        if isinstance(old_last_updated, dict):
            old_last_updated = old_last_updated.get("normalized")
        if isinstance(new_last_updated, dict):
            new_last_updated = new_last_updated.get("normalized")
        if old_last_updated != new_last_updated:
            changes.append(
                ProductChange(
                    field="metadata.last_updated",
                    old_value=old_last_updated,
                    new_value=new_last_updated,
                    change_type=(
                        "changed"
                        if old_last_updated and new_last_updated
                        else ("added" if new_last_updated else "removed")
                    ),
                )
            )

    # Prepare versions for response (remove source_path, keep essential info)
    versions_for_response = []
    for v in versions:
        versions_for_response.append(
            {
                "scraped_at": v.get("scraped_at"),
                "source_path": v.get("source_path"),
                "stats": v.get("stats", {}),
                "price": v.get("price"),
                "metadata": {
                    "version": v.get("metadata", {}).get("version"),
                    "last_updated": v.get("metadata", {}).get("last_updated"),
                },
            }
        )

    return ProductChangesResponse(
        product_id=product_id,
        versions=versions_for_response,
        changes=changes,
        meta={"timestamp": datetime.utcnow().isoformat() + "Z"},
    )


def load_all_products_from_json(base_path: Path, product_type: Optional[str] = None) -> List[Dict]:
    """Load all products from JSON files in a directory.

    Args:
        base_path: Base path to search
        product_type: Optional product type filter

    Returns:
        List of product data dicts
    """
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


class CategoryComparison(BaseModel):
    """Model for category comparison."""

    category: str
    scrap_1_date: str
    scrap_2_date: str
    products_count_1: int
    products_count_2: int
    total_views_1: int
    total_views_2: int
    views_change: int
    views_change_percent: float


class CategoryComparisonResponse(BaseModel):
    """Response model for category comparison."""

    data: List[CategoryComparison]
    meta: dict = Field(default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"})


@router.get("/categories/comparison", response_model=CategoryComparisonResponse)
async def get_category_comparison(
    product_type: Optional[str] = Query(
        None, description="Product type: template, component, vector, plugin"
    ),
    category: Optional[str] = Query(None, description="Filter by specific category"),
):
    """Compare total views by category between different scrapes.

    This endpoint compares the total number of views for each category
    across different scrape runs to identify growth trends.

    Args:
        product_type: Optional product type filter
        category: Optional specific category filter

    Returns:
        CategoryComparisonResponse with category statistics
    """
    # Validate product type
    if product_type and product_type not in ["template", "component", "vector", "plugin"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_PRODUCT_TYPE",
                    "message": (
                        "Invalid product type. Must be one of: template, component, vector, plugin"
                    ),
                    "details": {"type": product_type},
                }
            },
        )

    data_path = Path(settings.data_path)

    # Load products from main data directory (latest)
    products_scrap1 = load_all_products_from_json(data_path, product_type)

    # Load products from all historical scrapes
    products_scrap2 = []

    # Check legacy scraped-data (2) directory
    scraped_data_2 = data_path.parent / "scraped-data (2)" / "data"
    if scraped_data_2.exists():
        products_scrap2.extend(load_all_products_from_json(scraped_data_2, product_type))

    # Check all dated scrape directories (scraped-data-YYYY-MM-DD)
    for scrape_dir in sorted(data_path.parent.glob("scraped-data-*"), reverse=True):
        if scrape_dir.is_dir():
            # Try both: direct structure and nested data/ structure
            scrape_data = scrape_dir / "data"
            if not scrape_data.exists():
                scrape_data = scrape_dir  # Direct structure

            if scrape_data.exists():
                scraped_products = load_all_products_from_json(scrape_data, product_type)
                products_scrap2.extend(scraped_products)

    # Use the most recent scrape for comparison (if multiple found)
    # Group by scrape date and use the most recent one
    if products_scrap2:
        # Get unique scrape dates
        scrape_dates = {}
        for product in products_scrap2:
            scraped_at = product.get("scraped_at", "")
            if scraped_at:
                date_key = scraped_at[:10]  # YYYY-MM-DD
                if date_key not in scrape_dates:
                    scrape_dates[date_key] = []
                scrape_dates[date_key].append(product)

        # Use the most recent scrape date
        if scrape_dates:
            most_recent_date = max(scrape_dates.keys())
            products_scrap2 = scrape_dates[most_recent_date]

    # Get scrape dates
    scrap1_date = None
    scrap2_date = None
    if products_scrap1:
        scrap1_date = products_scrap1[0].get("scraped_at", "")[:10]
    if products_scrap2:
        scrap2_date = products_scrap2[0].get("scraped_at", "")[:10]

    # Group by category
    categories_scrap1 = defaultdict(lambda: {"views": [], "count": 0})
    categories_scrap2 = defaultdict(lambda: {"views": [], "count": 0})

    for product in products_scrap1:
        cat = product.get("category")
        if cat:
            views = product.get("stats", {}).get("views", {})
            views_val = views.get("normalized") if isinstance(views, dict) else views
            if views_val:
                categories_scrap1[cat]["views"].append(views_val)
            categories_scrap1[cat]["count"] += 1

    for product in products_scrap2:
        cat = product.get("category")
        if cat:
            views = product.get("stats", {}).get("views", {})
            views_val = views.get("normalized") if isinstance(views, dict) else views
            if views_val:
                categories_scrap2[cat]["views"].append(views_val)
            categories_scrap2[cat]["count"] += 1

    # Find common categories
    all_categories = set(categories_scrap1.keys()) | set(categories_scrap2.keys())

    if category:
        if category not in all_categories:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "CATEGORY_NOT_FOUND",
                        "message": f"Category '{category}' not found",
                        "details": {"category": category},
                    }
                },
            )
        all_categories = {category}

    # Build comparison
    comparisons = []
    for cat in sorted(all_categories):
        total_views_1 = sum(categories_scrap1[cat]["views"])
        total_views_2 = sum(categories_scrap2[cat]["views"])
        count_1 = categories_scrap1[cat]["count"]
        count_2 = categories_scrap2[cat]["count"]

        views_change = total_views_2 - total_views_1
        views_change_percent = 0.0
        if total_views_1 > 0:
            views_change_percent = (views_change / total_views_1) * 100

        comparisons.append(
            CategoryComparison(
                category=cat,
                scrap_1_date=scrap1_date or "",
                scrap_2_date=scrap2_date or "",
                products_count_1=count_1,
                products_count_2=count_2,
                total_views_1=total_views_1,
                total_views_2=total_views_2,
                views_change=views_change,
                views_change_percent=round(views_change_percent, 2),
            )
        )

    # Sort by absolute change
    comparisons.sort(key=lambda x: abs(x.views_change), reverse=True)

    return CategoryComparisonResponse(
        data=comparisons,
        meta={
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_categories": len(comparisons),
        },
    )


class TopCategoryByViews(BaseModel):
    """Model for top category by views."""

    category_name: str
    total_views: int
    products_count: int
    views_change: int = 0
    views_change_percent: float = 0.0


class TopCategoriesByViewsResponse(BaseModel):
    """Response model for top categories by views."""

    data: List[TopCategoryByViews]
    meta: dict = Field(
        default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"}
    )


@router.get("/categories/top-by-views", response_model=TopCategoriesByViewsResponse)
@cached(ttl=300, cache_type="product")  # Cache for 5 minutes
async def get_top_categories_by_views(
    limit: int = Query(10, ge=1, le=100, description="Number of categories to return"),
    period_hours: int = Query(24, ge=1, le=168, description="Period in hours for % change (1-168, default: 24)"),
    product_type: Optional[str] = Query(
        None, description="Filter by product type: template, component, vector, plugin"
    ),
):
    """Get top categories by total views with percentage change.

    This endpoint uses JSON files to get accurate product counts per category,
    because products can have multiple categories and only the main one is stored in DB.
    JSON files contain all categories for each product.
    
    For period comparison, it uses product_history from database to calculate views change.

    Args:
        limit: Number of top categories to return (1-100, default: 10)
        period_hours: Period in hours to compare for % change (1-168, default: 24)
        product_type: Optional filter by product type

    Returns:
        TopCategoriesByViewsResponse with top categories sorted by total views
    """
    # Validate product type
    if product_type and product_type not in ["template", "component", "vector", "plugin"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_PRODUCT_TYPE",
                    "message": (
                        "Invalid product type. Must be one of: template, component, vector, plugin"
                    ),
                    "details": {"type": product_type},
                }
            },
        )

    try:
        # Try to load from JSON files first (contains all categories)
        data_path = Path(settings.data_path)
        products = []
        
        if data_path.exists():
            products = load_all_products_from_json(data_path, product_type)
        
        # If no products from JSON, fallback to database
        if not products:
            engine = get_db_engine()
            if engine:
                try:
                    from sqlalchemy import text
                    
                    # Build WHERE clause
                    where_clause = "WHERE category IS NOT NULL AND views_normalized IS NOT NULL"
                    params = {}
                    if product_type:
                        where_clause += " AND type = :product_type"
                        params["product_type"] = product_type
                    
                    query_str = (
                        """
                        SELECT 
                            category,
                            categories,
                            views_normalized,
                            id
                        FROM products
                        """ + where_clause
                    )
                    query = text(query_str)
                    
                    import json
                    with engine.connect() as conn:
                        result = conn.execute(query, params)
                        for row in result:
                            # Use categories JSONB if available, fallback to category
                            categories_list = []
                            if row[1]:  # categories JSONB column
                                try:
                                    if isinstance(row[1], str):
                                        categories_list = json.loads(row[1])
                                    else:
                                        categories_list = row[1]  # Already parsed JSONB
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            
                            # Fallback to main category if categories list is empty
                            if not categories_list and row[0]:
                                categories_list = [row[0]]
                            
                            products.append({
                                "category": row[0],
                                "categories": categories_list,
                                "stats": {
                                    "views": {
                                        "normalized": row[2] or 0
                                    }
                                }
                            })
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Could not load products from database: {str(e)}")
        
        if not products:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"No products found in JSON files or database for type {product_type}")
            return TopCategoriesByViewsResponse(
                data=[],
                meta={
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "period_hours": period_hours,
                    "limit": limit,
                    "product_type": product_type,
                },
            )
        
        # Count products per category (using all categories from each product)
        category_counts: Dict[str, Dict[str, Any]] = {}
        
        for product in products:
            # Get all categories for this product
            categories_list = product.get("categories", [])
            # Fallback to main category if categories list is empty
            if not categories_list and product.get("category"):
                categories_list = [product.get("category")]
            
            # Get views for this product
            views = 0
            if product.get("stats") and product.get("stats").get("views"):
                views = product.get("stats").get("views").get("normalized") or 0
            
            # Count this product in all its categories
            for category_name in categories_list:
                if not category_name:
                    continue
                    
                if category_name not in category_counts:
                    category_counts[category_name] = {
                        "products_count": 0,
                        "total_views": 0
                    }
                
                category_counts[category_name]["products_count"] += 1
                category_counts[category_name]["total_views"] += views
        
        # Get period ago views from database for comparison
        period_ago_data: Dict[str, int] = {}
        engine = get_db_engine()
        if engine:
            try:
                from sqlalchemy import text
                now = datetime.utcnow()
                period_ago = now - timedelta(hours=period_hours)
                
                # Build WHERE clause for product type filter
                where_clause_period = "WHERE category IS NOT NULL AND views_normalized IS NOT NULL"
                params_period = {"period_ago_time": period_ago}
                if product_type:
                    where_clause_period += " AND type = :product_type"
                    params_period["product_type"] = product_type

                query_period_ago = text(
                    """
                    WITH period_views AS (
                        SELECT DISTINCT ON (product_id)
                            product_id,
                            category,
                            views_normalized
                        FROM product_history
                    """ + where_clause_period + """
                        AND scraped_at <= :period_ago_time
                        ORDER BY product_id, scraped_at DESC
                    )
                    SELECT 
                        category,
                        SUM(views_normalized) as total_views
                    FROM period_views
                    GROUP BY category
                """
                )

                with engine.connect() as conn:
                    result_period = conn.execute(query_period_ago, params_period)
                    period_ago_data = {
                        row[0]: int(row[1]) if row[1] else 0 for row in result_period
                    }
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not get period ago data from database: {str(e)}")
                # Continue without period comparison
        
        # Convert to list and calculate changes
        top_categories = []
        for category_name, data in category_counts.items():
            current_views = data["total_views"]
            previous_views = period_ago_data.get(category_name, 0)

            # Calculate change
            views_change = current_views - previous_views
            views_change_percent = 0.0
            if previous_views > 0:
                views_change_percent = (views_change / previous_views) * 100

            top_categories.append(
                TopCategoryByViews(
                    category_name=category_name,
                    total_views=current_views,
                    products_count=data["products_count"],
                    views_change=views_change,
                    views_change_percent=round(views_change_percent, 2),
                )
            )
        
        # Sort by total_views descending and take top N
        top_categories.sort(key=lambda x: x.total_views, reverse=True)
        top_categories = top_categories[:limit]
        
        return TopCategoriesByViewsResponse(
            data=top_categories,
            meta={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "period_hours": period_hours,
                "limit": limit,
                "product_type": product_type,
            },
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"Error calculating top categories: {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to calculate top categories: {str(e)}",
                    "details": {},
                }
            },
        )


class CategoryViewsResponse(BaseModel):
    """Response model for category views statistics."""

    category: str
    product_type: Optional[str] = None
    total_views: int
    products_count: int
    average_views_per_product: float
    free_products_count: int
    paid_products_count: int
    products: List[dict] = Field(
        default_factory=list, description="List of products in category (optional)"
    )
    meta: dict = Field(
        default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"}
    )


@router.get("/categories/{category_name}/views", response_model=CategoryViewsResponse)
@cached(ttl=300, cache_type="product")  # Cache for 5 minutes
async def get_category_views(
    category_name: str,
    product_type: Optional[str] = Query(
        None, description="Filter by product type: template, component, vector, plugin"
    ),
    include_products: bool = Query(
        False, description="Include list of products in response"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Max products to include (if include_products=true)"),
):
    """Get total views and statistics for a specific category.

    This endpoint calculates the total number of views, product count, and other
    statistics for a given category, optionally filtered by product type.

    Args:
        category_name: Name of the category
        product_type: Optional filter by product type
        include_products: Whether to include list of products in response
        limit: Maximum number of products to include (if include_products=true)

    Returns:
        CategoryViewsResponse with category statistics

    Raises:
        404: Category not found
    """
    # Validate product type
    if product_type and product_type not in ["template", "component", "vector", "plugin"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_PRODUCT_TYPE",
                    "message": (
                        "Invalid product type. Must be one of: template, component, vector, plugin"
                    ),
                    "details": {"type": product_type},
                }
            },
        )

    # Build query with prepared statements
    where_clause = "WHERE category = :category"
    params = {"category": category_name}
    if product_type:
        where_clause += " AND type = :product_type"
        params["product_type"] = product_type

    # Get category statistics
    stats_query = (
        """
        SELECT 
            COUNT(*) as products_count,
            SUM(views_normalized) as total_views,
            SUM(CASE WHEN is_free = true THEN 1 ELSE 0 END) as free_products_count,
            SUM(CASE WHEN is_free = false THEN 1 ELSE 0 END) as paid_products_count
        FROM products
        """
        + where_clause
        + """
        AND views_normalized IS NOT NULL
    """
    )
    stats_result = execute_query_one(stats_query, params)

    if not stats_result or stats_result.get("products_count", 0) == 0:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "CATEGORY_NOT_FOUND",
                    "message": f"Category '{category_name}' not found",
                    "details": {"category": category_name, "product_type": product_type},
                }
            },
        )

    products_count = stats_result.get("products_count", 0) or 0
    total_views = stats_result.get("total_views", 0) or 0
    free_products_count = stats_result.get("free_products_count", 0) or 0
    paid_products_count = stats_result.get("paid_products_count", 0) or 0

    # Calculate average views per product
    average_views = 0.0
    if products_count > 0:
        average_views = total_views / products_count

    # Get products list if requested
    products_list = []
    if include_products:
        products_query = (
            """
            SELECT id, name, type, views_normalized, is_free, price
            FROM products
            """
            + where_clause
            + """
            AND views_normalized IS NOT NULL
            ORDER BY views_normalized DESC
            LIMIT :limit
        """
        )
        params["limit"] = limit
        products_rows = execute_query(products_query, params)

        if products_rows:
            products_list = [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "type": row["type"],
                    "views": row["views_normalized"],
                    "is_free": row.get("is_free", False),
                    "price": float(row["price"]) if row.get("price") else None,
                }
                for row in products_rows
            ]

    return CategoryViewsResponse(
        category=category_name,
        product_type=product_type,
        total_views=total_views,
        products_count=products_count,
        average_views_per_product=round(average_views, 2),
        free_products_count=free_products_count,
        paid_products_count=paid_products_count,
        products=products_list,
        meta={
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@router.get("/categories/all-by-count", response_model=TopCategoriesByViewsResponse)
@cached(ttl=300, cache_type="product")  # Cache for 5 minutes
async def get_all_categories_by_count(
    limit: int = Query(100, ge=1, le=1000, description="Number of categories to return"),
    product_type: Optional[str] = Query(
        "template", description="Filter by product type: template, component, vector, plugin"
    ),
):
    """Get all categories sorted by product count.
    
    This endpoint uses JSON files to get accurate product counts per category,
    because products can have multiple categories and only the main one is stored in DB.
    JSON files contain all categories for each product.
    
    Args:
        limit: Number of categories to return (1-1000, default: 100)
        product_type: Product type filter (default: template)
    
    Returns:
        TopCategoriesByViewsResponse with categories sorted by product count
    """
    # Validate product type
    if product_type and product_type not in ["template", "component", "vector", "plugin"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_PRODUCT_TYPE",
                    "message": (
                        "Invalid product type. Must be one of: template, component, vector, plugin"
                    ),
                    "details": {"type": product_type},
                }
            },
        )
    
    try:
        # Try to load from JSON files first (contains all categories)
        data_path = Path(settings.data_path)
        products = []
        
        if data_path.exists():
            products = load_all_products_from_json(data_path, product_type)
        
        # If no products from JSON, fallback to database
        if not products:
            engine = get_db_engine()
            if engine:
                try:
                    from sqlalchemy import text
                    
                    # Build WHERE clause
                    where_clause = "WHERE category IS NOT NULL AND views_normalized IS NOT NULL"
                    params = {}
                    if product_type:
                        where_clause += " AND type = :product_type"
                        params["product_type"] = product_type
                    
                    query_str = (
                        """
                        SELECT 
                            category,
                            categories,
                            views_normalized,
                            id
                        FROM products
                        """ + where_clause
                    )
                    query = text(query_str)
                    
                    import json
                    with engine.connect() as conn:
                        result = conn.execute(query, params)
                        for row in result:
                            # Use categories JSONB if available, fallback to category
                            categories_list = []
                            if row[1]:  # categories JSONB column
                                try:
                                    if isinstance(row[1], str):
                                        categories_list = json.loads(row[1])
                                    else:
                                        categories_list = row[1]  # Already parsed JSONB
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            
                            # Fallback to main category if categories list is empty
                            if not categories_list and row[0]:
                                categories_list = [row[0]]
                            
                            products.append({
                                "category": row[0],
                                "categories": categories_list,
                                "stats": {
                                    "views": {
                                        "normalized": row[2] or 0
                                    }
                                }
                            })
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Could not load products from database: {str(e)}")
        
        if not products:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"No products found in JSON files or database for type {product_type}")
            return TopCategoriesByViewsResponse(
                data=[],
                meta={
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "limit": limit,
                    "product_type": product_type,
                },
            )
        
        # Count products per category (using all categories from each product)
        category_counts: Dict[str, Dict[str, Any]] = {}
        
        for product in products:
            # Get all categories for this product
            categories_list = product.get("categories", [])
            # Fallback to main category if categories list is empty
            if not categories_list and product.get("category"):
                categories_list = [product.get("category")]
            
            # Get views for this product
            views = 0
            if product.get("stats") and product.get("stats").get("views"):
                views = product.get("stats").get("views").get("normalized") or 0
            
            # Count this product in all its categories
            for category_name in categories_list:
                if not category_name:
                    continue
                    
                if category_name not in category_counts:
                    category_counts[category_name] = {
                        "products_count": 0,
                        "total_views": 0
                    }
                
                category_counts[category_name]["products_count"] += 1
                category_counts[category_name]["total_views"] += views
        
        # Convert to list and sort by products_count
        categories = []
        for category_name, data in category_counts.items():
            categories.append(
                TopCategoryByViews(
                    category_name=category_name,
                    total_views=data["total_views"],
                    products_count=data["products_count"],
                    views_change=0,
                    views_change_percent=0.0,
                )
            )
        
        # Sort by products_count ascending and take top N
        categories.sort(key=lambda x: x.products_count)
        categories = categories[:limit]
        
        return TopCategoriesByViewsResponse(
            data=categories,
            meta={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "limit": limit,
                "product_type": product_type,
            },
        )
    
    except Exception as e:
        import logging
        
        logger = logging.getLogger(__name__)
        logger.error(
            f"Error getting categories by count: {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to get categories by count: {str(e)}",
                    "details": {},
                }
            },
        )
