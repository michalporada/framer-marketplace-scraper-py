# Scraper Framer Marketplace V2

Zaawansowany scraper do zbierania danych z Framer Marketplace, umożliwiający automatyzację pobierania informacji o:

- **Produktach**: Szablony (templates), Komponenty (components), Wektory (vectors), **Wtyczki (plugins)** ⭐
- **Twórcach/Użytkownikach**: Profile z username (może zawierać znaki specjalne)
- **Kategoriach**: Kategorie produktów w marketplace
- **Recenzjach**: Opinie i oceny produktów

## 📚 Dokumentacja

### Główne Dokumenty

1. **[STACK_TECHNICZNY.md](./cursor%20documentation%20and%20rules/STACK_TECHNICZNY.md)** - Szczegółowy opis stacku technicznego, w tym:
   - Biblioteki Python i narzędzia
   - Opcje baz danych
   - GitHub Actions i Vercel
   - Rekomendacje deployment

2. **[PROPOZYCJA_ARCHITEKTURY.md](./cursor%20documentation%20and%20rules/PROPOZYCJA_ARCHITEKTURY.md)** - Propozycja struktury projektu:
   - Struktura folderów
   - Opis komponentów
   - Flow scrapowania
   - Deployment strategy

3. **[REKOMENDACJE_SCRAPERA_FRAMER.md](./cursor%20documentation%20and%20rules/REKOMENDACJE_SCRAPERA_FRAMER.md)** - Szczegółowa analiza Framer Marketplace:
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
python src/main.py

# Ograniczenie liczby produktów (np. 10 dla testów)
python src/main.py 10

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

Dane są automatycznie zapisywane jako artifacts w GitHub Actions.

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
- **Vercel** - API i dashboard (opcjonalnie, Faza 3)
- **PostgreSQL/Supabase** - baza danych (opcjonalnie)

### Storage
- **JSON/CSV** - podstawowe (zalecane na start)
- **PostgreSQL** - dla większych projektów
- **GitHub Artifacts** - backup danych

## 📋 Funkcjonalności

### ✅ Zaimplementowane

- [x] Scrapowanie produktów z sitemap.xml (templates/components/vectors/**plugins**)
- [x] Scrapowanie danych twórców (profile z `@username`)
- [x] Scrapowanie kategorii (opcjonalnie)
- [x] Parsowanie recenzji produktów
- [x] Rate limiting i error handling
- [x] Zapis do JSON/CSV (organizacja według typu produktu)
- [x] Automatyzacja przez GitHub Actions
- [x] Resume capability (wznowienie po przerwie) - checkpoint system
- [x] Walidacja danych (Pydantic)
- [x] Monitoring i logowanie (structlog)
- [x] Normalizacja danych (Opcja B - raw + normalized)
- [x] Obsługa różnych typów produktów (różne statystyki i pola)

### 🔮 Opcjonalne (Faza 2+)

- [ ] API endpoints (FastAPI)
- [ ] Dashboard (Next.js)
- [ ] Baza danych (PostgreSQL) - setup script gotowy
- [ ] Error tracking (Sentry)
- [ ] Notyfikacje (Slack/Email)

## 📁 Struktura Projektu

```
scraper-v2/
├── src/
│   ├── scrapers/          # Scrapery (sitemap, product, creator, category)
│   ├── parsers/           # Parsery HTML (product, creator, review, category)
│   ├── models/            # Modele Pydantic (Product, Creator, Review, Category)
│   ├── storage/           # Zapis danych (file_storage, database)
│   ├── utils/             # Narzędzia (logger, rate_limiter, retry, normalizers, checkpoint)
│   ├── config/            # Konfiguracja (settings)
│   └── main.py            # Entry point
├── data/
│   ├── products/          # Zapisane produkty (templates/, components/, vectors/, plugins/)
│   ├── creators/          # Dane twórców
│   ├── categories/        # Dane kategorii
│   ├── exports/           # Eksporty CSV
│   └── checkpoint.json    # Checkpoint dla resume capability
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

### Obsługa Różnych Typów Produktów
Każdy typ produktu ma unikalne pola i statystyki:
- **Templates**: Pages + Views
- **Plugins**: Version + Users + Changelog
- **Components**: Installs
- **Vectors**: Users + Views + Vectors (count)

## 📊 Przykładowe Komendy

```bash
# Scrapowanie z limitem (test)
python src/main.py 10

# Export wszystkich produktów do CSV
python scripts/export_data.py -o data/exports/all_products.csv

# Export tylko templates
python scripts/export_data.py --type template -o data/exports/templates.csv

# Export z limitem
python scripts/export_data.py --limit 100 -o data/exports/sample.csv

# Setup PostgreSQL database
python scripts/setup_db.py --db-type postgresql

# Wymuś nowe scrapowanie (wyczyść checkpoint)
rm data/checkpoint.json
python src/main.py
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

