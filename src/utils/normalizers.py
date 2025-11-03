"""Normalization utilities for dates and statistics (Option B - raw + normalized)."""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


def parse_relative_date(date_str: str) -> Dict[str, Optional[str]]:
    """Convert relative date format to normalized ISO 8601 format.

    Returns dictionary with raw and normalized formats (Option B).

    Args:
        date_str: Relative date string (e.g., "5 months ago", "3mo ago", "3w ago")

    Returns:
        Dictionary with:
        - raw: Original string
        - normalized: ISO 8601 format or None if parsing fails

    Examples:
        - "5 months ago" → {"raw": "5 months ago", "normalized": "2024-10-15T00:00:00Z"}
        - "3mo ago" → {"raw": "3mo ago", "normalized": "2024-12-15T00:00:00Z"}
        - "3w ago" → {"raw": "3w ago", "normalized": "2025-02-22T00:00:00Z"}
    """
    now = datetime.utcnow()
    raw = date_str.strip()

    try:
        # Pattern matching for different formats
        if "months ago" in raw or "month ago" in raw:
            match = re.search(r"(\d+)\s*months?", raw, re.IGNORECASE)
            if match:
                months = int(match.group(1))
                normalized_date = now - timedelta(days=months * 30)
                normalized = normalized_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                return {"raw": raw, "normalized": normalized}

        elif "mo ago" in raw or "mo" in raw:
            match = re.search(r"(\d+)mo", raw, re.IGNORECASE)
            if match:
                months = int(match.group(1))
                normalized_date = now - timedelta(days=months * 30)
                normalized = normalized_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                return {"raw": raw, "normalized": normalized}

        elif "weeks ago" in raw or "week ago" in raw or "w ago" in raw:
            match = re.search(r"(\d+)\s*w", raw, re.IGNORECASE)
            if match:
                weeks = int(match.group(1))
                normalized_date = now - timedelta(weeks=weeks)
                normalized = normalized_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                return {"raw": raw, "normalized": normalized}

        elif "days ago" in raw or "day ago" in raw:
            match = re.search(r"(\d+)\s*days?", raw, re.IGNORECASE)
            if match:
                days = int(match.group(1))
                normalized_date = now - timedelta(days=days)
                normalized = normalized_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                return {"raw": raw, "normalized": normalized}

        elif "hours ago" in raw or "hour ago" in raw:
            match = re.search(r"(\d+)\s*hours?", raw, re.IGNORECASE)
            if match:
                hours = int(match.group(1))
                normalized_date = now - timedelta(hours=hours)
                normalized = normalized_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                return {"raw": raw, "normalized": normalized}

        # If parsing fails, return raw with None normalized
        logger.warning("date_parse_failed", raw=raw)
        return {"raw": raw, "normalized": None}

    except Exception as e:
        logger.error("date_parse_error", raw=raw, error=str(e))
        return {"raw": raw, "normalized": None}


def parse_statistic(stat_str: str) -> Dict[str, Optional[int]]:
    """Convert abbreviated statistic formats to integers.

    Returns dictionary with raw and normalized formats (Option B).

    Args:
        stat_str: Statistic string (e.g., "19.8K Views", "1,200 Vectors", "181 Users")

    Returns:
        Dictionary with:
        - raw: Original string
        - normalized: Integer value or None if parsing fails

    Examples:
        - "19.8K Views" → {"raw": "19.8K Views", "normalized": 19800}
        - "10.4K Users" → {"raw": "10.4K Users", "normalized": 10400}
        - "1,200 Vectors" → {"raw": "1,200 Vectors", "normalized": 1200}
        - "181 Users" → {"raw": "181 Users", "normalized": 181}
    """
    raw = stat_str.strip()

    try:
        # Extract number from text
        number_match = re.search(r"([\d,.]+)", raw)
        if not number_match:
            logger.warning("statistic_parse_failed", raw=raw)
            return {"raw": raw, "normalized": None}

        number_str = number_match.group(1)

        # Remove commas and convert to float
        number_str_clean = number_str.replace(",", "")

        # Check for K (thousands) or M (millions)
        multiplier = 1
        if "K" in raw.upper() or "k" in raw:
            multiplier = 1000
        elif "M" in raw.upper():
            multiplier = 1000000

        number_value = float(number_str_clean)
        normalized = int(number_value * multiplier)

        return {"raw": raw, "normalized": normalized}

    except Exception as e:
        logger.error("statistic_parse_error", raw=raw, error=str(e))
        return {"raw": raw, "normalized": None}


def extract_statistic_label(stat_str: str) -> Optional[str]:
    """Extract label from statistic string (e.g., "Views", "Users", "Installs").

    Args:
        stat_str: Statistic string (e.g., "19.8K Views", "7.4K Installs")

    Returns:
        Label string or None
    """
    # Common labels
    labels = ["Views", "Users", "Installs", "Vectors", "Pages", "Remixes", "Previews"]
    for label in labels:
        if label in stat_str:
            return label
    return None
