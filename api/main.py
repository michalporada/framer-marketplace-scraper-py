"""FastAPI application for Framer Marketplace Scraper API."""

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from api.cache import (
    get_cache_stats,
    invalidate_all_cache,
    invalidate_creator_cache,
    invalidate_product_cache,
)
from api.routes import creators, metrics, products

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Framer Marketplace Scraper API",
    description="API for accessing scraped Framer Marketplace data",
    version="1.0.0",
)

# CORS Configuration
cors_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,https://framer-marketplace-scraper-py.vercel.app"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Framer Marketplace Scraper API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    from api.dependencies import get_db_engine

    db_status = "configured" if get_db_engine() else "not_configured"

    # Test simple query
    test_result = None
    test_error = None
    if db_status == "configured":
        try:
            from api.dependencies import get_db_engine
            from sqlalchemy import text

            engine = get_db_engine()
            if engine:
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1 as test"))
                    row = result.fetchone()
                    if row:
                        # Try to access the result
                        test_value = row[0] if row else None
                        test_result = (
                            f"connected (value: {test_value})" if test_value else "no_value"
                        )
                    else:
                        test_result = "no_result"
            else:
                test_result = "no_engine"
        except Exception as e:
            test_result = "error"
            test_error = f"{type(e).__name__}: {str(e)[:200]}"  # More details

    response = {"status": "healthy", "database": db_status, "database_test": test_result}
    if test_error:
        response["test_error"] = test_error
    return response


# Include routers
app.include_router(products.router)
app.include_router(creators.router)
app.include_router(metrics.router)


@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics.

    Returns:
        Dictionary with cache statistics
    """
    return get_cache_stats()


@app.post("/cache/invalidate")
async def cache_invalidate(
    cache_type: Optional[str] = Query(
        None, description="Cache type: product, creator, or None for all"
    ),
):
    """Invalidate cache.

    Args:
        cache_type: Type of cache to invalidate ("product", "creator", or None for all)

    Returns:
        Success message
    """
    if cache_type == "product":
        invalidate_product_cache()
        return {"message": "Product cache invalidated", "cache_type": "product"}
    elif cache_type == "creator":
        invalidate_creator_cache()
        return {"message": "Creator cache invalidated", "cache_type": "creator"}
    else:
        invalidate_all_cache()
        return {"message": "All cache invalidated"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
