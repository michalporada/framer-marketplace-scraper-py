# Stack Techniczny - Scraper Framer Marketplace

## 📋 Przegląd Projektu

Projekt to zaawansowany scraper do zbierania danych z Framer Marketplace, który umożliwia automatyzację pobierania informacji o:

- **Produktach**: Szablony (templates), Komponenty (components), Wektory (vectors), **Wtyczki (plugins)** ⭐
- **Twórcach/Użytkownikach**: Profile z username (może zawierać znaki specjalne)
- **Kategoriach**: Kategorie produktów w marketplace

**Kluczowa funkcjonalność:** Normalizacja danych - zapis zarówno formatów surowych z HTML jak i znormalizowanych (ISO 8601 dla dat, liczby całkowite dla statystyk) dla elastyczności analizy i weryfikacji danych.

## 🛠️ Stack Techniczny

### Backend / Scraper Core

#### Język Programowania
- **Python 3.11+** 
  - Nowoczesne funkcje (pattern matching, type hints)
  - Doskonała obsługa asynchroniczności
  - Bogaty ekosystem bibliotek

#### Biblioteki Core

**HTTP Client & Scraping:**
- **httpx** (async) lub **requests** (sync)
  - Asynchroniczne requesty dla lepszej wydajności
  - Obsługa sesji, cookies, headers
  - Wsparcie dla retry logic
  
- **BeautifulSoup4** (bs4)
  - Parsowanie HTML
  - Łatwe wyszukiwanie selektorów CSS
  
- **lxml**
  - Szybsze parsowanie XML/HTML dla sitemap

**Dane & Modele:**
- **pydantic v2**
  - Walidacja danych z modelem
  - Type safety
  - Automatyczna serializacja do JSON
  - Modele z normalizacją:
    - `NormalizedDate` - daty z formatem surowym i znormalizowanym
    - `NormalizedStatistic` - statystyki z formatem surowym i znormalizowanym
  
- **pandas**
  - Manipulacja i analiza danych
  - Eksport do CSV/Excel
  
- **SQLAlchemy 2.0** (opcjonalnie)
  - ORM dla bazy danych relacyjnej
  - Wsparcie dla PostgreSQL/MySQL

**Narzędzia Pomocnicze:**
- **python-dotenv**
  - Zarządzanie zmiennymi środowiskowymi
  
- **tqdm**
  - Pasek postępu dla długich operacji
  
- **tenacity**
  - Retry logic z exponential backoff
  
- **fake-useragent**
  - Rotacja User-Agent headers

- **aiofiles** (jeśli async)
  - Asynchroniczne operacje na plikach

**Logging & Monitoring:**
- **structlog**
  - Strukturalne logowanie
  - Łatwa integracja z systemami monitoringu

### Baza Danych

#### PostgreSQL (Rekomendowana)
- **Dlaczego:** Najlepsze dla relacyjnych danych (produkty ↔ twórcy ↔ recenzje)
- **ORM:** SQLAlchemy
- **Hosting:** 
  - Supabase (darmowy tier)
  - Railway
  - Neon (serverless PostgreSQL)
  - Vercel Postgres (integracja z Vercel)

#### Opcja 2: SQLite (Dla małych projektów)
- **Dlaczego:** Zero konfiguracji, plik lokalny
- **ORM:** SQLAlchemy
- **Limitations:** Nie nadaje się dla dużych danych

#### MongoDB (Dla dokumentów)
- **Dlaczego:** Elastyczny schemat, łatwe przechowywanie JSON
- **Driver:** pymongo lub motor (async)
- **Hosting:** MongoDB Atlas (darmowy tier)

#### Tylko Pliki (JSON/CSV)
- **Dlaczego:** Najprostsze, brak infrastruktury
- **Formaty:** JSON, CSV, Parquet (dla analiz)

### Storage & Hosting

#### GitHub Actions (CI/CD & Automatyzacja) ✅

**Zastosowanie:**
- **Scheduled Scraping:** Automatyczne uruchamianie scrapowania (np. codziennie o 2:00)
- **CI/CD:** Testy automatyczne przed merge
- **Data Backup:** Automatyczny backup danych do GitHub Releases/Artifacts
- **Monitoring:** Wysyłanie notyfikacji o statusie scrapowania

**Przykładowe workflow:**
```yaml
# .github/workflows/scrape.yml
name: Daily Scrape
on:
  schedule:
    - cron: '0 2 * * *'  # Codziennie o 2:00 UTC
  workflow_dispatch:  # Ręczne uruchomienie
```

**Zalety:**
- ✅ Darmowe dla publicznych repozytoriów
- ✅ 2000 minut/miesiąc dla private repos
- ✅ Integracja z GitHub
- ✅ Automatyczne uruchamianie
- ✅ Możliwość zapisywania artifacts (dane)

**Ograniczenia:**
- ⚠️ Czas wykonania: max 6 godzin
- ⚠️ Limit czasu dla scheduled workflows

#### Vercel (Hosting & API) ⚠️

**Zastosowanie:**
- **API Endpoints:** REST API do dostępu do danych (jeśli potrzebny)
- **Dashboard/Frontend:** Webowy interfejs do przeglądania danych
- **Serverless Functions:** Lekkie endpointy do zapytań

**Zalety:**
- ✅ Darmowe dla hobby projects
- ✅ Serverless (automatyczne skalowanie)
- ✅ Integracja z GitHub (auto-deploy)
- ✅ Edge Functions (szybkie API)
- ✅ Vercel Postgres (jeśli potrzebna baza)

**Ograniczenia:**
- ⚠️ Vercel jest głównie dla Node.js/Python (ograniczenia dla Python)
- ⚠️ Funkcje serverless mają limit czasu (10s hobby, 60s pro)
- ⚠️ Nie idealne do długotrwałych scrapowania

**Rekomendacja:**
- ✅ **Użyj Vercel** jeśli potrzebujesz:
  - API do dostępu do danych
  - Dashboard/frontend
  - Integrację z Vercel Postgres
- ❌ **NIE używaj Vercel** do:
  - Głównego procesu scrapowania (użyj GitHub Actions lub dedykowany serwer)
  - Długotrwałych operacji (>10s)

**Alternatywy dla Vercel (jeśli potrzebny API):**
- **FastAPI + Railway/Render** (Python-native)
- **Flask + Heroku** (prostsze, ale droższe)
- **Next.js API Routes** (jeśli frontend w Next.js)

### Struktura Deployment

#### Opcja 1: GitHub Actions (Rekomendowana dla startu)
```
GitHub Actions (scheduled)
  ↓
  Scraper Python
  ↓
  Zapis do JSON/CSV
  ↓
  GitHub Artifacts / Releases
  ↓
  (Opcjonalnie) Push do bazy danych
```

**Zalety:**
- ✅ Zero kosztów (dla public repos)
- ✅ Automatyzacja out-of-the-box
- ✅ Integracja z GitHub

```
GitHub Actions (scraping)
  ↓
  Zapis do bazy (Vercel Postgres / Supabase)
  ↓
  Vercel API (dostęp do danych)
  ↓
  Frontend (Vercel) - dashboard
```

**Zalety:**
- ✅ Automatyzacja scrapowania
- ✅ API do danych
- ✅ Dashboard dla użytkowników

#### Opcja 3: Dedicated Server (VPS/Cloud)
- **Railway** - łatwa konfiguracja, darmowy tier
- **Render** - darmowy tier z limitami
- **DigitalOcean App Platform** - płatne, ale elastyczne
- **AWS EC2 / Lambda** - zaawansowane, ale bardziej skomplikowane

### Narzędzia Deweloperskie

#### Development
- **poetry** lub **pip-tools** - zarządzanie zależnościami
- **pre-commit** - hooks przed commit (formatting, linting)
- **black** - formatowanie kodu
- **ruff** lub **pylint** - linting
- **mypy** - type checking

#### Testing
- **pytest** - framework testowy
- **pytest-asyncio** - testy async
- **pytest-cov** - coverage
- **httpx mock** - mockowanie requestów HTTP

#### Monitoring & Alerting
- **Sentry** (opcjonalnie) - error tracking
- **GitHub Actions notifications** - email/Slack o statusie
- **Health checks** - monitoring scrapowania

### Rekomendowana Architektura

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Repository                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────┐         ┌──────────────────┐      │
│  │  GitHub Actions  │         │   Vercel (API)   │      │
│  │  (Scheduled)     │         │   (Opcjonalnie) │      │
│  │                  │         │                  │      │
│  │  - Scraping      │────────▶│  - REST API      │      │
│  │  - Data Storage  │         │  - Dashboard     │      │
│  │  - Backup        │         │  - Frontend      │      │
│  └──────────────────┘         └──────────────────┘      │
│           │                            │                 │
│           ▼                            ▼                 │
│  ┌──────────────────┐         ┌──────────────────┐      │
│  │  Data Storage    │         │  Database        │      │
│  │                  │         │  (Opcjonalnie)   │      │
│  │  - JSON/CSV      │         │  - PostgreSQL    │      │
│  │  - GitHub        │         │  - Supabase      │      │
│  │    Artifacts     │         │  - Vercel Postgres│     │
│  └──────────────────┘         └──────────────────┘      │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Rekomendacja Startowa

### Faza 1: MVP (Minimum Viable Product)
1. **Backend:** Python scraper z httpx + BeautifulSoup
2. **Storage:** JSON/CSV files
3. **Automation:** GitHub Actions (scheduled)
4. **Deployment:** Zero (lokalne uruchomienie lub GitHub Actions)

### Faza 2: Rozszerzenie
1. **Database:** PostgreSQL (Supabase/Railway)
2. **API:** FastAPI + Railway (lub Vercel jeśli Next.js)
3. **Monitoring:** GitHub Actions notifications

### Faza 3: Production
1. **Frontend:** Next.js dashboard (Vercel)
2. **API:** Vercel API Routes lub FastAPI
3. **Database:** Vercel Postgres lub Supabase
4. **Monitoring:** Sentry + Health checks

## 📦 Zalecane Zależności (requirements.txt)

```txt
# HTTP & Scraping
httpx>=0.25.0
beautifulsoup4>=4.12.0
lxml>=5.0.0

# Data & Validation
pydantic>=2.5.0
pandas>=2.1.0
python-dotenv>=1.0.0

# Utilities
tqdm>=4.66.0
tenacity>=8.2.0
fake-useragent>=1.4.0
structlog>=23.2.0

# Database (opcjonalnie)
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9  # PostgreSQL
# lub
pymongo>=4.6.0  # MongoDB

# Development
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.11.0
ruff>=0.1.0
mypy>=1.7.0
```

## 🎯 Podsumowanie

### GitHub Actions ✅
**Użyj do:**
- Automatycznego scrapowania (scheduled)
- CI/CD
- Backup danych
- Notyfikacji

### Vercel ⚠️
**Użyj do:**
- API endpoints (jeśli potrzebny dostęp do danych)
- Frontend/dashboard (jeśli potrzebny)
- Integracji z Vercel Postgres

**Nie używaj do:**
- Głównego procesu scrapowania (za długie operacje)

### Rekomendacja
**Start:** GitHub Actions + JSON/CSV storage  
**Rozwój:** + Database (Supabase/Railway) + API (FastAPI)  
**Production:** + Vercel (dashboard) + Monitoring

---

*Ostatnia aktualizacja: 2024-12-19*

