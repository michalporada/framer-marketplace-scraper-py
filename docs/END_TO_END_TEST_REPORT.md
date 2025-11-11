# End-to-End Test Report & Improvement Suggestions

**Data testów:** 2025-11-11  
**Wersja:** 1.0.0

## 📊 Podsumowanie Testów

### ✅ Co działa poprawnie:

1. **Baza danych:**
   - ✅ Połączenie z Supabase działa (Session Mode)
   - ✅ W bazie jest 5807 produktów
   - ✅ W bazie jest 1368 kreatorów
   - ✅ Tabela `products` ma kolumnę `scraped_at` z indeksem

2. **API Endpoints:**
   - ✅ `/health` - działa, pokazuje status DB
   - ✅ `/api/products` - lista produktów z paginacją, filtrowaniem, sortowaniem
   - ✅ `/api/products/{id}` - pojedynczy produkt
   - ✅ `/api/creators` - lista kreatorów
   - ✅ `/api/creators/{username}` - pojedynczy kreator
   - ✅ `/api/products/categories/comparison` - porównywanie kategorii

3. **Scraping:**
   - ✅ Scraper zapisuje produkty do JSON
   - ✅ Scraper zapisuje produkty do bazy danych podczas scrapowania
   - ✅ Checkpoint system działa
   - ✅ Metrics tracking działa

### ⚠️ Problemy znalezione:

1. **Endpoint `/api/products/{id}/changes` nie działa poprawnie:**
   - ❌ Szuka wersji produktu tylko w plikach JSON (nie w bazie danych)
   - ❌ Nie znajduje produktów, które są tylko w bazie danych
   - ❌ Nie wykorzystuje historii z bazy danych (`scraped_at`)

2. **Brak historii w bazie danych:**
   - ⚠️ Tabela `products` używa `ON CONFLICT (id) DO UPDATE` - nadpisuje dane zamiast tworzyć nowe wersje
   - ⚠️ Nie można śledzić zmian w czasie dla produktów, które są tylko w DB
   - ⚠️ `scraped_at` jest aktualizowany przy każdym scrapowaniu, ale stara wersja jest tracona

3. **Porównywanie zmian w czasie:**
   - ⚠️ `/categories/comparison` działa tylko z plikami JSON
   - ⚠️ Nie wykorzystuje danych z bazy danych do porównań

## 🔧 Proponowane Ulepszenia

### 1. **Historia w bazie danych (HIGH PRIORITY)**

**Problem:** Obecna struktura bazy danych nadpisuje dane zamiast przechowywać historię.

**Rozwiązanie A: Tabela historii produktów (Recommended)**
```sql
-- Nowa tabela dla historii
CREATE TABLE product_history (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    scraped_at TIMESTAMP NOT NULL,
    -- wszystkie pola produktu
    name VARCHAR(500),
    views_normalized INTEGER,
    price DECIMAL(10, 2),
    -- ... wszystkie inne pola
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_product_history_product_id ON product_history(product_id);
CREATE INDEX idx_product_history_scraped_at ON product_history(scraped_at);
```

**Rozwiązanie B: Zmiana PRIMARY KEY (Alternative)**
```sql
-- Zmiana PRIMARY KEY na (id, scraped_at)
ALTER TABLE products DROP CONSTRAINT products_pkey;
ALTER TABLE products ADD PRIMARY KEY (id, scraped_at);
-- Usunięcie UNIQUE constraint z url (może się zmienić)
ALTER TABLE products DROP CONSTRAINT IF EXISTS products_url_key;
```

**Rekomendacja:** Rozwiązanie A - łatwiejsze w utrzymaniu, lepsze dla query, nie wymaga zmian w istniejących danych.

### 2. **Endpoint `/api/products/{id}/changes` - użyj bazy danych**

**Obecny problem:** Szuka tylko w plikach JSON.

**Proponowane rozwiązanie:**
```python
@router.get("/{product_id}/changes", response_model=ProductChangesResponse)
async def get_product_changes(product_id: str):
    """Get changes in product data across different scrapes."""
    # 1. Sprawdź w bazie danych (jeśli mamy historię)
    db_versions = get_product_versions_from_db(product_id)
    
    # 2. Sprawdź w plikach JSON (fallback)
    json_versions = find_all_product_versions(product_id)
    
    # 3. Połącz i posortuj
    all_versions = merge_versions(db_versions, json_versions)
    
    # 4. Porównaj wersje
    changes = compare_versions(all_versions)
    
    return ProductChangesResponse(...)
```

### 3. **Automatyczne tworzenie historii podczas scrapowania**

**Proponowane zmiany w `src/storage/database.py`:**

```python
async def save_product_db(self, product: Product) -> bool:
    """Save product to database with history tracking."""
    # 1. Zapisz do głównej tabeli (aktualna wersja)
    await self._save_product_current(product)
    
    # 2. Zapisz do tabeli historii (wszystkie wersje)
    await self._save_product_history(product)
    
    return True

async def _save_product_history(self, product: Product) -> bool:
    """Save product version to history table."""
    # INSERT INTO product_history (...) VALUES (...)
    # Zawsze insert, nigdy UPDATE
    pass
```

### 4. **Query do porównywania zmian z bazy danych**

**Nowy endpoint lub rozszerzenie istniejącego:**

```python
@router.get("/{product_id}/changes/db", response_model=ProductChangesResponse)
async def get_product_changes_from_db(
    product_id: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """Get product changes from database history."""
    query = """
        SELECT * FROM product_history
        WHERE product_id = :product_id
        AND scraped_at BETWEEN :from_date AND :to_date
        ORDER BY scraped_at DESC
    """
    # ... implementacja
```

### 5. **Optymalizacja zapytań do bazy danych**

**Problemy:**
- String formatting w query (SQL injection risk)
- Brak prepared statements dla niektórych query

**Rozwiązanie:**
```python
# Zamiast:
where_clause = f"WHERE type = '{type}'"

# Użyj:
where_clause = "WHERE type = :type"
params = {"type": type}
result = execute_query(query, params)
```

### 6. **Monitoring i alerting**

**Proponowane ulepszenia:**
- Dashboard z metrykami scrapowania
- Alerty gdy scraping się nie powiedzie
- Monitoring zmian w statystykach produktów
- Wykrywanie anomalii (np. nagły spadek views)

### 7. **Cache dla API**

**Proponowane:**
- Redis cache dla często używanych endpointów
- TTL: 5-15 minut dla danych produktów
- Cache invalidation po nowym scrapowaniu

### 8. **Batch operations dla historii**

**Proponowane:**
- Batch insert do `product_history` podczas scrapowania
- Bulk operations dla lepszej wydajności
- Async batch processing

### 9. **Data retention policy**

**Proponowane:**
- Automatyczne usuwanie starych wersji (np. > 90 dni)
- Archiwizacja starych danych
- Kompresja historii

### 10. **Testy end-to-end**

**Proponowane:**
- Automatyczne testy E2E dla całego flow
- Testy integracyjne dla API + DB
- Testy wydajnościowe

## 📋 Priorytetyzacja

### HIGH PRIORITY (Zrobić najpierw):
1. ✅ Historia w bazie danych (tabela `product_history`)
2. ✅ Endpoint `/changes` - użyj bazy danych
3. ✅ Automatyczne tworzenie historii podczas scrapowania

### MEDIUM PRIORITY:
4. ⚠️ Optymalizacja zapytań (prepared statements)
5. ⚠️ Cache dla API
6. ⚠️ Batch operations

### LOW PRIORITY:
7. 📝 Monitoring i alerting
8. 📝 Data retention policy
9. 📝 Testy E2E

## 🔍 Szczegółowe Testy

### Test 1: Scraping → JSON → DB
**Status:** ✅ PASS
- Scraper zapisuje do JSON: ✅
- Scraper zapisuje do DB: ✅
- Checkpoint działa: ✅

### Test 2: API Endpoints
**Status:** ✅ PASS (z wyjątkiem `/changes`)
- Lista produktów: ✅
- Pojedynczy produkt: ✅
- Filtrowanie: ✅
- Paginacja: ✅
- Sortowanie: ✅
- Changes endpoint: ❌ (szuka tylko w JSON)

### Test 3: Porównywanie zmian
**Status:** ⚠️ PARTIAL
- Categories comparison: ✅ (tylko z JSON)
- Product changes: ❌ (nie działa z DB)

### Test 4: Sync JSON to DB
**Status:** ✅ PASS
- Script `sync_json_to_db.py` działa: ✅
- GitHub Actions workflow: ✅

## 📝 Rekomendacje

1. **Natychmiast:** Zaimplementuj tabelę `product_history` i zapisuj historię podczas scrapowania
2. **Wkrótce:** Popraw endpoint `/changes` aby używał bazy danych
3. **Długoterminowo:** Dodaj monitoring, cache, i optymalizacje

## 🚀 Następne kroki

1. Stwórz migration dla tabeli `product_history`
2. Zaktualizuj `DatabaseStorage.save_product_db()` aby zapisywał historię
3. Zaktualizuj endpoint `/changes` aby używał bazy danych
4. Dodaj testy dla nowej funkcjonalności
5. Zaktualizuj dokumentację

---

**Uwaga:** Jeśli potrzebujesz dostępu do bazy danych lub innych zasobów do testów, daj znać!

