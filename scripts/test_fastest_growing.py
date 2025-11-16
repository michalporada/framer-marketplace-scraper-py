#!/usr/bin/env python3
"""Test the fastest-growing products endpoint directly."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.routes.products import get_fastest_growing_products
from datetime import datetime

async def test_endpoint():
    """Test the fastest-growing endpoint."""
    print("\n" + "=" * 80)
    print("TESTING /api/products/fastest-growing ENDPOINT")
    print("=" * 80)
    
    # Test 1: All products, sorted by percent
    print("\n📊 Test 1: All products, sorted by percent growth (24h)")
    print("-" * 80)
    try:
        result = await get_fastest_growing_products(
            product_type=None,
            limit=10,
            period_hours=24,
            sort_by="percent"
        )
        print(f"✅ Success! Found {len(result.data)} products")
        print(f"\nTop 5 fastest growing products:")
        for i, product in enumerate(result.data[:5], 1):
            print(f"\n{i}. {product.name} ({product.type})")
            print(f"   Creator: @{product.creator_username}" + (f" ({product.creator_name})" if product.creator_name else ""))
            print(f"   Growth: +{product.views_change_percent:.2f}% ({product.views_change:,} views)")
            print(f"   Current views: {product.views:,}")
            print(f"   Previous views: {product.views - product.views_change:,}")
            if product.category:
                print(f"   Category: {product.category}")
            print(f"   Price: {'Free' if product.is_free else f'${product.price:.2f}' if product.price else 'N/A'}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Templates only
    print("\n\n📊 Test 2: Templates only, sorted by percent growth (24h)")
    print("-" * 80)
    try:
        result = await get_fastest_growing_products(
            product_type="template",
            limit=5,
            period_hours=24,
            sort_by="percent"
        )
        print(f"✅ Success! Found {len(result.data)} templates")
        print(f"\nTop 5 fastest growing templates:")
        for i, product in enumerate(result.data[:5], 1):
            print(f"\n{i}. {product.name}")
            print(f"   Growth: +{product.views_change_percent:.2f}% ({product.views_change:,} views)")
            print(f"   Current views: {product.views:,}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
    
    # Test 3: Sorted by absolute change
    print("\n\n📊 Test 3: All products, sorted by absolute change (24h)")
    print("-" * 80)
    try:
        result = await get_fastest_growing_products(
            product_type=None,
            limit=5,
            period_hours=24,
            sort_by="absolute"
        )
        print(f"✅ Success! Found {len(result.data)} products")
        print(f"\nTop 5 products by absolute views change:")
        for i, product in enumerate(result.data[:5], 1):
            print(f"\n{i}. {product.name} ({product.type})")
            print(f"   Absolute change: +{product.views_change:,} views")
            print(f"   Growth: +{product.views_change_percent:.2f}%")
            print(f"   Current views: {product.views:,}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
    
    # Test 4: 7 days period
    print("\n\n📊 Test 4: All products, 7 days period, sorted by percent")
    print("-" * 80)
    try:
        result = await get_fastest_growing_products(
            product_type=None,
            limit=5,
            period_hours=168,  # 7 days
            sort_by="percent"
        )
        print(f"✅ Success! Found {len(result.data)} products")
        print(f"\nTop 5 fastest growing products (7 days):")
        for i, product in enumerate(result.data[:5], 1):
            print(f"\n{i}. {product.name} ({product.type})")
            print(f"   Growth: +{product.views_change_percent:.2f}% ({product.views_change:,} views)")
            print(f"   Current views: {product.views:,}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
    
    # Test 5: Components only
    print("\n\n📊 Test 5: Components only, sorted by percent growth (24h)")
    print("-" * 80)
    try:
        result = await get_fastest_growing_products(
            product_type="component",
            limit=5,
            period_hours=24,
            sort_by="percent"
        )
        print(f"✅ Success! Found {len(result.data)} components")
        if result.data:
            print(f"\nTop fastest growing components:")
            for i, product in enumerate(result.data[:5], 1):
                print(f"\n{i}. {product.name}")
                print(f"   Growth: +{product.views_change_percent:.2f}% ({product.views_change:,} views)")
                print(f"   Current views: {product.views:,}")
        else:
            print("⚠️  No components with growth found")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✅ Testing complete!")
    print("=" * 80)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_endpoint())

