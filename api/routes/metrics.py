"""API routes for metrics and monitoring."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.config.settings import settings
from src.utils.metrics import get_metrics

# Try to import cache stats (may not be available in all branches)
try:
    from api.cache import get_cache_stats
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    def get_cache_stats():
        return None

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


class MetricsSummaryResponse(BaseModel):
    """Response model for metrics summary."""
    
    duration_seconds: float
    duration_formatted: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    products: Dict
    creators: Dict
    categories: Dict
    requests: Dict
    retries: Dict
    errors: Dict
    cache_stats: Optional[Dict] = None


class MetricsHistoryResponse(BaseModel):
    """Response model for metrics history."""
    
    metrics: List[Dict]
    total: int
    limit: int
    offset: int


@router.get("/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary():
    """Get current metrics summary.
    
    Returns:
        MetricsSummaryResponse with current metrics
    """
    metrics = get_metrics()
    summary = metrics.get_summary()
    
    # Add cache stats if available
    try:
        cache_stats = get_cache_stats()
        summary["cache_stats"] = cache_stats
    except Exception:
        summary["cache_stats"] = None
    
    return MetricsSummaryResponse(**summary)


@router.get("/history", response_model=MetricsHistoryResponse)
async def get_metrics_history(
    limit: int = Query(50, ge=1, le=1000, description="Number of metrics entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
):
    """Get metrics history from metrics.log file.
    
    Args:
        limit: Number of entries to return (1-1000)
        offset: Number of entries to skip
        
    Returns:
        MetricsHistoryResponse with metrics history
    """
    try:
        metrics_file = Path(settings.data_dir) / "metrics.log"
        
        if not metrics_file.exists():
            return MetricsHistoryResponse(
                metrics=[],
                total=0,
                limit=limit,
                offset=offset,
            )
        
        # Read all metrics entries
        metrics_entries = []
        with open(metrics_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    import json
                    entry = json.loads(line)
                    metrics_entries.append(entry)
                except json.JSONDecodeError:
                    continue
        
        # Reverse to get most recent first
        metrics_entries.reverse()
        
        # Apply pagination
        total = len(metrics_entries)
        paginated_entries = metrics_entries[offset:offset + limit]
        
        return MetricsHistoryResponse(
            metrics=paginated_entries,
            total=total,
            limit=limit,
            offset=offset,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to read metrics history: {str(e)}",
                    "details": {},
                }
            },
        )


@router.get("/stats")
async def get_stats():
    """Get combined stats (metrics + cache + database).
    
    Returns:
        Dictionary with combined stats
    """
    metrics = get_metrics()
    summary = metrics.get_summary()
    
    # Get cache stats
    cache_stats = None
    try:
        cache_stats = get_cache_stats()
    except Exception:
        pass
    
    # Get database stats
    db_stats = None
    try:
        from api.dependencies import get_db_engine, execute_query_one
        
        engine = get_db_engine()
        if engine:
            from sqlalchemy import text
            
            with engine.connect() as conn:
                # Get product count
                result = conn.execute(text("SELECT COUNT(*) as count FROM products"))
                product_count = result.fetchone()[0] if result else 0
                
                # Get creator count
                result = conn.execute(text("SELECT COUNT(*) as count FROM creators"))
                creator_count = result.fetchone()[0] if result else 0
                
                # Get product history count
                result = conn.execute(text("SELECT COUNT(*) as count FROM product_history"))
                history_count = result.fetchone()[0] if result else 0
                
                db_stats = {
                    "products": product_count,
                    "creators": creator_count,
                    "product_history": history_count,
                }
    except Exception:
        pass
    
    return {
        "metrics": summary,
        "cache": cache_stats,
        "database": db_stats,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

