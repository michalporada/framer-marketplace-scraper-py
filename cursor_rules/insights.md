# Insights Rules

**Cel:** Zapewnić spójność logik analizy danych.

## Definicja Insights

Insights to analizy danych scrapowanych z Framer Marketplace, które dostarczają wartościowych informacji o trendach, wzorcach i statystykach.

## Typy Insights

### 1. Product Insights

#### Popularity Trends
- Najpopularniejsze produkty według typu
- Trendy popularności w czasie
- Ranking produktów według statystyk (views, installs, users)

#### Pricing Analysis
- Rozkład cen według typu produktu
- Średnie ceny
- Free vs Paid products ratio

#### Category Distribution
- Rozkład produktów według kategorii
- Najpopularniejsze kategorie
- Trendy w kategoriach

### 2. Creator Insights

#### Creator Performance
- Top creators według liczby produktów
- Top creators według popularności produktów
- Creator success rate

#### Creator Diversity
- Rozkład creatorów według liczby produktów
- Most active creators
- New creators trends

### 3. Temporal Insights

#### Time-based Analysis
- Trendy w czasie (nowe produkty, aktualizacje)
- Sezonowe wzorce
- Growth rate

#### Update Patterns
- Częstotliwość aktualizacji produktów
- Products z najnowszymi aktualizacjami
- Stale products (nieaktualizowane)

### 4. Quality Insights

#### Data Completeness
- Products z pełnymi danymi
- Missing fields analysis
- Data quality score

#### Review Analysis
- Average ratings
- Review distribution
- Products z największą liczbą recenzji

## Zasady Implementacji

### 1. Data Source

- Używaj danych z `data/products/` (JSON files)
- Używaj danych z `data/creators/` (JSON files)
- Używaj danych z `data/categories/` (JSON files, jeśli dostępne)

### 2. Normalized Data

- Zawsze używaj `normalized` formatów z models
- Używaj `NormalizedStatistic.normalized` dla liczb
- Używaj `NormalizedDate.normalized` dla dat (ISO 8601)

### 3. Performance

- Cache wyniki insights (jeśli kosztowne obliczenia)
- Używaj generatorów dla dużych datasetów
- Optymalizuj queries do danych

### 4. Accuracy

- Waliduj dane przed analizą
- Obsługuj missing values gracefully
- Dokumentuj założenia i ograniczenia

## Struktura Implementacji

### Katalog Insights

```
src/
└── insights/
    ├── __init__.py
    ├── product_insights.py    # Product insights
    ├── creator_insights.py     # Creator insights
    ├── temporal_insights.py    # Time-based insights
    ├── quality_insights.py     # Data quality insights
    └── utils.py                # Helper functions
```

### Przykład Implementacji

```python
# src/insights/product_insights.py
from typing import List, Dict
from pathlib import Path
import json

from src.models.product import Product

def get_top_products_by_views(
    product_type: str,
    limit: int = 10
) -> List[Dict]:
    """
    Get top products by views.
    
    Args:
        product_type: template | component | vector | plugin
        limit: Number of products to return
    
    Returns:
        List of products sorted by views (descending)
    """
    products_dir = Path("data/products") / product_type
    products = []
    
    for product_file in products_dir.glob("*.json"):
        with open(product_file) as f:
            data = json.load(f)
            product = Product(**data)
            
            if product.stats and product.stats.views:
                # Używaj normalized value
                views = product.stats.views.normalized
                products.append({
                    "product_id": product.id,
                    "name": product.name,
                    "views": views,
                    "creator": product.creator.username,
                })
    
    # Sort by views descending
    products.sort(key=lambda x: x["views"], reverse=True)
    return products[:limit]
```

## Zasady Analizy

### 1. Normalized Values

**Zawsze używaj normalized values:**
```python
# ✅ Dobrze
views = product.stats.views.normalized  # int
date = product.metadata.published_date.normalized  # ISO 8601

# ❌ Źle
views = product.stats.views.raw  # "19.8K Views" - nie do obliczeń
date = product.metadata.published_date.raw  # "5 months ago" - nie do sortowania
```

### 2. Missing Data

**Obsługuj missing data:**
```python
if product.stats and product.stats.views:
    views = product.stats.views.normalized
else:
    views = 0  # lub skip product
```

### 3. Type Safety

**Używaj Pydantic models:**
```python
product = Product(**data)  # Walidacja automatyczna
# Nie używaj surowych dict bez walidacji
```

### 4. Error Handling

**Obsługuj błędy gracefully:**
```python
try:
    product = Product(**data)
except ValidationError as e:
    logger.warning("invalid_product_data", file=product_file, error=str(e))
    continue  # Skip invalid products
```

## Format Wyników

### Standardowy Format

```python
{
    "insight_type": "top_products_by_views",
    "parameters": {
        "product_type": "template",
        "limit": 10
    },
    "results": [
        {
            "product_id": "product-1",
            "name": "Product Name",
            "views": 19800,
            "creator": "creator-username",
            "rank": 1
        },
        # ...
    ],
    "metadata": {
        "total_products": 1000,
        "generated_at": "2024-01-01T00:00:00Z"
    }
}
```

### Aggregated Statistics

```python
{
    "insight_type": "pricing_analysis",
    "product_type": "template",
    "statistics": {
        "total_products": 1000,
        "free_count": 200,
        "paid_count": 800,
        "average_price": 25.50,
        "min_price": 5.0,
        "max_price": 199.0,
        "price_distribution": {
            "0-10": 150,
            "10-25": 300,
            "25-50": 250,
            "50-100": 80,
            "100+": 20
        }
    },
    "metadata": {
        "generated_at": "2024-01-01T00:00:00Z"
    }
}
```

## Caching

### Strategia Cache

1. **Cache Results**
   - Cache wyniki kosztownych obliczeń
   - TTL: 1-24 godzin (zależnie od insight)
   - Invalidate cache po nowym scrapowaniu

2. **Implementation**
   ```python
   from functools import lru_cache
   import json
   from pathlib import Path
   
   CACHE_DIR = Path("data/insights_cache")
   
   def get_cached_insight(insight_name: str, params: dict):
       cache_file = CACHE_DIR / f"{insight_name}_{hash(str(params))}.json"
       if cache_file.exists():
           # Check TTL
           if is_cache_valid(cache_file):
               return json.loads(cache_file.read_text())
       return None
   ```

## Export Insights

### JSON Export

```python
def export_insights_to_json(insights: dict, filename: str):
    output_dir = Path("data/exports/insights")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{filename}.json"
    with open(output_file, "w") as f:
        json.dump(insights, f, indent=2)
```

### CSV Export

```python
import pandas as pd

def export_insights_to_csv(insights: List[dict], filename: str):
    df = pd.DataFrame(insights)
    output_dir = Path("data/exports/insights")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{filename}.csv"
    df.to_csv(output_file, index=False)
```

## Testing

### Unit Tests

```python
# tests/test_insights/test_product_insights.py
def test_get_top_products_by_views():
    # Setup test data
    # ...
    
    results = get_top_products_by_views("template", limit=5)
    
    assert len(results) == 5
    assert results[0]["views"] >= results[1]["views"]  # Sorted descending
```

### Integration Tests

- Test z rzeczywymi danymi
- Test performance dla dużych datasetów
- Test edge cases (empty data, missing fields)

## Documentation

### Docstrings

```python
def get_pricing_analysis(product_type: str) -> Dict:
    """
    Analyze pricing distribution for a product type.
    
    Args:
        product_type: template | component | vector | plugin
    
    Returns:
        Dictionary with pricing statistics:
        - total_products: int
        - free_count: int
        - paid_count: int
        - average_price: float
        - price_distribution: dict
    
    Raises:
        ValueError: If product_type is invalid
    
    Examples:
        >>> analysis = get_pricing_analysis("template")
        >>> print(analysis["average_price"])
        25.50
    """
```

## Checklist

- [ ] Używa normalized values z models
- [ ] Obsługuje missing data gracefully
- [ ] Waliduje dane przez Pydantic models
- [ ] Error handling zaimplementowany
- [ ] Performance zoptymalizowana (cache jeśli potrzebne)
- [ ] Dokumentacja z docstrings
- [ ] Testy napisane
- [ ] Export funkcjonalności (JSON/CSV)
- [ ] Format wyników jest spójny

---

**Uwaga:** Te reguły są draftem i mogą być rozszerzone/zmodyfikowane w przyszłości.

