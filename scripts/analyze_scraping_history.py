#!/usr/bin/env python3
"""Analyze scraping history to determine how many days of data we have and identify trends."""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from src.models.product import Product
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_product_files(data_dir: Path) -> List[Dict]:
    """Load all product JSON files and return list of product data."""
    products = []
    products_dir = data_dir / "products"
    
    if not products_dir.exists():
        logger.warning(f"Products directory not found: {products_dir}")
        return products
    
    # Iterate through all product types
    for product_type in ["templates", "components", "vectors", "plugins"]:
        type_dir = products_dir / product_type
        if not type_dir.exists():
            continue
        
        logger.info(f"Loading {product_type}...")
        json_files = list(type_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} {product_type} files")
        
        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    products.append(data)
            except Exception as e:
                logger.warning(f"Error loading {json_file}: {e}")
                continue
    
    return products


def analyze_scraping_dates(products: List[Dict]) -> Dict:
    """Analyze scraping dates to determine historical data coverage."""
    scraped_dates = []
    dates_by_type = defaultdict(list)
    
    for product in products:
        scraped_at = product.get("scraped_at")
        if not scraped_at:
            continue
        
        try:
            # Parse scraped_at (can be string or datetime)
            if isinstance(scraped_at, str):
                # Try different formats
                for fmt in [
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                ]:
                    try:
                        dt = datetime.strptime(scraped_at, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    logger.warning(f"Could not parse date: {scraped_at}")
                    continue
            else:
                dt = scraped_at
            
            scraped_dates.append(dt)
            product_type = product.get("type", "unknown")
            dates_by_type[product_type].append(dt)
        except Exception as e:
            logger.warning(f"Error parsing date {scraped_at}: {e}")
            continue
    
    if not scraped_dates:
        return {
            "total_days": 0,
            "earliest_date": None,
            "latest_date": None,
            "date_range": None,
            "dates_by_type": {},
        }
    
    earliest_date = min(scraped_dates)
    latest_date = max(scraped_dates)
    date_range = (latest_date - earliest_date).days + 1
    
    # Group by date (day)
    dates_by_day = defaultdict(int)
    for dt in scraped_dates:
        day_key = dt.date()
        dates_by_day[day_key] += 1
    
    # Analyze by type
    type_analysis = {}
    for product_type, dates in dates_by_type.items():
        if dates:
            type_earliest = min(dates)
            type_latest = max(dates)
            type_range = (type_latest - type_earliest).days + 1
            type_analysis[product_type] = {
                "earliest": type_earliest.isoformat(),
                "latest": type_latest.isoformat(),
                "days": type_range,
                "count": len(dates),
            }
    
    return {
        "total_days": date_range,
        "earliest_date": earliest_date.isoformat(),
        "latest_date": latest_date.isoformat(),
        "date_range": f"{earliest_date.date()} to {latest_date.date()}",
        "unique_days": len(dates_by_day),
        "dates_by_day": {str(k): v for k, v in sorted(dates_by_day.items())},
        "dates_by_type": type_analysis,
        "total_products": len(products),
    }


def analyze_trends(products: List[Dict]) -> Dict:
    """Analyze trends in product data over time."""
    # Group products by scrape date
    products_by_date = defaultdict(list)
    
    for product in products:
        scraped_at = product.get("scraped_at")
        if not scraped_at:
            continue
        
        try:
            if isinstance(scraped_at, str):
                for fmt in [
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                ]:
                    try:
                        dt = datetime.strptime(scraped_at, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    continue
            else:
                dt = scraped_at
            
            day_key = dt.date()
            products_by_date[day_key].append(product)
        except Exception:
            continue
    
    if not products_by_date:
        return {
            "trends_available": False,
            "message": "No date information available for trend analysis",
        }
    
    # Analyze trends by day
    daily_stats = []
    for date in sorted(products_by_date.keys()):
        day_products = products_by_date[date]
        
        # Calculate statistics
        total_products = len(day_products)
        free_count = sum(1 for p in day_products if p.get("is_free", False))
        paid_count = total_products - free_count
        
        # Calculate average views (if available)
        views_list = []
        for p in day_products:
            stats = p.get("stats", {})
            views = stats.get("views")
            if views and isinstance(views, dict):
                normalized = views.get("normalized")
                if normalized is not None:
                    views_list.append(normalized)
        
        avg_views = sum(views_list) / len(views_list) if views_list else None
        
        daily_stats.append({
            "date": str(date),
            "total_products": total_products,
            "free_count": free_count,
            "paid_count": paid_count,
            "avg_views": round(avg_views, 2) if avg_views else None,
        })
    
    # Determine if we have enough data for trends
    unique_days = len(products_by_date)
    has_trends = unique_days >= 2  # Need at least 2 days to see trends
    
    return {
        "trends_available": has_trends,
        "unique_days": unique_days,
        "daily_stats": daily_stats,
        "message": f"Trends available: {unique_days} days of data" if has_trends else "Need at least 2 days of data for trend analysis",
    }


def main():
    """Main function to analyze scraping history."""
    # Get data directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return
    
    logger.info("Loading product files...")
    products = load_product_files(data_dir)
    logger.info(f"Loaded {len(products)} products")
    
    if not products:
        logger.warning("No products found!")
        return
    
    # Analyze scraping dates
    logger.info("Analyzing scraping dates...")
    date_analysis = analyze_scraping_dates(products)
    
    print("\n" + "=" * 80)
    print("SCRAPING HISTORY ANALYSIS")
    print("=" * 80)
    print(f"\nTotal products analyzed: {date_analysis['total_products']}")
    print(f"Date range: {date_analysis['date_range']}")
    print(f"Earliest scrape: {date_analysis['earliest_date']}")
    print(f"Latest scrape: {date_analysis['latest_date']}")
    print(f"Total days covered: {date_analysis['total_days']} days")
    print(f"Unique scraping days: {date_analysis['unique_days']} days")
    
    print("\n" + "-" * 80)
    print("BY PRODUCT TYPE:")
    print("-" * 80)
    for product_type, stats in date_analysis["dates_by_type"].items():
        print(f"\n{product_type.upper()}:")
        print(f"  Count: {stats['count']}")
        print(f"  Days: {stats['days']}")
        print(f"  Range: {stats['earliest']} to {stats['latest']}")
    
    # Analyze trends
    logger.info("Analyzing trends...")
    trends = analyze_trends(products)
    
    print("\n" + "-" * 80)
    print("TREND ANALYSIS:")
    print("-" * 80)
    print(f"\n{trends['message']}")
    
    if trends["trends_available"]:
        print(f"\nDaily statistics (last 10 days):")
        for stat in trends["daily_stats"][-10:]:
            print(f"  {stat['date']}: {stat['total_products']} products "
                  f"(Free: {stat['free_count']}, Paid: {stat['paid_count']})"
                  f"{', Avg Views: ' + str(stat['avg_views']) if stat['avg_views'] else ''}")
        
        if len(trends["daily_stats"]) > 10:
            print(f"\n... and {len(trends['daily_stats']) - 10} more days")
    
    print("\n" + "=" * 80)
    
    # Save results to file
    results = {
        "date_analysis": date_analysis,
        "trends": trends,
        "generated_at": datetime.utcnow().isoformat(),
    }
    
    output_file = data_dir / "scraping_history_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Analysis saved to: {output_file}")


if __name__ == "__main__":
    main()

