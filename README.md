# Scraper Framer Marketplace V2

Zaawansowany scraper do zbierania danych z Framer Marketplace, umożliwiający automatyzację pobierania informacji o:

- **Produktach**: Szablony (templates), Komponenty (components), Wektory (vectors), **Wtyczki (plugins)** ⭐
- **Twórcach/Użytkownikach**: Profile z username (może zawierać znaki specjalne)
- **Kategoriach**: Kategorie produktów w marketplace

## 📚 Dokumentacja

### Główne Dokumenty

1. **[DEPLOYMENT_PLAN.md](./docs/DEPLOYMENT_PLAN.md)** - Kompletny plan wdrożenia (Vercel + Railway + Supabase):
   - Krok po kroku instrukcje deploymentu
   - Konfiguracja wszystkich serwisów
   - Troubleshooting i best practices

2. **[STACK_TECHNICZNY.md](./documentation_sources/STACK_TECHNICZNY.md)** - Szczegółowy opis stacku technicznego, w tym:
   - Biblioteki Python i narzędzia
   - Opcje baz danych
   - GitHub Actions i Vercel
   - Rekomendacje deployment

3. **[PROPOZYCJA_ARCHITEKTURY.md](./documentation_sources/PROPOZYCJA_ARCHITEKTURY.md)** - Propozycja struktury projektu:
   - Struktura folderów
   - Opis komponentów
   - Flow scrapowania
   - Deployment strategy

4. **[REKOMENDACJE_SCRAPERA_FRAMER.md](./documentation_sources/REKOMENDACJE_SCRAPERA_FRAMER.md)** - Szczegółowa analiza Framer Marketplace:
   - Analiza techniczna strony
   - Struktura URL-i i selektory CSS
   - Zalecane dane do zbierania
   - Uwagi techniczne

## 🚀 Quick Start

### 1. Instalacja

```bash
# Sklonuj repozytorium
git clone <repo-url>
cd scraper-v2

# Utwórz środowisko wirtualne
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate  # Windows

# Zainstaluj zależności
pip install -r requirements.txt
```

### 2. Konfiguracja

```bash
# Skopiuj przykładowy plik .env
cp .env.example .env

# Edytuj .env z odpowiednimi wartościami
# Większość wartości ma sensowne domyślne ustawienia
```

Główne zmienne środowiskowe:
- `FRAMER_BASE_URL` - URL do Framer (domyślnie: https://www.framer.com)
- `RATE_LIMIT` - Limit requestów na sekundę (domyślnie: 1.0)
- `MAX_RETRIES` - Maksymalna liczba ponownych prób (domyślnie: 3)
- `LOG_LEVEL` - Poziom logowania (INFO, DEBUG, WARNING, ERROR)
- `CHECKPOINT_ENABLED` - Włącz checkpoint system (domyślnie: true)
- `SCRAPE_TEMPLATES`, `SCRAPE_COMPONENTS`, `SCRAPE_VECTORS`, `SCRAPE_PLUGINS` - Typy produktów do scrapowania

### 3. Uruchomienie

```bash
# Podstawowe uruchomienie (scrapuje wszystkie produkty)
python3 -m src.main

# Ograniczenie liczby produktów (np. 10 dla testów)
python3 -m src.main 10

# Scrapowanie tylko określonych typów produktów
python3 -m src.main --templates-only 10    # Tylko szablony
python3 -m src.main --components-only 10   # Tylko komponenty
python3 -m src.main --vectors-only 10      # Tylko wektory
python3 -m src.main --plugins-only 10      # Tylko wtyczki

# Scrapowanie tylko kreatorów
python3 -m src.main --creators-only        # Wszyscy kreatorzy
python3 -m src.main --creators-only 10     # Z limitem
python3 -m src.main -c 10                  # Krótka wersja

# Scrapowanie tylko kategorii
python3 -m src.main --categories-only       # Wszystkie kategorie
python3 -m src.main --categories-only 10   # Z limitem
python3 -m src.main -cat 10                # Krótka wersja

# Export danych do CSV
python scripts/export_data.py

# Export tylko określonego typu produktu
python scripts/export_data.py --type template

# Setup bazy danych (opcjonalnie)
python scripts/setup_db.py --db-type postgresql
```

### 4. GitHub Actions (Automatyzacja)

Scraper może być uruchamiany automatycznie przez GitHub Actions:

- **Scheduled**: Codziennie o 2:00 UTC (zobacz `.github/workflows/scrape.yml`)
- **Manual**: Ręczne uruchomienie przez `workflow_dispatch`

**Zachowanie historii:**
- Najnowsze dane: `data/` (nadpisywane przy każdym scrapie)
- Archiwum z datą: `scraped-data-YYYY-MM-DD/` (zachowuje historię)
- Artifacts w GitHub: 90 dni przechowywania

**Automatyczne porównywanie:**
Po kilku dniach scrapowania możesz porównywać zmiany w czasie przez API (zobacz sekcję API poniżej).

## 🛠️ Stack Techniczny

### Backend
- **Python 3.11+** - język główny
- **httpx** - async HTTP client
- **BeautifulSoup4** - parsowanie HTML
- **pydantic v2** - walidacja danych z normalizacją (Opcja B)
- **pandas** - manipulacja danych i eksport do CSV
- **SQLAlchemy** - ORM (opcjonalnie, dla PostgreSQL)

### Narzędzia
- **structlog** - strukturalne logowanie
- **tenacity** - retry logic z exponential backoff
- **fake-useragent** - rotacja User-Agent headers
- **tqdm** - progress bars

### Deployment & Automation
- **GitHub Actions** - automatyczne scrapowanie (scheduled)
- **Railway** - FastAPI backend (https://framer-marketplace-scraper-py-production.up.railway.app)
- **Vercel** - Next.js frontend (https://framer-marketplace-scraper-py.vercel.app)
- **Supabase** - PostgreSQL database (skonfigurowana)

### Storage
- **JSON/CSV** - podstawowe (zalecane na start)
- **PostgreSQL** - dla większych projektów
- **GitHub Artifacts** - backup danych

## 📋 Funkcjonalności

### ✅ Zaimplementowane

- [x] Scrapowanie produktów z sitemap.xml (templates/components/vectors/**plugins**)
- [x] Scrapowanie danych twórców (profile z `@username`)
- [x] Zapisywanie profilów twórców jako osobne pliki JSON (`data/creators/{username}.json`)
- [x] Scrapowanie kategorii (opcjonalnie)
- [x] Rate limiting i error handling
- [x] Zapis do JSON/CSV (organizacja według typu produktu)
- [x] Eksport kreatorów do CSV (`export_creators_to_csv()`)
- [x] Automatyzacja przez GitHub Actions
- [x] Resume capability (wznowienie po przerwie) - checkpoint system
- [x] Walidacja danych (Pydantic)
- [x] Monitoring i logowanie (structlog)
- [x] Normalizacja danych (Opcja B - raw + normalized)
- [x] Obsługa różnych typów produktów (różne statystyki i pola)

### ✅ API Endpoints (FastAPI)

API jest dostępne i gotowe do użycia:

**Porównywanie produktów w czasie:**
```bash
GET /api/products/{product_id}/changes
```
Porównuje dane produktu między różnymi scrapami, wykrywa zmiany w statystykach, cenie i metadanych.

**Porównywanie kategorii:**
```bash
GET /api/products/categories/comparison
GET /api/products/categories/comparison?product_type=template
GET /api/products/categories/comparison?category=Agency
```
Porównuje łączną liczbę wyświetleń kategorii między scrapami z procentowym wzrostem/spadkiem.

**Inne endpointy:**
- `GET /api/products` - lista produktów
- `GET /api/products/{id}` - pojedynczy produkt
- `GET /api/creators` - lista twórców
- `GET /api/creators/{username}` - pojedynczy twórca

### 🔮 Opcjonalne (Faza 2+)

- [ ] Dashboard (Next.js)
- [ ] Baza danych (PostgreSQL) - setup script gotowy
- [ ] Error tracking (Sentry)
- [ ] Notyfikacje (Slack/Email)

## 📁 Struktura Projektu

```
scraper-v2/
├── src/
│   ├── scrapers/          # Scrapery (sitemap, product, creator, category)
│   ├── parsers/           # Parsery HTML (product, creator, category)
│   ├── models/            # Modele Pydantic (Product, Creator, Category)
│   ├── storage/           # Zapis danych (file_storage, database)
│   ├── utils/             # Narzędzia (logger, rate_limiter, retry, normalizers, checkpoint)
│   ├── config/            # Konfiguracja (settings)
│   └── main.py            # Entry point
├── data/
│   ├── products/          # Zapisane produkty (templates/, components/, vectors/, plugins/)
│   ├── creators/           # Profile twórców jako osobne pliki JSON ({username}.json)
│   ├── categories/         # Dane kategorii
│   ├── exports/            # Eksporty CSV
│   └── checkpoint.json     # Checkpoint dla resume capability
├── tests/                 # Testy jednostkowe
├── scripts/               # Skrypty pomocnicze
│   ├── export_data.py     # Export do CSV
│   └── setup_db.py        # Setup bazy danych
├── .github/workflows/     # GitHub Actions
│   ├── scrape.yml         # Scheduled scraping
│   └── ci.yml             # CI/CD
└── logs/                  # Logi scrapera
```

Szczegółowa struktura: [PROPOZYCJA_ARCHITEKTURY.md](./cursor%20documentation%20and%20rules/PROPOZYCJA_ARCHITEKTURY.md)

## 🎯 Kluczowe Funkcjonalności

### Normalizacja Danych (Opcja B)
Scraper zapisuje zarówno formaty surowe z HTML jak i znormalizowane:
- **Daty**: `{"raw": "5 months ago", "normalized": "2024-10-15T00:00:00Z"}`
- **Statystyki**: `{"raw": "19.8K Views", "normalized": 19800}`

Zapewnia to elastyczność w analizie i możliwość weryfikacji danych źródłowych.

### Checkpoint System
Scraper automatycznie zapisuje postęp scrapowania, umożliwiając wznowienie po przerwie:
- Automatyczne pomijanie już przetworzonych URL-i
- Śledzenie nieudanych URL-i do ponownego przetworzenia
- Zapisywanie statystyk w checkpointie

### Zapisywanie Profili Kreatorów
Profile kreatorów są zapisywane jako osobne pliki JSON:
- Lokalizacja: `data/creators/{username}.json`
- Każdy kreator ma jeden plik, nawet jeśli ma wiele produktów
- Zawiera pełne dane: bio, avatar, stats, social media
- Można eksportować do CSV używając `export_creators_to_csv()`

**Techniczne szczegóły parsowania:**
- **Avatar**: Wyciągany z JSON danych Next.js (priorytet), pomijane placeholdery API (`api/og/creator`)
- **Social Media**: Wyciągane z JSON danych Next.js, automatycznie filtrowane linki Framer. Obsługiwane platformy: Twitter/X, LinkedIn, Instagram, GitHub, Dribbble, Behance, YouTube

### Obsługa Różnych Typów Produktów
Każdy typ produktu ma unikalne pola i statystyki:
- **Templates**: Pages + Views
- **Plugins**: Version + Users + Changelog
- **Components**: Installs (wyciągane z JSON danych Next.js lub HTML tekstu)
- **Vectors**: Users + Views + Vectors (count)

## 📊 Przykładowe Komendy

### Scrapowanie produktów

```bash
# Scrapowanie wszystkich typów produktów
python3 -m src.main

# Scrapowanie z limitem (test)
python3 -m src.main 10

# Scrapowanie tylko określonych typów
python3 -m src.main --templates-only 10    # Tylko szablony
python3 -m src.main --components-only 10   # Tylko komponenty
python3 -m src.main --vectors-only 10      # Tylko wektory
python3 -m src.main --plugins-only 10      # Tylko wtyczki
```

### Scrapowanie kreatorów

```bash
# Wszyscy kreatorzy
python3 -m src.main --creators-only

# Z limitem
python3 -m src.main --creators-only 10
python3 -m src.main -c 10  # Krótka wersja
```

### Scrapowanie kategorii

```bash
# Wszystkie kategorie
python3 -m src.main --categories-only

# Z limitem
python3 -m src.main --categories-only 10
python3 -m src.main -cat 10  # Krótka wersja
```

### Export danych

```bash
# Export wszystkich produktów do CSV
python scripts/export_data.py -o data/exports/all_products.csv

# Export tylko templates
python scripts/export_data.py --type template -o data/exports/templates.csv

# Export z limitem
python scripts/export_data.py --limit 100 -o data/exports/sample.csv

# Export kreatorów do CSV
python -c "from src.storage.file_storage import FileStorage; storage = FileStorage(); storage.export_creators_to_csv()"
```

### Inne

```bash
# Setup PostgreSQL database
python scripts/setup_db.py --db-type postgresql

# Wymuś nowe scrapowanie (wyczyść checkpoint)
rm data/checkpoint.json
python3 -m src.main
```

## 🔐 Uwagi Prawne

⚠️ **Ważne:**
- Przeczytaj Terms of Service Framer przed scrapowaniem
- Respektuj robots.txt
- Nie przeciążaj serwerów (rate limiting)
- Nie scrapuj danych osobowych bez zgody
- Rozważ kontakt z Framer - mogą oferować API

## 📝 Następne Kroki

1. **Przetestuj lokalnie** - uruchom z limitem 10-20 produktów
2. **Sprawdź dane** - zweryfikuj jakość zebranych danych
3. **Skonfiguruj GitHub Actions** - dodaj secrets jeśli potrzebne
4. **Rozszerz funkcjonalności** - dodaj testy, monitoring, itp.

## 🤝 Contributing

Projekt jest w fazie rozwoju. Wszelkie sugestie i PR-y są mile widziane!

## 📄 License

[TODO: Dodaj licencję]

---

*Ostatnia aktualizacja: 2024-12-19*

