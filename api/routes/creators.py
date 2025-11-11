"""API routes for creators."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.dependencies import execute_query, execute_query_one
from api.cache import cached
from src.models.creator import Creator, CreatorStats

router = APIRouter(prefix="/api/creators", tags=["creators"])


def db_row_to_creator(row: dict) -> Creator:
    """Convert database row to Creator model.

    Args:
        row: Database row as dict

    Returns:
        Creator model
    """
    # Build stats
    stats = CreatorStats(
        total_products=row.get("total_products", 0),
        templates_count=row.get("templates_count", 0),
        components_count=row.get("components_count", 0),
        vectors_count=row.get("vectors_count", 0),
        plugins_count=row.get("plugins_count", 0),
        total_sales=row.get("total_sales"),
    )

    # Parse social_media JSONB
    social_media = {}
    if row.get("social_media"):
        if isinstance(row["social_media"], dict):
            social_media = row["social_media"]
        elif isinstance(row["social_media"], str):
            import json

            try:
                social_media = json.loads(row["social_media"])
            except (json.JSONDecodeError, TypeError):
                social_media = {}

    # Build creator
    creator = Creator(
        username=row["username"],
        name=row.get("name"),
        profile_url=row["profile_url"],
        avatar_url=row.get("avatar_url"),
        bio=row.get("bio"),
        website=row.get("website"),
        social_media=social_media,
        stats=stats,
    )

    return creator


class CreatorListResponse(BaseModel):
    """Response model for creator list."""

    data: List[Creator]
    meta: dict = Field(
        default_factory=lambda: {
            "total": 0,
            "limit": 100,
            "offset": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )


class CreatorResponse(BaseModel):
    """Response model for single creator."""

    data: Creator
    meta: dict = Field(default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"})


@router.get("", response_model=CreatorListResponse)
@cached(ttl=300, cache_type="creator")  # Cache for 5 minutes
async def get_creators(
    limit: int = Query(100, ge=1, le=1000, description="Number of creators to return"),
    offset: int = Query(0, ge=0, description="Number of creators to skip"),
    sort: str = Query("username", description="Sort field: username, total_products"),
    order: str = Query("asc", description="Sort order: asc, desc"),
):
    """Get list of creators.

    Args:
        limit: Number of creators to return (1-1000)
        offset: Number of creators to skip
        sort: Sort field
        order: Sort order (asc/desc)

    Returns:
        CreatorListResponse with creators and metadata
    """
    # Validate sort field
    valid_sorts = ["username", "total_products", "created_at"]
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

    # Map sort field to database column
    sort_column_map = {
        "username": "username",
        "total_products": "total_products",
        "created_at": "created_at",
    }
    sort_column = sort_column_map.get(sort, "username")

    # Validate order (whitelist for security)
    order_upper = order.upper()
    if order_upper not in ["ASC", "DESC"]:
        order_upper = "ASC"

    # Get total count
    count_query = "SELECT COUNT(*) as total FROM creators"
    count_result = execute_query_one(count_query)
    total = count_result["total"] if count_result else 0

    # Get creators using prepared statements
    # Note: ORDER BY column name must use whitelist (cannot be parameterized)
    query = (
        f"SELECT * FROM creators ORDER BY {sort_column} {order_upper} LIMIT :limit OFFSET :offset"
    )
    params = {"limit": limit, "offset": offset}

    rows = execute_query(query, params)
    if rows is None:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to fetch creators from database",
                    "details": {},
                }
            },
        )

    # Convert to Creator models (rows is empty list if no results)
    creators = [db_row_to_creator(row) for row in rows]

    return CreatorListResponse(
        data=creators,
        meta={
            "total": total,
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@router.get("/{username}", response_model=CreatorResponse)
@cached(ttl=300, cache_type="creator")  # Cache for 5 minutes
async def get_creator(username: str):
    """Get single creator by username.

    Args:
        username: Creator username

    Returns:
        CreatorResponse with creator data

    Raises:
        404: Creator not found
    """
    query = "SELECT * FROM creators WHERE username = :username"
    row = execute_query_one(query, {"username": username})

    if not row:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "CREATOR_NOT_FOUND",
                    "message": f"Creator with username '{username}' not found",
                    "details": {"username": username},
                }
            },
        )

    creator = db_row_to_creator(row)

    return CreatorResponse(
        data=creator,
        meta={"timestamp": datetime.utcnow().isoformat() + "Z"},
    )


@router.get("/{username}/products", response_model=dict)
@cached(ttl=300, cache_type="product")  # Cache for 5 minutes
async def get_creator_products(
    username: str,
    type: Optional[str] = Query(
        None, description="Product type: template, component, vector, plugin"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Number of products to return"),
    offset: int = Query(0, ge=0, description="Number of products to skip"),
):
    """Get products by creator username.

    Args:
        username: Creator username
        type: Filter by product type
        limit: Number of products to return (1-1000)
        offset: Number of products to skip

    Returns:
        ProductListResponse with products and metadata
    """
    # Validate type
    if type and type not in ["template", "component", "vector", "plugin"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_PRODUCT_TYPE",
                    "message": "Invalid product type. Must be one of: template, component, vector, plugin",
                    "details": {"type": type},
                }
            },
        )

    # Check if creator exists
    creator_query = "SELECT username FROM creators WHERE username = :username"
    creator_row = execute_query_one(creator_query, {"username": username})
    if not creator_row:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "CREATOR_NOT_FOUND",
                    "message": f"Creator with username '{username}' not found",
                    "details": {"username": username},
                }
            },
        )

    # Build query
    where_clause = "WHERE creator_username = :username"
    params = {"username": username}
    if type:
        where_clause += " AND type = :type"
        params["type"] = type

    # Get total count using prepared statement
    count_query = "SELECT COUNT(*) as total FROM products " + where_clause
    count_result = execute_query_one(count_query, params)
    total = count_result["total"] if count_result else 0

    # Get products using prepared statements
    # Note: LIMIT and OFFSET use parameters (prepared statements)
    query = (
        "SELECT * FROM products "
        + where_clause
        + " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    )
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

    # Import here to avoid circular import
    from api.routes.products import db_row_to_product

    # Convert to Product models
    products = [db_row_to_product(row) for row in rows]

    return {
        "data": products,
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }
