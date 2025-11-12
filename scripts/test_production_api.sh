#!/bin/bash
# Script to test all API endpoints on production

PRODUCTION_API_URL="${PRODUCTION_API_URL:-https://framer-marketplace-scraper-py-production.up.railway.app}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}======================================================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}======================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED_TESTS++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED_TESTS++))
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

test_endpoint() {
    local method=$1
    local endpoint=$2
    local params=$3
    local expected_status=$4
    local description=$5
    
    ((TOTAL_TESTS++))
    
    local url="${PRODUCTION_API_URL}${endpoint}"
    if [ -n "$params" ]; then
        url="${url}?${params}"
    fi
    
    local response
    local status_code
    local response_time
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}\n%{time_total}" "$url" --max-time 30)
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}\n%{time_total}" -X POST "$url" --max-time 30)
    else
        print_error "$endpoint - $description - Unsupported method: $method"
        return 1
    fi
    
    # Extract status code and time from response
    status_code=$(echo "$response" | tail -2 | head -1)
    response_time=$(echo "$response" | tail -1)
    response_body=$(echo "$response" | head -n -2)
    
    # Convert time to milliseconds
    response_time_ms=$(echo "$response_time * 1000" | bc)
    
    if [ "$status_code" = "$expected_status" ]; then
        print_success "$endpoint - $description (${status_code}, ${response_time_ms}ms)"
        return 0
    else
        error_msg=$(echo "$response_body" | head -c 100)
        print_error "$endpoint - $description - Status: $status_code (expected: $expected_status) - $error_msg"
        return 1
    fi
}

# Main
print_header "🧪 TESTY ENDPOINTÓW API - PRODUKCJA"
print_info "API URL: $PRODUCTION_API_URL"
print_info "Data testu: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# Root & Health
print_header "📋 Root & Health"
test_endpoint "GET" "/" "" 200 "Root endpoint"
test_endpoint "GET" "/health" "" 200 "Health check"

# Products
print_header "📦 Products"
test_endpoint "GET" "/api/products" "limit=5" 200 "Lista produktów"
test_endpoint "GET" "/api/products" "type=template&limit=5" 200 "Lista templates"
test_endpoint "GET" "/api/products" "type=component&limit=5" 200 "Lista components"
test_endpoint "GET" "/api/products" "type=vector&limit=5" 200 "Lista vectors"
test_endpoint "GET" "/api/products" "type=plugin&limit=5" 200 "Lista plugins"
test_endpoint "GET" "/api/products/portfolite" "" 200 "Pojedynczy produkt"
test_endpoint "GET" "/api/products/portfolite/changes" "" 200 "Zmiany produktu"
test_endpoint "GET" "/api/products/categories/comparison" "" 200 "Porównanie kategorii"
test_endpoint "GET" "/api/products/categories/comparison" "product_type=template" 200 "Porównanie kategorii (templates)"
test_endpoint "GET" "/api/products/views-change-24h" "product_type=template" 200 "Views change 24h"
test_endpoint "GET" "/api/products/categories/Agency/views" "product_type=template" 200 "Views kategorii"

# Creators
print_header "👤 Creators"
test_endpoint "GET" "/api/creators" "limit=5" 200 "Lista kreatorów"
test_endpoint "GET" "/api/creators/099supply" "" 200 "Pojedynczy kreator"
test_endpoint "GET" "/api/creators/099supply/products" "" 200 "Produkty kreatora"
test_endpoint "GET" "/api/creators/099supply/products-growth" "product_type=component&period_hours=24" 200 "Wzrost views produktów kreatora"

# Metrics
print_header "📊 Metrics"
test_endpoint "GET" "/api/metrics/summary" "" 200 "Metryki summary"
test_endpoint "GET" "/api/metrics/history" "limit=5" 200 "Historia metryk"
test_endpoint "GET" "/api/metrics/stats" "" 200 "Statystyki"

# Cache
print_header "🔧 Cache"
test_endpoint "GET" "/cache/stats" "" 200 "Statystyki cache"
test_endpoint "POST" "/cache/invalidate" "cache_type=product" 200 "Invalidate cache"

# Summary
print_header "📊 Podsumowanie"
echo "Łącznie testów: $TOTAL_TESTS"
echo -e "${GREEN}Przeszło: $PASSED_TESTS${NC}"
echo -e "${RED}Nie przeszło: $FAILED_TESTS${NC}"

if [ $TOTAL_TESTS -gt 0 ]; then
    success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
    echo "Success rate: ${success_rate}%"
fi

echo ""
echo -e "${BOLD}${BLUE}======================================================================${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Wszystkie testy przeszły pomyślnie! ✅${NC}"
    exit 0
else
    echo -e "${RED}✗ Niektóre testy nie przeszły ($FAILED_TESTS błędów)${NC}"
    exit 1
fi

