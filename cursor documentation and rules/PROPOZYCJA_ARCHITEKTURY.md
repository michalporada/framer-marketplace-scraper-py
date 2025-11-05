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
│   │   ├── category_scraper.py      # Scraper kategorii
│   │   └── sitemap_scraper.py       # Scraper sitemap.xml
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── product_parser.py       # Parsowanie danych produktu
│   │   ├── creator_parser.py       # Parsowanie danych twórcy
│   │   └── category_parser.py       # Parsowanie danych kategorii
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product.py              # Model Pydantic produktu
│   │   ├── creator.py              # Model Pydantic twórcy
│   │   └── category.py             # Model Pydantic kategorii
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   └── file_storage.py         # Zapis do plików (JSON, CSV)
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── rate_limiter.py        # Ograniczenie częstotliwości requestów
│   │   ├── user_agents.py          # Rotacja User-Agent
│   │   ├── logger.py               # Konfiguracja logowania
│   │   ├── retry.py                # Retry logic
│   │   ├── normalizers.py          # Normalizacja dat i statystyk (Opcja B) ⭐
│   │   ├── checkpoint.py           # Checkpoint system (resume capability)
│   │   └── metrics.py              # Tracking metryk scrapowania
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py             # Konfiguracja (pydantic-settings)
│   │
│   └── main.py                     # Entry point aplikacji
│
├── data/
│   ├── products/                   # Zapisane dane produktów (JSON)
│   │   ├── templates/              # Szablony ({product_id}.json)
│   │   ├── components/             # Komponenty ({product_id}.json)
│   │   ├── vectors/                # Wektory ({product_id}.json)
│   │   └── plugins/                 # Wtyczki ({product_id}.json) ⭐
│   ├── creators/                   # Profile twórców jako osobne pliki JSON ({username}.json)
│   ├── categories/                 # Zapisane dane kategorii (JSON)
│   ├── exports/                    # Eksporty CSV
│   └── images/                     # Pobrane obrazy
│
├── logs/                           # Logi scrapera
│
├── tests/
│   ├── __init__.py
│   ├── fixtures/                      # Pliki danych testowych (HTML, JSON, XML)
│   │   ├── html/                      # HTML fixtures dla różnych typów stron
│   │   │   ├── products/              # Strony produktów
│   │   │   ├── creators/              # Profile twórców
│   │   │   ├── categories/            # Strony kategorii
│   │   │   └── sitemap/               # Pliki sitemap.xml
│   │   ├── json/                      # JSON fixtures dla różnych scenariuszy
│   │   │   ├── products/              # Dane produktów
│   │   │   ├── creators/              # Dane twórców
│   │   │   └── categories/            # Dane kategorii
│   │   └── README.md                  # Dokumentacja fixture'ów
│   ├── conftest.py                    # Główne fixture'y współdzielone
│   ├── test_scrapers/
│   │   ├── __init__.py
│   │   ├── conftest.py                # Fixture'y specyficzne dla scrapers
│   │   └── test_sitemap_scraper.py
│   ├── test_parsers/
│   │   ├── __init__.py
│   │   ├── conftest.py                # Fixture'y specyficzne dla parsers
│   │   └── test_product_parser.py
│   ├── test_models/
│   │   ├── __init__.py
│   │   ├── conftest.py                # Fixture'y specyficzne dla models
│   │   └── test_product.py
│   └── test_utils/
│       ├── __init__.py
│       ├── conftest.py                # Fixture'y specyficzne dla utils
│       └── test_normalizers.py

**📚 Dokumentacja testów:** Zobacz [`TESTING_AND_FIXTURES.md`](./TESTING_AND_FIXTURES.md) dla pełnej dokumentacji struktury testów, fixture'ów i best practices.
│
├── scripts/
│   ├── setup_db.py                 # Setup bazy danych (PostgreSQL/MongoDB)
│   └── export_data.py              # Export danych do CSV
│   # clean_data.py - nie zaimplementowane (opcjonalne)
│
│   # docs/ - folder nie istnieje (dokumentacja w głównym katalogu)
│
├── .env.example                    # Przykładowe zmienne środowiskowe
├── .gitignore
├── pyproject.toml                   # Python project config (poetry/pip)
├── requirements.txt                 # Zależności Python
├── requirements-dev.txt             # Zależności dev
├── pytest.ini                       # Konfiguracja pytest
├── cursor documentation and rules/  # Dokumentacja techniczna
│   ├── REKOMENDACJE_SCRAPERA_FRAMER.md
│   ├── PROPOZYCJA_ARCHITEKTURY.md
│   └── STACK_TECHNICZNY.md
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
- Ekstrahuje: nazwa, cena, opis, funkcje, obrazy, typ produktu, kategorie
- Używa selektorów CSS z dokumentacji
- Identyfikuje typ produktu z URL lub HTML
- **Components Installs**: Wyciągane z JSON danych Next.js (priorytet) lub z HTML tekstu. Może być niedostępne dla niektórych komponentów.
- Dekodowanie URL-i obrazów Next.js do oryginalnych URL-i

#### `category_parser.py`
- Parsuje stronę kategorii
- Ekstrahuje: nazwa kategorii, opis, liczbę produktów, typy produktów, subkategorie
- **find_product_position()**: Znajduje pozycję produktu w kategorii (od lewej do prawej, od góry do dołu, 1-indexed). Tylko dla szablonów.

#### `creator_parser.py`
- Parsuje profil twórcy
- Ekstrahuje: statystyki, produkty, bio, social media, avatar
- Profil jest zapisywany jako osobny plik JSON: `data/creators/{username}.json`
- **Avatar**: Wyciągany z JSON danych Next.js (priorytet), pomijane placeholdery API
- **Social Media**: Wyciągane z JSON danych Next.js, automatycznie filtrowane linki Framer. Obsługiwane: Twitter/X, LinkedIn, Instagram, GitHub, Dribbble, Behance, YouTube


### 3. Models (`src/models/`)

#### Pydantic Models

**Product Model (Normalizacja):**
- **NormalizedDate:** Format daty z surowym i znormalizowanym formatem
  - `raw`: Format surowy z HTML (np. "5 months ago", "3mo ago")
  - `normalized`: ISO 8601 (np. "2024-10-15T00:00:00Z")
- **NormalizedStatistic:** Format statystyki z surowym i znormalizowanym formatem
  - `raw`: Format surowy z HTML (np. "19.8K Views", "1,200 Vectors")
  - `normalized`: Liczba całkowita (np. 19800, 1200)
- **ProductStats:** Statystyki produktu (różne dla różnych typów)
  - `views`, `pages`, `users`, `installs`, `vectors`
  - Wszystkie jako `NormalizedStatistic`
- **ProductMetadata:** Metadane produktu
  - `published_date`, `last_updated` jako `NormalizedDate`
  - `version` (string, dla plugins)
- **Product:** Główny model produktu
  - Typ produktu: `template`, `component`, `vector`, **`plugin`** ⭐
  - Obsługa wszystkich pól z dokumentacji
  - Wszystkie daty i statystyki w formacie znormalizowanym
  - **category_positions**: Pozycja produktu w każdej kategorii (Dict[str, int]) - tylko dla szablonów

**Creator Model:**
- **Creator:** Walidacja danych twórcy
  - Username może zawierać znaki specjalne (np. `/@-790ivi/`)
  - Lista produktów (templates/components/vectors/plugins)

**Category Model:**
- **Category:** Walidacja danych kategorii
  - Nazwa, URL, opis, lista produktów

**Automatyczna serializacja:** Wszystkie modele automatycznie serializują do JSON

**UWAGA:** Recenzje nie są dostępne na Framer Marketplace, więc nie są zbierane.

### 4. Storage (`src/storage/`)

#### `file_storage.py`
- Zapis produktów do JSON (jeden plik per produkt: `products/{type}/{product_id}.json`)
- Zapis kreatorów do JSON (jeden plik per kreator: `creators/{username}.json`)
- Zapis kategorii do JSON (jeden plik per kategoria: `categories/{slug}.json`)
- Eksport produktów do CSV (`export_products_to_csv()`)
- Eksport kreatorów do CSV (`export_creators_to_csv()`)
- **Zawsze nadpisuje pliki** - produkty są zawsze aktualizowane z najnowszymi danymi (views, ceny, stats)
- Dodaje timestamp `scraped_at` do każdego produktu

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
- **Normalizacja dat**:
  - `parse_relative_date()`: Konwertuje "X months ago" → ISO 8601
  - Obsługuje formaty: "X months ago", "Xmo ago", "Xw ago", "X days ago"
  - Zwraca: `{"raw": "...", "normalized": "ISO 8601"}`
- **Normalizacja statystyk**:
  - `parse_statistic()`: Konwertuje "19.8K Views" → 19800
  - Obsługuje formaty: "X.XK", "XK", "X,XXX", "XXX"
  - Zwraca: `{"raw": "...", "normalized": int}`
- **Użycie:** Parser wywołuje normalizatory przed zapisem do modelu

#### `checkpoint.py`
- System checkpoint do zapisywania postępu scrapowania
- Zapisuje przetworzone URL-e i nieudane URL-e
- **Automatyczny retry failed URLs** - na końcu scrapowania ponawia próbę dla nieudanych URL-i
- Zapis do `data/checkpoint.json`
- **Uwaga**: Checkpoint służy głównie do śledzenia błędów i retry, nie do pomijania już przetworzonych (produkty są zawsze aktualizowane)

#### `metrics.py`
- Tracking metryk scrapowania
- Śledzi: liczbę produktów, kreatorów, kategorii, czas wykonania, success rate
- Logowanie podsumowania po zakończeniu scrapowania

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
   ├─▶ sitemap_scraper.py → pobierz sitemap.xml
   │   ├─▶ Spróbuj: `/marketplace/sitemap.xml`
   │   └─▶ Fallback: `/sitemap.xml` (jeśli marketplace nie działa)
   ├─▶ Wyodrębnij wszystkie URL-e:
   │   ├─▶ Produkty:
   │   │   ├─▶ Templates: `/marketplace/templates/{nazwa}/`
   │   │   ├─▶ Components: `/marketplace/components/{nazwa}/`
   │   │   ├─▶ Vectors: `/marketplace/vectors/{nazwa}/`
   │   │   └─▶ Plugins: `/marketplace/plugins/{nazwa}/` ⭐
   │   ├─▶ Kategorie: `/marketplace/category/{nazwa}/`
   │   ├─▶ Profile: `/@{username}/` (wszystko z `@`)
   │   └─▶ Strony pomocowe: `/help/articles/...marketplace...`
   └─▶ Filtruj według typu (templates/components/vectors/plugins)
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
   │   ├─▶ save_creator_json() → zapisz profil twórcy jako osobny plik (data/creators/{username}.json)
   │   ├─▶ (Tylko dla szablonów) Dla każdej kategorii produktu:
   │   │   ├─▶ category_scraper.py → pobierz stronę kategorii
   │   │   ├─▶ category_parser.find_product_position() → znajdź pozycję produktu
   │   │   └─▶ Zapisz pozycję w product.category_positions[category]
   │   ├─▶ Walidacja danych (Pydantic)
   │   ├─▶ Zapis danych (file_storage.py)
   │   │   ├─▶ Zapis produktu: products/{type}/{product_id}.json (zawsze nadpisuje - aktualizuje views, ceny, stats)
   │   │   └─▶ Zapis kreatora: creators/{username}.json (osobny plik)
   │   ├─▶ Aktualizacja checkpoint (checkpoint.py)
   │   └─▶ Na końcu scrapowania: Retry failed URLs (ponowna próba dla nieudanych URL-i)
   │
4b. SCRAPE CATEGORIES
   ├─▶ Dla każdej kategorii z sitemap:
   │   ├─▶ category_scraper.py → pobierz `/marketplace/category/{nazwa}/`
   │   ├─▶ category_parser.py → ekstrahuj:
   │   │   ├─▶ Nazwa kategorii
   │   │   ├─▶ Opis kategorii
   │   │   ├─▶ Lista produktów w kategorii
   │   │   └─▶ Liczba produktów
   │   └─▶ Zapis danych kategorii
   │
4c. SCRAPE PROFILES
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
   ├─▶ Zapis do JSON/CSV (file_storage.py)
   │   └─▶ Zawsze nadpisuje pliki - aktualizuje views, ceny, stats
   ├─▶ Zapis checkpoint (checkpoint.py)
   ├─▶ Retry failed URLs (ponowna próba dla nieudanych URL-i)
   │   └─▶ Z niższą współbieżnością (max 3 concurrent) aby nie przeciążać serwera
   ├─▶ Logowanie metryk (metrics.py)
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

### Data Normalization ⭐
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
5. ✅ Implementuj normalizację danych ⭐
   - `utils/normalizers.py` z funkcjami parse_relative_date() i parse_statistic()
   - Modele Pydantic z NormalizedDate i NormalizedStatistic
6. ✅ Test na małej próbce (10-20 produktów)

### Faza 2: Rozszerzenie
1. ✅ Dodaj scraping wszystkich typów produktów (templates/components/vectors/**plugins**)
2. ✅ Dodaj scraping twórców
3. ✅ Dodaj scraping kategorii
4. ✅ Setup GitHub Actions
5. ✅ Monitoring i metryki

---

*Dokument wygenerowany na podstawie REKOMENDACJE_SCRAPERA_FRAMER.md*

