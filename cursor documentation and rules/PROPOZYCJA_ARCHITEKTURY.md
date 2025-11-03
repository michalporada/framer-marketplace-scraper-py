# Propozycja Architektury Projektu - Scraper Framer Marketplace

## 📁 Struktura Projektu

```
scraper-v2/
├── .github/
│   └── workflows/
│       ├── scrape.yml              # GitHub Actions - scheduled scraping
│       ├── ci.yml                   # GitHub Actions - CI/CD
│       └── backup.yml               # GitHub Actions - backup danych
│
├── src/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── marketplace_scraper.py  # Główny scraper marketplace
│   │   ├── product_scraper.py       # Scraper pojedynczego produktu
│   │   ├── creator_scraper.py       # Scraper profilu twórcy
│   │   ├── category_scraper.py      # Scraper kategorii (opcjonalnie)
│   │   └── sitemap_scraper.py       # Scraper sitemap.xml
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── product_parser.py       # Parsowanie danych produktu
│   │   ├── creator_parser.py       # Parsowanie danych twórcy
│   │   ├── category_parser.py       # Parsowanie danych kategorii (opcjonalnie)
│   │   └── review_parser.py        # Parsowanie recenzji
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product.py              # Model Pydantic produktu
│   │   ├── creator.py              # Model Pydantic twórcy
│   │   ├── category.py             # Model Pydantic kategorii (opcjonalnie)
│   │   └── review.py               # Model Pydantic recenzji
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py             # Połączenie z bazą danych
│   │   ├── file_storage.py         # Zapis do plików (JSON, CSV)
│   │   └── backup.py               # Backup danych
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── rate_limiter.py        # Ograniczenie częstotliwości requestów
│   │   ├── user_agents.py          # Rotacja User-Agent
│   │   ├── logger.py               # Konfiguracja logowania
│   │   ├── retry.py                # Retry logic
│   │   ├── validators.py           # Walidacja danych
│   │   └── normalizers.py          # Normalizacja dat i statystyk (Opcja B) ⭐
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py             # Konfiguracja (pydantic-settings)
│   │
│   └── main.py                     # Entry point aplikacji
│
├── api/                            # (Opcjonalnie) API endpoints
│   ├── __init__.py
│   ├── main.py                     # FastAPI app
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── products.py
│   │   ├── creators.py
│   │   └── reviews.py
│   └── dependencies.py
│
├── frontend/                       # (Opcjonalnie) Dashboard
│   ├── package.json
│   ├── next.config.js
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   └── public/
│
├── data/
│   ├── products/                   # Zapisane dane produktów (JSON)
│   │   ├── templates/              # Szablony
│   │   ├── components/             # Komponenty
│   │   ├── vectors/                # Wektory
│   │   └── plugins/                 # Wtyczki ⭐
│   ├── creators/                   # Zapisane dane twórców (JSON)
│   ├── categories/                 # Zapisane dane kategorii (JSON) (opcjonalnie)
│   ├── exports/                    # Eksporty CSV
│   └── images/                     # Pobrane obrazy (opcjonalnie)
│
├── logs/                           # Logi scrapera
│
├── tests/
│   ├── __init__.py
│   ├── test_scrapers/
│   ├── test_parsers/
│   ├── test_models/
│   └── fixtures/
│
├── scripts/
│   ├── setup_db.py                 # Setup bazy danych
│   └── export_data.py              # Export danych do CSV
│   # clean_data.py - nie zaimplementowane (opcjonalne)
│
│   # docs/ - folder nie istnieje (dokumentacja w głównym katalogu i README.md)
│
├── .env.example                    # Przykładowe zmienne środowiskowe
├── .gitignore
├── .pre-commit-config.yaml          # Pre-commit hooks
├── pyproject.toml                   # Python project config (poetry/pip)
├── requirements.txt                 # Zależności Python
├── requirements-dev.txt             # Zależności dev
├── README.md
├── STACK_TECHNICZNY.md              # Dokument o stacku
└── PROPOZYCJA_ARCHITEKTURY.md      # Ten dokument
```

## 🔧 Komponenty Systemu

### 1. Scrapers (`src/scrapers/`)

#### `marketplace_scraper.py`
- Główny orchestrator scrapowania
- Koordynuje pracę innych scraperów
- Zarządza kolejką URL-i do przetworzenia
- Obsługuje resume capability

#### `sitemap_scraper.py`
- Pobiera i parsuje `sitemap.xml` (marketplace lub główny sitemap)
- Wyodrębnia wszystkie URL-e:
  - **Produkty**: templates, components, vectors, **plugins** ⭐
  - **Kategorie**: `/marketplace/category/{nazwa}/`
  - **Profile**: `/@{username}/` (wszystko zaczynające się od `@`)
  - **Strony pomocowe**: `/help/articles/...marketplace...`
- Filtruje według typu produktu
- Obsługuje fallback jeśli marketplace sitemap nie działa

#### `product_scraper.py`
- Scrapuje pojedynczy produkt (template/component/vector/**plugin**)
- Obsługuje wszystkie typy produktów:
  - Templates: `/marketplace/templates/{nazwa}/`
  - Components: `/marketplace/components/{nazwa}/`
  - Vectors: `/marketplace/vectors/{nazwa}/`
  - **Plugins**: `/marketplace/plugins/{nazwa}/` ⭐
- Pobiera stronę produktu
- Wywołuje parsery do ekstrakcji danych

#### `creator_scraper.py`
- Scrapuje profil twórcy (`/@username/`)
- **UWAGA**: Username może zawierać znaki specjalne (np. `/@-790ivi/`)
- Obsługuje wszystkie profile zaczynające się od `@`
- Pobiera statystyki twórcy
- Zbiera informacje o wszystkich produktach twórcy (templates/components/vectors/plugins)

### 2. Parsers (`src/parsers/`)

#### `product_parser.py`
- Parsuje HTML strony produktu
- Obsługuje wszystkie typy produktów (templates/components/vectors/**plugins**)
- Ekstrahuje: nazwa, cena, opis, funkcje, obrazy, recenzje, typ produktu
- Używa selektorów CSS z dokumentacji
- Identyfikuje typ produktu z URL lub HTML

#### `creator_parser.py`
- Parsuje profil twórcy
- Ekstrahuje: statystyki, produkty, bio, social media

#### `review_parser.py`
- Parsuje recenzje produktu
- Ekstrahuje: ocena, treść, autor, data

### 3. Models (`src/models/`)

#### Pydantic Models

**Product Model (Opcja B - Normalizacja):**
- **NormalizedDate:** Format daty z surowym i znormalizowanym formatem
  - `raw`: Format surowy z HTML (np. "5 months ago", "3mo ago")
  - `normalized`: ISO 8601 (np. "2024-10-15T00:00:00Z")
- **NormalizedStatistic:** Format statystyki z surowym i znormalizowanym formatem
  - `raw`: Format surowy z HTML (np. "19.8K Views", "1,200 Vectors")
  - `normalized`: Liczba całkowita (np. 19800, 1200)
- **ProductStats:** Statystyki produktu (różne dla różnych typów)
  - `views`, `pages`, `users`, `installs`, `vectors` (opcjonalnie)
  - Wszystkie jako `NormalizedStatistic`
- **ProductMetadata:** Metadane produktu
  - `published_date`, `last_updated` jako `NormalizedDate`
  - `version` (string, dla plugins)
- **Product:** Główny model produktu
  - Typ produktu: `template`, `component`, `vector`, **`plugin`** ⭐
  - Obsługa wszystkich pól z dokumentacji
  - Wszystkie daty i statystyki w formacie Opcji B

**Creator Model:**
- **Creator:** Walidacja danych twórcy
  - Username może zawierać znaki specjalne (np. `/@-790ivi/`)
  - Lista produktów (templates/components/vectors/plugins)

**Category Model (opcjonalnie):**
- **Category:** Walidacja danych kategorii
  - Nazwa, URL, opis, lista produktów

**Review Model:**
- **Review:** Walidacja recenzji
  - Ocena, treść, autor, data

**Automatyczna serializacja:** Wszystkie modele automatycznie serializują do JSON

### 4. Storage (`src/storage/`)

#### `file_storage.py`
- Zapis do JSON (jeden plik per produkt)
- Zapis do CSV (dla analiz)
- Incremental saves (zapis przyrostowy)

#### `database.py`
- Połączenie z PostgreSQL/MongoDB
- Zapis danych przez SQLAlchemy/ORM
- Migracje schematu

#### `backup.py`
- Backup danych do GitHub Releases
- Backup do cloud storage (S3, etc.)

### 5. Utils (`src/utils/`)

#### `rate_limiter.py`
- Ograniczenie do 1-2 req/s
- Randomizacja opóźnień
- Respektowanie robots.txt

#### `retry.py`
- Exponential backoff
- Obsługa timeoutów
- Retry logic dla failed requests

#### `logger.py`
- Strukturalne logowanie (structlog)
- Różne poziomy logowania
- Rotacja logów

#### `normalizers.py` ⭐
- **Normalizacja dat** (Opcja B):
  - `parse_relative_date()`: Konwertuje "X months ago" → ISO 8601
  - Obsługuje formaty: "X months ago", "Xmo ago", "Xw ago", "X days ago"
  - Zwraca: `{"raw": "...", "normalized": "ISO 8601"}`
- **Normalizacja statystyk** (Opcja B):
  - `parse_statistic()`: Konwertuje "19.8K Views" → 19800
  - Obsługuje formaty: "X.XK", "XK", "X,XXX", "XXX"
  - Zwraca: `{"raw": "...", "normalized": int}`
- **Użycie:** Parser wywołuje normalizatory przed zapisem do modelu

## 🔄 Flow Scrapowania

```
1. START
   │
   ├─▶ main.py (entry point)
   │
2. INITIALIZATION
   ├─▶ Wczytaj konfigurację (.env)
   ├─▶ Sprawdź robots.txt
   ├─▶ Inicjalizuj logger
   └─▶ Przygotuj sesję HTTP
   │
3. GET PRODUCT LIST
   ├─▶ OPCJA A: Sitemap (REKOMENDOWANE) ⭐
   │   ├─▶ sitemap_scraper.py → pobierz sitemap.xml
   │   │   ├─▶ Spróbuj: `/marketplace/sitemap.xml`
   │   │   └─▶ Fallback: `/sitemap.xml` (jeśli marketplace nie działa)
   │   ├─▶ Wyodrębnij wszystkie URL-e:
   │   │   ├─▶ Produkty:
   │   │   │   ├─▶ Templates: `/marketplace/templates/{nazwa}/`
   │   │   │   ├─▶ Components: `/marketplace/components/{nazwa}/`
   │   │   │   ├─▶ Vectors: `/marketplace/vectors/{nazwa}/`
   │   │   │   └─▶ Plugins: `/marketplace/plugins/{nazwa}/` ⭐
   │   │   ├─▶ Kategorie: `/marketplace/category/{nazwa}/`
   │   │   ├─▶ Profile: `/@{username}/` (wszystko z `@`)
   │   │   └─▶ Strony pomocowe: `/help/articles/...marketplace...`
   │   └─▶ Filtruj według typu (templates/components/vectors/plugins)
   │
   └─▶ OPCJA B: Scraping listy
       ├─▶ marketplace_scraper.py → pobierz /marketplace
       └─▶ Parsuj karty produktów
   │
4. SCRAPE PRODUCTS
   ├─▶ Dla każdego produktu (równolegle z limitem):
   │   ├─▶ product_scraper.py → pobierz stronę produktu
   │   │   └─▶ Obsługuje: templates/components/vectors/**plugins** ⭐
   │   ├─▶ product_parser.py → ekstrahuj dane
   │   │   └─▶ Identyfikuj typ produktu (template/component/vector/plugin)
   │   ├─▶ creator_scraper.py → pobierz profil twórcy (`/@username/`)
   │   │   └─▶ Obsługuje username z znakami specjalnymi
   │   ├─▶ creator_parser.py → ekstrahuj dane twórcy
   │   ├─▶ review_parser.py → ekstrahuj recenzje
   │   ├─▶ Walidacja danych (Pydantic)
   │   └─▶ Zapis danych (file_storage.py lub database.py)
   │       └─▶ Organizuj według typu: products/templates/, products/components/, etc.
   │
4b. SCRAPE CATEGORIES (opcjonalnie)
   ├─▶ Dla każdej kategorii z sitemap:
   │   ├─▶ category_scraper.py → pobierz `/marketplace/category/{nazwa}/`
   │   ├─▶ category_parser.py → ekstrahuj:
   │   │   ├─▶ Nazwa kategorii
   │   │   ├─▶ Opis kategorii
   │   │   ├─▶ Lista produktów w kategorii
   │   │   └─▶ Liczba produktów
   │   └─▶ Zapis danych kategorii
   │
4c. SCRAPE PROFILES (opcjonalnie)
   ├─▶ Dla każdego profilu z sitemap (`/@username/`):
   │   ├─▶ creator_scraper.py → pobierz profil
   │   │   └─▶ Obsługuje username z znakami specjalnymi (np. `/@-790ivi/`)
   │   ├─▶ creator_parser.py → ekstrahuj:
   │   │   ├─▶ Username (z URL)
   │   │   ├─▶ Nazwa wyświetlana
   │   │   ├─▶ Bio/opis
   │   │   ├─▶ Avatar
   │   │   ├─▶ Lista produktów (templates/components/vectors/plugins)
   │   │   ├─▶ Statystyki
   │   │   └─▶ Linki do social media
   │   └─▶ Zapis danych profilu
   │
5. POST-PROCESSING
   ├─▶ Czyszczenie danych
   ├─▶ Normalizacja danych (Opcja B) ⭐
   │   ├─▶ normalizers.py → parse_relative_date() dla dat
   │   └─▶ normalizers.py → parse_statistic() dla statystyk
   ├─▶ Weryfikacja kompletności
   ├─▶ Dekodowanie URL-i obrazów (Next.js Image → oryginalny URL)
   └─▶ Generowanie raportów
   │
6. SAVE & BACKUP
   ├─▶ Zapis do JSON/CSV
   ├─▶ Zapis do bazy danych (opcjonalnie)
   └─▶ Backup (GitHub Actions artifacts)
   │
7. END
```

## 🚀 Deployment Strategy

### GitHub Actions Workflows

#### 1. `.github/workflows/scrape.yml`
```yaml
name: Daily Scrape
on:
  schedule:
    - cron: '0 2 * * *'  # Codziennie o 2:00 UTC
  workflow_dispatch:     # Ręczne uruchomienie

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run scraper
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python src/main.py
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: scraped-data
          path: data/
```

#### 2. `.github/workflows/ci.yml`
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest
      - name: Lint
        run: ruff check .
      - name: Type check
        run: mypy src/
```

### Vercel Deployment (Opcjonalnie)

#### Struktura dla API:
```
api/
├── main.py              # FastAPI app
├── vercel.json          # Vercel config
└── routes/
```

#### `vercel.json`:
```json
{
  "builds": [
    {
      "src": "api/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/main.py"
    }
  ]
}
```

## 📊 Monitoring & Logging

### Logging Structure
```python
# Przykład użycia structlog
logger.info("scraping_started", product_count=1000)
logger.info("product_scraped", product_id="123", status="success")
logger.error("scraping_failed", error="timeout", retry_count=2)
```

### Metrics to Track
- Liczba przetworzonych produktów
- Liczba błędów
- Czas scrapowania
- Success rate
- Rate limit violations

### Notifications
- GitHub Actions: email/Slack o statusie
- Error tracking: Sentry (opcjonalnie)

## 🔐 Security & Best Practices

### Environment Variables
```bash
# .env.example
DATABASE_URL=postgresql://...
FRAMER_BASE_URL=https://www.framer.com
MARKETPLACE_SITEMAP_URL=https://www.framer.com/marketplace/sitemap.xml
MAIN_SITEMAP_URL=https://www.framer.com/sitemap.xml  # Fallback
RATE_LIMIT=1.0
MAX_RETRIES=3
LOG_LEVEL=INFO
# Opcjonalne - typy produktów do scrapowania
SCRAPE_TEMPLATES=true
SCRAPE_COMPONENTS=true
SCRAPE_VECTORS=true
SCRAPE_PLUGINS=true  # ⭐
SCRAPE_CATEGORIES=false  # Opcjonalnie
SCRAPE_PROFILES=false  # Opcjonalnie
```

### Rate Limiting
- 1-2 requestów na sekundę
- Randomizacja opóźnień (0.5-2s)
- Respektowanie robots.txt

### Error Handling
- Retry z exponential backoff
- Timeout handling
- Graceful degradation
- Checkpoint system (resume capability)

### Data Validation
- Pydantic models dla wszystkich danych
- Walidacja przed zapisem
- Sprawdzanie wymaganych pól

### Data Normalization (Opcja B) ⭐
- **Normalizacja dat**: Relatywne daty ("X months ago") → ISO 8601
  - Format: `{"raw": "5 months ago", "normalized": "2024-10-15T00:00:00Z"}`
  - Funkcja: `utils/normalizers.py::parse_relative_date()`
- **Normalizacja statystyk**: Skrócone formaty ("19.8K") → liczby całkowite
  - Format: `{"raw": "19.8K Views", "normalized": 19800}`
  - Funkcja: `utils/normalizers.py::parse_statistic()`
- **Zapis obu formatów**: Zapewnia weryfikację i elastyczność analizy
- **Modele Pydantic**: `NormalizedDate`, `NormalizedStatistic` w modelach produktu

## 🎯 Next Steps

### Faza 1: Setup (MVP)
1. ✅ Stwórz strukturę projektu
2. ✅ Setup Python environment (poetry/pip)
3. ✅ Implementuj podstawowy scraper (sitemap → products)
4. ✅ Implementuj rate limiting i error handling
5. ✅ Implementuj normalizację danych (Opcja B) ⭐
   - `utils/normalizers.py` z funkcjami parse_relative_date() i parse_statistic()
   - Modele Pydantic z NormalizedDate i NormalizedStatistic
6. ✅ Test na małej próbce (10-20 produktów)

### Faza 2: Rozszerzenie
1. ⬜ Dodaj scraping wszystkich typów produktów (templates/components/vectors/**plugins**)
2. ⬜ Dodaj scraping twórców i recenzji
3. ⬜ Dodaj scraping kategorii (opcjonalnie)
4. ⬜ Implementuj storage (database)
5. ⬜ Setup GitHub Actions
6. ⬜ Dodaj monitoring i notyfikacje

### Faza 3: Production
1. ⬜ API endpoints (FastAPI/Vercel)
2. ⬜ Dashboard (Next.js/Vercel)
3. ⬜ Production database
4. ⬜ Error tracking (Sentry)

---

*Dokument wygenerowany na podstawie REKOMENDACJE_SCRAPERA_FRAMER.md*

