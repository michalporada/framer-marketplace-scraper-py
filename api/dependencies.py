"""Shared dependencies for API endpoints."""

import os
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

# Global database engine (singleton)
_db_engine: Optional[object] = None


def get_db_engine():
    """Get database engine (singleton pattern).

    Returns:
        SQLAlchemy engine or None if not configured
    """
    global _db_engine

    if _db_engine is not None:
        return _db_engine

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None

    try:
        _db_engine = create_engine(
            database_url,
            poolclass=NullPool,
            connect_args={"connect_timeout": 10},
        )
        return _db_engine
    except Exception:
        return None


def execute_query(query: str, params: Optional[dict] = None):
    """Execute a SQL query and return results.

    Args:
        query: SQL query string
        params: Optional query parameters

    Returns:
        List of rows (as dicts), empty list if no results, or None on error
    """
    engine = get_db_engine()
    if not engine:
        return None

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            rows = result.fetchall()
            # Convert rows to dicts
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
    except SQLAlchemyError as e:
        # Log error for debugging (but don't expose sensitive info)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database query error: {str(e)}")
        return None
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected database error: {str(e)}")
        return None


def execute_query_one(query: str, params: Optional[dict] = None):
    """Execute a SQL query and return single result.

    Args:
        query: SQL query string
        params: Optional query parameters

    Returns:
        Single row (as dict) or None if not found/error
    """
    engine = get_db_engine()
    if not engine:
        return None

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            row = result.fetchone()
            if not row:
                return None
            # Convert row to dict
            columns = result.keys()
            return dict(zip(columns, row))
    except SQLAlchemyError as e:
        # Log error for debugging (but don't expose sensitive info)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database query error: {str(e)}")
        return None
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected database error: {str(e)}")
        return None

