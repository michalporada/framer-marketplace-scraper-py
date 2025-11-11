"""Test script for API endpoints after JSON to database sync."""

import json
import os
import sys
from pathlib import Path

import httpx
from rich.console import Console
from rich.table import Table

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()

# API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def print_header(text: str):
    """Print formatted header."""
    console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
    console.print(f"[bold cyan]{text}[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")


def print_success(text: str):
    """Print success message."""
    console.print(f"[green]✓[/green] {text}")


def print_error(text: str):
    """Print error message."""
    console.print(f"[red]✗[/red] {text}")


def print_warning(text: str):
    """Print warning message."""
    console.print(f"[yellow]⚠[/yellow] {text}")


def print_info(text: str):
    """Print info message."""
    console.print(f"[blue]ℹ[/blue] {text}")


def test_endpoint(
    method: str,
    endpoint: str,
    description: str,
    params: dict = None,
    expected_status: int = 200,
    validate_response: callable = None,
):
    """Test a single API endpoint.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        description: Description of what is being tested
        params: Query parameters
        expected_status: Expected HTTP status code
        validate_response: Optional function to validate response data

    Returns:
        Tuple of (success: bool, response_data: dict, status_code: int)
    """
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method.upper() == "GET":
            response = httpx.get(url, params=params, timeout=30.0)
        else:
            response = httpx.request(method.upper(), url, json=params, timeout=30.0)

        status_code = response.status_code
        success = status_code == expected_status

        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"raw": response.text[:200]}

        if success:
            print_success(f"{description} - Status: {status_code}")
            if validate_response:
                try:
                    validate_response(response_data)
                    print_success("  Response validation passed")
                except AssertionError as e:
                    print_error(f"  Response validation failed: {e}")
                    success = False
        else:
            print_error(f"{description} - Status: {status_code} (expected {expected_status})")
            if response_data.get("error"):
                print_error(f"  Error: {response_data['error']}")

        return success, response_data, status_code

    except httpx.ConnectError:
        print_error(f"{description} - Connection error (is API running?)")
        return False, None, None
    except httpx.TimeoutException:
        print_error(f"{description} - Timeout")
        return False, None, None
    except Exception as e:
        print_error(f"{description} - Unexpected error: {type(e).__name__}: {str(e)}")
        return False, None, None


def validate_product_list(response_data: dict):
    """Validate product list response."""
    assert "data" in response_data, "Missing 'data' field"
    assert "meta" in response_data, "Missing 'meta' field"
    assert isinstance(response_data["data"], list), "'data' must be a list"
    assert "total" in response_data["meta"], "Missing 'total' in meta"
    assert "limit" in response_data["meta"], "Missing 'limit' in meta"
    assert "offset" in response_data["meta"], "Missing 'offset' in meta"


def validate_product(response_data: dict):
    """Validate single product response."""
    assert "data" in response_data, "Missing 'data' field"
    assert "meta" in response_data, "Missing 'meta' field"
    product = response_data["data"]
    assert "id" in product, "Missing 'id' in product"
    assert "name" in product, "Missing 'name' in product"
    assert "type" in product, "Missing 'type' in product"


def validate_creator_list(response_data: dict):
    """Validate creator list response."""
    assert "data" in response_data, "Missing 'data' field"
    assert "meta" in response_data, "Missing 'meta' field"
    assert isinstance(response_data["data"], list), "'data' must be a list"


def validate_creator(response_data: dict):
    """Validate single creator response."""
    assert "data" in response_data, "Missing 'data' field"
    assert "meta" in response_data, "Missing 'meta' field"
    creator = response_data["data"]
    assert "username" in creator, "Missing 'username' in creator"


def main():
    """Run all API tests."""
    print_header("Framer Marketplace Scraper API - Test Suite")

    # Check if API is running
    print_info(f"Testing API at: {API_BASE_URL}")
    print_info("Make sure API is running: uvicorn api.main:app --reload\n")

    results = []

    # Test 1: Root endpoint
    print_header("1. Root Endpoint")
    success, data, status = test_endpoint("GET", "/", "Root endpoint")
    results.append(("Root", success))

    # Test 2: Health check
    print_header("2. Health Check")
    success, data, status = test_endpoint("GET", "/health", "Health check")
    results.append(("Health", success))
    if data:
        print_info(f"  Database status: {data.get('database', 'unknown')}")
        print_info(f"  Database test: {data.get('database_test', 'unknown')}")

    # Test 3: Products list (all)
    print_header("3. Products - List All")
    success, data, status = test_endpoint(
        "GET",
        "/api/products",
        "Get all products",
        validate_response=validate_product_list,
    )
    results.append(("Products List", success))
    if data and "meta" in data:
        total = data["meta"].get("total", 0)
        count = len(data.get("data", []))
        print_info(f"  Total products in DB: {total}")
        print_info(f"  Products returned: {count}")

    # Test 4: Products list with filters
    print_header("4. Products - Filter by Type")
    for product_type in ["template", "component", "vector", "plugin"]:
        success, data, status = test_endpoint(
            "GET",
            "/api/products",
            f"Get {product_type} products",
            params={"type": product_type, "limit": 10},
            validate_response=validate_product_list,
        )
        results.append((f"Products {product_type}", success))
        if data and "data" in data:
            count = len(data["data"])
            print_info(f"  {product_type.capitalize()} products: {count}")

    # Test 5: Products pagination
    print_header("5. Products - Pagination")
    success, data1, _ = test_endpoint(
        "GET",
        "/api/products",
        "Get first page",
        params={"limit": 5, "offset": 0},
        validate_response=validate_product_list,
    )
    results.append(("Products Pagination Page 1", success))

    success, data2, _ = test_endpoint(
        "GET",
        "/api/products",
        "Get second page",
        params={"limit": 5, "offset": 5},
        validate_response=validate_product_list,
    )
    results.append(("Products Pagination Page 2", success))

    if data1 and data2 and "data" in data1 and "data" in data2:
        ids1 = {p.get("id") for p in data1["data"]}
        ids2 = {p.get("id") for p in data2["data"]}
        if ids1 & ids2:
            print_warning("  Overlap between pages detected")
        else:
            print_success("  No overlap between pages")

    # Test 6: Products sorting
    print_header("6. Products - Sorting")
    for sort_field in ["created_at", "views_normalized", "name"]:
        success, data, _ = test_endpoint(
            "GET",
            "/api/products",
            f"Sort by {sort_field}",
            params={"sort": sort_field, "order": "desc", "limit": 5},
            validate_response=validate_product_list,
        )
        results.append((f"Products Sort {sort_field}", success))

    # Test 7: Single product (if we have products)
    print_header("7. Products - Single Product")
    # First get a product ID
    success, data, _ = test_endpoint(
        "GET", "/api/products", "Get first product for detail test", params={"limit": 1}
    )
    if success and data and "data" in data and len(data["data"]) > 0:
        product_id = data["data"][0].get("id")
        if product_id:
            success, data, _ = test_endpoint(
                "GET",
                f"/api/products/{product_id}",
                f"Get product {product_id}",
                validate_response=validate_product,
            )
            results.append(("Product Detail", success))
            if data and "data" in data:
                product = data["data"]
                print_info(f"  Product: {product.get('name')} ({product.get('type')})")
        else:
            print_warning("  No product ID found for detail test")
            results.append(("Product Detail", False))
    else:
        print_warning("  No products available for detail test")
        results.append(("Product Detail", False))

    # Test 8: Product not found
    print_header("8. Products - Not Found")
    success, data, status = test_endpoint(
        "GET",
        "/api/products/non-existent-product-id-12345",
        "Get non-existent product",
        expected_status=404,
    )
    results.append(("Product Not Found", success))

    # Test 9: Creators list
    print_header("9. Creators - List All")
    success, data, status = test_endpoint(
        "GET",
        "/api/creators",
        "Get all creators",
        validate_response=validate_creator_list,
    )
    results.append(("Creators List", success))
    if data and "meta" in data:
        total = data["meta"].get("total", 0)
        count = len(data.get("data", []))
        print_info(f"  Total creators in DB: {total}")
        print_info(f"  Creators returned: {count}")

    # Test 10: Creators pagination
    print_header("10. Creators - Pagination")
    success, data, _ = test_endpoint(
        "GET",
        "/api/creators",
        "Get creators with pagination",
        params={"limit": 10, "offset": 0},
        validate_response=validate_creator_list,
    )
    results.append(("Creators Pagination", success))

    # Test 11: Single creator (if we have creators)
    print_header("11. Creators - Single Creator")
    success, data, _ = test_endpoint(
        "GET", "/api/creators", "Get first creator for detail test", params={"limit": 1}
    )
    if success and data and "data" in data and len(data["data"]) > 0:
        username = data["data"][0].get("username")
        if username:
            success, data, _ = test_endpoint(
                "GET",
                f"/api/creators/{username}",
                f"Get creator {username}",
                validate_response=validate_creator,
            )
            results.append(("Creator Detail", success))
            if data and "data" in data:
                creator = data["data"]
                print_info(f"  Creator: {creator.get('name', 'N/A')} (@{creator.get('username')})")
                print_info(f"  Products: {creator.get('stats', {}).get('total_products', 0)}")
        else:
            print_warning("  No creator username found for detail test")
            results.append(("Creator Detail", False))
    else:
        print_warning("  No creators available for detail test")
        results.append(("Creator Detail", False))

    # Test 12: Creator products
    print_header("12. Creators - Creator Products")
    success, data, _ = test_endpoint(
        "GET", "/api/creators", "Get first creator for products test", params={"limit": 1}
    )
    if success and data and "data" in data and len(data["data"]) > 0:
        username = data["data"][0].get("username")
        if username:
            success, data, _ = test_endpoint(
                "GET",
                f"/api/creators/{username}/products",
                f"Get products for creator {username}",
                params={"limit": 10},
            )
            results.append(("Creator Products", success))
            if data and "data" in data:
                count = len(data["data"])
                print_info(f"  Products found: {count}")
        else:
            print_warning("  No creator username found for products test")
            results.append(("Creator Products", False))
    else:
        print_warning("  No creators available for products test")
        results.append(("Creator Products", False))

    # Test 13: Creator not found
    print_header("13. Creators - Not Found")
    success, data, status = test_endpoint(
        "GET",
        "/api/creators/non-existent-creator-12345",
        "Get non-existent creator",
        expected_status=404,
    )
    results.append(("Creator Not Found", success))

    # Test 14: Invalid product type
    print_header("14. Products - Invalid Type")
    success, data, status = test_endpoint(
        "GET",
        "/api/products",
        "Invalid product type",
        params={"type": "invalid_type"},
        expected_status=422,
    )
    results.append(("Invalid Product Type", success))

    # Test 15: Invalid sort field
    print_header("15. Products - Invalid Sort")
    success, data, status = test_endpoint(
        "GET",
        "/api/products",
        "Invalid sort field",
        params={"sort": "invalid_sort"},
        expected_status=422,
    )
    results.append(("Invalid Sort", success))

    # Summary
    print_header("Test Summary")
    table = Table(title="Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status", justify="center")

    passed = 0
    failed = 0
    for test_name, success in results:
        status = "[green]PASS[/green]" if success else "[red]FAIL[/red]"
        table.add_row(test_name, status)
        if success:
            passed += 1
        else:
            failed += 1

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {len(results)} tests")
    console.print(f"[green]Passed:[/green] {passed}")
    console.print(f"[red]Failed:[/red] {failed}")

    if failed == 0:
        console.print("\n[bold green]All tests passed! ✓[/bold green]")
        return 0
    else:
        console.print(f"\n[bold red]{failed} test(s) failed! ✗[/bold red]")
        return 1


if __name__ == "__main__":
    exit(main())
