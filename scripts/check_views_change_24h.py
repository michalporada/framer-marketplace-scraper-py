#!/usr/bin/env python3
"""Script to check views change in templates over last 24 hours via API."""

import os
import sys
from typing import Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API URL from environment or use default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def format_number(num: int) -> str:
    """Format number with thousand separators."""
    return f"{num:,}".replace(",", " ")


def check_views_change_24h(product_type: str = "template") -> Optional[dict]:
    """Check views change for products in last 24 hours via API.

    Args:
        product_type: Product type to check (default: template)

    Returns:
        Response data or None on error
    """
    endpoint = f"{API_BASE_URL}/api/products/views-change-24h"
    params = {"product_type": product_type}

    try:
        print(f"🔍 Sprawdzanie zmian views dla {product_type} w ostatnich 24h...")
        print(f"📡 API URL: {endpoint}")
        print(f"📊 Parametry: {params}\n")

        response = requests.get(endpoint, params=params, timeout=30)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503:
            print("❌ Błąd: Baza danych nie jest dostępna")
            print("   Sprawdź czy DATABASE_URL jest skonfigurowane w API")
            return None
        elif response.status_code == 404:
            print("❌ Błąd: Endpoint nie znaleziony")
            print("   Sprawdź czy API jest uruchomione i ma najnowszą wersję")
            return None
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("detail", {}).get("error", {}).get("message", "Unknown error")
            print(f"❌ Błąd API ({response.status_code}): {error_msg}")
            return None

    except requests.exceptions.ConnectionError:
        print(f"❌ Błąd: Nie można połączyć się z API")
        print(f"   Sprawdź czy API jest uruchomione na: {API_BASE_URL}")
        print(f"   Możesz uruchomić API lokalnie: uvicorn api.main:app --reload")
        return None
    except requests.exceptions.Timeout:
        print("❌ Błąd: Timeout - API nie odpowiedziało w czasie 30s")
        return None
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {type(e).__name__}: {str(e)}")
        return None


def main():
    """Main function."""
    product_type = sys.argv[1] if len(sys.argv) > 1 else "template"

    if product_type not in ["template", "component", "vector", "plugin"]:
        print(f"❌ Nieprawidłowy typ produktu: {product_type}")
        print("   Dozwolone typy: template, component, vector, plugin")
        sys.exit(1)

    result = check_views_change_24h(product_type)

    if not result:
        sys.exit(1)

    # Display results
    print("=" * 60)
    print(f"📊 WYNIKI DLA {product_type.upper()}")
    print("=" * 60)
    print()

    total_change = result.get("total_views_change", 0)
    products_count = result.get("products_count", 0)
    products_with_changes = result.get("products_with_changes", 0)
    meta = result.get("meta", {})

    # Format change with sign
    change_sign = "+" if total_change >= 0 else ""
    change_formatted = f"{change_sign}{format_number(total_change)}"

    print(f"🔄 Zmiana views (24h): {change_formatted}")
    print(f"📦 Łączna liczba produktów: {format_number(products_count)}")
    print(f"📈 Produkty ze zmianami: {format_number(products_with_changes)}")
    print()

    if meta:
        period_start = meta.get("period_start", "")
        period_end = meta.get("period_end", "")
        if period_start and period_end:
            print(f"⏰ Okres analizy:")
            print(f"   Od: {period_start}")
            print(f"   Do: {period_end}")
            print()

    # Calculate percentage if we have data
    if products_count > 0:
        change_percent = (products_with_changes / products_count) * 100
        print(f"📊 Procent produktów ze zmianami: {change_percent:.1f}%")
        print()

    print("=" * 60)
    print("✅ Analiza zakończona pomyślnie")
    print("=" * 60)


if __name__ == "__main__":
    main()

