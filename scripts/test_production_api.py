#!/usr/bin/env python3
"""Script to test all API endpoints on production."""

import os
import sys
from typing import Dict, List, Optional
from datetime import datetime

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Production API URL from README
PRODUCTION_API_URL = os.getenv(
    "PRODUCTION_API_URL", "https://framer-marketplace-scraper-py-production.up.railway.app"
)

# Colors for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ{Colors.RESET} {text}")


def test_endpoint(
    method: str,
    endpoint: str,
    params: Optional[Dict] = None,
    expected_status: int = 200,
    description: str = "",
) -> Dict:
    """Test a single endpoint.

    Args:
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        expected_status: Expected HTTP status code
        description: Description of the endpoint

    Returns:
        Dict with test results
    """
    url = f"{PRODUCTION_API_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, params=params, timeout=30)
        else:
            return {
                "success": False,
                "error": f"Unsupported method: {method}",
                "status_code": None,
            }

        success = response.status_code == expected_status
        result = {
            "success": success,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "response_time_ms": response.elapsed.total_seconds() * 1000,
            "description": description,
        }

        if success:
            try:
                data = response.json()
                # Check if response has expected structure
                if isinstance(data, dict):
                    if "data" in data or "error" in data or "message" in data:
                        result["has_valid_structure"] = True
                    else:
                        result["has_valid_structure"] = False
                else:
                    result["has_valid_structure"] = True
            except Exception:
                result["has_valid_structure"] = False
        else:
            result["error"] = response.text[:200] if response.text else "No error message"

        return result

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Timeout (30s)",
            "status_code": None,
            "description": description,
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Connection error",
            "status_code": None,
            "description": description,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)[:200]}",
            "status_code": None,
            "description": description,
        }


def main():
    """Test all endpoints."""
    print_header(f"🧪 TESTY ENDPOINTÓW API - PRODUKCJA")
    print_info(f"API URL: {PRODUCTION_API_URL}")
    print_info(f"Data testu: {datetime.now().isoformat()}\n")

    results = []
    total_tests = 0
    passed_tests = 0

    # Root & Health
    print_header("📋 Root & Health")
    test_cases = [
        ("GET", "/", None, 200, "Root endpoint"),
        ("GET", "/health", None, 200, "Health check"),
    ]

    for method, endpoint, params, expected, desc in test_cases:
        total_tests += 1
        result = test_endpoint(method, endpoint, params, expected, desc)
        results.append((endpoint, result))
        if result["success"]:
            passed_tests += 1
            print_success(
                f"{endpoint} - {desc} ({result['status_code']}, {result['response_time_ms']:.0f}ms)"
            )
        else:
            print_error(f"{endpoint} - {desc} - {result.get('error', 'Unknown error')}")

    # Products
    print_header("📦 Products")
    test_cases = [
        ("GET", "/api/products", {"limit": 5}, 200, "Lista produktów"),
        ("GET", "/api/products", {"type": "template", "limit": 5}, 200, "Lista templates"),
        ("GET", "/api/products", {"type": "component", "limit": 5}, 200, "Lista components"),
        ("GET", "/api/products", {"type": "vector", "limit": 5}, 200, "Lista vectors"),
        ("GET", "/api/products", {"type": "plugin", "limit": 5}, 200, "Lista plugins"),
        ("GET", "/api/products/portfolite", None, 200, "Pojedynczy produkt"),
        ("GET", "/api/products/portfolite/changes", None, 200, "Zmiany produktu"),
        ("GET", "/api/products/categories/comparison", None, 200, "Porównanie kategorii"),
        (
            "GET",
            "/api/products/categories/comparison",
            {"product_type": "template"},
            200,
            "Porównanie kategorii (templates)",
        ),
        ("GET", "/api/products/views-change-24h", {"product_type": "template"}, 200, "Views change 24h"),
        ("GET", "/api/products/categories/Agency/views", {"product_type": "template"}, 200, "Views kategorii"),
    ]

    for method, endpoint, params, expected, desc in test_cases:
        total_tests += 1
        result = test_endpoint(method, endpoint, params, expected, desc)
        results.append((endpoint, result))
        if result["success"]:
            passed_tests += 1
            print_success(
                f"{endpoint} - {desc} ({result['status_code']}, {result['response_time_ms']:.0f}ms)"
            )
        else:
            print_error(f"{endpoint} - {desc} - {result.get('error', 'Unknown error')}")

    # Creators
    print_header("👤 Creators")
    test_cases = [
        ("GET", "/api/creators", {"limit": 5}, 200, "Lista kreatorów"),
        ("GET", "/api/creators/099supply", None, 200, "Pojedynczy kreator"),
        ("GET", "/api/creators/099supply/products", None, 200, "Produkty kreatora"),
        (
            "GET",
            "/api/creators/099supply/products-growth",
            {"product_type": "component", "period_hours": 24},
            200,
            "Wzrost views produktów kreatora",
        ),
    ]

    for method, endpoint, params, expected, desc in test_cases:
        total_tests += 1
        result = test_endpoint(method, endpoint, params, expected, desc)
        results.append((endpoint, result))
        if result["success"]:
            passed_tests += 1
            print_success(
                f"{endpoint} - {desc} ({result['status_code']}, {result['response_time_ms']:.0f}ms)"
            )
        else:
            print_error(f"{endpoint} - {desc} - {result.get('error', 'Unknown error')}")

    # Metrics
    print_header("📊 Metrics")
    test_cases = [
        ("GET", "/api/metrics/summary", None, 200, "Metryki summary"),
        ("GET", "/api/metrics/history", {"limit": 5}, 200, "Historia metryk"),
        ("GET", "/api/metrics/stats", None, 200, "Statystyki"),
    ]

    for method, endpoint, params, expected, desc in test_cases:
        total_tests += 1
        result = test_endpoint(method, endpoint, params, expected, desc)
        results.append((endpoint, result))
        if result["success"]:
            passed_tests += 1
            print_success(
                f"{endpoint} - {desc} ({result['status_code']}, {result['response_time_ms']:.0f}ms)"
            )
        else:
            print_error(f"{endpoint} - {desc} - {result.get('error', 'Unknown error')}")

    # Cache
    print_header("🔧 Cache")
    test_cases = [
        ("GET", "/cache/stats", None, 200, "Statystyki cache"),
        ("POST", "/cache/invalidate", {"cache_type": "product"}, 200, "Invalidate cache"),
    ]

    for method, endpoint, params, expected, desc in test_cases:
        total_tests += 1
        result = test_endpoint(method, endpoint, params, expected, desc)
        results.append((endpoint, result))
        if result["success"]:
            passed_tests += 1
            print_success(
                f"{endpoint} - {desc} ({result['status_code']}, {result['response_time_ms']:.0f}ms)"
            )
        else:
            print_error(f"{endpoint} - {desc} - {result.get('error', 'Unknown error')}")

    # Summary
    print_header("📊 Podsumowanie")
    print(f"Łącznie testów: {total_tests}")
    print(f"{Colors.GREEN}Przeszło: {passed_tests}{Colors.RESET}")
    print(f"{Colors.RED}Nie przeszło: {total_tests - passed_tests}{Colors.RESET}")
    print(f"Success rate: {(passed_tests / total_tests * 100):.1f}%")

    # Failed tests details
    failed_tests = [(endpoint, result) for endpoint, result in results if not result["success"]]
    if failed_tests:
        print(f"\n{Colors.RED}Nieudane testy:{Colors.RESET}")
        for endpoint, result in failed_tests:
            print(f"  - {endpoint}: {result.get('error', 'Unknown error')}")

    # Response times
    response_times = [
        result["response_time_ms"] for _, result in results if result.get("response_time_ms")
    ]
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        print(f"\n{Colors.BLUE}Czasy odpowiedzi:{Colors.RESET}")
        print(f"  Średnia: {avg_time:.0f}ms")
        print(f"  Min: {min_time:.0f}ms")
        print(f"  Max: {max_time:.0f}ms")

    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

    # Exit code
    if passed_tests == total_tests:
        print_success("Wszystkie testy przeszły pomyślnie! ✅")
        sys.exit(0)
    else:
        print_error(f"Niektóre testy nie przeszły ({total_tests - passed_tests} błędów)")
        sys.exit(1)


if __name__ == "__main__":
    main()

