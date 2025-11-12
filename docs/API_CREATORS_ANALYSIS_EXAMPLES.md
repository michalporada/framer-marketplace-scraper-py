# Przykłady Analizy Danych Kreatorów

**Base URL:** `http://localhost:8000` (lokalnie) lub `https://your-api.railway.app` (produkcja)

---

## 📊 Nowy Endpoint: Analiza Wzrostu Views Produktów Kreatora

### `GET /api/creators/{username}/products-growth`

**Opis:** Analizuje wzrost views dla wszystkich produktów danego kreatora w określonym okresie.

**Path Parameters:**
- `username` (required): Username kreatora (bez `@`, np. `creator-name`)

**Query Parameters:**
- `product_type` (optional): `template | component | vector | plugin` - filtruj po typie produktu
- `period_hours` (default: 24, max: 168): Okres w godzinach do porównania (1-168, domyślnie 24h = 1 dzień)

**Response Model:** `CreatorProductsGrowthResponse`

---

## 📝 Przykłady Użycia

### Przykład 1: Wzrost views wszystkich templates kreatora w ostatnich 24h

```bash
curl "http://localhost:8000/api/creators/designer-name/products-growth?product_type=template&period_hours=24"
```

**Response:**
```json
{
  "creator_username": "designer-name",
  "creator_name": "Designer Name",
  "product_type": "template",
  "period_hours": 24,
  "total_products": 5,
  "products_with_data": 5,
  "total_views_current": 125000,
  "total_views_previous": 120000,
  "total_views_change": 5000,
  "total_views_change_percent": 4.17,
  "products": [
    {
      "product_id": "agency-template",
      "product_name": "Agency Template",
      "product_type": "template",
      "current_views": 50000,
      "previous_views": 48000,
      "views_change": 2000,
      "views_change_percent": 4.17
    },
    {
      "product_id": "portfolio-template",
      "product_name": "Portfolio Template",
      "product_type": "template",
      "current_views": 30000,
      "previous_views": 29000,
      "views_change": 1000,
      "views_change_percent": 3.45
    },
    {
      "product_id": "business-template",
      "product_name": "Business Template",
      "product_type": "template",
      "current_views": 25000,
      "previous_views": 24000,
      "views_change": 1000,
      "views_change_percent": 4.17
    },
    {
      "product_id": "blog-template",
      "product_name": "Blog Template",
      "product_type": "template",
      "current_views": 15000,
      "previous_views": 14000,
      "views_change": 1000,
      "views_change_percent": 7.14
    },
    {
      "product_id": "landing-template",
      "product_name": "Landing Template",
      "product_type": "template",
      "current_views": 5000,
      "previous_views": 5000,
      "views_change": 0,
      "views_change_percent": 0.0
    }
  ],
  "meta": {
    "timestamp": "2024-01-02T12:00:00Z",
    "period_start": "2024-01-01T12:00:00Z",
    "period_end": "2024-01-02T12:00:00Z"
  }
}
```

---

### Przykład 2: Wzrost views wszystkich produktów kreatora (wszystkie typy) w ostatnich 7 dniach

```bash
curl "http://localhost:8000/api/creators/ui-designer/products-growth?period_hours=168"
```

**Response:**
```json
{
  "creator_username": "ui-designer",
  "creator_name": "UI Designer",
  "product_type": null,
  "period_hours": 168,
  "total_products": 15,
  "products_with_data": 15,
  "total_views_current": 250000,
  "total_views_previous": 220000,
  "total_views_change": 30000,
  "total_views_change_percent": 13.64,
  "products": [
    {
      "product_id": "button-component",
      "product_name": "Button Component",
      "product_type": "component",
      "current_views": 50000,
      "previous_views": 40000,
      "views_change": 10000,
      "views_change_percent": 25.0
    },
    {
      "product_id": "card-component",
      "product_name": "Card Component",
      "product_type": "component",
      "current_views": 40000,
      "previous_views": 35000,
      "views_change": 5000,
      "views_change_percent": 14.29
    },
    {
      "product_id": "icon-pack-vector",
      "product_name": "Icon Pack Vector",
      "product_type": "vector",
      "current_views": 30000,
      "previous_views": 28000,
      "views_change": 2000,
      "views_change_percent": 7.14
    }
    // ... więcej produktów
  ],
  "meta": {
    "timestamp": "2024-01-08T12:00:00Z",
    "period_start": "2024-01-01T12:00:00Z",
    "period_end": "2024-01-08T12:00:00Z"
  }
}
```

---

### Przykład 3: Wzrost views tylko components kreatora w ostatnich 24h

```bash
curl "http://localhost:8000/api/creators/ui-designer/products-growth?product_type=component&period_hours=24"
```

**Response:**
```json
{
  "creator_username": "ui-designer",
  "creator_name": "UI Designer",
  "product_type": "component",
  "period_hours": 24,
  "total_products": 8,
  "products_with_data": 8,
  "total_views_current": 120000,
  "total_views_previous": 118000,
  "total_views_change": 2000,
  "total_views_change_percent": 1.69,
  "products": [
    {
      "product_id": "button-component",
      "product_name": "Button Component",
      "product_type": "component",
      "current_views": 50000,
      "previous_views": 49000,
      "views_change": 1000,
      "views_change_percent": 2.04
    },
    {
      "product_id": "card-component",
      "product_name": "Card Component",
      "product_type": "component",
      "current_views": 40000,
      "previous_views": 39500,
      "views_change": 500,
      "views_change_percent": 1.27
    }
    // ... więcej components
  ],
  "meta": {
    "timestamp": "2024-01-02T12:00:00Z",
    "period_start": "2024-01-01T12:00:00Z",
    "period_end": "2024-01-02T12:00:00Z"
  }
}
```

---

### Przykład 4: Wzrost views vectors kreatora w ostatnich 48h

```bash
curl "http://localhost:8000/api/creators/icon-designer/products-growth?product_type=vector&period_hours=48"
```

---

### Przykład 5: Wzrost views plugins kreatora w ostatnich 7 dniach

```bash
curl "http://localhost:8000/api/creators/plugin-developer/products-growth?product_type=plugin&period_hours=168"
```

---

## 🐍 Przykłady w Python

### Analiza wzrostu views templates kreatora

```python
import requests

username = "designer-name"
response = requests.get(
    f"http://localhost:8000/api/creators/{username}/products-growth",
    params={
        "product_type": "template",
        "period_hours": 24
    }
)

data = response.json()

print(f"Kreator: {data['creator_name']} (@{data['creator_username']})")
print(f"Typ produktów: {data['product_type'] or 'Wszystkie'}")
print(f"Okres: {data['period_hours']} godzin")
print()
print(f"📊 Statystyki:")
print(f"  Łączna liczba produktów: {data['total_products']}")
print(f"  Produkty z danymi historycznymi: {data['products_with_data']}")
print(f"  Łączne views (obecnie): {data['total_views_current']:,}")
print(f"  Łączne views (poprzednio): {data['total_views_previous']:,}")
print(f"  Zmiana views: +{data['total_views_change']:,} ({data['total_views_change_percent']:.2f}%)")
print()

print("📈 Top produkty według wzrostu views:")
for i, product in enumerate(data['products'][:5], 1):
    change_sign = "+" if product['views_change'] >= 0 else ""
    print(f"{i}. {product['product_name']}")
    print(f"   Views: {product['current_views']:,} ({change_sign}{product['views_change']:,}, {product['views_change_percent']:.2f}%)")
```

### Porównanie wzrostu views dla różnych typów produktów

```python
import requests

username = "ui-designer"
product_types = ["template", "component", "vector", "plugin"]

print(f"Analiza wzrostu views dla @{username}:")
print("=" * 60)

for product_type in product_types:
    response = requests.get(
        f"http://localhost:8000/api/creators/{username}/products-growth",
        params={
            "product_type": product_type,
            "period_hours": 24
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        change_sign = "+" if data['total_views_change'] >= 0 else ""
        print(f"\n{product_type.capitalize()}:")
        print(f"  Produkty: {data['total_products']}")
        print(f"  Zmiana views: {change_sign}{data['total_views_change']:,} ({data['total_views_change_percent']:.2f}%)")
    else:
        print(f"\n{product_type.capitalize()}: Brak danych")
```

### Znajdź kreatorów z największym wzrostem views

```python
import requests

# Pobierz listę kreatorów
creators_response = requests.get(
    "http://localhost:8000/api/creators",
    params={"limit": 100, "sort": "total_products", "order": "desc"}
)

creators = creators_response.json()["data"]

# Analizuj wzrost views dla każdego kreatora
growth_data = []

for creator in creators[:20]:  # Top 20 kreatorów
    username = creator.username
    response = requests.get(
        f"http://localhost:8000/api/creators/{username}/products-growth",
        params={"period_hours": 24}
    )
    
    if response.status_code == 200:
        data = response.json()
        growth_data.append({
            "username": username,
            "name": data["creator_name"],
            "total_views_change": data["total_views_change"],
            "total_views_change_percent": data["total_views_change_percent"],
            "total_products": data["total_products"]
        })

# Sortuj według wzrostu views
growth_data.sort(key=lambda x: x["total_views_change"], reverse=True)

print("🏆 Top kreatorzy według wzrostu views (24h):")
print("=" * 60)
for i, creator in enumerate(growth_data[:10], 1):
    change_sign = "+" if creator["total_views_change"] >= 0 else ""
    print(f"{i}. @{creator['username']} ({creator['name']})")
    print(f"   Zmiana views: {change_sign}{creator['total_views_change']:,} ({creator['total_views_change_percent']:.2f}%)")
    print(f"   Produkty: {creator['total_products']}")
    print()
```

---

## 📊 Interpretacja Wyników

### Kluczowe Metryki:

1. **`total_views_change`** - Łączna zmiana views wszystkich produktów kreatora
   - Dodatnia wartość = wzrost views
   - Ujemna wartość = spadek views

2. **`total_views_change_percent`** - Procentowa zmiana views
   - Względny wzrost/spadek w procentach

3. **`products_with_data`** - Liczba produktów z danymi historycznymi
   - Produkty, które istniały już w poprzednim okresie

4. **`products`** - Lista produktów z szczegółami wzrostu
   - Posortowane według `views_change` (malejąco)
   - Każdy produkt ma: `current_views`, `previous_views`, `views_change`, `views_change_percent`

---

## 💡 Przypadki Użycia

### 1. Analiza Performance Kreatora
```bash
# Sprawdź jak rosną views wszystkich produktów kreatora
curl "http://localhost:8000/api/creators/{username}/products-growth?period_hours=168"
```

### 2. Analiza Konkretnego Typu Produktu
```bash
# Sprawdź wzrost views tylko templates
curl "http://localhost:8000/api/creators/{username}/products-growth?product_type=template&period_hours=24"
```

### 3. Porównanie Okresów
```bash
# Porównaj wzrost w różnych okresach
curl "http://localhost:8000/api/creators/{username}/products-growth?period_hours=24"   # 1 dzień
curl "http://localhost:8000/api/creators/{username}/products-growth?period_hours=168" # 7 dni
```

### 4. Identyfikacja Najszybciej Rosnących Produktów
```python
# Produkty są automatycznie sortowane według views_change (malejąco)
# Pierwsze produkty w liście to te z największym wzrostem
```

---

## ⚠️ Uwagi

1. **Dane Historyczne:** Endpoint wymaga danych w tabeli `product_history`
   - Jeśli produkt nie miał danych w poprzednim okresie, `previous_views` = 0
   - `products_with_data` pokazuje ile produktów ma dane historyczne

2. **Okres:** Maksymalny okres to 168 godzin (7 dni)
   - Dłuższe okresy mogą nie mieć danych w `product_history`

3. **Typ Produktu:** Możesz filtrować po typie lub analizować wszystkie
   - `product_type=template` - tylko templates
   - `product_type=component` - tylko components
   - `product_type=vector` - tylko vectors
   - `product_type=plugin` - tylko plugins
   - Brak parametru - wszystkie typy

4. **Cache:** Endpoint nie jest cachowany (dane zmieniają się dynamicznie)

---

## 🔗 Powiązane Endpointy

- `GET /api/creators/{username}` - Informacje o kreatorze
- `GET /api/creators/{username}/products` - Lista produktów kreatora
- `GET /api/products/{product_id}/changes` - Zmiany pojedynczego produktu

---

*Ostatnia aktualizacja: 2024-01-01*

