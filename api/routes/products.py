"""API routes for products."""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.dependencies import execute_query, execute_query_one, get_db_engine
from api.cache import cached, invalidate_product_cache
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
                features.features = [
                    f.strip() for f in features_list_str.split(",") if f.strip()
                ]
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
@cached(ttl=300, cache_type="product")  # Cache for 5 minutes
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
        query = text("""
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
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"product_id": product_id})
            rows = result.fetchall()
        
        versions = []
        for row in rows:
            row_dict = dict(row._mapping)
            
            # Convert to format expected by comparison logic
            version_dict = {
                "id": row_dict["product_id"],
                "scraped_at": row_dict["scraped_at"].isoformat() + "Z" if row_dict["scraped_at"] else None,
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
                        published_date["normalized"] = row_dict["published_date_normalized"].isoformat() + "Z"
                    else:
                        published_date["normalized"] = row_dict["published_date_normalized"]
                metadata["published_date"] = published_date
            if row_dict.get("last_updated_raw") or row_dict.get("last_updated_normalized"):
                last_updated = {}
                if row_dict.get("last_updated_raw"):
                    last_updated["raw"] = row_dict["last_updated_raw"]
                if row_dict.get("last_updated_normalized"):
                    if isinstance(row_dict["last_updated_normalized"], datetime):
                        last_updated["normalized"] = row_dict["last_updated_normalized"].isoformat() + "Z"
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
                        version["source_path"] = str(scraped_data)
                        versions.append(version)
    
    return versions

    
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
    meta: dict = Field(
        default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"}
    )


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
    versions.sort(
        key=lambda v: v.get("scraped_at", ""),
        reverse=True
    )
    
    # Compare versions if we have multiple
    changes = []
    if len(versions) >= 2:
        old_version = versions[-1]  # Oldest
        new_version = versions[0]    # Newest
        
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
                changes.append(ProductChange(
                    field=f"stats.{field}",
                    old_value=old_val,
                    new_value=new_val,
                    change_type="changed" if old_val is not None and new_val is not None else ("added" if new_val is not None else "removed")
                ))
        
        # Compare price
        old_price = old_version.get("price")
        new_price = new_version.get("price")
        if old_price != new_price:
            changes.append(ProductChange(
                field="price",
                old_value=old_price,
                new_value=new_price,
                change_type="changed" if old_price is not None and new_price is not None else ("added" if new_price is not None else "removed")
            ))
        
        # Compare metadata
        old_metadata = old_version.get("metadata", {})
        new_metadata = new_version.get("metadata", {})
        
        # Compare version
        old_version_str = old_metadata.get("version")
        new_version_str = new_metadata.get("version")
        if old_version_str != new_version_str:
            changes.append(ProductChange(
                field="metadata.version",
                old_value=old_version_str,
                new_value=new_version_str,
                change_type="changed" if old_version_str and new_version_str else ("added" if new_version_str else "removed")
            ))
        
        # Compare last_updated
        old_last_updated = old_metadata.get("last_updated", {})
        new_last_updated = new_metadata.get("last_updated", {})
        if isinstance(old_last_updated, dict):
            old_last_updated = old_last_updated.get("normalized")
        if isinstance(new_last_updated, dict):
            new_last_updated = new_last_updated.get("normalized")
        if old_last_updated != new_last_updated:
            changes.append(ProductChange(
                field="metadata.last_updated",
                old_value=old_last_updated,
                new_value=new_last_updated,
                change_type="changed" if old_last_updated and new_last_updated else ("added" if new_last_updated else "removed")
            ))
    
    # Prepare versions for response (remove source_path, keep essential info)
    versions_for_response = []
    for v in versions:
        versions_for_response.append({
            "scraped_at": v.get("scraped_at"),
            "source_path": v.get("source_path"),
            "stats": v.get("stats", {}),
            "price": v.get("price"),
            "metadata": {
                "version": v.get("metadata", {}).get("version"),
                "last_updated": v.get("metadata", {}).get("last_updated"),
            }
        })
    
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
    meta: dict = Field(
        default_factory=lambda: {"timestamp": datetime.utcnow().isoformat() + "Z"}
    )


@router.get("/categories/comparison", response_model=CategoryComparisonResponse)
async def get_category_comparison(
    product_type: Optional[str] = Query(None, description="Product type: template, component, vector, plugin"),
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
                    "message": f"Invalid product type. Must be one of: template, component, vector, plugin",
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
        
        comparisons.append(CategoryComparison(
            category=cat,
            scrap_1_date=scrap1_date or "",
            scrap_2_date=scrap2_date or "",
            products_count_1=count_1,
            products_count_2=count_2,
            total_views_1=total_views_1,
            total_views_2=total_views_2,
            views_change=views_change,
            views_change_percent=round(views_change_percent, 2),
        ))
    
    # Sort by absolute change
    comparisons.sort(key=lambda x: abs(x.views_change), reverse=True)
    
    return CategoryComparisonResponse(
        data=comparisons,
        meta={
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_categories": len(comparisons),
        },
    )

