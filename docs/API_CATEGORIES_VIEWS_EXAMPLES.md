# Przykłady: Sprawdzanie Views Kategorii

**Base URL:** `http://localhost:8000` (lokalnie) lub `https://your-api.railway.app` (produkcja)

---

## 📊 Nowy Endpoint: Views Kategorii

### `GET /api/products/categories/{category_name}/views`

**Opis:** Zwraca aktualną liczbę views i statystyki dla danej kategorii.

**Path Parameters:**
- `category_name` (required): Nazwa kategorii (np. `Agency`, `Portfolio`, `Business`)

**Query Parameters:**
- `product_type` (optional): `template | component | vector | plugin` - filtruj po typie produktu
- `include_products` (default: `false`): Czy dołączyć listę produktów w odpowiedzi
- `limit` (default: 100, max: 1000): Maksymalna liczba produktów do zwrócenia (jeśli `include_products=true`)

**Response Model:** `CategoryViewsResponse`

**Cache:** ✅ 5 minut (TTL: 300s)

---

## 📝 Przykłady Użycia

### Przykład 1: Views kategorii "Agency" dla templates

```bash
curl "http://localhost:8000/api/products/categories/Agency/views?product_type=template"
```

**Response:**
```json
{
  "category": "Agency",
  "product_type": "template",
  "total_views": 9105358,
  "products_count": 775,
  "average_views_per_product": 11748.85,
  "free_products_count": 291,
  "paid_products_count": 484,
  "products": [],
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Interpretacja:**
- Kategoria "Agency" ma **9,105,358 views** w templates
- Jest **775 produktów** w tej kategorii
- Średnio **11,748.85 views** na produkt
- **291 darmowych** i **484 płatnych** produktów

---

### Przykład 2: Views kategorii "Portfolio" (wszystkie typy produktów)

```bash
curl "http://localhost:8000/api/products/categories/Portfolio/views"
```

**Response:**
```json
{
  "category": "Portfolio",
  "product_type": null,
  "total_views": 15234567,
  "products_count": 1200,
  "average_views_per_product": 12695.47,
  "free_products_count": 450,
  "paid_products_count": 750,
  "products": [],
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

### Przykład 3: Views kategorii "UI Elements" dla components z listą produktów

```bash
curl "http://localhost:8000/api/products/categories/UI%20Elements/views?product_type=component&include_products=true&limit=10"
```

**Response:**
```json
{
  "category": "UI Elements",
  "product_type": "component",
  "total_views": 3456789,
  "products_count": 500,
  "average_views_per_product": 6913.58,
  "free_products_count": 400,
  "paid_products_count": 100,
  "products": [
    {
      "id": "button-component",
      "name": "Button Component",
      "type": "component",
      "views": 50000,
      "is_free": true,
      "price": null
    },
    {
      "id": "card-component",
      "name": "Card Component",
      "type": "component",
      "views": 45000,
      "is_free": true,
      "price": null
    },
    {
      "id": "form-component",
      "name": "Form Component",
      "type": "component",
      "views": 40000,
      "is_free": false,
      "price": 19.0
    }
    // ... więcej produktów (posortowane według views DESC)
  ],
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

### Przykład 4: Views kategorii "Icons" dla vectors

```bash
curl "http://localhost:8000/api/products/categories/Icons/views?product_type=vector"
```

**Response:**
```json
{
  "category": "Icons",
  "product_type": "vector",
  "total_views": 1234567,
  "products_count": 200,
  "average_views_per_product": 6172.84,
  "free_products_count": 50,
  "paid_products_count": 150,
  "products": [],
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

### Przykład 5: Views kategorii "Analytics" dla plugins

```bash
curl "http://localhost:8000/api/products/categories/Analytics/views?product_type=plugin"
```

---

### Przykład 6: Views kategorii z listą top produktów

```bash
curl "http://localhost:8000/api/products/categories/Agency/views?product_type=template&include_products=true&limit=20"
```

**Response:** Zwraca top 20 produktów w kategorii posortowanych według views (malejąco).

---

## 🐍 Przykłady w Python

### Sprawdź views dla kategorii

```python
import requests

category = "Agency"
product_type = "template"

response = requests.get(
    f"http://localhost:8000/api/products/categories/{category}/views",
    params={"product_type": product_type}
)

data = response.json()

print(f"📊 Kategoria: {data['category']}")
print(f"Typ produktów: {data['product_type'] or 'Wszystkie'}")
print()
print(f"Łączne views: {data['total_views']:,}")
print(f"Liczba produktów: {data['products_count']:,}")
print(f"Średnia views na produkt: {data['average_views_per_product']:,.2f}")
print(f"Darmowe produkty: {data['free_products_count']}")
print(f"Płatne produkty: {data['paid_products_count']}")
```

### Porównaj views różnych kategorii

```python
import requests

categories = ["Agency", "Portfolio", "Business", "E-commerce"]
product_type = "template"

print("📊 Porównanie views kategorii (templates):")
print("=" * 60)

for category in categories:
    response = requests.get(
        f"http://localhost:8000/api/products/categories/{category}/views",
        params={"product_type": product_type}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n{category}:")
        print(f"  Views: {data['total_views']:,}")
        print(f"  Produkty: {data['products_count']}")
        print(f"  Średnia: {data['average_views_per_product']:,.2f}")
    else:
        print(f"\n{category}: Nie znaleziono")
```

### Znajdź top kategorie według views

```python
import requests

# Najpierw pobierz wszystkie kategorie z comparison endpoint
response = requests.get(
    "http://localhost:8000/api/products/categories/comparison",
    params={"product_type": "template"}
)

comparisons = response.json()["data"]

# Pobierz szczegóły views dla każdej kategorii
category_stats = []

for comp in comparisons:
    category = comp["category"]
    views_response = requests.get(
        f"http://localhost:8000/api/products/categories/{category}/views",
        params={"product_type": "template"}
    )
    
    if views_response.status_code == 200:
        views_data = views_response.json()
        category_stats.append({
            "category": category,
            "total_views": views_data["total_views"],
            "products_count": views_data["products_count"],
            "average_views": views_data["average_views_per_product"]
        })

# Sortuj według total_views
category_stats.sort(key=lambda x: x["total_views"], reverse=True)

print("🏆 Top kategorie według views:")
print("=" * 60)
for i, cat in enumerate(category_stats[:10], 1):
    print(f"{i}. {cat['category']}")
    print(f"   Views: {cat['total_views']:,}")
    print(f"   Produkty: {cat['products_count']}")
    print(f"   Średnia: {cat['average_views']:,.2f}")
    print()
```

### Pobierz top produkty w kategorii

```python
import requests

category = "Agency"
product_type = "template"

response = requests.get(
    f"http://localhost:8000/api/products/categories/{category}/views",
    params={
        "product_type": product_type,
        "include_products": True,
        "limit": 10
    }
)

data = response.json()

print(f"📊 Top 10 produktów w kategorii '{category}':")
print("=" * 60)

for i, product in enumerate(data["products"], 1):
    price_info = "Darmowy" if product["is_free"] else f"${product['price']}"
    print(f"{i}. {product['name']}")
    print(f"   Views: {product['views']:,}")
    print(f"   Cena: {price_info}")
    print()
```

---

## 📊 Interpretacja Wyników

### Kluczowe Metryki:

1. **`total_views`** - Łączna liczba views wszystkich produktów w kategorii
   - Suma views wszystkich produktów

2. **`products_count`** - Liczba produktów w kategorii
   - Produkty z views (nie NULL)

3. **`average_views_per_product`** - Średnia views na produkt
   - `total_views / products_count`

4. **`free_products_count`** - Liczba darmowych produktów
   - Produkty z `is_free = true`

5. **`paid_products_count`** - Liczba płatnych produktów
   - Produkty z `is_free = false`

6. **`products`** - Lista produktów (opcjonalnie)
   - Tylko jeśli `include_products=true`
   - Posortowane według views (malejąco)
   - Limitowane przez parametr `limit`

---

## 💡 Przypadki Użycia

### 1. Sprawdź popularność kategorii
```bash
# Sprawdź ile views ma kategoria "Agency" w templates
curl "http://localhost:8000/api/products/categories/Agency/views?product_type=template"
```

### 2. Porównaj kategorie
```python
# Porównaj views różnych kategorii
categories = ["Agency", "Portfolio", "Business"]
for cat in categories:
    # Pobierz views dla każdej kategorii
```

### 3. Znajdź top produkty w kategorii
```bash
# Pobierz top 20 produktów w kategorii
curl "http://localhost:8000/api/products/categories/Agency/views?include_products=true&limit=20"
```

### 4. Analiza free vs paid
```python
# Sprawdź rozkład free/paid w kategorii
data = requests.get(".../categories/Agency/views").json()
print(f"Free: {data['free_products_count']}")
print(f"Paid: {data['paid_products_count']}")
```

---

## 🔗 Powiązane Endpointy

- `GET /api/products/categories/comparison` - Porównanie kategorii między scrapami
- `GET /api/products?category=Agency` - Lista produktów w kategorii
- `GET /api/products/views-change-24h` - Zmiana views dla typu produktu

---

## ⚠️ Uwagi

1. **Nazwa kategorii:** Musi być dokładnie taka sama jak w bazie danych
   - Użyj URL encoding dla spacji (np. `UI%20Elements`)
   - Sprawdź dostępne kategorie przez `/api/products/categories/comparison`

2. **Filtrowanie:** Możesz filtrować po typie produktu lub analizować wszystkie
   - `product_type=template` - tylko templates
   - Brak parametru - wszystkie typy

3. **Lista produktów:** Domyślnie nie jest zwracana (dla wydajności)
   - Ustaw `include_products=true` aby otrzymać listę
   - Produkty są posortowane według views (malejąco)

4. **Cache:** Endpoint jest cachowany (TTL: 5 minut)

---

*Ostatnia aktualizacja: 2024-01-01*

