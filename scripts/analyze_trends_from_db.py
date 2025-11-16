#!/usr/bin/env python3
"""Analyze trends from product_history table in database."""

import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.dependencies import get_db_engine
from sqlalchemy import text

def analyze_trends():
    """Analyze trends from product_history table."""
    engine = get_db_engine()
    if not engine:
        print("❌ Database engine not available")
        return
    
    with engine.connect() as conn:
        # Get date range and basic stats
        result = conn.execute(text("""
            SELECT 
                MIN(scraped_at) as earliest,
                MAX(scraped_at) as latest,
                COUNT(DISTINCT DATE(scraped_at)) as unique_days,
                COUNT(*) as total_records,
                COUNT(DISTINCT product_id) as unique_products
            FROM product_history
        """))
        stats = result.fetchone()
        
        if not stats or not stats[0]:
            print("⚠️  No data in product_history table")
            return
        
        earliest = stats[0]
        latest = stats[1]
        unique_days = stats[2]
        total_records = stats[3]
        unique_products = stats[4]
        
        print("\n" + "=" * 80)
        print("TREND ANALYSIS FROM DATABASE")
        print("=" * 80)
        print(f"\n📊 Data Overview:")
        print(f"   Total records: {total_records:,}")
        print(f"   Unique products: {unique_products:,}")
        print(f"   Date range: {earliest.date()} to {latest.date()}")
        print(f"   Historical days: {unique_days} days")
        
        # Daily statistics
        print(f"\n📈 Daily Statistics:")
        result = conn.execute(text("""
            SELECT 
                DATE(scraped_at) as scrape_date,
                COUNT(*) as records_count,
                COUNT(DISTINCT product_id) as products_count
            FROM product_history
            GROUP BY DATE(scraped_at)
            ORDER BY scrape_date
        """))
        
        daily_stats = []
        for row in result:
            daily_stats.append({
                "date": row[0],
                "records": row[1],
                "products": row[2]
            })
        
        print(f"\n   Date          | Records  | Products")
        print(f"   " + "-" * 40)
        for stat in daily_stats:
            print(f"   {stat['date']} | {stat['records']:8,} | {stat['products']:8,}")
        
        # Product type distribution over time
        print(f"\n📦 Product Type Distribution (by day):")
        result = conn.execute(text("""
            SELECT 
                DATE(scraped_at) as scrape_date,
                type,
                COUNT(DISTINCT product_id) as products_count
            FROM product_history
            GROUP BY DATE(scraped_at), type
            ORDER BY scrape_date, type
        """))
        
        type_by_day = defaultdict(lambda: defaultdict(int))
        for row in result:
            type_by_day[str(row[0])][row[1]] = row[2]
        
        print(f"\n   Date          | Templates | Components | Vectors | Plugins")
        print(f"   " + "-" * 60)
        for date in sorted(type_by_day.keys()):
            types = type_by_day[date]
            print(f"   {date} | {types.get('template', 0):9,} | {types.get('component', 0):10,} | {types.get('vector', 0):7,} | {types.get('plugin', 0):7,}")
        
        # Views trends (if available)
        print(f"\n👁️  Views Trends (average views per day):")
        result = conn.execute(text("""
            SELECT 
                DATE(scraped_at) as scrape_date,
                AVG(views_normalized) as avg_views,
                COUNT(*) FILTER (WHERE views_normalized IS NOT NULL) as products_with_views
            FROM product_history
            WHERE views_normalized IS NOT NULL
            GROUP BY DATE(scraped_at)
            ORDER BY scrape_date
        """))
        
        views_trends = []
        for row in result:
            views_trends.append({
                "date": row[0],
                "avg_views": float(row[1]) if row[1] else 0,
                "products_with_views": row[2]
            })
        
        if views_trends:
            print(f"\n   Date          | Avg Views  | Products with Views")
            print(f"   " + "-" * 50)
            for trend in views_trends:
                print(f"   {trend['date']} | {trend['avg_views']:10,.0f} | {trend['products_with_views']:20,}")
            
            # Calculate growth
            if len(views_trends) >= 2:
                first_avg = views_trends[0]['avg_views']
                last_avg = views_trends[-1]['avg_views']
                if first_avg > 0:
                    growth = ((last_avg - first_avg) / first_avg) * 100
                    print(f"\n   📊 Growth: {growth:+.2f}% (from {first_avg:,.0f} to {last_avg:,.0f})")
        else:
            print("   ⚠️  No views data available")
        
        # Top growing products (if we have multiple scrapes)
        if unique_days >= 2:
            print(f"\n🚀 Top 10 Products with Highest Views Growth:")
            result = conn.execute(text("""
                WITH latest_views AS (
                    SELECT DISTINCT ON (product_id)
                        product_id,
                        name,
                        views_normalized as latest_views,
                        scraped_at
                    FROM product_history
                    WHERE views_normalized IS NOT NULL
                    ORDER BY product_id, scraped_at DESC
                ),
                earliest_views AS (
                    SELECT DISTINCT ON (product_id)
                        product_id,
                        views_normalized as earliest_views
                    FROM product_history
                    WHERE views_normalized IS NOT NULL
                    ORDER BY product_id, scraped_at ASC
                )
                SELECT 
                    l.product_id,
                    l.name,
                    COALESCE(e.earliest_views, 0) as start_views,
                    l.latest_views as end_views,
                    (l.latest_views - COALESCE(e.earliest_views, 0)) as views_change,
                    CASE 
                        WHEN COALESCE(e.earliest_views, 0) > 0 
                        THEN ((l.latest_views - COALESCE(e.earliest_views, 0))::float / e.earliest_views::float * 100)
                        ELSE NULL
                    END as growth_percent
                FROM latest_views l
                LEFT JOIN earliest_views e ON l.product_id = e.product_id
                WHERE l.latest_views > COALESCE(e.earliest_views, 0)
                ORDER BY views_change DESC
                LIMIT 10
            """))
            
            growing_products = []
            for row in result:
                growing_products.append({
                    "product_id": row[0],
                    "name": row[1],
                    "start_views": row[2],
                    "end_views": row[3],
                    "views_change": row[4],
                    "growth_percent": float(row[5]) if row[5] else None
                })
            
            if growing_products:
                print(f"\n   Product ID                    | Name                          | Start  | End    | Change  | Growth")
                print(f"   " + "-" * 100)
                for product in growing_products:
                    name = (product['name'][:28] + '...') if len(product['name']) > 31 else product['name']
                    growth_str = f"{product['growth_percent']:+.1f}%" if product['growth_percent'] else "N/A"
                    print(f"   {product['product_id']:30} | {name:30} | {product['start_views']:6,} | {product['end_views']:6,} | {product['views_change']:7,} | {growth_str}")
            else:
                print("   ⚠️  No products with view growth found")
        
        print("\n" + "=" * 80)
        print(f"\n✅ Summary:")
        print(f"   You have {unique_days} days of historical data")
        print(f"   This is {'sufficient' if unique_days >= 7 else 'good' if unique_days >= 3 else 'minimal'} for trend analysis")
        if unique_days >= 2:
            print(f"   ✅ You can already observe trends!")
        else:
            print(f"   ⚠️  Need at least 2 days for trend analysis")
        print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_trends()

