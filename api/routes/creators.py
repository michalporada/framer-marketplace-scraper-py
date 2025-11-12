"""API routes for creators."""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.dependencies import execute_query, execute_query_one, get_db_engine
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


class TopCreatorByViews(BaseModel):
    """Model for top creator by template views."""

    username: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    total_views: int
    templates_count: int
    views_change: int = 0
    views_change_percent: float = 0.0


class TopCreatorsByViewsResponse(BaseModel):
    """Response model for top creators by template views."""

    data: List[TopCreatorByViews]
    meta: dict = Field(
        default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"}
    )


class TopCreatorByTemplateCount(BaseModel):
    """Model for top creator by template count."""

    username: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    templates_count: int
    total_products: int
    templates_change: int = 0
    templates_change_percent: float = 0.0


class TopCreatorsByTemplateCountResponse(BaseModel):
    """Response model for top creators by template count."""

    data: List[TopCreatorByTemplateCount]
    meta: dict = Field(
        default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"}
    )


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


@router.get("/top-by-template-views", response_model=TopCreatorsByViewsResponse)
@cached(ttl=300, cache_type="creator")  # Cache for 5 minutes
async def get_top_creators_by_template_views(
    limit: int = Query(10, ge=1, le=100, description="Number of creators to return"),
    period_hours: int = Query(24, ge=1, le=168, description="Period in hours for % change (1-168, default: 24)"),
):
    """Get top creators by total views of their templates.

    This endpoint aggregates views_normalized from product_history for all templates
    of each creator, calculates total views, and compares with period ago to calculate
    percentage change.

    Args:
        limit: Number of top creators to return (1-100, default: 10)
        period_hours: Period in hours to compare for % change (1-168, default: 24)

    Returns:
        TopCreatorsByViewsResponse with top creators sorted by total views

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

        # Query to get latest total views per creator for templates
        # Uses DISTINCT ON to get the most recent scrape for each product
        # Then aggregates by creator_username
        query_latest = text(
            """
            WITH latest_views AS (
                SELECT DISTINCT ON (product_id)
                    product_id,
                    creator_username,
                    views_normalized
                FROM product_history
                WHERE type = 'template'
                    AND views_normalized IS NOT NULL
                    AND scraped_at <= :now_time
                ORDER BY product_id, scraped_at DESC
            )
            SELECT 
                creator_username,
                SUM(views_normalized) as total_views,
                COUNT(*) as templates_count
            FROM latest_views
            GROUP BY creator_username
            ORDER BY total_views DESC
            LIMIT :limit
        """
        )

        # Query to get views from period ago
        query_period_ago = text(
            """
            WITH period_views AS (
                SELECT DISTINCT ON (product_id)
                    product_id,
                    creator_username,
                    views_normalized
                FROM product_history
                WHERE type = 'template'
                    AND views_normalized IS NOT NULL
                    AND scraped_at <= :period_ago_time
                ORDER BY product_id, scraped_at DESC
            )
            SELECT 
                creator_username,
                SUM(views_normalized) as total_views
            FROM period_views
            GROUP BY creator_username
        """
        )

        with engine.connect() as conn:
            # Get latest views aggregated by creator
            result_latest = conn.execute(
                query_latest, {"now_time": now, "limit": limit}
            )
            latest_data = {}
            for row in result_latest:
                latest_data[row[0]] = {
                    "total_views": int(row[1]) if row[1] else 0,
                    "templates_count": int(row[2]) if row[2] else 0,
                }

            # Get views from period ago
            result_period = conn.execute(
                query_period_ago, {"period_ago_time": period_ago}
            )
            period_ago_data = {
                row[0]: int(row[1]) if row[1] else 0 for row in result_period
            }

        # Get creator details (name, avatar) from creators table
        creators_usernames = list(latest_data.keys())
        if not creators_usernames:
            return TopCreatorsByViewsResponse(
                data=[],
                meta={
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "period_hours": period_hours,
                },
            )

        # Get creator details (name, avatar) from creators table
        # Use simple loop with prepared statements for safety
        creator_details = {}
        if creators_usernames:
            for username in creators_usernames:
                creator_query = "SELECT username, name, avatar_url FROM creators WHERE username = :username"
                creator_row = execute_query_one(creator_query, {"username": username})
                if creator_row:
                    creator_details[username] = {
                        "name": creator_row.get("name"),
                        "avatar_url": creator_row.get("avatar_url"),
                    }

        # Calculate changes and build response
        top_creators = []
        for username, views_data in latest_data.items():
            current_views = views_data["total_views"]
            previous_views = period_ago_data.get(username, 0)

            # Calculate change
            views_change = current_views - previous_views
            views_change_percent = 0.0
            if previous_views > 0:
                views_change_percent = (views_change / previous_views) * 100

            creator_info = creator_details.get(username, {})
            top_creators.append(
                TopCreatorByViews(
                    username=username,
                    name=creator_info.get("name"),
                    avatar_url=creator_info.get("avatar_url"),
                    total_views=current_views,
                    templates_count=views_data["templates_count"],
                    views_change=views_change,
                    views_change_percent=round(views_change_percent, 2),
                )
            )

        # Sort by total_views (should already be sorted, but ensure it)
        top_creators.sort(key=lambda x: x.total_views, reverse=True)

        return TopCreatorsByViewsResponse(
            data=top_creators,
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
            f"Error calculating top creators by template views: {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to calculate top creators: {str(e)}",
                    "details": {},
                }
            },
        )


@router.get("/top-by-template-count", response_model=TopCreatorsByTemplateCountResponse)
@cached(ttl=300, cache_type="creator")  # Cache for 5 minutes
async def get_top_creators_by_template_count(
    limit: int = Query(10, ge=1, le=100, description="Number of creators to return"),
    period_hours: int = Query(24, ge=1, le=168, description="Period in hours for % change (1-168, default: 24)"),
):
    """Get top creators by number of templates with percentage change.

    This endpoint counts unique templates from product_history for each creator,
    calculates total templates count, and compares with period ago to calculate
    percentage change in template count.

    Args:
        limit: Number of top creators to return (1-100, default: 10)
        period_hours: Period in hours to compare for % change (1-168, default: 24)

    Returns:
        TopCreatorsByTemplateCountResponse with top creators sorted by template count

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

        # Query to get latest template count per creator
        query_latest = text(
            """
            WITH latest_templates AS (
                SELECT DISTINCT ON (product_id)
                    product_id,
                    creator_username
                FROM product_history
                WHERE type = 'template'
                    AND scraped_at <= :now_time
                ORDER BY product_id, scraped_at DESC
            )
            SELECT 
                creator_username,
                COUNT(*) as templates_count
            FROM latest_templates
            GROUP BY creator_username
            ORDER BY templates_count DESC
            LIMIT :limit
        """
        )

        # Query to get template count from period ago
        query_period_ago = text(
            """
            WITH period_templates AS (
                SELECT DISTINCT ON (product_id)
                    product_id,
                    creator_username
                FROM product_history
                WHERE type = 'template'
                    AND scraped_at <= :period_ago_time
                ORDER BY product_id, scraped_at DESC
            )
            SELECT 
                creator_username,
                COUNT(*) as templates_count
            FROM period_templates
            GROUP BY creator_username
        """
        )

        with engine.connect() as conn:
            # Get latest template counts aggregated by creator
            result_latest = conn.execute(
                query_latest, {"now_time": now, "limit": limit}
            )
            latest_data = {}
            for row in result_latest:
                latest_data[row[0]] = {
                    "templates_count": int(row[1]) if row[1] else 0,
                }

            # Get template counts from period ago
            result_period = conn.execute(
                query_period_ago, {"period_ago_time": period_ago}
            )
            period_ago_data = {
                row[0]: int(row[1]) if row[1] else 0 for row in result_period
            }

        # Get creator details (name, avatar, total_products) from creators table
        creators_usernames = list(latest_data.keys())
        creator_details = {}
        if creators_usernames:
            for username in creators_usernames:
                creator_query = "SELECT username, name, avatar_url, total_products FROM creators WHERE username = :username"
                creator_row = execute_query_one(creator_query, {"username": username})
                if creator_row:
                    creator_details[username] = {
                        "name": creator_row.get("name"),
                        "avatar_url": creator_row.get("avatar_url"),
                        "total_products": creator_row.get("total_products", 0),
                    }

        # Calculate changes and build response
        top_creators = []
        for username, count_data in latest_data.items():
            current_count = count_data["templates_count"]
            previous_count = period_ago_data.get(username, 0)

            # Calculate change
            templates_change = current_count - previous_count
            templates_change_percent = 0.0
            if previous_count > 0:
                templates_change_percent = (templates_change / previous_count) * 100

            creator_info = creator_details.get(username, {})

            top_creators.append(
                TopCreatorByTemplateCount(
                    username=username,
                    name=creator_info.get("name"),
                    avatar_url=creator_info.get("avatar_url"),
                    templates_count=current_count,
                    total_products=creator_info.get("total_products", 0),
                    templates_change=templates_change,
                    templates_change_percent=round(templates_change_percent, 2),
                )
            )

        # Sort by templates_count (should already be sorted, but ensure it)
        top_creators.sort(key=lambda x: x.templates_count, reverse=True)

        return TopCreatorsByTemplateCountResponse(
            data=top_creators,
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
            f"Error calculating top creators by template count: {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to calculate top creators: {str(e)}",
                    "details": {},
                }
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
                    "message": (
                        "Invalid product type. Must be one of: template, component, vector, plugin"
                    ),
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


class ProductGrowth(BaseModel):
    """Model for single product growth."""

    product_id: str
    product_name: str
    product_type: str
    current_views: int
    previous_views: int
    views_change: int
    views_change_percent: float


class CreatorProductsGrowthResponse(BaseModel):
    """Response model for creator products growth analysis."""

    creator_username: str
    creator_name: Optional[str] = None
    product_type: Optional[str] = None
    period_hours: int
    total_products: int
    products_with_data: int
    total_views_current: int
    total_views_previous: int
    total_views_change: int
    total_views_change_percent: float
    products: List[ProductGrowth]
    meta: dict = Field(
        default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"}
    )


@router.get("/{username}/products-growth", response_model=CreatorProductsGrowthResponse)
async def get_creator_products_growth(
    username: str,
    product_type: Optional[str] = Query(
        None, description="Filter by product type: template, component, vector, plugin"
    ),
    period_hours: int = Query(24, ge=1, le=168, description="Period in hours (1-168, default: 24)"),
):
    """Analyze growth of views for creator's products over time.

    This endpoint compares the latest scrape with a scrape from the specified period ago
    and calculates the total change in views for all creator's products.

    Args:
        username: Creator username
        product_type: Optional filter by product type
        period_hours: Period in hours to compare (default: 24, max: 168 = 7 days)

    Returns:
        CreatorProductsGrowthResponse with growth statistics

    Raises:
        404: Creator not found
        503: Database not available
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

    # Check if creator exists
    creator_query = "SELECT username, name FROM creators WHERE username = :username"
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

        # Build where clause for product type filter
        # Using prepared statements to prevent SQL injection
        where_clause = "WHERE creator_username = :username AND views_normalized IS NOT NULL"
        params = {"username": username, "now_time": now, "period_ago_time": period_ago}
        if product_type:
            where_clause += " AND type = :product_type"
            params["product_type"] = product_type

        # Query to get latest views for each product of this creator
        # Uses DISTINCT ON to get the most recent scrape for each product
        # Prepared statement prevents SQL injection
        query_latest = text(
            """
            SELECT DISTINCT ON (product_id)
                product_id,
                name,
                type,
                views_normalized
            FROM product_history
            """ + where_clause + """
                AND scraped_at <= :now_time
            ORDER BY product_id, scraped_at DESC
        """
        )

        # Query to get views from period ago
        # Uses DISTINCT ON to get the most recent scrape before the period mark
        # Prepared statement prevents SQL injection
        query_period_ago = text(
            """
            SELECT DISTINCT ON (product_id)
                product_id,
                views_normalized
            FROM product_history
            """ + where_clause + """
                AND scraped_at <= :period_ago_time
            ORDER BY product_id, scraped_at DESC
        """
        )

        with engine.connect() as conn:
            # Get latest views
            result_latest = conn.execute(query_latest, params)
            latest_data = {}
            for row in result_latest:
                if row[3] is not None:  # views_normalized
                    latest_data[row[0]] = {
                        "name": row[1],
                        "type": row[2],
                        "views": row[3],
                    }

            # Get views from period ago
            result_period = conn.execute(query_period_ago, params)
            period_ago_data = {row[0]: row[1] for row in result_period if row[1] is not None}

        # Calculate growth for each product
        # Compare current views with views from period ago
        products_growth = []
        total_views_current = 0
        total_views_previous = 0

        for product_id, product_data in latest_data.items():
            current_views = product_data["views"]
            previous_views = period_ago_data.get(product_id, 0)  # 0 if product didn't exist

            # Calculate absolute and percentage change
            views_change = current_views - previous_views
            views_change_percent = 0.0
            if previous_views > 0:
                views_change_percent = (views_change / previous_views) * 100

            products_growth.append(
                ProductGrowth(
                    product_id=product_id,
                    product_name=product_data["name"],
                    product_type=product_data["type"],
                    current_views=current_views,
                    previous_views=previous_views,
                    views_change=views_change,
                    views_change_percent=round(views_change_percent, 2),
                )
            )

            total_views_current += current_views
            total_views_previous += previous_views

        # Calculate total change
        total_views_change = total_views_current - total_views_previous
        total_views_change_percent = 0.0
        if total_views_previous > 0:
            total_views_change_percent = (total_views_change / total_views_previous) * 100

        # Sort by views change (descending)
        products_growth.sort(key=lambda x: x.views_change, reverse=True)

        return CreatorProductsGrowthResponse(
            creator_username=username,
            creator_name=creator_row.get("name"),
            product_type=product_type,
            period_hours=period_hours,
            total_products=len(latest_data),
            products_with_data=len([p for p in products_growth if p.previous_views > 0]),
            total_views_current=total_views_current,
            total_views_previous=total_views_previous,
            total_views_change=total_views_change,
            total_views_change_percent=round(total_views_change_percent, 2),
            products=products_growth,
            meta={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "period_start": period_ago.isoformat() + "Z",
                "period_end": now.isoformat() + "Z",
            },
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating creator products growth: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to calculate products growth: {str(e)}",
                    "details": {},
                }
            },
        )
    limit: int = Query(10, ge=1, le=100, description="Number of creators to return"),
    period_hours: int = Query(24, ge=1, le=168, description="Period in hours for % change (1-168, default: 24)"),
):
    """Get top creators by total views of their templates.

    This endpoint aggregates views_normalized from product_history for all templates
    of each creator, calculates total views, and compares with period ago to calculate
    percentage change.

    Args:
        limit: Number of top creators to return (1-100, default: 10)
        period_hours: Period in hours to compare for % change (1-168, default: 24)

    Returns:
        TopCreatorsByViewsResponse with top creators sorted by total views

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

        # Query to get latest total views per creator for templates
        # Uses DISTINCT ON to get the most recent scrape for each product
        # Then aggregates by creator_username
        query_latest = text(
            """
            WITH latest_views AS (
                SELECT DISTINCT ON (product_id)
                    product_id,
                    creator_username,
                    views_normalized
                FROM product_history
                WHERE type = 'template'
                    AND views_normalized IS NOT NULL
                    AND scraped_at <= :now_time
                ORDER BY product_id, scraped_at DESC
            )
            SELECT 
                creator_username,
                SUM(views_normalized) as total_views,
                COUNT(*) as templates_count
            FROM latest_views
            GROUP BY creator_username
            ORDER BY total_views DESC
            LIMIT :limit
        """
        )

        # Query to get views from period ago
        query_period_ago = text(
            """
            WITH period_views AS (
                SELECT DISTINCT ON (product_id)
                    product_id,
                    creator_username,
                    views_normalized
                FROM product_history
                WHERE type = 'template'
                    AND views_normalized IS NOT NULL
                    AND scraped_at <= :period_ago_time
                ORDER BY product_id, scraped_at DESC
            )
            SELECT 
                creator_username,
                SUM(views_normalized) as total_views
            FROM period_views
            GROUP BY creator_username
        """
        )

        with engine.connect() as conn:
            # Get latest views aggregated by creator
            result_latest = conn.execute(
                query_latest, {"now_time": now, "limit": limit}
            )
            latest_data = {}
            for row in result_latest:
                latest_data[row[0]] = {
                    "total_views": int(row[1]) if row[1] else 0,
                    "templates_count": int(row[2]) if row[2] else 0,
                }

            # Get views from period ago
            result_period = conn.execute(
                query_period_ago, {"period_ago_time": period_ago}
            )
            period_ago_data = {
                row[0]: int(row[1]) if row[1] else 0 for row in result_period
            }

        # Get creator details (name, avatar) from creators table
        creators_usernames = list(latest_data.keys())
        if not creators_usernames:
            return TopCreatorsByViewsResponse(
                data=[],
                meta={
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "period_hours": period_hours,
                },
            )

        # Get creator details (name, avatar) from creators table
        # Use simple loop with prepared statements for safety
        creator_details = {}
        if creators_usernames:
            for username in creators_usernames:
                creator_query = "SELECT username, name, avatar_url FROM creators WHERE username = :username"
                creator_row = execute_query_one(creator_query, {"username": username})
                if creator_row:
                    creator_details[username] = {
                        "name": creator_row.get("name"),
                        "avatar_url": creator_row.get("avatar_url"),
                    }

        # Calculate changes and build response
        top_creators = []
        for username, views_data in latest_data.items():
            current_views = views_data["total_views"]
            previous_views = period_ago_data.get(username, 0)

            # Calculate change
            views_change = current_views - previous_views
            views_change_percent = 0.0
            if previous_views > 0:
                views_change_percent = (views_change / previous_views) * 100

            creator_info = creator_details.get(username, {})
            top_creators.append(
                TopCreatorByViews(
                    username=username,
                    name=creator_info.get("name"),
                    avatar_url=creator_info.get("avatar_url"),
                    total_views=current_views,
                    templates_count=views_data["templates_count"],
                    views_change=views_change,
                    views_change_percent=round(views_change_percent, 2),
                )
            )

        # Sort by total_views (should already be sorted, but ensure it)
        top_creators.sort(key=lambda x: x.total_views, reverse=True)

        return TopCreatorsByViewsResponse(
            data=top_creators,
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
            f"Error calculating top creators by template views: {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to calculate top creators: {str(e)}",
                    "details": {},
                }
            },
        )


class TopCreatorByTemplateCount(BaseModel):
    """Model for top creator by template count."""

    username: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    templates_count: int
    total_products: int
    templates_change: int = 0
    templates_change_percent: float = 0.0


class TopCreatorsByTemplateCountResponse(BaseModel):
    """Response model for top creators by template count."""

    data: List[TopCreatorByTemplateCount]
    meta: dict = Field(
        default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"}
    )


@router.get("/top-by-template-count", response_model=TopCreatorsByTemplateCountResponse)
@cached(ttl=300, cache_type="creator")  # Cache for 5 minutes
async def get_top_creators_by_template_count(
    limit: int = Query(10, ge=1, le=100, description="Number of creators to return"),
    period_hours: int = Query(24, ge=1, le=168, description="Period in hours for % change (1-168, default: 24)"),
):
    """Get top creators by number of templates with percentage change.

    This endpoint counts unique templates from product_history for each creator,
    calculates total templates count, and compares with period ago to calculate
    percentage change in template count.

    Args:
        limit: Number of top creators to return (1-100, default: 10)
        period_hours: Period in hours to compare for % change (1-168, default: 24)

    Returns:
        TopCreatorsByTemplateCountResponse with top creators sorted by template count

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

        # Query to get latest template count per creator
        query_latest = text(
            """
            WITH latest_templates AS (
                SELECT DISTINCT ON (product_id)
                    product_id,
                    creator_username
                FROM product_history
                WHERE type = 'template'
                    AND scraped_at <= :now_time
                ORDER BY product_id, scraped_at DESC
            )
            SELECT 
                creator_username,
                COUNT(*) as templates_count
            FROM latest_templates
            GROUP BY creator_username
            ORDER BY templates_count DESC
            LIMIT :limit
        """
        )

        # Query to get template count from period ago
        query_period_ago = text(
            """
            WITH period_templates AS (
                SELECT DISTINCT ON (product_id)
                    product_id,
                    creator_username
                FROM product_history
                WHERE type = 'template'
                    AND scraped_at <= :period_ago_time
                ORDER BY product_id, scraped_at DESC
            )
            SELECT 
                creator_username,
                COUNT(*) as templates_count
            FROM period_templates
            GROUP BY creator_username
        """
        )

        with engine.connect() as conn:
            # Get latest template counts aggregated by creator
            result_latest = conn.execute(
                query_latest, {"now_time": now, "limit": limit}
            )
            latest_data = {}
            for row in result_latest:
                latest_data[row[0]] = {
                    "templates_count": int(row[1]) if row[1] else 0,
                }

            # Get template counts from period ago
            result_period = conn.execute(
                query_period_ago, {"period_ago_time": period_ago}
            )
            period_ago_data = {
                row[0]: int(row[1]) if row[1] else 0 for row in result_period
            }

        # Get creator details (name, avatar, total_products) from creators table
        creators_usernames = list(latest_data.keys())
        creator_details = {}
        if creators_usernames:
            for username in creators_usernames:
                creator_query = "SELECT username, name, avatar_url, total_products FROM creators WHERE username = :username"
                creator_row = execute_query_one(creator_query, {"username": username})
                if creator_row:
                    creator_details[username] = {
                        "name": creator_row.get("name"),
                        "avatar_url": creator_row.get("avatar_url"),
                        "total_products": creator_row.get("total_products", 0),
                    }

        # Calculate changes and build response
        top_creators = []
        for username, count_data in latest_data.items():
            current_count = count_data["templates_count"]
            previous_count = period_ago_data.get(username, 0)

            # Calculate change
            templates_change = current_count - previous_count
            templates_change_percent = 0.0
            if previous_count > 0:
                templates_change_percent = (templates_change / previous_count) * 100

            creator_info = creator_details.get(username, {})

            top_creators.append(
                TopCreatorByTemplateCount(
                    username=username,
                    name=creator_info.get("name"),
                    avatar_url=creator_info.get("avatar_url"),
                    templates_count=current_count,
                    total_products=creator_info.get("total_products", 0),
                    templates_change=templates_change,
                    templates_change_percent=round(templates_change_percent, 2),
                )
            )

        # Sort by templates_count (should already be sorted, but ensure it)
        top_creators.sort(key=lambda x: x.templates_count, reverse=True)

        return TopCreatorsByTemplateCountResponse(
            data=top_creators,
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
            f"Error calculating top creators by template count: {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to calculate top creators: {str(e)}",
                    "details": {},
                }
            },
        )
