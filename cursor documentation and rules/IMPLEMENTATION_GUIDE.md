# Implementation Guide — Amonit API

**Cel:** Strategiczne sugestie i prompt do implementacji API dla Amonit

**Data:** 2025-01-XX  
**Status:** Przed implementacją

---

## 🎯 Strategiczne Sugestie

### 1. Start Small, Iterate Fast

**Podejście:**
- ✅ Zacznij od **najmniejszego działającego API** — jeden endpoint (np. `GET /api/categories`)
- ✅ Przetestuj end-to-end: scraper → DB → API → response
- ✅ Potem dodawaj kolejne endpointy jeden po drugim

**Dlaczego:**
- Szybciej zobaczysz rezultaty
- Łatwiej debugować problemy
- Możesz przetestować cały flow przed rozbudową

**Przykład:**
```
Dzień 1: GET /api/categories (bez filtrowania)
Dzień 2: Dodać sortowanie i filtrowanie
Dzień 3: GET /api/categories/{slug}
Dzień 4: GET /api/templates (podstawowe)
```

---

### 2. Database First, API Second

**Podejście:**
- ✅ Najpierw upewnij się, że dane są w PostgreSQL i są poprawne
- ✅ Sprawdź zapytania SQL ręcznie (pgAdmin, Supabase dashboard)
- ✅ Potem buduj API endpointy

**Dlaczego:**
- Jeśli dane są złe, API też będzie złe
- Łatwiej debugować problemy w bazie niż przez API
- Możesz testować query bez API

**Checklist:**
- [ ] Czy `template_snapshots` zawiera historię?
- [ ] Czy `rank_in_category` jest obliczany poprawnie?
- [ ] Czy agregacje (sum, avg) działają?

---

### 3. Reuse Existing Code

**Podejście:**
- ✅ Użyj istniejących Pydantic models z scrapera
- ✅ Użyj istniejących helper functions (normalizers, etc.)
- ✅ Nie przepisuj kodu, który już działa

**Dlaczego:**
- Mniej kodu = mniej błędów
- Spójność między scraperem a API
- Szybsza implementacja

**Przykład:**
```python
# Reuse z scrapera
from src.models.product import Product
from src.utils.normalizers import parse_relative_date

# W API
from api.models.schemas import TemplateResponse  # Może używać Product model
```

---

### 4. Test-Driven Development (Optional, ale Recommended)

**Podejście:**
- ✅ Napisz test dla endpointu PRZED implementacją
- ✅ Implementuj do momentu, aż test przejdzie
- ✅ Refactor, jeśli potrzeba

**Dlaczego:**
- Jasne wymagania (test = spec)
- Mniej regresji
- Lepsze pokrycie testami

**Przykład:**
```python
# test_api/test_categories.py
def test_get_categories_sorted_by_views():
    response = client.get("/api/categories?sort=views&order=desc")
    assert response.status_code == 200
    categories = response.json()["categories"]
    assert categories[0]["total_views"] >= categories[1]["total_views"]
```

---

### 5. Use Type Hints Everywhere

**Podejście:**
- ✅ Wszystkie funkcje z type hints
- ✅ Pydantic models dla request/response
- ✅ SQLAlchemy models z type hints

**Dlaczego:**
- Lepsze IDE support (autocomplete)
- Mniej błędów w runtime
- Łatwiejsze utrzymanie

**Przykład:**
```python
from typing import List, Optional
from pydantic import BaseModel

class CategoryResponse(BaseModel):
    slug: str
    name: str
    templates_count: int
    total_views: int

async def get_categories(
    sort: str = "views",
    limit: int = 100,
    offset: int = 0
) -> List[CategoryResponse]:
    ...
```

---

### 6. Keep It Simple (KISS)

**Podejście:**
- ✅ Dla ETAP 1: in-memory cache, nie Redis
- ✅ Dla ETAP 1: JSON file dla market context, nie DB
- ✅ Dla ETAP 1: public API, nie auth

**Dlaczego:**
- Mniej rzeczy może się zepsuć
- Szybsza implementacja
- Możesz dodać complexity później (ETAP 2+)

**Przykład:**
```python
# ETAP 1: Simple
cache = {}

# ETAP 2: Możesz dodać Redis
if USE_REDIS:
    cache = redis_client
else:
    cache = {}
```

---

## 🤖 Prompt dla Cursora/Agenta AI

### Prompt: Setup FastAPI + Supabase

```
Jesteś doświadczonym backend developerem pracującym nad Amonit API.

KONTEKST:
- Masz działający Python scraper, który zbiera dane z Framer Marketplace
- Dane są obecnie zapisywane jako JSON files w `data/`
- Chcesz stworzyć FastAPI, które serwuje te dane przez REST API
- Baza danych: Supabase (PostgreSQL)

ZADANIE:
1. Utwórz strukturę projektu dla FastAPI API zgodnie z API_SPECIFICATION.md
2. Skonfiguruj połączenie z Supabase (SQLAlchemy)
3. Stwórz podstawowe SQLAlchemy models (Category, Template, TemplateSnapshot, Creator, CreatorSnapshot)
4. Stwórz Alembic migration dla tych tabel
5. Stwórz pierwszy endpoint: GET /api/categories (bez filtrowania, tylko lista)
6. Dodaj health check endpoint: GET /health

WYMAGANIA:
- Użyj istniejących Pydantic models z `src/models/` jeśli możliwe
- Type hints wszędzie
- Dokumentacja w docstrings
- Error handling (404, 500)
- CORS middleware dla localhost:3000 (frontend)

STRUKTURA:
```
api/
├── main.py
├── dependencies.py
├── config.py
├── models/
│   ├── database.py  # SQLAlchemy models
│   └── schemas.py   # Pydantic response models
└── routes/
    └── categories.py
```

Zacznij od utworzenia struktury i podstawowego setupu.
```

---

### Prompt: Migracja Danych z JSON do PostgreSQL

```
Jesteś doświadczonym backend developerem pracującym nad migracją danych Amonit.

KONTEKST:
- Masz dane w JSON files w `data/products/`, `data/creators/`, `data/categories/`
- Masz już schema PostgreSQL (Supabase) z tabelami: categories, templates, template_snapshots, creators, creator_snapshots
- Chcesz zmigrować wszystkie dane z JSON do PostgreSQL

ZADANIE:
1. Stwórz skrypt migracji: `scripts/migrate_json_to_db.py`
2. Skrypt powinien:
   - Wczytać wszystkie JSON files
   - Znormalizować dane (użyć istniejących Pydantic models)
   - Wstawić do odpowiednich tabel
   - Stworzyć pierwsze snapshots dla każdego template/creator
   - Pokazać progress bar (tqdm)
   - Logować błędy do pliku

WYMAGANIA:
- Idempotentność: możliwość uruchomienia wiele razy (upsert, nie insert)
- Walidacja: sprawdź czy dane są poprawne przed wstawieniem
- Progress tracking: pokaż ile rekordów przetworzono
- Error handling: jeśli jeden rekord się nie powiedzie, kontynuuj z resztą

PRZYKŁAD USAGE:
```bash
python scripts/migrate_json_to_db.py --dry-run  # Test bez zapisu
python scripts/migrate_json_to_db.py           # Pełna migracja
```

Zacznij od implementacji.
```

---

### Prompt: Implementacja Endpointów ETAP 1

```
Jesteś doświadczonym backend developerem pracującym nad Amonit API.

KONTEKST:
- Masz już setup FastAPI + Supabase
- Dane są w PostgreSQL
- Chcesz zaimplementować endpointy ETAP 1 zgodnie z API_SPECIFICATION.md

ZADANIE:
Zaimplementuj endpoint: GET /api/templates

WYMAGANIA z API_SPECIFICATION.md:
- Query params: category, creator, sort, order, min_price, max_price, min_views, limit, offset
- Response: lista szablonów z podstawowymi danymi
- Paginacja: limit (max 100), offset
- Sortowanie: views, price, updated, rank (default: views)
- Filtrowanie: category, creator, price range, views range

IMPLEMENTACJA:
1. Stwórz Pydantic schema: TemplateListResponse
2. Stwórz route handler z wszystkimi query params
3. Zbuduj SQLAlchemy query z filtrowaniem i sortowaniem
4. Dodaj paginację
5. Zwróć response zgodnie z formatem z API_SPECIFICATION.md

PRZYKŁAD RESPONSE:
```json
{
  "templates": [
    {
      "slug": "calisto",
      "title": "Calisto — SaaS Template",
      "category_slug": "business",
      "creator_handle": "aster-themes",
      "price_cents": 9900,
      "views": 28400,
      "rank_in_category": 3,
      "estimated_revenue": 141.24,
      "framer_url": "https://..."
    }
  ],
  "total": 1234,
  "limit": 50,
  "offset": 0
}
```

Dodaj też:
- Error handling (404 dla nieistniejących kategorii)
- Validation (min_price < max_price)
- Type hints wszędzie

Zacznij od implementacji.
```

---

### Prompt: Implementacja Derived Metrics

```
Jesteś doświadczonym backend developerem pracującym nad Amonit API.

KONTEKST:
- Masz już endpointy dla categories, templates, creators
- Chcesz dodać obliczanie metryk pochodnych: Difficulty Score i Estimated Revenue

ZADANIE:
Zaimplementuj obliczanie Difficulty Score zgodnie z PRODUCT_ROADMAP.md

WZÓR z PRODUCT_ROADMAP.md:
```
difficulty_score = qnorm(templates_count) × 0.6 + qnorm(views_per_template) × 0.4
Buckets: Low / Medium / High / Very High (quartiles)
```

IMPLEMENTACJA:
1. Stwórz service: `services/metrics_calculator.py`
2. Funkcja: `calculate_difficulty(category_slug: str) -> Dict[str, Any]`
3. Oblicz:
   - templates_count dla kategorii
   - avg_views_per_template dla kategorii
   - Quantile normalization dla wszystkich kategorii
   - difficulty_score
   - Bucket (Low/Medium/High/Very High)
4. Dodaj do response `GET /api/categories/{slug}`

DODATKOWO:
- Zaimplementuj `estimate_template_revenue()`:
  - Używa `get_latest_market_payout()` z market_context.json
  - Wzór: `(template_views / total_market_views) × latest_payout`
- Dodaj do response `GET /api/templates/{slug}`

WYMAGANIA:
- Type hints
- Error handling (jeśli brak danych)
- Cache wyników (dla tej samej kategorii, żeby nie liczyć za każdym razem)

Zacznij od implementacji.
```

---

### Prompt: Update Scrapera do PostgreSQL

```
Jesteś doświadczonym backend developerem pracującym nad Amonit scraperem.

KONTEKST:
- Masz działający scraper, który zapisuje do JSON files
- Masz już schema PostgreSQL z tabelami do time-series snapshots
- Chcesz zaktualizować scraper, aby zapisywał do PostgreSQL zamiast JSON

ZADANIE:
Zaktualizuj scraper, aby zapisywał do PostgreSQL:
1. Templates → `templates` + `template_snapshots`
2. Creators → `creators` + `creator_snapshots`
3. Categories → `categories`
4. Jobs → `jobs_runs`

WYMAGANIA:
- Backward compatible: możliwość zapisu do JSON (opcjonalne, dla backup)
- Incremental updates: sprawdź czy template już istnieje (upsert)
- Snapshots: zawsze dodawaj nowy snapshot, nawet jeśli dane się nie zmieniły
- Hash-based change detection (opcjonalne): jeśli page_hash się nie zmienił, skip parse
- Error handling: jeśli zapis do DB się nie powiedzie, loguj i kontynuuj

STRUKTURA:
```
src/
├── storage/
│   ├── file_storage.py      # Istniejący (JSON)
│   └── db_storage.py        # Nowy (PostgreSQL)
└── main.py                  # Używa db_storage zamiast file_storage
```

IMPLEMENTACJA:
1. Stwórz `storage/db_storage.py` z funkcjami:
   - `save_template(template: Product, snapshot_date: datetime)`
   - `save_creator(creator: Creator, snapshot_date: datetime)`
   - `save_category(category: Category)`
   - `record_job_run(job_name: str, started_at: datetime, ...)`

2. Zaktualizuj `main.py` aby używał `db_storage` zamiast `file_storage`

3. Przetestuj na małej próbce (10 produktów)

Zacznij od implementacji.
```

---

## 📚 Best Practices

### 1. Database Queries

**DO:**
```python
# Używaj SQLAlchemy ORM z type hints
from sqlalchemy.orm import Session
from api.models.database import Template

def get_templates(db: Session, category_slug: Optional[str] = None) -> List[Template]:
    query = db.query(Template).filter(Template.is_active == True)
    if category_slug:
        query = query.filter(Template.category_slug == category_slug)
    return query.all()
```

**DON'T:**
```python
# Nie używaj raw SQL jeśli nie musisz
db.execute("SELECT * FROM templates WHERE category_slug = %s", (category_slug,))
```

---

### 2. Error Handling

**DO:**
```python
from fastapi import HTTPException

@app.get("/api/templates/{slug}")
async def get_template(slug: str, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.slug == slug).first()
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{slug}' not found")
    return template
```

**DON'T:**
```python
# Nie zwracaj None bez sprawdzenia
template = db.query(Template).filter(Template.slug == slug).first()
return template  # Może być None!
```

---

### 3. Response Models

**DO:**
```python
from pydantic import BaseModel

class TemplateResponse(BaseModel):
    slug: str
    title: str
    views: int
    price_cents: int
    
    class Config:
        from_attributes = True  # Pydantic v2

@app.get("/api/templates/{slug}", response_model=TemplateResponse)
async def get_template(slug: str):
    ...
```

**DON'T:**
```python
# Nie zwracaj dict bez modelu
return {"slug": template.slug, "title": template.title}  # Brak walidacji!
```

---

### 4. Query Parameters

**DO:**
```python
from typing import Optional
from fastapi import Query

@app.get("/api/templates")
async def get_templates(
    category: Optional[str] = None,
    sort: str = Query(default="views", regex="^(views|price|updated)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    ...
```

**DON'T:**
```python
# Nie używaj request.query_params bezpośrednio
category = request.query_params.get("category")  # Brak walidacji!
```

---

## ⚠️ Common Pitfalls

### 1. N+1 Query Problem

**Problem:**
```python
# Złe: każdy template robi osobne query dla creatora
templates = db.query(Template).all()
for template in templates:
    creator = db.query(Creator).filter(Creator.handle == template.creator_handle).first()
```

**Rozwiązanie:**
```python
# Dobre: użyj joinedload
from sqlalchemy.orm import joinedload

templates = db.query(Template).options(joinedload(Template.creator)).all()
```

---

### 2. Missing Indexes

**Problem:**
```python
# Query bez indeksu może być wolne
db.query(Template).filter(Template.category_slug == "business").all()
```

**Rozwiązanie:**
```sql
-- Dodaj indeks w migracji
CREATE INDEX idx_templates_category ON templates(category_slug);
```

---

### 3. Race Conditions

**Problem:**
```python
# Dwa requesty mogą stworzyć duplikat
template = db.query(Template).filter(Template.slug == slug).first()
if not template:
    template = Template(slug=slug, ...)  # Race condition!
    db.add(template)
```

**Rozwiązanie:**
```python
# Użyj upsert
from sqlalchemy.dialects.postgresql import insert

stmt = insert(Template).values(slug=slug, ...)
stmt = stmt.on_conflict_do_update(
    index_elements=['slug'],
    set_=dict(title=stmt.excluded.title, ...)
)
db.execute(stmt)
```

---

## 🎯 Quick Start Checklist

Przed rozpoczęciem implementacji:

- [ ] Przeczytałeś API_SPECIFICATION.md
- [ ] Przeczytałeś API_IMPLEMENTATION_CHECKLIST.md
- [ ] Masz dostęp do Supabase (projekt utworzony)
- [ ] Masz connection string do Supabase
- [ ] Zainstalowałeś dependencies (FastAPI, SQLAlchemy, etc.)
- [ ] Wiesz gdzie są dane JSON (do migracji)

---

## 📝 Template: Prompt dla Cursora

```
Jesteś doświadczonym backend developerem pracującym nad [NAZWA_ZADANIA].

KONTEKST:
[Opisz kontekst projektu i co już masz]

ZADANIE:
[Opisz konkretne zadanie do wykonania]

WYMAGANIA:
- [Lista wymagań]
- [Odniesienia do dokumentacji]
- [Przykłady]

IMPLEMENTACJA:
[Kroki do wykonania]

Zacznij od [pierwszy krok].
```

---

**Wersja:** 1.0  
**Ostatnia aktualizacja:** 2025-01-XX  
**Status:** Ready to Use

