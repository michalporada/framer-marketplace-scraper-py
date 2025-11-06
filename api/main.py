"""FastAPI application for Framer Marketplace Scraper API."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Initialize FastAPI app
app = FastAPI(
    title="Framer Marketplace Scraper API",
    description="API for accessing scraped Framer Marketplace data",
    version="1.0.0",
)

# CORS Configuration
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,https://framer-marketplace-scraper-py.vercel.app"
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
    from api.dependencies import get_db_engine, execute_query_one
    
    db_status = "configured" if get_db_engine() else "not_configured"
    
    # Test simple query
    test_result = None
    if db_status == "configured":
        try:
            test_result = execute_query_one("SELECT 1 as test")
            test_result = "connected" if test_result else "query_failed"
        except Exception:
            test_result = "error"
    
    return {
        "status": "healthy",
        "database": db_status,
        "database_test": test_result
    }


# Import routes
from api.routes import creators, products

# Include routers
app.include_router(products.router)
app.include_router(creators.router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

