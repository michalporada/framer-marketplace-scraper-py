# Lista Wszystkich Endpointów API

**Base URL:** `http://localhost:8000` (lokalnie) lub `https://your-api.railway.app` (produkcja)

**Dokumentacja:** `/docs` (Swagger UI) lub `/redoc` (ReDoc)

---

## 📋 Root & Health

### `GET /`
**Opis:** Root endpoint - informacje o API

**Response:**
```json
{
  "message": "Framer Marketplace Scraper API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### `GET /health`
**Opis:** Health check endpoint - sprawdza status API i bazy danych

**Response:**
```json
{
  "status": "healthy",
  "database": "configured|not_configured",
  "database_test": "connected (value: 1)|error|no_engine"
}
```

---

## 📦 Products (`/api/products`)

### `GET /api/products`
**Opis:** Lista produktów z paginacją i filtrowaniem

**Query Parameters:**
- `type` (optional): `template | component | vector | plugin`
- `limit` (default: 100, max: 1000): Liczba produktów do zwrócenia
- `offset` (default: 0): Liczba produktów do pominięcia
- `sort` (default: `created_at`): `created_at | updated_at | scraped_at | views_normalized | name`
- `order` (default: `desc`): `asc | desc`

**Response Model:** `ProductListResponse`
```json
{
  "data": [Product, ...],
  "meta": {
    "total": 1000,
    "limit": 100,
    "offset": 0,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Cache:** ✅ 5 minut (TTL: 300s)

---

### `GET /api/products/{product_id}`
**Opis:** Pojedynczy produkt po ID

**Path Parameters:**
- `product_id` (required): ID produktu (np. `template-name`)

**Response Model:** `ProductResponse`
```json
{
  "data": Product,
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Cache:** ✅ 5 minut (TTL: 300s)

**Error Codes:**
- `404`: `PRODUCT_NOT_FOUND`

---

### `GET /api/products/{product_id}/changes`
**Opis:** Porównuje dane produktu między różnymi scrapami - wykrywa zmiany w statystykach, cenie i metadanych

**Path Parameters:**
- `product_id` (required): ID produktu

**Response Model:** `ProductChangesResponse`
```json
{
  "product_id": "template-name",
  "versions": [
    {
      "scraped_at": "2024-01-01T00:00:00Z",
      "source_path": "database",
      "stats": {...},
      "price": 25.0,
      "metadata": {...}
    }
  ],
  "changes": [
    {
      "field": "stats.views",
      "old_value": 1000,
      "new_value": 1500,
      "change_type": "changed"
    }
  ],
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Data Source:** `product_history` table (priorytet), JSON files (fallback)

**Cache:** ✅ 10 minut (TTL: 600s)

**Error Codes:**
- `404`: `PRODUCT_NOT_FOUND`

---

### `GET /api/products/categories/comparison`
**Opis:** Porównuje trendy kategorii między scrapami - łączna liczba views z procentowym wzrostem/spadkiem

**Uwaga:** Endpoint używa automatycznego mapowania kategorii - produkty z podkategorii (np. "Education") są liczone również w nadrzędnych kategoriach (np. "Community"). Więcej informacji: [CATEGORY_MAPPING.md](./CATEGORY_MAPPING.md)

**Query Parameters:**
- `product_type` (optional): `template | component | vector | plugin`
- `category` (optional): Nazwa kategorii (np. `Agency`)

**Response Model:** `CategoryComparisonResponse`
```json
{
  "data": [
    {
      "category": "Agency",
      "scrap_1_date": "2024-01-01",
      "scrap_2_date": "2024-01-02",
      "products_count_1": 100,
      "products_count_2": 105,
      "total_views_1": 50000,
      "total_views_2": 55000,
      "views_change": 5000,
      "views_change_percent": 10.0
    }
  ],
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "total_categories": 10
  }
}
```

**Data Source:** JSON files (porównuje najnowszy scrape z poprzednim)

---

### `GET /api/products/categories/{category_name}/views`
**Opis:** Zwraca aktualną liczbę views i statystyki dla danej kategorii

**Uwaga:** Endpoint używa automatycznego mapowania kategorii - produkty z podkategorii (np. "Education") są liczone również w nadrzędnych kategoriach (np. "Community"). Więcej informacji: [CATEGORY_MAPPING.md](./CATEGORY_MAPPING.md)

**Path Parameters:**
- `category_name` (required): Nazwa kategorii (np. `Agency`, `Portfolio`)

**Query Parameters:**
- `product_type` (optional): `template | component | vector | plugin`
- `include_products` (default: `false`): Czy dołączyć listę produktów w odpowiedzi
- `limit` (default: 100, max: 1000): Maksymalna liczba produktów (jeśli `include_products=true`)

**Response Model:** `CategoryViewsResponse`
```json
{
  "category": "Agency",
  "product_type": "template",
  "total_views": 9105358,
  "products_count": 775,
  "average_views_per_product": 11748.85,
  "free_products_count": 291,
  "paid_products_count": 484,
  "products": [
    {
      "id": "portfolite",
      "name": "Portfolite",
      "type": "template",
      "views": 202000,
      "is_free": false,
      "price": 79.0
    }
  ],
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Cache:** ✅ 5 minut (TTL: 300s)

**Error Codes:**
- `404`: `CATEGORY_NOT_FOUND`
- `422`: `INVALID_PRODUCT_TYPE`

---

### `GET /api/products/categories/top-by-views`
**Opis:** Zwraca top kategorie według łącznej liczby views z procentową zmianą w określonym okresie

**Uwaga:** Endpoint używa automatycznego mapowania kategorii - produkty z podkategorii (np. "Education") są liczone również w nadrzędnych kategoriach (np. "Community"). Więcej informacji: [CATEGORY_MAPPING.md](./CATEGORY_MAPPING.md)

**Query Parameters:**
- `limit` (default: 10, max: 100): Liczba kategorii do zwrócenia
- `period_hours` (default: 24, max: 168): Okres w godzinach do porównania dla % zmiany
- `product_type` (optional): `template | component | vector | plugin`

**Response Model:** `TopCategoriesByViewsResponse`
```json
{
  "data": [
    {
      "category_name": "Business",
      "products_count": 2112,
      "total_views": 20455279,
      "views_change_percent": 2.5
    }
  ],
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "total_categories": 10
  }
}
```

**Cache:** ✅ 5 minut (TTL: 300s)

**Data Source:** JSON files (dla aktualnych liczb produktów) + `product_history` table (dla obliczenia % zmiany)

**Error Codes:**
- `422`: `INVALID_PRODUCT_TYPE`

---

### `GET /api/products/categories/all-by-count`
**Opis:** Zwraca wszystkie kategorie posortowane według liczby produktów (rosnąco)

**Uwaga:** Endpoint używa automatycznego mapowania kategorii - produkty z podkategorii (np. "Education") są liczone również w nadrzędnych kategoriach (np. "Community"). Więcej informacji: [CATEGORY_MAPPING.md](./CATEGORY_MAPPING.md)

**Query Parameters:**
- `limit` (default: 100, max: 1000): Liczba kategorii do zwrócenia
- `product_type` (default: `template`): `template | component | vector | plugin`

**Response Model:** `TopCategoriesByViewsResponse`
```json
{
  "data": [
    {
      "category_name": "Travel",
      "products_count": 17,
      "total_views": 101678,
      "views_change_percent": null
    },
    {
      "category_name": "Health",
      "products_count": 106,
      "total_views": 672200,
      "views_change_percent": null
    }
  ],
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "total_categories": 106
  }
}
```

**Cache:** ✅ 5 minut (TTL: 300s)

**Data Source:** JSON files (dla aktualnych liczb produktów) lub baza danych (fallback)

**Error Codes:**
- `422`: `INVALID_PRODUCT_TYPE`

---

### `GET /api/products/views-change-24h`
**Opis:** Oblicza łączną zmianę views dla wszystkich produktów danego typu w ostatnich 24 godzinach

**Query Parameters:**
- `product_type` (default: `template`): `template | component | vector | plugin`

**Response Model:** `ViewsChange24hResponse`
```json
{
  "product_type": "template",
  "total_views_change": 86304,
  "products_count": 3109,
  "products_with_changes": 748,
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "period_start": "2024-01-01T00:00:00Z",
    "period_end": "2024-01-02T00:00:00Z"
  }
}
```

**Data Source:** `product_history` table (porównuje najnowszy scrape z scrape sprzed 24h)

**Error Codes:**
- `422`: `INVALID_PRODUCT_TYPE`
- `503`: `DATABASE_NOT_AVAILABLE`
- `500`: `INTERNAL_ERROR`

---

## 👤 Creators (`/api/creators`)

### `GET /api/creators`
**Opis:** Lista twórców z paginacją i sortowaniem

**Query Parameters:**
- `limit` (default: 100, max: 1000): Liczba twórców do zwrócenia
- `offset` (default: 0): Liczba twórców do pominięcia
- `sort` (default: `username`): `username | products_count`
- `order` (default: `asc`): `asc | desc`

**Response Model:** `CreatorListResponse`
```json
{
  "data": [Creator, ...],
  "meta": {
    "total": 500,
    "limit": 100,
    "offset": 0,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Cache:** ✅ 5 minut (TTL: 300s)

---

### `GET /api/creators/{username}`
**Opis:** Pojedynczy twórca po username

**Path Parameters:**
- `username` (required): Username twórcy (bez `@`, np. `creator-name`)

**Response Model:** `CreatorResponse`
```json
{
  "data": Creator,
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Cache:** ✅ 5 minut (TTL: 300s)

**Error Codes:**
- `404`: `CREATOR_NOT_FOUND`

---

### `GET /api/creators/{username}/products`
**Opis:** Lista produktów danego twórcy

**Path Parameters:**
- `username` (required): Username twórcy

**Query Parameters:**
- `type` (optional): `template | component | vector | plugin`
- `limit` (default: 100, max: 1000): Liczba produktów do zwrócenia
- `offset` (default: 0): Liczba produktów do pominięcia

**Response:** `dict`
```json
{
  "data": [Product, ...],
  "meta": {
    "total": 50,
    "limit": 100,
    "offset": 0,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Cache:** ✅ 5 minut (TTL: 300s)

**Error Codes:**
- `404`: `CREATOR_NOT_FOUND`

---

### `GET /api/creators/{username}/products-growth`
**Opis:** Analizuje wzrost views dla wszystkich produktów danego kreatora w określonym okresie

**Path Parameters:**
- `username` (required): Username kreatora (bez `@`, np. `creator-name`)

**Query Parameters:**
- `product_type` (optional): `template | component | vector | plugin` - filtruj po typie produktu
- `period_hours` (default: 24, max: 168): Okres w godzinach do porównania (1-168, domyślnie 24h = 1 dzień)

**Response Model:** `CreatorProductsGrowthResponse`
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
    }
  ],
  "meta": {
    "timestamp": "2024-01-02T12:00:00Z",
    "period_start": "2024-01-01T12:00:00Z",
    "period_end": "2024-01-02T12:00:00Z"
  }
}
```

**Data Source:** `product_history` table (porównuje najnowszy scrape z scrape sprzed okresu)

**Error Codes:**
- `404`: `CREATOR_NOT_FOUND`
- `422`: `INVALID_PRODUCT_TYPE`
- `503`: `DATABASE_NOT_AVAILABLE`
- `500`: `INTERNAL_ERROR`

---

## 📊 Metrics (`/api/metrics`)

### `GET /api/metrics/summary`
**Opis:** Aktualne metryki scrapera (liczba scrapowanych produktów, czas, success rate)

**Response Model:** `MetricsSummaryResponse`
```json
{
  "duration_seconds": 3600,
  "duration_formatted": "1h 0m 0s",
  "start_time": "2024-01-01T00:00:00Z",
  "end_time": "2024-01-01T01:00:00Z",
  "products": {
    "scraped": 1000,
    "failed": 10,
    "total": 1010,
    "success_rate": 0.99,
    "per_second": 0.28
  },
  "creators": {
    "scraped": 500,
    "failed": 5,
    "total": 505
  },
  "categories": {
    "scraped": 50,
    "failed": 0,
    "total": 50
  },
  "requests": {
    "total": 1500,
    "total_wait_time": 750.0,
    "average_wait_time": 0.5
  },
  "retries": {
    "total": 20
  },
  "errors": {
    "by_type": {
      "TimeoutError": 5,
      "HTTPError": 5
    },
    "total_unique_urls_failed": 10
  }
}
```

**Data Source:** `src/utils/metrics.py` (singleton)

---

### `GET /api/metrics/history`
**Opis:** Historyczne metryki z pliku `metrics.log` z paginacją

**Query Parameters:**
- `limit` (default: 50, max: 1000): Liczba wpisów do zwrócenia
- `offset` (default: 0): Liczba wpisów do pominięcia

**Response Model:** `MetricsHistoryResponse`
```json
{
  "data": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "metrics": {...}
    }
  ],
  "meta": {
    "total": 100,
    "limit": 50,
    "offset": 0,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Data Source:** `logs/metrics.log` (jeśli istnieje)

**Error Codes:**
- `404`: `METRICS_FILE_NOT_FOUND`

---

### `GET /api/metrics/stats`
**Opis:** Połączone statystyki: metryki scrapera, cache stats i database stats

**Response:** `dict`
```json
{
  "metrics": {
    "duration_seconds": 3600,
    "products": {...},
    "creators": {...},
    "categories": {...},
    "requests": {...},
    "retries": {...},
    "errors": {...}
  },
  "cache": {
    "product_cache": {
      "size": 100,
      "max_size": 1000,
      "ttl": 300,
      "hits": 500,
      "misses": 200
    },
    "creator_cache": {...}
  },
  "database": {
    "products": 1000,
    "creators": 500,
    "product_history": 5000
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Data Source:** 
- Metrics: `src/utils/metrics.py`
- Cache: `api/cache.py`
- Database: `products`, `creators`, `product_history` tables

---

## 🔧 Cache Management

### `GET /cache/stats`
**Opis:** Statystyki cache (rozmiar, TTL, hit rate)

**Response:** `dict`
```json
{
  "product_cache": {
    "size": 100,
    "max_size": 1000,
    "ttl": 300,
    "hits": 500,
    "misses": 200,
    "hit_rate": 0.71
  },
  "creator_cache": {
    "size": 50,
    "max_size": 500,
    "ttl": 300,
    "hits": 200,
    "misses": 100,
    "hit_rate": 0.67
  }
}
```

**Data Source:** `api/cache.py`

---

### `POST /cache/invalidate`
**Opis:** Czyści cache (product, creator lub wszystkie)

**Query Parameters:**
- `cache_type` (optional): `product | creator | None` (None = wszystkie)

**Response:** `dict`
```json
{
  "message": "Product cache invalidated",
  "cache_type": "product"
}
```

**Przykłady:**
- `POST /cache/invalidate?cache_type=product` - czyści cache produktów
- `POST /cache/invalidate?cache_type=creator` - czyści cache twórców
- `POST /cache/invalidate` - czyści wszystkie cache

---

## 📝 Podsumowanie

### Statystyki:
- **Łącznie endpointów:** 22
- **Products:** 7 endpointów
- **Creators:** 4 endpointy (w tym 1 nowy: products-growth)
- **Metrics:** 3 endpointy
- **Cache:** 2 endpointy
- **Root & Health:** 2 endpointy

### Cache:
- ✅ **Cached:** `/api/products`, `/api/products/{id}`, `/api/creators`, `/api/creators/{username}`, `/api/creators/{username}/products`, `/api/products/{id}/changes`, `/api/products/categories/{category_name}/views`
- ❌ **Not cached:** `/api/products/views-change-24h`, `/api/products/categories/comparison`, `/api/creators/{username}/products-growth`, `/api/metrics/*`, `/cache/*`

### Response Models:
- Wszystkie endpointy używają Pydantic models (type safety)
- Struktura: `{data: ..., meta: {timestamp: ...}}`
- Error responses: `{error: {code: ..., message: ..., details: ...}}`

### Data Sources:
- **Database (PostgreSQL):** Products, Creators, Product History
- **JSON files:** Fallback dla product history, category comparison
- **Metrics:** Singleton z `src/utils/metrics.py`
- **Cache:** `api/cache.py` (TTLCache)

---

## 🔗 Przydatne Linki

- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **OpenAPI Schema:** `/openapi.json`

---

*Ostatnia aktualizacja: 2025-11-12*

