"""Script to fix creator names in database by removing 'Creator' suffix.

This script:
1. Removes 'Creator' suffix from creator names in 'creators' table
2. Removes 'Creator' suffix from creator names in 'products' table
3. Checks for invalid/inadequate rows in database
"""

import re
import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.database import DatabaseStorage
from src.utils.logger import get_logger

logger = get_logger(__name__)


def remove_creator_suffix(name: str) -> str:
    """Remove 'Creator' suffix from name (case-insensitive, with or without space).

    Args:
        name: Creator name

    Returns:
        Name without 'Creator' suffix
    """
    if not name:
        return name
    # Remove 'Creator' at the end (with optional whitespace before it)
    return re.sub(r"Creator\s*$", "", name, flags=re.IGNORECASE).strip()


def fix_creators_table(db_storage: DatabaseStorage) -> dict:
    """Fix creator names in 'creators' table.

    Args:
        db_storage: DatabaseStorage instance

    Returns:
        Dictionary with statistics
    """
    if not db_storage.is_available():
        logger.error("database_not_available")
        return {"fixed": 0, "total": 0, "errors": 0}

    stats = {"fixed": 0, "total": 0, "errors": 0}

    try:
        # Get all creators with names ending in 'Creator'
        query = text("""
            SELECT username, name 
            FROM creators 
            WHERE name IS NOT NULL 
            AND (name ILIKE '%Creator' OR name ILIKE '%Creator ')
        """)

        with db_storage.engine.begin() as conn:
            result = conn.execute(query)
            rows = result.fetchall()

            stats["total"] = len(rows)
            logger.info("found_creators_to_fix", count=stats["total"])

            for row in rows:
                username = row[0]
                old_name = row[1]
                new_name = remove_creator_suffix(old_name)

                if new_name != old_name:
                    try:
                        update_query = text("""
                            UPDATE creators 
                            SET name = :new_name, updated_at = CURRENT_TIMESTAMP
                            WHERE username = :username
                        """)
                        conn.execute(update_query, {"new_name": new_name, "username": username})

                        stats["fixed"] += 1
                        logger.info(
                            "creator_name_fixed",
                            username=username,
                            old_name=old_name,
                            new_name=new_name,
                        )
                    except Exception as e:
                        stats["errors"] += 1
                        logger.error(
                            "creator_name_fix_error",
                            username=username,
                            error=str(e),
                            error_type=type(e).__name__,
                        )

    except Exception as e:
        logger.error(
            "creators_table_fix_error",
            error=str(e),
            error_type=type(e).__name__,
        )
        stats["errors"] += 1

    return stats


def fix_products_table(db_storage: DatabaseStorage) -> dict:
    """Fix creator names in 'products' table.

    Args:
        db_storage: DatabaseStorage instance

    Returns:
        Dictionary with statistics
    """
    if not db_storage.is_available():
        logger.error("database_not_available")
        return {"fixed": 0, "total": 0, "errors": 0}

    stats = {"fixed": 0, "total": 0, "errors": 0}

    try:
        # Get all products with creator_name ending in 'Creator'
        query = text("""
            SELECT id, creator_name 
            FROM products 
            WHERE creator_name IS NOT NULL 
            AND (creator_name ILIKE '%Creator' OR creator_name ILIKE '%Creator ')
        """)

        with db_storage.engine.begin() as conn:
            result = conn.execute(query)
            rows = result.fetchall()

            stats["total"] = len(rows)
            logger.info("found_products_to_fix", count=stats["total"])

            for row in rows:
                product_id = row[0]
                old_name = row[1]
                new_name = remove_creator_suffix(old_name)

                if new_name != old_name:
                    try:
                        update_query = text("""
                            UPDATE products 
                            SET creator_name = :new_name, updated_at = CURRENT_TIMESTAMP
                            WHERE id = :product_id
                        """)
                        conn.execute(update_query, {"new_name": new_name, "product_id": product_id})

                        stats["fixed"] += 1
                        logger.info(
                            "product_creator_name_fixed",
                            product_id=product_id,
                            old_name=old_name,
                            new_name=new_name,
                        )
                    except Exception as e:
                        stats["errors"] += 1
                        logger.error(
                            "product_creator_name_fix_error",
                            product_id=product_id,
                            error=str(e),
                            error_type=type(e).__name__,
                        )

    except Exception as e:
        logger.error(
            "products_table_fix_error",
            error=str(e),
            error_type=type(e).__name__,
        )
        stats["errors"] += 1

    return stats


def check_invalid_rows(db_storage: DatabaseStorage) -> dict:
    """Check for invalid/inadequate rows in database.

    Args:
        db_storage: DatabaseStorage instance

    Returns:
        Dictionary with statistics about invalid rows
    """
    if not db_storage.is_available():
        logger.error("database_not_available")
        return {}

    issues = {}

    try:
        with db_storage.engine.connect() as conn:
            # Check products without creator_username (orphaned products)
            query = text("""
                SELECT COUNT(*) as count 
                FROM products 
                WHERE creator_username IS NULL OR creator_username = ''
            """)
            result = conn.execute(query)
            row = result.fetchone()
            issues["products_without_creator"] = row[0] if row else 0

            # Check products with creator_username that doesn't exist in creators table
            query = text("""
                SELECT COUNT(DISTINCT p.creator_username) as count
                FROM products p
                LEFT JOIN creators c ON p.creator_username = c.username
                WHERE p.creator_username IS NOT NULL 
                AND c.username IS NULL
            """)
            result = conn.execute(query)
            row = result.fetchone()
            issues["products_with_missing_creator"] = row[0] if row else 0

            # Check creators without any products
            query = text("""
                SELECT COUNT(*) as count
                FROM creators c
                LEFT JOIN products p ON c.username = p.creator_username
                WHERE p.id IS NULL
            """)
            result = conn.execute(query)
            row = result.fetchone()
            issues["creators_without_products"] = row[0] if row else 0

            # Check products with empty/null names
            query = text("""
                SELECT COUNT(*) as count 
                FROM products 
                WHERE name IS NULL OR name = ''
            """)
            result = conn.execute(query)
            row = result.fetchone()
            issues["products_without_name"] = row[0] if row else 0

            # Check products with empty/null URLs
            query = text("""
                SELECT COUNT(*) as count 
                FROM products 
                WHERE url IS NULL OR url = ''
            """)
            result = conn.execute(query)
            row = result.fetchone()
            issues["products_without_url"] = row[0] if row else 0

            # Check creators with empty/null usernames
            query = text("""
                SELECT COUNT(*) as count 
                FROM creators 
                WHERE username IS NULL OR username = ''
            """)
            result = conn.execute(query)
            row = result.fetchone()
            issues["creators_without_username"] = row[0] if row else 0

            # Check products with invalid product_type
            query = text("""
                SELECT COUNT(*) as count 
                FROM products 
                WHERE type NOT IN ('template', 'component', 'vector', 'plugin')
            """)
            result = conn.execute(query)
            row = result.fetchone()
            issues["products_with_invalid_type"] = row[0] if row else 0

    except Exception as e:
        logger.error(
            "invalid_rows_check_error",
            error=str(e),
            error_type=type(e).__name__,
        )
        issues["check_error"] = str(e)

    return issues


def main():
    """Main function."""
    logger.info("starting_creator_name_fix")

    db_storage = DatabaseStorage()

    if not db_storage.is_available():
        logger.error("database_not_configured")
        print("❌ Database not configured. Please set DATABASE_URL in .env file.")
        return

    print("🔍 Checking for creator names with 'Creator' suffix...")
    print()

    # Fix creators table
    print("📝 Fixing 'creators' table...")
    creators_stats = fix_creators_table(db_storage)
    print(f"   Found: {creators_stats['total']} creators with 'Creator' suffix")
    print(f"   Fixed: {creators_stats['fixed']} creators")
    if creators_stats["errors"] > 0:
        print(f"   Errors: {creators_stats['errors']}")
    print()

    # Fix products table
    print("📝 Fixing 'products' table...")
    products_stats = fix_products_table(db_storage)
    print(f"   Found: {products_stats['total']} products with 'Creator' suffix")
    print(f"   Fixed: {products_stats['fixed']} products")
    if products_stats["errors"] > 0:
        print(f"   Errors: {products_stats['errors']}")
    print()

    # Check for invalid rows
    print("🔍 Checking for invalid/inadequate rows...")
    issues = check_invalid_rows(db_storage)
    if issues:
        print("   Issues found:")
        for issue_name, count in issues.items():
            if isinstance(count, int) and count > 0:
                print(f"   - {issue_name}: {count}")
        if "check_error" in issues:
            print(f"   - Error during check: {issues['check_error']}")
    else:
        print("   ✅ No issues found")
    print()

    total_fixed = creators_stats["fixed"] + products_stats["fixed"]
    print(f"✅ Done! Fixed {total_fixed} records total.")
    logger.info("creator_name_fix_completed", total_fixed=total_fixed)


if __name__ == "__main__":
    main()

