#!/bin/bash
# Quick test script for scraper stability improvements

set -e

echo "🧪 Quick Test - Scraper Stability Improvements"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if scraper runs with small limit
echo "Test 1: Basic scraper run (10 products)..."
python -m src.main 10
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Test 1 PASSED${NC}"
else
    echo -e "${RED}❌ Test 1 FAILED (exit code: $EXIT_CODE)${NC}"
fi
echo ""

# Test 2: Check if sitemap cache was created
echo "Test 2: Sitemap cache..."
if [ -f "data/sitemap_cache.xml" ]; then
    CACHE_SIZE=$(stat -f%z "data/sitemap_cache.xml" 2>/dev/null || stat -c%s "data/sitemap_cache.xml" 2>/dev/null)
    echo -e "${GREEN}✅ Test 2 PASSED - Cache exists (${CACHE_SIZE} bytes)${NC}"
else
    echo -e "${YELLOW}⚠️  Test 2 WARNING - Cache not found (may be normal on first run)${NC}"
fi
echo ""

# Test 3: Check if metrics.log was created
echo "Test 3: Metrics log..."
if [ -f "data/metrics.log" ]; then
    METRICS_COUNT=$(wc -l < "data/metrics.log")
    echo -e "${GREEN}✅ Test 3 PASSED - Metrics log exists (${METRICS_COUNT} entries)${NC}"
    echo "Last metrics entry:"
    tail -1 data/metrics.log | python -m json.tool 2>/dev/null || tail -1 data/metrics.log
else
    echo -e "${RED}❌ Test 3 FAILED - Metrics log not found${NC}"
fi
echo ""

# Test 4: Check for duplicates in logs
echo "Test 4: Duplicate detection..."
if grep -q "duplicates_found\|duplicate_product" logs/*.log 2>/dev/null; then
    DUPLICATE_COUNT=$(grep -c "duplicate_product" logs/*.log 2>/dev/null || echo "0")
    echo -e "${YELLOW}⚠️  Test 4 WARNING - Found ${DUPLICATE_COUNT} duplicate warnings (check if expected)${NC}"
else
    echo -e "${GREEN}✅ Test 4 PASSED - No duplicates detected${NC}"
fi
echo ""

# Test 5: Check for slow requests
echo "Test 5: Slow requests detection..."
if grep -q "slow_request" logs/*.log 2>/dev/null; then
    SLOW_COUNT=$(grep -c "slow_request" logs/*.log 2>/dev/null || echo "0")
    echo -e "${YELLOW}⚠️  Test 5 WARNING - Found ${SLOW_COUNT} slow requests (>10s)${NC}"
    echo "Slow requests:"
    grep "slow_request" logs/*.log | tail -3
else
    echo -e "${GREEN}✅ Test 5 PASSED - No slow requests detected${NC}"
fi
echo ""

# Test 6: Check exit code
echo "Test 6: Exit code..."
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Test 6 PASSED - Exit code 0 (success)${NC}"
elif [ $EXIT_CODE -eq 2 ]; then
    echo -e "${YELLOW}⚠️  Test 6 WARNING - Exit code 2 (upstream error)${NC}"
else
    echo -e "${RED}❌ Test 6 FAILED - Exit code $EXIT_CODE${NC}"
fi
echo ""

# Summary
echo "=============================================="
echo "📊 Test Summary"
echo "=============================================="
echo "Exit code: $EXIT_CODE"
echo "Products scraped: $(find data/products -name "*.json" 2>/dev/null | wc -l | tr -d ' ')"
echo "Creators scraped: $(find data/creators -name "*.json" 2>/dev/null | wc -l | tr -d ' ')"
echo "Cache exists: $([ -f "data/sitemap_cache.xml" ] && echo "Yes" || echo "No")"
echo "Metrics log exists: $([ -f "data/metrics.log" ] && echo "Yes" || echo "No")"
echo ""
echo "For detailed testing, see: docs/TESTING_PLAN.md"

