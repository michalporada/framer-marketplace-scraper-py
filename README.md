# Scraper Framer Marketplace V2

Zaawansowany scraper do zbierania danych z Framer Marketplace, umożliwiający automatyzację pobierania informacji o produktach, twórcach i kategoriach.

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
pip install -e .  # Lub: pip install -r requirements.txt
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
- `RATE_LIMIT` - Limit requestów na sekundę (domyślnie: 2.0)
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
python3 -m src.main --components-only 10     # Tylko komponenty
python3 -m src.main --vectors-only 10       # Tylko wektory
python3 -m src.main --plugins-only 10        # Tylko wtyczki

# Scrapowanie tylko kreatorów
python3 -m src.main --creators-only          # Wszyscy kreatorzy
python3 -m src.main --creators-only 10      # Z limitem
python3 -m src.main -c 10                    # Krótka wersja

# Scrapowanie tylko kategorii
python3 -m src.main --categories-only        # Wszystkie kategorie
python3 -m src.main --categories-only 10    # Z limitem
python3 -m src.main -cat 10                  # Krótka wersja
```

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
│   ├── creators/          # Profile twórców jako osobne pliki JSON ({username}.json)
│   ├── categories/       # Dane kategorii
│   ├── exports/          # Eksporty CSV
│   └── checkpoint.json    # Checkpoint dla resume capability
├── tests/                # Testy jednostkowe
├── scripts/              # Skrypty pomocnicze
│   ├── export_data.py    # Export do CSV
│   └── setup_db.py      # Setup bazy danych
├── logs/                 # Logi scrapera
└── .github/workflows/    # GitHub Actions
```

## 🛠️ Stack Techniczny

### Backend
- **Python 3.11+** - język główny
- **httpx** - async HTTP client
- **BeautifulSoup4** - parsowanie HTML
- **pydantic v2** - walidacja danych z normalizacją
- **pandas** - manipulacja danych i eksport do CSV
- **SQLAlchemy** - ORM (dla PostgreSQL)

### Narzędzia
- **structlog** - strukturalne logowanie
- **tenacity** - retry logic z exponential backoff
- **fake-useragent** - rotacja User-Agent headers
- **tqdm** - progress bars

### Deployment & Automation
- **GitHub Actions** - automatyczne scrapowanie (scheduled)
- **PostgreSQL/Supabase** - baza danych

### Storage
- **JSON/CSV** - podstawowe (zalecane na start)
- **PostgreSQL** - dla większych projektów
- **GitHub Artifacts** - backup danych

## 📋 Funkcjonalności

### ✅ Zaimplementowane

- [x] Scrapowanie produktów z sitemap.xml (templates/components/vectors/plugins)
- [x] Scrapowanie danych twórców (profile z `@username`)
- [x] Zapisywanie profilów twórców jako osobne pliki JSON
- [x] Scrapowanie kategorii
- [x] Pozycja w kategorii - zbieranie pozycji szablonu w każdej kategorii
- [x] Rate limiting i error handling
- [x] Zapis do JSON/CSV (organizacja według typu produktu)
- [x] Eksport kreatorów do CSV
- [x] Automatyzacja przez GitHub Actions
- [x] Resume capability (wznowienie po przerwie) - checkpoint system
- [x] Walidacja danych (Pydantic)
- [x] Monitoring i logowanie (structlog)
- [x] Normalizacja danych (raw + normalized)
- [x] Obsługa różnych typów produktów (różne statystyki i pola)

### 🔮 Przyszłe rozszerzenia

- [ ] API endpoints (FastAPI)
- [ ] Dashboard (Next.js)
- [ ] Baza danych (PostgreSQL) - setup script gotowy
- [ ] Error tracking (Sentry)
- [ ] Notyfikacje (Slack/Email)

## 🎯 Kluczowe Funkcjonalności

### Normalizacja Danych
Scraper zapisuje zarówno formaty surowe z HTML jak i znormalizowane:
- **Daty**: `{"raw": "5 months ago", "normalized": "2024-10-15T00:00:00Z"}`
- **Statystyki**: `{"raw": "19.8K Views", "normalized": 19800}`

### Checkpoint System
Scraper automatycznie zapisuje postęp scrapowania:
- **Zawsze aktualizuje wszystkie produkty** - aby śledzić zmiany w views, cenach, statystykach
- **Śledzenie nieudanych URL-i** - automatycznie ponawia próbę na końcu scrapowania
- **Retry failed URLs** - na końcu każdego scrapowania próbuje ponownie przetworzyć nieudane URL-e

## 📊 Przykładowe Komendy

### Export danych

```bash
# Export wszystkich produktów do CSV
python scripts/export_data.py -o data/exports/all_products.csv

# Export tylko templates
python scripts/export_data.py --type template -o data/exports/templates.csv

# Export kreatorów do CSV
python -c "from src.storage.file_storage import FileStorage; storage = FileStorage(); storage.export_creators_to_csv()"
```

### GitHub Actions

Scraper może być uruchamiany automatycznie przez GitHub Actions:
- **Scheduled**: Codziennie o 2:00 UTC
- **Manual**: Ręczne uruchomienie przez `workflow_dispatch`

Dane są automatycznie zapisywane jako artifacts w GitHub Actions.

## 📚 Dokumentacja

Szczegółowa dokumentacja znajduje się w katalogu `cursor documentation and rules/`:

- **[README.md](./cursor%20documentation%20and%20rules/README.md)** - Szczegółowa dokumentacja
- **[STACK_TECHNICZNY.md](./cursor%20documentation%20and%20rules/STACK_TECHNICZNY.md)** - Stack techniczny
- **[PROPOZYCJA_ARCHITEKTURY.md](./cursor%20documentation%20and%20rules/PROPOZYCJA_ARCHITEKTURY.md)** - Architektura projektu
- **[REKOMENDACJE_SCRAPERA_FRAMER.md](./cursor%20documentation%20and%20rules/REKOMENDACJE_SCRAPERA_FRAMER.md)** - Rekomendacje scrapowania
- **[TESTING_AND_FIXTURES.md](./cursor%20documentation%20and%20rules/TESTING_AND_FIXTURES.md)** - Dokumentacja testów

## 🔐 Uwagi Prawne

⚠️ **Ważne:**
- Przeczytaj Terms of Service Framer przed scrapowaniem
- Respektuj robots.txt
- Nie przeciążaj serwerów (rate limiting)
- Nie scrapuj danych osobowych bez zgody
- Rozważ kontakt z Framer - mogą oferować API

## 🤝 Contributing

Projekt jest w fazie rozwoju. Wszelkie sugestie i PR-y są mile widziane!

## 📄 License

[TODO: Dodaj licencję]

---

*Ostatnia aktualizacja: 2025-01-XX*

