"""API routes for products."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.dependencies import execute_query, execute_query_one
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
        features.features = [
            f.strip() for f in row["features_list"].split(",") if f.strip()
        ]
    features.is_responsive = row.get("is_responsive", False)
    features.has_animations = row.get("has_animations", False)
    features.cms_integration = row.get("cms_integration", False)
    features.pages_count = row.get("pages_count")

    # Build media
    media = ProductMedia()
    if row.get("thumbnail_url"):
        media.thumbnail = row["thumbnail_url"]
    media.screenshots_count = row.get("screenshots_count", 0)

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
                product.scraped_at = datetime.fromisoformat(row["scraped_at"].replace("Z", "+00:00"))
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
    meta: dict = Field(
        default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"}
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: dict


@router.get("", response_model=ProductListResponse)
async def get_products(
    type: Optional[str] = Query(None, description="Product type: template, component, vector, plugin"),
    limit: int = Query(100, ge=1, le=1000, description="Number of products to return"),
    offset: int = Query(0, ge=0, description="Number of products to skip"),
    sort: str = Query("created_at", description="Sort field: created_at, updated_at, views_normalized"),
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
                    "message": f"Invalid product type. Must be one of: template, component, vector, plugin",
                    "details": {"type": type},
                }
            },
        )

    # Build query
    where_clause = ""
    params = {}
    if type:
        where_clause = "WHERE type = :type"
        params["type"] = type

    # Map sort field to database column
    sort_column_map = {
        "created_at": "created_at",
        "updated_at": "updated_at",
        "scraped_at": "scraped_at",
        "views_normalized": "views_normalized",
        "name": "name",
    }
    sort_column = sort_column_map.get(sort, "created_at")

    # Get total count - create separate params dict without limit/offset
    count_params = {k: v for k, v in params.items() if k not in ["limit", "offset"]}
    count_query = f"SELECT COUNT(*) as total FROM products {where_clause}"
    count_result = execute_query_one(count_query, count_params)
    total = count_result["total"] if count_result else 0

    # Get products - use bindparam for LIMIT and OFFSET
    from sqlalchemy import bindparam
    
    query_parts = ["SELECT * FROM products"]
    if where_clause:
        query_parts.append(where_clause)
    query_parts.append(f"ORDER BY {sort_column} {order.upper()}")
    query_parts.append("LIMIT :limit OFFSET :offset")
    
    query = " ".join(query_parts)
    params["limit"] = limit
    params["offset"] = offset

    rows = execute_query(query, params)
    if rows is None:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to fetch products from database",
                    "details": {},
                }
            },
        )

    # Convert to Product models (rows is empty list if no results)
    products = [db_row_to_product(row) for row in rows]

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

