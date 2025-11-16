#!/usr/bin/env python3
"""Check if database has historical data in product_history table."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import DatabaseStorage
from api.dependencies import get_db_engine
from sqlalchemy import text

def check_history():
    """Check product_history table for historical data."""
    db_storage = DatabaseStorage()
    
    if not db_storage.is_available():
        print("❌ Database not available")
        return
    
    engine = get_db_engine()
    if not engine:
        print("❌ Database engine not available")
        return
    
    with engine.connect() as conn:
        # Check total records
        result = conn.execute(text("SELECT COUNT(*) FROM product_history"))
        total_count = result.fetchone()[0]
        
        # Check unique products
        result = conn.execute(text("SELECT COUNT(DISTINCT product_id) FROM product_history"))
        unique_products = result.fetchone()[0]
        
        # Check date range
        result = conn.execute(text("""
            SELECT 
                MIN(scraped_at) as earliest,
                MAX(scraped_at) as latest,
                COUNT(DISTINCT DATE(scraped_at)) as unique_days
            FROM product_history
        """))
        date_info = result.fetchone()
        
        print("\n" + "=" * 80)
        print("DATABASE HISTORY ANALYSIS")
        print("=" * 80)
        print(f"\nTotal records in product_history: {total_count}")
        print(f"Unique products: {unique_products}")
        
        if date_info and date_info[0]:
            earliest = date_info[0]
            latest = date_info[1]
            unique_days = date_info[2]
            
            print(f"\nDate range:")
            print(f"  Earliest: {earliest}")
            print(f"  Latest: {latest}")
            print(f"  Unique days: {unique_days} days")
            
            if unique_days > 1:
                print(f"\n✅ You have {unique_days} days of historical data!")
                print("   You can analyze trends!")
            else:
                print(f"\n⚠️  Only 1 day of data - need at least 2 days for trend analysis")
        else:
            print("\n⚠️  No data in product_history table")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    check_history()

