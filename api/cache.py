"""Cache utilities for API endpoints."""

import hashlib
import json
from functools import wraps
from typing import Any, Callable, Optional
from cachetools import TTLCache
from datetime import datetime

# Cache instances
_product_cache: Optional[TTLCache] = None
_creator_cache: Optional[TTLCache] = None

# Default TTL: 5 minutes (300 seconds)
DEFAULT_TTL = 300


def get_product_cache() -> TTLCache:
    """Get or create product cache instance.
    
    Returns:
        TTLCache instance for products
    """
    global _product_cache
    if _product_cache is None:
        # Max 1000 items, TTL 5 minutes
        _product_cache = TTLCache(maxsize=1000, ttl=DEFAULT_TTL)
    return _product_cache


def get_creator_cache() -> TTLCache:
    """Get or create creator cache instance.
    
    Returns:
        TTLCache instance for creators
    """
    global _creator_cache
    if _creator_cache is None:
        # Max 500 items, TTL 5 minutes
        _creator_cache = TTLCache(maxsize=500, ttl=DEFAULT_TTL)
    return _creator_cache


def generate_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Sort kwargs for consistent keys
    sorted_kwargs = sorted(kwargs.items())
    key_data = {
        "args": args,
        "kwargs": sorted_kwargs,
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(ttl: int = DEFAULT_TTL, cache_type: str = "product"):
    """Decorator for caching API endpoint responses.
    
    Args:
        ttl: Time to live in seconds (default: 300 = 5 minutes)
        cache_type: Type of cache ("product" or "creator")
        
    Returns:
        Decorated function with caching
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get appropriate cache
            if cache_type == "product":
                cache = get_product_cache()
            elif cache_type == "creator":
                cache = get_creator_cache()
            else:
                cache = get_product_cache()
            
            # Generate cache key
            cache_key = generate_cache_key(func.__name__, *args, **kwargs)
            
            # Check cache
            if cache_key in cache:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Cache hit for {func.__name__}: {cache_key[:8]}")
                return cache[cache_key]
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache (only if result is valid)
            if result is not None:
                cache[cache_key] = result
                
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Cache miss for {func.__name__}: {cache_key[:8]}")
            
            return result
        
        return wrapper
    return decorator


def invalidate_product_cache():
    """Invalidate all product cache entries."""
    cache = get_product_cache()
    cache.clear()
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Product cache invalidated")


def invalidate_creator_cache():
    """Invalidate all creator cache entries."""
    cache = get_creator_cache()
    cache.clear()
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Creator cache invalidated")


def invalidate_all_cache():
    """Invalidate all cache entries."""
    invalidate_product_cache()
    invalidate_creator_cache()
    import logging
    logger = logging.getLogger(__name__)
    logger.info("All cache invalidated")


def get_cache_stats() -> dict:
    """Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    product_cache = get_product_cache()
    creator_cache = get_creator_cache()
    
    return {
        "product_cache": {
            "size": len(product_cache),
            "maxsize": product_cache.maxsize,
            "ttl": product_cache.ttl,
        },
        "creator_cache": {
            "size": len(creator_cache),
            "maxsize": creator_cache.maxsize,
            "ttl": creator_cache.ttl,
        },
    }

