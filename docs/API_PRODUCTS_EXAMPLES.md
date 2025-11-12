# Przykłady Użycia Endpointów Products - Różne Typy Produktów

**Base URL:** `http://localhost:8000` (lokalnie) lub `https://your-api.railway.app` (produkcja)

---

## 📦 Typy Produktów

Projekt obsługuje 4 typy produktów:
- **`template`** - Szablony (templates)
- **`component`** - Komponenty (components)
- **`vector`** - Wektory (vectors)
- **`plugin`** - Wtyczki (plugins)

---

## 1. Lista Produktów (`GET /api/products`)

### Przykład 1: Wszystkie templates
```bash
curl "http://localhost:8000/api/products?type=template&limit=10"
```

**Response:**
```json
{
  "data": [
    {
      "id": "agency-template",
      "name": "Agency Template",
      "type": "template",
      "category": "Agency",
      "url": "https://www.framer.com/marketplace/templates/agency-template/",
      "price": 49.0,
      "currency": "USD",
      "is_free": false,
      "stats": {
        "views": {
          "raw": "19.8K Views",
          "normalized": 19800
        },
        "pages": {
          "raw": "25 Pages",
          "normalized": 25
        }
      },
      "creator": {
        "username": "designer-name",
        "name": "Designer Name"
      }
    }
  ],
  "meta": {
    "total": 3109,
    "limit": 10,
    "offset": 0,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Przykład 2: Wszystkie components
```bash
curl "http://localhost:8000/api/products?type=component&limit=10&sort=views_normalized&order=desc"
```

**Response:**
```json
{
  "data": [
    {
      "id": "button-component",
      "name": "Button Component",
      "type": "component",
      "category": "UI Elements",
      "url": "https://www.framer.com/marketplace/components/button-component/",
      "price": 0.0,
      "currency": "USD",
      "is_free": true,
      "stats": {
        "installs": {
          "raw": "5.2K Installs",
          "normalized": 5200
        }
      },
      "creator": {
        "username": "ui-designer",
        "name": "UI Designer"
      }
    }
  ],
  "meta": {
    "total": 1500,
    "limit": 10,
    "offset": 0,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Przykład 3: Wszystkie vectors
```bash
curl "http://localhost:8000/api/products?type=vector&limit=20&offset=0"
```

**Response:**
```json
{
  "data": [
    {
      "id": "icon-pack-vector",
      "name": "Icon Pack Vector",
      "type": "vector",
      "category": "Icons",
      "url": "https://www.framer.com/marketplace/vectors/icon-pack-vector/",
      "price": 15.0,
      "currency": "USD",
      "is_free": false,
      "stats": {
        "views": {
          "raw": "8.5K Views",
          "normalized": 8500
        },
        "users": {
          "raw": "1.2K Users",
          "normalized": 1200
        },
        "vectors": {
          "raw": "100 Vectors",
          "normalized": 100
        }
      },
      "creator": {
        "username": "icon-designer",
        "name": "Icon Designer"
      }
    }
  ],
  "meta": {
    "total": 800,
    "limit": 20,
    "offset": 0,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Przykład 4: Wszystkie plugins
```bash
curl "http://localhost:8000/api/products?type=plugin&limit=10&sort=created_at&order=desc"
```

**Response:**
```json
{
  "data": [
    {
      "id": "analytics-plugin",
      "name": "Analytics Plugin",
      "type": "plugin",
      "category": "Analytics",
      "url": "https://www.framer.com/marketplace/plugins/analytics-plugin/",
      "price": 29.0,
      "currency": "USD",
      "is_free": false,
      "stats": {
        "users": {
          "raw": "3.5K Users",
          "normalized": 3500
        }
      },
      "metadata": {
        "version": "1.2.0"
      },
      "creator": {
        "username": "plugin-developer",
        "name": "Plugin Developer"
      }
    }
  ],
  "meta": {
    "total": 200,
    "limit": 10,
    "offset": 0,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Przykład 5: Wszystkie produkty (bez filtru typu)
```bash
curl "http://localhost:8000/api/products?limit=50&sort=views_normalized&order=desc"
```

**Response:** Zwraca produkty wszystkich typów, posortowane według views.

---

## 2. Pojedynczy Produkt (`GET /api/products/{product_id}`)

### Przykład 1: Template
```bash
curl "http://localhost:8000/api/products/agency-template"
```

**Response:**
```json
{
  "data": {
    "id": "agency-template",
    "name": "Agency Template",
    "type": "template",
    "category": "Agency",
    "url": "https://www.framer.com/marketplace/templates/agency-template/",
    "price": 49.0,
    "currency": "USD",
    "is_free": false,
    "description": "Professional agency template with modern design...",
    "short_description": "Agency template for modern businesses",
    "stats": {
      "views": {
        "raw": "19.8K Views",
        "normalized": 19800
      },
      "pages": {
        "raw": "25 Pages",
        "normalized": 25
      }
    },
    "metadata": {
      "published_date": {
        "raw": "6 months ago",
        "normalized": "2023-07-01T00:00:00Z"
      },
      "last_updated": {
        "raw": "2 weeks ago",
        "normalized": "2023-12-15T00:00:00Z"
      }
    },
    "features": {
      "features": ["Responsive", "CMS Integration", "Animations"],
      "is_responsive": true,
      "has_animations": true,
      "cms_integration": true,
      "pages_count": 25
    },
    "media": {
      "thumbnail": "https://framerusercontent.com/..."
    },
    "creator": {
      "username": "designer-name",
      "name": "Designer Name",
      "profile_url": "https://www.framer.com/@designer-name/"
    }
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Przykład 2: Component
```bash
curl "http://localhost:8000/api/products/button-component"
```

**Response:**
```json
{
  "data": {
    "id": "button-component",
    "name": "Button Component",
    "type": "component",
    "category": "UI Elements",
    "url": "https://www.framer.com/marketplace/components/button-component/",
    "price": 0.0,
    "currency": "USD",
    "is_free": true,
    "stats": {
      "installs": {
        "raw": "5.2K Installs",
        "normalized": 5200
      }
    },
    "creator": {
      "username": "ui-designer",
      "name": "UI Designer"
    }
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Przykład 3: Vector
```bash
curl "http://localhost:8000/api/products/icon-pack-vector"
```

**Response:**
```json
{
  "data": {
    "id": "icon-pack-vector",
    "name": "Icon Pack Vector",
    "type": "vector",
    "category": "Icons",
    "url": "https://www.framer.com/marketplace/vectors/icon-pack-vector/",
    "price": 15.0,
    "currency": "USD",
    "is_free": false,
    "stats": {
      "views": {
        "raw": "8.5K Views",
        "normalized": 8500
      },
      "users": {
        "raw": "1.2K Users",
        "normalized": 1200
      },
      "vectors": {
        "raw": "100 Vectors",
        "normalized": 100
      }
    },
    "creator": {
      "username": "icon-designer",
      "name": "Icon Designer"
    }
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Przykład 4: Plugin
```bash
curl "http://localhost:8000/api/products/analytics-plugin"
```

**Response:**
```json
{
  "data": {
    "id": "analytics-plugin",
    "name": "Analytics Plugin",
    "type": "plugin",
    "category": "Analytics",
    "url": "https://www.framer.com/marketplace/plugins/analytics-plugin/",
    "price": 29.0,
    "currency": "USD",
    "is_free": false,
    "stats": {
      "users": {
        "raw": "3.5K Users",
        "normalized": 3500
      }
    },
    "metadata": {
      "version": "1.2.0",
      "published_date": {
        "raw": "3 months ago",
        "normalized": "2023-10-01T00:00:00Z"
      }
    },
    "creator": {
      "username": "plugin-developer",
      "name": "Plugin Developer"
    }
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

## 3. Zmiany Produktu (`GET /api/products/{product_id}/changes`)

### Przykład: Template - zmiany w czasie
```bash
curl "http://localhost:8000/api/products/agency-template/changes"
```

**Response:**
```json
{
  "product_id": "agency-template",
  "versions": [
    {
      "scraped_at": "2024-01-02T00:00:00Z",
      "source_path": "database",
      "stats": {
        "views": {
          "raw": "19.8K Views",
          "normalized": 19800
        },
        "pages": {
          "raw": "25 Pages",
          "normalized": 25
        }
      },
      "price": 49.0,
      "metadata": {
        "version": null,
        "last_updated": {
          "normalized": "2023-12-15T00:00:00Z"
        }
      }
    },
    {
      "scraped_at": "2024-01-01T00:00:00Z",
      "source_path": "database",
      "stats": {
        "views": {
          "raw": "19.5K Views",
          "normalized": 19500
        },
        "pages": {
          "raw": "25 Pages",
          "normalized": 25
        }
      },
      "price": 49.0,
      "metadata": {
        "version": null,
        "last_updated": {
          "normalized": "2023-12-15T00:00:00Z"
        }
      }
    }
  ],
  "changes": [
    {
      "field": "stats.views",
      "old_value": 19500,
      "new_value": 19800,
      "change_type": "changed"
    }
  ],
  "meta": {
    "timestamp": "2024-01-02T00:00:00Z"
  }
}
```

---

## 4. Porównanie Kategorii (`GET /api/products/categories/comparison`)

### Przykład 1: Wszystkie kategorie dla templates
```bash
curl "http://localhost:8000/api/products/categories/comparison?product_type=template"
```

**Response:**
```json
{
  "data": [
    {
      "category": "Agency",
      "scrap_1_date": "2024-01-01",
      "scrap_2_date": "2024-01-02",
      "products_count_1": 150,
      "products_count_2": 152,
      "total_views_1": 500000,
      "total_views_2": 520000,
      "views_change": 20000,
      "views_change_percent": 4.0
    },
    {
      "category": "Portfolio",
      "scrap_1_date": "2024-01-01",
      "scrap_2_date": "2024-01-02",
      "products_count_1": 200,
      "products_count_2": 205,
      "total_views_1": 800000,
      "total_views_2": 850000,
      "views_change": 50000,
      "views_change_percent": 6.25
    }
  ],
  "meta": {
    "timestamp": "2024-01-02T00:00:00Z",
    "total_categories": 20
  }
}
```

### Przykład 2: Konkretna kategoria dla components
```bash
curl "http://localhost:8000/api/products/categories/comparison?product_type=component&category=UI%20Elements"
```

**Response:**
```json
{
  "data": [
    {
      "category": "UI Elements",
      "scrap_1_date": "2024-01-01",
      "scrap_2_date": "2024-01-02",
      "products_count_1": 300,
      "products_count_2": 305,
      "total_views_1": 200000,
      "total_views_2": 210000,
      "views_change": 10000,
      "views_change_percent": 5.0
    }
  ],
  "meta": {
    "timestamp": "2024-01-02T00:00:00Z",
    "total_categories": 1
  }
}
```

### Przykład 3: Wszystkie kategorie dla vectors
```bash
curl "http://localhost:8000/api/products/categories/comparison?product_type=vector"
```

### Przykład 4: Wszystkie kategorie dla plugins
```bash
curl "http://localhost:8000/api/products/categories/comparison?product_type=plugin"
```

---

## 5. Zmiana Views w 24h (`GET /api/products/views-change-24h`)

### Przykład 1: Templates
```bash
curl "http://localhost:8000/api/products/views-change-24h?product_type=template"
```

**Response:**
```json
{
  "product_type": "template",
  "total_views_change": 86304,
  "products_count": 3109,
  "products_with_changes": 748,
  "meta": {
    "timestamp": "2024-01-02T12:00:00Z",
    "period_start": "2024-01-01T12:00:00Z",
    "period_end": "2024-01-02T12:00:00Z"
  }
}
```

### Przykład 2: Components
```bash
curl "http://localhost:8000/api/products/views-change-24h?product_type=component"
```

**Response:**
```json
{
  "product_type": "component",
  "total_views_change": 45230,
  "products_count": 1500,
  "products_with_changes": 320,
  "meta": {
    "timestamp": "2024-01-02T12:00:00Z",
    "period_start": "2024-01-01T12:00:00Z",
    "period_end": "2024-01-02T12:00:00Z"
  }
}
```

### Przykład 3: Vectors
```bash
curl "http://localhost:8000/api/products/views-change-24h?product_type=vector"
```

**Response:**
```json
{
  "product_type": "vector",
  "total_views_change": 12340,
  "products_count": 800,
  "products_with_changes": 150,
  "meta": {
    "timestamp": "2024-01-02T12:00:00Z",
    "period_start": "2024-01-01T12:00:00Z",
    "period_end": "2024-01-02T12:00:00Z"
  }
}
```

### Przykład 4: Plugins
```bash
curl "http://localhost:8000/api/products/views-change-24h?product_type=plugin"
```

**Response:**
```json
{
  "product_type": "plugin",
  "total_views_change": 5670,
  "products_count": 200,
  "products_with_changes": 45,
  "meta": {
    "timestamp": "2024-01-02T12:00:00Z",
    "period_start": "2024-01-01T12:00:00Z",
    "period_end": "2024-01-02T12:00:00Z"
  }
}
```

---

## 📊 Różnice Między Typami Produktów

### Templates
- **Statystyki:** `views`, `pages`
- **Cena:** Często płatne (49-199 USD)
- **Kategorie:** Agency, Portfolio, Business, etc.
- **Features:** `pages_count`, `is_responsive`, `has_animations`, `cms_integration`

### Components
- **Statystyki:** `installs` (główna metryka)
- **Cena:** Często darmowe (0 USD)
- **Kategorie:** UI Elements, Navigation, Forms, etc.
- **Features:** `is_responsive`, `has_animations`

### Vectors
- **Statystyki:** `views`, `users`, `vectors` (count)
- **Cena:** Zazwyczaj płatne (5-50 USD)
- **Kategorie:** Icons, Illustrations, Graphics, etc.
- **Features:** `vectors` count (liczba wektorów w pakiecie)

### Plugins
- **Statystyki:** `users` (główna metryka)
- **Cena:** Często płatne (19-99 USD)
- **Kategorie:** Analytics, SEO, Marketing, etc.
- **Features:** `version` (wersja pluginu)

---

## 🔍 Przykłady Zaawansowanych Zapytań

### Top 10 templates według views
```bash
curl "http://localhost:8000/api/products?type=template&limit=10&sort=views_normalized&order=desc"
```

### Najnowsze components
```bash
curl "http://localhost:8000/api/products?type=component&limit=20&sort=created_at&order=desc"
```

### Darmowe vectors
```bash
curl "http://localhost:8000/api/products?type=vector&limit=50&sort=views_normalized&order=desc"
# Następnie filtruj po is_free=true w aplikacji
```

### Plugins z największą liczbą użytkowników
```bash
curl "http://localhost:8000/api/products?type=plugin&limit=10&sort=users_normalized&order=desc"
```

### Paginacja - strona 2 (produkty 101-200)
```bash
curl "http://localhost:8000/api/products?type=template&limit=100&offset=100"
```

---

## 🐍 Przykłady w Python

### Pobierz wszystkie templates
```python
import requests

response = requests.get(
    "http://localhost:8000/api/products",
    params={
        "type": "template",
        "limit": 100,
        "offset": 0,
        "sort": "views_normalized",
        "order": "desc"
    }
)

data = response.json()
templates = data["data"]
total = data["meta"]["total"]

print(f"Znaleziono {total} templates")
for template in templates:
    print(f"- {template['name']}: {template['stats']['views']['normalized']} views")
```

### Sprawdź zmianę views dla wszystkich typów
```python
import requests

base_url = "http://localhost:8000/api/products/views-change-24h"

for product_type in ["template", "component", "vector", "plugin"]:
    response = requests.get(base_url, params={"product_type": product_type})
    data = response.json()
    
    print(f"{product_type.capitalize()}:")
    print(f"  Zmiana views: +{data['total_views_change']:,}")
    print(f"  Produktów: {data['products_count']}")
    print(f"  Ze zmianami: {data['products_with_changes']}")
    print()
```

### Porównaj kategorie dla templates
```python
import requests

response = requests.get(
    "http://localhost:8000/api/products/categories/comparison",
    params={"product_type": "template"}
)

data = response.json()
categories = data["data"]

# Sortuj według zmiany views
categories.sort(key=lambda x: x["views_change"], reverse=True)

print("Top kategorie według wzrostu views:")
for cat in categories[:10]:
    print(f"{cat['category']}: +{cat['views_change']:,} views ({cat['views_change_percent']:.1f}%)")
```

---

## 📝 Uwagi

1. **Cache:** Większość endpointów jest cachowana (TTL: 5 minut)
2. **Paginacja:** Domyślny limit: 100, maksymalny: 1000
3. **Sortowanie:** Domyślnie `created_at desc`
4. **Type Safety:** Wszystkie parametry są walidowane przez Pydantic
5. **Error Handling:** Wszystkie błędy zwracają strukturalne odpowiedzi

---

*Ostatnia aktualizacja: 2024-01-01*

