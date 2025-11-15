-- SQL script to check products with price that might be incorrectly marked as paid
-- This is a READ-ONLY query for verification purposes

-- Find all products with price != NULL and is_free = FALSE
-- These might be incorrectly marked as paid when they're actually free
SELECT 
    id,
    name,
    type,
    price,
    is_free,
    url,
    scraped_at
FROM products
WHERE price IS NOT NULL
AND is_free = FALSE
ORDER BY type, name;

-- Count by type
SELECT 
    type,
    COUNT(*) as count
FROM products
WHERE price IS NOT NULL
AND is_free = FALSE
GROUP BY type
ORDER BY type;

