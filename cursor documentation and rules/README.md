# Scraper Framer Marketplace V2

Zaawansowany scraper do zbierania danych z Framer Marketplace, umożliwiający automatyzację pobierania informacji o:

- **Produktach**: Szablony (templates), Komponenty (components), Wektory (vectors), **Wtyczki (plugins)** ⭐
- **Twórcach/Użytkownikach**: Profile z username (może zawierać znaki specjalne)
- **Kategoriach**: Kategorie produktów w marketplace
- **Recenzjach**: Opinie i oceny produktów

## 📚 Dokumentacja

### Główne Dokumenty

1. **[STACK_TECHNICZNY.md](./STACK_TECHNICZNY.md)** - Szczegółowy opis stacku technicznego, w tym:
   - Biblioteki Python i narzędzia
   - Opcje baz danych
   - GitHub Actions i Vercel
   - Rekomendacje deployment

2. **[PROPOZYCJA_ARCHITEKTURY.md](./PROPOZYCJA_ARCHITEKTURY.md)** - Propozycja struktury projektu:
   - Struktura folderów
   - Opis komponentów
   - Flow scrapowania
   - Deployment strategy

3. **[Cursor Rules/REKOMENDACJE_SCRAPERA_FRAMER.md](./Cursor%20Rules/REKOMENDACJE_SCRAPERA_FRAMER.md)** - Szczegółowa analiza Framer Marketplace:
   - Analiza techniczna strony
   - Struktura URL-i i selektory CSS
   - Zalecane dane do zbierania
   - Uwagi techniczne

## 🚀 Quick Start

### 1. Przegląd Dokumentacji

Najpierw przeczytaj dokumenty, aby zrozumieć:
- Jak działa Framer Marketplace (REKOMENDACJE_SCRAPERA_FRAMER.md)
- Jaki stack techniczny jest rekomendowany (STACK_TECHNICZNY.md)
- Jak zorganizować projekt (PROPOZYCJA_ARCHITEKTURY.md)

### 2. Setup Projektu

```bash
# Stwórz strukturę projektu zgodnie z PROPOZYCJA_ARCHITEKTURY.md
# Zainstaluj zależności
pip install -r requirements.txt

# Skonfiguruj zmienne środowiskowe
cp .env.example .env
# Edytuj .env z odpowiednimi wartościami
```

### 3. Uruchomienie

```bash
# Podstawowe uruchomienie (scrapuje wszystkie produkty)
python -m src.main

# Ograniczenie liczby produktów (np. 10 dla testów)
python -m src.main 10

# Export danych do CSV
python scripts/export_data.py

# Lub przez GitHub Actions (scheduled lub manual)
# Zobacz .github/workflows/scrape.yml
```

## 🛠️ Stack Techniczny (Podsumowanie)

### Backend
- **Python 3.11+** - język główny
- **httpx** - async HTTP client
- **BeautifulSoup4** - parsowanie HTML
- **pydantic** - walidacja danych
- **SQLAlchemy** - ORM (opcjonalnie)

### Deployment & Automation
- **GitHub Actions** - automatyczne scrapowanie (scheduled)
- **Vercel** - API i dashboard (opcjonalnie)
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
- [x] Automatyzacja przez GitHub Actions (scheduled + manual)
- [x] Resume capability (wznowienie po przerwie) - checkpoint system
- [x] Walidacja danych (Pydantic v2)
- [x] Monitoring i logowanie (structlog)
- [x] Normalizacja danych (Opcja B - raw + normalized)
- [x] Obsługa różnych typów produktów (różne statystyki i pola)
- [x] CI/CD workflow (tests, linting, formatting)
- [x] Metrics tracking (success rate, errors, timing)

### 🔮 Opcjonalne (Faza 2+)

- [ ] API endpoints (FastAPI)
- [ ] Dashboard (Next.js)
- [ ] Baza danych (PostgreSQL)
- [ ] Error tracking (Sentry)
- [ ] Notyfikacje (Slack/Email)

## 📁 Struktura Projektu

```
scraper-v2/
├── src/
│   ├── scrapers/          # Scrapery (sitemap, product, creator, category)
│   ├── parsers/           # Parsery HTML (product, creator, review, category)
│   ├── models/            # Modele Pydantic (Product, Creator, Review, Category)
│   ├── storage/           # Zapis danych (file_storage)
│   ├── utils/             # Narzędzia (logger, rate_limiter, retry, normalizers, checkpoint, metrics)
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
│   ├── scrape.yml         # Scheduled scraping + manual
│   └── ci.yml             # CI/CD (tests, linting, formatting)
└── logs/                  # Logi scrapera
```

Szczegółowa struktura: [PROPOZYCJA_ARCHITEKTURY.md](./PROPOZYCJA_ARCHITEKTURY.md)

## 🔐 Uwagi Prawne

⚠️ **Ważne:**
- Przeczytaj Terms of Service Framer przed scrapowaniem
- Respektuj robots.txt
- Nie przeciążaj serwerów (rate limiting)
- Nie scrapuj danych osobowych bez zgody
- Rozważ kontakt z Framer - mogą oferować API

## 📝 Następne Kroki

1. **Przeczytaj dokumentację** - szczególnie REKOMENDACJE_SCRAPERA_FRAMER.md
2. **Zdecyduj o stacku** - zobacz STACK_TECHNICZNY.md
3. **Stwórz strukturę projektu** - zgodnie z PROPOZYCJA_ARCHITEKTURY.md
4. **Zaimplementuj MVP** - podstawowy scraper z sitemap (wszystkie typy produktów)
5. **Testuj na małej próbce** - 10-20 produktów (różne typy)
6. **Setup GitHub Actions** - automatyzacja
7. **Rozszerz funkcjonalności** - twórcy, kategorie, recenzje, baza danych

## 🤝 Contributing

Projekt jest w fazie rozwoju. Wszelkie sugestie i PR-y są mile widziane!

## 📄 License

[TODO: Dodaj licencję]

---

*Ostatnia aktualizacja: 2025-11-03*

