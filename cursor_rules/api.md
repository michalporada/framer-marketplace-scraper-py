# API Rules

**Cel:** Zachować czystość API i wydajny dostęp do danych historycznych.

## Architektura API

### Stack Techniczny

- **Framework**: FastAPI (Python)
- **Deployment**: Vercel (opcjonalnie) lub Railway/Render
- **Database**: PostgreSQL/Supabase (opcjonalnie) lub JSON files
- **Format**: REST API z JSON responses

### Struktura Katalogów

```
api/
├── __init__.py
├── main.py              # FastAPI app
├── cache.py             # Cache implementation (cachetools)
├── routes/
│   ├── __init__.py
│   ├── products.py      # Endpointy produktów
│   ├── creators.py      # Endpointy twórców
│   ├── categories.py    # Endpointy kategorii
│   ├── reviews.py       # Endpointy recenzji
│   └── metrics.py       # Endpointy metryk i monitoringu
├── dependencies.py      # Shared dependencies
└── models.py           # API response models
```

## Zasady Projektowania API

### RESTful Design

1. **Naming Conventions**
   - Endpointy: kebab-case (np. `/api/products`, `/api/creators/{username}`)
   - Parametry query: snake_case (np. `?product_type=template`)
   - Response fields: snake_case (zgodne z Pydantic models)

2. **HTTP Methods**
   - `GET`: Tylko odczyt danych
   - `POST`: Tworzenie zasobów (jeśli potrzebne)
   - `PUT/PATCH`: Aktualizacja (jeśli potrzebne)
   - `DELETE`: Usuwanie (jeśli potrzebne)

3. **Status Codes**
   - `200 OK`: Sukces
   - `201 Created`: Zasób utworzony
   - `400 Bad Request`: Błędne zapytanie
   - `404 Not Found`: Zasób nie znaleziony
   - `422 Unprocessable Entity`: Walidacja nie powiodła się
   - `500 Internal Server Error`: Błąd serwera

### Endpointy

#### Products

```
GET /api/products
  - Query params:
    - type: template | component | vector | plugin
    - limit: int (default: 100, max: 1000)
    - offset: int (default: 0)
    - sort: created_at | updated_at | popularity (default: created_at)
    - order: asc | desc (default: desc)
  - Response: List[ProductResponse]

GET /api/products/{product_id}
  - Response: ProductResponse

GET /api/products/{product_id}/reviews
  - Query params:
    - limit: int (default: 50)
    - offset: int (default: 0)
  - Response: List[ReviewResponse]
```

#### Creators

```
GET /api/creators
  - Query params:
    - limit: int (default: 100)
    - offset: int (default: 0)
    - sort: username | products_count (default: username)
  - Response: List[CreatorResponse]

GET /api/creators/{username}
  - Response: CreatorResponse

GET /api/creators/{username}/products
  - Query params:
    - type: template | component | vector | plugin
    - limit: int (default: 100)
    - offset: int (default: 0)
  - Response: List[ProductResponse]
```

#### Categories

```
GET /api/categories
  - Response: List[CategoryResponse]

GET /api/categories/{category_name}
  - Response: CategoryResponse

GET /api/categories/{category_name}/products
  - Query params:
    - limit: int (default: 100)
    - offset: int (default: 0)
  - Response: List[ProductResponse]
```

#### Products - History & Trends

```
GET /api/products/{product_id}/changes
  - Response: ProductChangesResponse
  - Description: Porównuje dane produktu między różnymi scrapami
  - Data source: product_history table (priorytet), JSON files (fallback)

GET /api/products/categories/comparison
  - Query params:
    - product_type: template | component | vector | plugin (opcjonalnie)
    - category: string (opcjonalnie, nazwa kategorii)
  - Response: CategoryComparisonResponse
  - Description: Porównuje trendy kategorii między scrapami
```

#### Metrics & Monitoring

```
GET /api/metrics/summary
  - Response: MetricsSummaryResponse
  - Description: Aktualne metryki scrapera (liczba scrapowanych produktów, czas, success rate)

GET /api/metrics/history
  - Query params:
    - limit: int (default: 50, max: 1000)
    - offset: int (default: 0)
  - Response: MetricsHistoryResponse
  - Description: Historyczne metryki z pliku metrics.log

GET /api/metrics/stats
  - Response: CombinedStatsResponse
  - Description: Połączone statystyki: scraper metrics, cache stats, database stats
```

#### Cache Management

```
GET /cache/stats
  - Response: CacheStatsResponse
  - Description: Statystyki cache (rozmiar, TTL, hit rate)

POST /cache/invalidate
  - Query params:
    - type: product | creator | all (default: all)
  - Response: CacheInvalidateResponse
  - Description: Czyści cache (product, creator lub wszystkie)
```

## Response Models

### Zasady

1. **Używaj Pydantic Models**
   - Response models dziedziczą z BaseModel
   - Używaj istniejących models z `src/models/`
   - Nie duplikuj logiki walidacji

2. **Struktura Response**

```python
# Single resource
{
  "data": ProductResponse,
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}

# List of resources
{
  "data": [ProductResponse, ...],
  "meta": {
    "total": 1000,
    "limit": 100,
    "offset": 0,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}

# Error response
{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product with ID 'xyz' not found",
    "details": {}
  }
}
```

3. **Normalizacja Danych**
   - Zawsze zwracaj oba formaty (raw + normalized)
   - Nie usuwaj raw data - może być potrzebne do weryfikacji
   - Używaj formatów z `src/models/` (NormalizedDate, NormalizedStatistic)

## Data Access

### Storage Backend

1. **File-based (JSON)**
   - Domyślne dla MVP
   - Odczyt z `data/products/{type}/{product_id}.json`
   - Odczyt z `data/creators/{username}.json`
   - Cache w pamięci (opcjonalnie)

2. **Database (PostgreSQL)**
   - Opcjonalne dla większych projektów
   - Używaj SQLAlchemy ORM
   - Migracje przez Alembic
   - **Tabele:**
     - `products` - najnowsze wersje produktów (UPSERT)
     - `product_history` - pełna historia zmian (INSERT only, nigdy UPDATE)
     - `creators` - dane twórców
   - **Product History:**
     - Każdy scrap tworzy nowy wpis w `product_history`
     - Timestamp `scraped_at` pozwala śledzić zmiany w czasie
     - Endpoint `/api/products/{id}/changes` używa `product_history` (priorytet)
     - Fallback do JSON files jeśli brak danych w bazie

3. **Hybrid**
   - JSON jako primary source
   - Database jako cache/index
   - Sync między nimi

### Caching

1. **Strategia**
   - Cache response dla statycznych danych (produkty, twórcy)
   - TTL: 1-5 minut dla danych scrapowanych
   - Cache invalidation po nowym scrapowaniu

2. **Implementacja**
   - Używaj `cachetools.TTLCache` (zaimplementowane w `api/cache.py`)
   - Osobne cache dla produktów i twórców
   - Cache key: MD5 hash z funkcji + args + kwargs
   - TTL: 5 minut (domyślnie, konfigurowalne przez `API_CACHE_TTL`)
   - Decorator `@cached(ttl=300, cache_type="product|creator")`
   - Loguj cache hits/misses (DEBUG level)
   - **Ważne:** Cache nie przechowuje `None` - tylko poprawne odpowiedzi są cachowane
   - Endpointy cache management: `/cache/stats`, `/cache/invalidate`

## Performance

### Pagination

1. **Zawsze używaj paginacji**
   - Default limit: 100
   - Max limit: 1000
   - Offset-based pagination (dla prostoty)
   - Cursor-based pagination (opcjonalnie, dla lepszej wydajności)

2. **Response Time**
   - Target: < 200ms dla pojedynczego zasobu
   - Target: < 500ms dla listy zasobów
   - Monitoruj response times

### Query Optimization

1. **Database Queries**
   - Używaj indeksów (product_id, username, type, scraped_at)
   - Unikaj N+1 queries
   - Używaj eager loading dla relacji
   - **Prepared Statements (OBOWIĄZKOWE):**
     - Zawsze używaj parametrów w zapytaniach SQL
     - NIE używaj string formatting dla wartości (`f"SELECT * FROM products WHERE id = '{id}'"` ❌)
     - Używaj `:param` syntax z SQLAlchemy `text()` i `execute(query, params)`
     - Dla `ORDER BY` - whitelist dozwolonych kolumn (nie parametr, ale walidacja)
     - Przykład:
       ```python
       query = text("SELECT * FROM products WHERE type = :type LIMIT :limit OFFSET :offset")
       result = conn.execute(query, {"type": type, "limit": limit, "offset": offset})
       ```

2. **File-based Queries**
   - Cache lista plików
   - Lazy loading plików
   - Używaj generatorów dla dużych list

## Error Handling

### Zasady

1. **Strukturalne Błędy**
   ```python
   {
     "error": {
       "code": "ERROR_CODE",
       "message": "Human-readable message",
       "details": {
         "field": "additional context"
       }
     }
   }
   ```

2. **Error Codes**
   - `PRODUCT_NOT_FOUND`: Produkt nie znaleziony
   - `CREATOR_NOT_FOUND`: Twórca nie znaleziony
   - `INVALID_PRODUCT_TYPE`: Nieprawidłowy typ produktu
   - `VALIDATION_ERROR`: Błąd walidacji
   - `INTERNAL_ERROR`: Błąd serwera

3. **Logging**
   - Loguj wszystkie błędy na poziomie ERROR
   - Zawieraj kontekst (endpoint, params, error)
   - Nie loguj wrażliwych danych

## Validation

### Input Validation

1. **Query Parameters**
   - Używaj Pydantic dla walidacji
   - Waliduj typy, zakresy, formaty
   - Zwracaj 422 dla błędnych parametrów

2. **Path Parameters**
   - Waliduj format (product_id, username)
   - Zwracaj 404 dla nieprawidłowych wartości

### Output Validation

1. **Response Models**
   - Wszystkie response używają Pydantic models
   - Serializacja automatyczna
   - Walidacja przed zwróceniem

## Documentation

### OpenAPI/Swagger

1. **Auto-generated Docs**
   - FastAPI automatycznie generuje OpenAPI schema
   - Dostępne pod `/docs` (Swagger UI)
   - Dostępne pod `/redoc` (ReDoc)

2. **Dokumentacja Endpointów**
   - Opisz każdy endpoint w docstring
   - Opisz parametry query
   - Opisz response model
   - Dodaj przykłady

### Example

```python
@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str = Path(..., description="Product ID"),
) -> ProductResponse:
    """
    Get product by ID.
    
    Args:
        product_id: Product identifier (e.g., 'template-name')
    
    Returns:
        ProductResponse with product data
    
    Raises:
        404: Product not found
    """
    # Implementation
```

## Security

### Rate Limiting

1. **API Rate Limits**
   - Domyślnie: 100 requests/minute per IP
   - Konfigurowalne przez environment variables
   - Zwracaj 429 (Too Many Requests) przy przekroczeniu

2. **CORS**
   - Konfiguruj CORS dla frontend
   - Whitelist tylko potrzebne origins
   - Używaj FastAPI CORSMiddleware

### Authentication (Opcjonalnie)

1. **API Keys**
   - Jeśli potrzebne, używaj API keys
   - Przechowuj w environment variables
   - Waliduj w dependencies

2. **Headers**
   - `X-API-Key`: dla API key authentication
   - `Authorization: Bearer {token}`: dla token-based auth

## Testing

### Testy API

1. **Unit Tests**
   - Testuj logikę endpointów
   - Mock data access layer
   - Testuj error handling

2. **Integration Tests**
   - Testuj pełny flow (request → response)
   - Używaj test database/files
   - Testuj edge cases

3. **Performance Tests**
   - Testuj response times
   - Testuj pod obciążeniem
   - Monitoruj resource usage

## Deployment

### Vercel (Opcjonalnie)

1. **Configuration**
   ```json
   {
     "builds": [{
       "src": "api/main.py",
       "use": "@vercel/python"
     }],
     "routes": [{
       "src": "/api/(.*)",
       "dest": "api/main.py"
     }]
   }
   ```

2. **Limitations**
   - Max execution time: 10s (hobby), 60s (pro)
   - Nie idealne dla długich operacji
   - Używaj dla lekkich endpointów

### Railway/Render (Rekomendowane)

1. **Deployment**
   - Continuous deployment z GitHub
   - Environment variables w dashboard
   - Health checks

2. **Advantages**
   - Dłuższy timeout
   - Lepsze dla Python API
   - Większa kontrola

## Checklist przed Implementacją

- [ ] Endpointy zdefiniowane zgodnie z REST
- [ ] Response models z Pydantic
- [ ] Pagination zaimplementowana
- [ ] Error handling z strukturalnymi błędami
- [ ] Input validation zaimplementowana
- [ ] OpenAPI docs wygenerowane
- [ ] Rate limiting zaimplementowany
- [ ] CORS skonfigurowany
- [ ] Testy napisane
- [ ] Performance zoptymalizowana
- [ ] Logging zaimplementowany

---

**Uwaga:** Te reguły są draftem i mogą być rozszerzone/zmodyfikowane w przyszłości.

