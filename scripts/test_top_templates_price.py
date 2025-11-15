"""Test script to check what price data is returned for top templates from screenshot."""

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

# Templates from screenshot (in order)
SCREENSHOT_TEMPLATES = [
    "Atomic",
    "Portfolite",
    "Pearl",
    "Landio",
    "Cohesion",
    "Athos 2.0",
    "Xtract",
    "Athos Dark",
    "Blocks",
    "Agentic",
]


def test_top_templates():
    """Test /api/products/top-templates endpoint and check price data."""
    console.print("\n[bold cyan]Testing Top Templates Endpoint[/bold cyan]\n")
    
    url = f"{API_BASE_URL}/api/products/top-templates"
    params = {"limit": 10, "period_hours": 24}
    
    try:
        console.print(f"[blue]Fetching:[/blue] {url}?limit=10&period_hours=24")
        response = httpx.get(url, params=params, timeout=30.0)
        
        if response.status_code != 200:
            console.print(f"[red]Error:[/red] Status {response.status_code}")
            console.print(response.text[:500])
            return
        
        data = response.json()
        
        if "data" not in data:
            console.print("[red]Error:[/red] No 'data' field in response")
            console.print(json.dumps(data, indent=2))
            return
        
        templates = data["data"]
        console.print(f"[green]✓[/green] Found {len(templates)} templates\n")
        
        # Create table
        table = Table(title="Top Templates - Price Data")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Name", style="magenta", width=20)
        table.add_column("Price (API)", style="yellow", width=15)
        table.add_column("is_free", style="blue", width=8)
        table.add_column("Views", style="green", width=12)
        table.add_column("In Screenshot", style="cyan", width=12)
        
        for idx, template in enumerate(templates, 1):
            name = template.get("name", "N/A")
            price = template.get("price")
            is_free = template.get("is_free", False)
            views = template.get("views", 0)
            
            # Format price
            if is_free:
                price_display = "[green]Free[/green]"
            elif price is not None and price > 0:
                price_display = f"[yellow]${price:.2f}[/yellow]"
            else:
                price_display = "[red]None/Paid[/red]"
            
            # Check if in screenshot
            in_screenshot = "✓" if name in SCREENSHOT_TEMPLATES else ""
            
            table.add_row(
                str(idx),
                name,
                price_display,
                "Yes" if is_free else "No",
                f"{views:,}" if views else "-",
                in_screenshot
            )
        
        console.print(table)
        
        # Check for screenshot templates
        console.print("\n[bold cyan]Checking Screenshot Templates:[/bold cyan]\n")
        
        screenshot_table = Table(title="Screenshot Templates Status")
        screenshot_table.add_column("Name", style="magenta", width=20)
        screenshot_table.add_column("Found in API", style="cyan", width=12)
        screenshot_table.add_column("Price (API)", style="yellow", width=15)
        screenshot_table.add_column("is_free", style="blue", width=8)
        screenshot_table.add_column("Expected Price", style="green", width=15)
        
        # Expected prices from screenshot
        expected_prices = {
            "Atomic": "$99.00",
            "Portfolite": "$79.00",
            "Pearl": "Paid",
            "Landio": "$79.00",
            "Cohesion": "Paid",
            "Athos 2.0": "Paid",
            "Xtract": "Paid",
            "Athos Dark": "Paid",
            "Blocks": "Paid",
            "Agentic": "Paid",
        }
        
        found_templates = {t.get("name"): t for t in templates}
        
        for template_name in SCREENSHOT_TEMPLATES:
            template = found_templates.get(template_name)
            if template:
                price = template.get("price")
                is_free = template.get("is_free", False)
                
                if is_free:
                    price_display = "[green]Free[/green]"
                elif price is not None and price > 0:
                    price_display = f"[yellow]${price:.2f}[/yellow]"
                else:
                    price_display = "[red]None/Paid[/red]"
                
                expected = expected_prices.get(template_name, "?")
                match = "✓" if (
                    (expected.startswith("$") and price and abs(float(expected.replace("$", "")) - price) < 0.01) or
                    (expected == "Paid" and not is_free and (price is None or price == 0))
                ) else "✗"
                
                screenshot_table.add_row(
                    template_name,
                    "[green]✓ Yes[/green]",
                    price_display,
                    "Yes" if is_free else "No",
                    f"{expected} {match}"
                )
            else:
                screenshot_table.add_row(
                    template_name,
                    "[red]✗ No[/red]",
                    "-",
                    "-",
                    expected_prices.get(template_name, "?")
                )
        
        console.print(screenshot_table)
        
        # Show raw data for first few templates
        console.print("\n[bold cyan]Raw API Response (first 3 templates):[/bold cyan]\n")
        for template in templates[:3]:
            console.print(f"[blue]Template:[/blue] {template.get('name')}")
            console.print(json.dumps({
                "product_id": template.get("product_id"),
                "name": template.get("name"),
                "price": template.get("price"),
                "is_free": template.get("is_free"),
                "views": template.get("views"),
                "creator_username": template.get("creator_username"),
                "category": template.get("category"),
            }, indent=2))
            console.print()
        
    except httpx.ConnectError:
        console.print(f"[red]✗[/red] Connection error - is API running at {API_BASE_URL}?")
        console.print("[yellow]Start API with:[/yellow] python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")
    except httpx.TimeoutException:
        console.print("[red]✗[/red] Request timeout")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {type(e).__name__}: {str(e)}")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    test_top_templates()

