# API Implementation Checklist — Amonit

**Cel:** Konkretna lista rzeczy do zrobienia, aby stworzyć działające API dla ETAP 1 (Foundation)

**Data:** 2025-01-XX  
**Status:** Przed implementacją

---

## 📊 Analiza Dokumentów

### TECHNICAL_BACKLOG.md — Podsumowanie

**Cel:** Identyfikacja luk technicznych i plan implementacji

**Główne punkty:**
- ✅ **Scraper jest wystarczający** — działa stabilnie, zbiera wszystkie potrzebne dane
- ❌ **Brakuje:** Time-series database, insight engine, watchlist, API, dashboard
- 📋 **Priorytety:** Time-series DB → Insights → Watchlist → API → Dashboard

**Kluczowe wnioski:**
- Scraper działa, ale dane są w JSON — potrzeba migracji do PostgreSQL
- Bez historii zmian nie można generować insightów
- API jest fundamentem dla dashboardu

---

### API_SPECIFICATION.md — Podsumowanie

**Cel:** Kompletna dokumentacja API od Foundation do Prediction

**Główne punkty:**
- 🏗️ **Architektura:** FastAPI (Python) + Supabase (PostgreSQL + Auth)
- 📊 **ETAP 1:** Categories, Templates, Creators, Market Context (public API)
- 📈 **ETAP 2:** Insights, Trends, Watchlist, Alerts (z auth)
- 🔮 **ETAP 3:** Predictive Analytics, AI Insights (zaawansowane)

**Kluczowe decyzje:**
- FastAPI (Python) — reuse scrapera
- Supabase Auth — gotowe rozwiązanie
- In-memory cache dla ETAP 1
- JSON file dla market context (ETAP 1)

---

### PRODUCT_ROADMAP.md — Kontekst Strategiczny

**Cel:** Wizja produktu i strategiczne kierunki

**ETAP 1 (Foundation):**
- Stabilny scraper ✅
- Baza historyczna (SQLite/Supabase) ❌
- Dashboard MVP ❌
- Wskaźniki: Difficulty, Total Views, Est. Revenue ❌

**Filozofia:** Nie sprzedajemy danych — sprzedajemy przewagę informacyjną

---

## 🔍 Różnice i Spójność

### TECHNICAL_BACKLOG vs API_SPECIFICATION

| Aspekt | TECHNICAL_BACKLOG | API_SPECIFICATION |
|--------|-------------------|-------------------|
| **Focus** | Co brakuje, co trzeba zbudować | Jak to zbudować (konkretna spec) |
| **Database** | PostgreSQL/Supabase (ogólne) | Supabase (konkretna decyzja) |
| **Auth** | FastAPI + JWT lub Supabase Auth | Supabase Auth (konkretna decyzja) |
| **Timeline** | Fazy 1-4 (miesiące) | Fazy 1-3 (tygodnie, fokus na API) |
| **Scope** | Wszystko (DB, insights, alerts, API, dashboard) | Tylko API (endpointy, struktura) |

### Spójność z PRODUCT_ROADMAP

✅ **Zgodne:**
- Time-series database (snapshots) — wymagane dla ETAP 1
- Public API dla podstawowych danych — ETAP 1
- Difficulty, Opportunity Score — wymagane dla dashboardu
- Market context integration — wymagane dla revenue estimation

⚠️ **Wymaga uwagi:**
- PRODUCT_ROADMAP mówi o "SQLite/Supabase" — API_SPECIFICATION wybiera Supabase
- PRODUCT_ROADMAP nie precyzuje struktury API — API_SPECIFICATION to uzupełnia

---

## ✅ Checklist: Co Musi Się Wydarzyć Przed Stworzeniem API

### PRIORYTET 1: Time-Series Database (Fundament)

#### 1.1 Setup Supabase
- [ ] Utworzyć projekt Supabase
- [ ] Skonfigurować connection string
- [ ] Testować połączenie z lokalnego środowiska

**Szacowany czas:** 1-2 godziny

---

#### 1.2 Database Schema Migration
- [ ] Stworzyć migrację Alembic dla tabel:
  - [ ] `categories` (slug, name, first_seen_at, last_seen_at)
  - [ ] `templates` (slug, title, category_slug, creator_handle, is_active)
  - [ ] `template_snapshots` (time-series, append-only)
  - [ ] `creators` (handle, name, profile_url)
  - [ ] `creator_snapshots` (time-series)
  - [ ] `jobs_runs` (tracking scrapowania)
  - [ ] `market_context` (opcjonalnie dla ETAP 1, JSON file też OK)

- [ ] Dodać indeksy:
  - [ ] `idx_template_snapshots_captured_at` (DESC)
  - [ ] `idx_template_snapshots_template_slug`
  - [ ] `idx_template_snapshots_category`

- [ ] Przetestować schema (CREATE TABLE ręcznie lub przez Alembic)

**Szacowany czas:** 1 dzień

---

#### 1.3 Migracja Danych z JSON do PostgreSQL
- [ ] Stworzyć skrypt migracji danych:
  - [ ] Wczytać istniejące JSON z `data/products/`, `data/creators/`, `data/categories/`
  - [ ] Znormalizować dane (Pydantic models)
  - [ ] Wstawić do odpowiednich tabel (categories, templates, creators)
  - [ ] Stworzyć pierwsze snapshots dla każdego template/creator

- [ ] Przetestować migrację na małej próbce (10-20 produktów)
- [ ] Uruchomić pełną migrację
- [ ] Zweryfikować dane (SELECT queries, sprawdzić liczbę rekordów)

**Szacowany czas:** 2-3 dni

---

#### 1.4 Update Scrapera do Zapisu do PostgreSQL
- [ ] Zintegrować SQLAlchemy z istniejącym scraperem
- [ ] Zastąpić zapis do JSON zapisem do PostgreSQL:
  - [ ] Templates → `templates` + `template_snapshots`
  - [ ] Creators → `creators` + `creator_snapshots`
  - [ ] Categories → `categories`
  - [ ] Jobs → `jobs_runs`

- [ ] Dodać hash-based change detection (opcjonalne dla ETAP 1, ale warto)
- [ ] Przetestować scraper z nowym storage
- [ ] Upewnić się, że GitHub Actions workflow działa z PostgreSQL

**Szacowany czas:** 2-3 dni

---

### PRIORYTET 2: FastAPI Setup

#### 2.1 Projekt Structure
- [ ] Utworzyć strukturę katalogów:
  ```
  api/
  ├── main.py
  ├── dependencies.py
  ├── config.py
  ├── routes/
  │   ├── templates.py
  │   ├── categories.py
  │   ├── creators.py
  │   └── market.py
  ├── models/
  │   ├── schemas.py
  │   └── database.py
  └── services/
      └── market_context.py
  ```

- [ ] Zainstalować dependencies:
  - [ ] `fastapi`
  - [ ] `uvicorn`
  - [ ] `sqlalchemy`
  - [ ] `alembic`
  - [ ] `python-dotenv`
  - [ ] `supabase` (dla auth, później)

**Szacowany czas:** 1-2 godziny

---

#### 2.2 Database Connection & Models
- [ ] Skonfigurować SQLAlchemy engine i session
- [ ] Stworzyć SQLAlchemy models (database.py):
  - [ ] `Category`, `Template`, `TemplateSnapshot`
  - [ ] `Creator`, `CreatorSnapshot`
  - [ ] `JobRun`

- [ ] Przetestować connection i basic queries

**Szacowany czas:** 1 dzień

---

#### 2.3 Basic API Structure
- [ ] Stworzyć `main.py` z FastAPI app
- [ ] Skonfigurować CORS middleware
- [ ] Dodać basic health check endpoint (`/health`)
- [ ] Przetestować uruchomienie (`uvicorn api.main:app --reload`)

**Szacowany czas:** 2-3 godziny

---

### PRIORYTET 3: ETAP 1 Endpoints (Foundation)

#### 3.1 Categories Endpoints
- [ ] `GET /api/categories` — lista kategorii
  - [ ] Query params: sort, order, limit, offset
  - [ ] Response: lista z podstawowymi metrykami
  - [ ] Testy: sprawdzić różne kombinacje query params

- [ ] `GET /api/categories/{slug}` — szczegóły kategorii
  - [ ] Response: pełne dane kategorii + metryki
  - [ ] Testy: valid slug, invalid slug (404)

**Szacowany czas:** 1 dzień

---

#### 3.2 Templates Endpoints
- [ ] `GET /api/templates` — lista szablonów
  - [ ] Query params: category, creator, sort, order, min_price, max_price, min_views, limit, offset
  - [ ] Response: lista szablonów z podstawowymi danymi
  - [ ] Testy: filtrowanie, sortowanie, paginacja

- [ ] `GET /api/templates/{slug}` — szczegóły szablonu
  - [ ] Response: pełne dane szablonu
  - [ ] Testy: valid slug, invalid slug (404)

**Szacowany czas:** 1-2 dni

---

#### 3.3 Creators Endpoints
- [ ] `GET /api/creators` — lista twórców
  - [ ] Query params: sort, order, min_templates, limit, offset
  - [ ] Response: lista twórców z podstawowymi statystykami
  - [ ] Testy: sortowanie, filtrowanie

- [ ] `GET /api/creators/{handle}` — szczegóły twórcy
  - [ ] Response: pełne dane twórcy + lista szablonów
  - [ ] Testy: valid handle, invalid handle (404)

**Szacowany czas:** 1 dzień

---

#### 3.4 Market Context Endpoint
- [ ] Stworzyć `data/market_context.json` z danymi payoutów
- [ ] Stworzyć `services/market_context.py` z helper functions
- [ ] `GET /api/market/context` — globalne dane rynkowe
  - [ ] Response: latest payout, historical payouts, summary
  - [ ] Testy: sprawdzić czy dane są poprawnie zwracane

**Szacowany czas:** 2-3 godziny

---

### PRIORYTET 4: Derived Metrics & Calculations

#### 4.1 Difficulty Score Calculator
- [ ] Zaimplementować `calculate_difficulty()` zgodnie z PRODUCT_ROADMAP:
  - [ ] Quantile normalization
  - [ ] Wzór: `qnorm(templates_count) × 0.6 + qnorm(views_per_template) × 0.4`
  - [ ] Buckets: Low / Medium / High / Very High

- [ ] Dodać do response `GET /api/categories/{slug}`

**Szacowany czas:** 1 dzień

---

#### 4.2 Estimated Revenue Calculator
- [ ] Zaimplementować `estimate_template_revenue()`:
  - [ ] Używa `get_latest_market_payout()` z market_context
  - [ ] Wzór: `(template_views / total_market_views) × latest_payout`

- [ ] Dodać do response `GET /api/templates/{slug}` i `GET /api/templates`

**Szacowany czas:** 2-3 godziny

---

#### 4.3 Category Volume & Basic Metrics
- [ ] Zaimplementować agregacje dla kategorii:
  - [ ] Total views per category
  - [ ] Average views per template
  - [ ] Average price per category
  - [ ] Templates count

- [ ] Dodać do response `GET /api/categories` i `GET /api/categories/{slug}`

**Szacowany czas:** 1 dzień

---

### PRIORYTET 5: Error Handling & Documentation

#### 5.1 Error Handling
- [ ] Stworzyć standard error response format
- [ ] Dodać error handlers:
  - [ ] 404 Not Found
  - [ ] 422 Validation Error
  - [ ] 500 Server Error

- [ ] Przetestować error responses

**Szacowany czas:** 2-3 godziny

---

#### 5.2 Rate Limiting (Basic)
- [ ] Dodać rate limiting middleware (dla ETAP 1: prosty, np. 100 req/min)
- [ ] Dodać rate limit headers
- [ ] Przetestować rate limiting

**Szacowany czas:** 1 dzień

---

#### 5.3 API Documentation
- [ ] Sprawdzić czy Swagger UI działa (`/docs`)
- [ ] Zweryfikować czy wszystkie endpointy są udokumentowane
- [ ] Dodać przykładowe responses w docstrings

**Szacowany czas:** 1-2 godziny

---

### PRIORYTET 6: Testing & Validation

#### 6.1 Unit Tests
- [ ] Testy dla services (market_context, metrics calculator)
- [ ] Testy dla database queries
- [ ] Testy dla Pydantic schemas

**Szacowany czas:** 2-3 dni

---

#### 6.2 Integration Tests
- [ ] Testy dla endpointów (GET requests)
- [ ] Testy dla query params i filtrowania
- [ ] Testy dla error handling

**Szacowany czas:** 1-2 dni

---

#### 6.3 Manual Testing
- [ ] Przetestować wszystkie endpointy w Swagger UI
- [ ] Przetestować z Postman/curl
- [ ] Sprawdzić performance (response times)

**Szacowany czas:** 1 dzień

---

## 📅 Timeline Implementacji

### Tydzień 1: Database Foundation
- **Dzień 1-2:** Setup Supabase + Schema migration
- **Dzień 3-4:** Migracja danych z JSON do PostgreSQL
- **Dzień 5:** Update scrapera do zapisu do PostgreSQL

### Tydzień 2: FastAPI Setup + Basic Endpoints
- **Dzień 1:** Projekt structure + Database connection
- **Dzień 2-3:** Categories endpoints
- **Dzień 4-5:** Templates endpoints

### Tydzień 3: Creators + Market Context + Metrics
- **Dzień 1:** Creators endpoints
- **Dzień 2:** Market context endpoint
- **Dzień 3-4:** Derived metrics (Difficulty, Revenue)
- **Dzień 5:** Error handling + Rate limiting

### Tydzień 4: Testing + Documentation
- **Dzień 1-2:** Unit tests
- **Dzień 3:** Integration tests
- **Dzień 4:** Manual testing + Documentation
- **Dzień 5:** Bug fixes + Final polish

---

## 🎯 Definition of Done

API jest gotowe gdy:

- [ ] ✅ Wszystkie endpointy ETAP 1 działają (Categories, Templates, Creators, Market Context)
- [ ] ✅ Dane są w PostgreSQL (nie w JSON)
- [ ] ✅ Scraper zapisuje do PostgreSQL (nie do JSON)
- [ ] ✅ Difficulty Score i Estimated Revenue są obliczane i zwracane
- [ ] ✅ Error handling działa poprawnie
- [ ] ✅ Rate limiting działa
- [ ] ✅ Swagger UI pokazuje wszystkie endpointy
- [ ] ✅ Podstawowe testy przechodzą
- [ ] ✅ API jest deployowane (lokalnie lub na staging)

---

## 🚨 Blokery i Zależności

### Blokery (muszą być zrobione najpierw):
1. **Supabase setup** — bez tego nie ma bazy danych
2. **Schema migration** — bez tego nie ma struktury danych
3. **Migracja danych** — bez tego API nie ma danych do zwracania

### Zależności:
- **Difficulty Score** wymaga danych w PostgreSQL (agregacje)
- **Estimated Revenue** wymaga market_context.json
- **Error handling** wymaga działających endpointów

---

## 📝 Notatki

- **Market Context:** Dla ETAP 1 wystarczy JSON file — można później zrobić migrację do DB
- **Caching:** Dla ETAP 1 wystarczy in-memory cache — Redis później
- **Authentication:** Dla ETAP 1 nie jest potrzebne — API jest publiczne
- **Testing:** Zacznij od manual testing w Swagger UI, potem dodaj automatyzację

---

**Wersja:** 1.0  
**Ostatnia aktualizacja:** 2025-01-XX  
**Status:** Ready to Start

