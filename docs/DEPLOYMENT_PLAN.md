# Plan Wdrożenia - Vercel + Railway + Supabase

**Data utworzenia:** 2025-01-06  
**Architektura:** Frontend (Vercel) + API (Railway) + Database (Supabase)  
**Szacowany czas:** 60-90 minut

---

## 📋 Spis Treści

1. [Faza 0: Przygotowanie](#faza-0-przygotowanie-lokalnie)
2. [Faza 1: Supabase (Database)](#faza-1-supabase-database---15-20-minut)
3. [Faza 2: Railway (API)](#faza-2-railway-api---20-30-minut)
4. [Faza 3: Vercel (Frontend)](#faza-3-vercel-frontend---15-20-minut)
5. [Faza 4: Konfiguracja Połączeń](#faza-4-konfiguracja-połączeń---10-minut)
6. [Faza 5: GitHub Actions](#faza-5-github-actions---aktualizacja-5-minut)
7. [Faza 6: Monitoring i Testy](#faza-6-monitoring-i-testy---10-minut)
8. [Checklist Wdrożenia](#checklist-wdrożenia)
9. [Troubleshooting](#troubleshooting)
10. [Następne Kroki](#następne-kroki-po-wdrożeniu)

---

## Faza 0: Przygotowanie (Lokalnie)

### Krok 0.1: Sprawdź obecną strukturę projektu

```bash
# Sprawdź czy masz folder api/ i frontend/
ls -la

# Sprawdź strukturę
tree -L 2 -I 'node_modules|venv|__pycache__|.git'
```

**Oczekiwana struktura:**
```
scraper-v2/
├── api/              # FastAPI backend
├── frontend/         # Next.js frontend
├── src/              # Scraper code
├── data/             # Scraped data
└── .env.example      # Environment variables template
```

### Krok 0.2: Przygotuj zmienne środowiskowe

**Zaktualizuj `.env.example`:**

```bash
# ============================================
# Database (Supabase)
# ============================================
DATABASE_URL=postgresql://user:password@host:port/database

# ============================================
# API Configuration
# ============================================
API_BASE_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,https://your-project.vercel.app

# ============================================
# Frontend
# ============================================
NEXT_PUBLIC_API_URL=http://localhost:8000

# ============================================
# Scraper (już masz)
# ============================================
FRAMER_BASE_URL=https://www.framer.com
RATE_LIMIT=1.0
MAX_RETRIES=3
LOG_LEVEL=INFO
CHECKPOINT_ENABLED=true

# ============================================
# Scraping Options
# ============================================
SCRAPE_TEMPLATES=true
SCRAPE_COMPONENTS=true
SCRAPE_VECTORS=true
SCRAPE_PLUGINS=true
SCRAPE_CATEGORIES=false
SCRAPE_PROFILES=false
```

**Utwórz lokalny `.env`:**
```bash
cp .env.example .env
# Edytuj .env z lokalnymi wartościami
```

---

## Faza 1: Supabase (Database) - 15-20 minut

### Krok 1.1: Utwórz projekt Supabase

1. **Przejdź na:** https://supabase.com
2. **Zaloguj się** używając GitHub
3. **Kliknij:** "New Project"
4. **Wypełnij formularz:**
   - **Name:** `framer-scraper-db` (lub dowolna nazwa)
   - **Database Password:** 
     - Wygeneruj silne hasło (min. 12 znaków)
     - ⚠️ **ZAPISZ HASŁO** - będziesz potrzebować później
     - Przykład: użyj generatora haseł lub zapisz w menedżerze haseł
   - **Region:** Wybierz najbliższą (np. `West EU (Frankfurt)`)
   - **Pricing Plan:** Free (darmowy plan)

5. **Kliknij:** "Create new project"
6. **Poczekaj** na utworzenie projektu (2-3 minuty)

### Krok 1.2: Pobierz Connection String

1. **W projekcie Supabase:**
   - Przejdź do: **Settings** → **Database**
   - Znajdź sekcję: **Connection string**
   - Wybierz zakładkę: **URI** (nie "Session mode")
   - Skopiuj connection string

2. **Connection string wygląda tak:**
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```

3. **Zastąp `[YOUR-PASSWORD]`** rzeczywistym hasłem z kroku 1.1

### Krok 1.3: Testuj połączenie lokalnie (Opcjonalnie)

**Opcja A: Używając psql**
```bash
# Zainstaluj psql (jeśli nie masz)
# Mac: brew install postgresql
# Ubuntu: sudo apt-get install postgresql-client

# Test połączenia
psql "postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres"

# Jeśli połączenie działa, zobaczysz prompt:
# postgres=>
# Wpisz \q aby wyjść
```

**Opcja B: Używając Python**
```bash
python -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres'); print('Connected!')"
```

### Krok 1.4: Dodaj do projektu

1. **Dodaj do `.env`:**
   ```bash
   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```

2. **Upewnij się, że `.env` jest w `.gitignore`:**
   ```bash
   # Sprawdź
   cat .gitignore | grep .env
   
   # Jeśli nie ma, dodaj:
   echo ".env" >> .gitignore
   ```

3. **Zapisz connection string bezpiecznie:**
   - W menedżerze haseł
   - Lub w notatkach (tylko dla developmentu)

### Krok 1.5: Sprawdź limity darmowego planu

**Supabase Free Plan:**
- ✅ 500 MB database storage
- ✅ 2 GB bandwidth
- ✅ 50,000 monthly active users
- ✅ Unlimited API requests

**Dla Twojego projektu:** Wystarczy na start (możesz przechować ~100k produktów)

---

## Faza 2: Railway (API) - 20-30 minut

### Krok 2.1: Utwórz konto Railway

1. **Przejdź na:** https://railway.app
2. **Kliknij:** "Start a New Project"
3. **Zaloguj się** używając GitHub
4. **Zaakceptuj** uprawnienia (Railway potrzebuje dostępu do repozytoriów)

### Krok 2.2: Połącz repozytorium

1. **Kliknij:** "Deploy from GitHub repo"
2. **Wybierz repozytorium:** `Scraper V2` (lub nazwa Twojego repo)
3. **Railway automatycznie:**
   - Wykryje Python
   - Rozpocznie deployment
   - Pokaże logi budowania

### Krok 2.3: Skonfiguruj deployment

1. **W projekcie Railway:**
   - Kliknij na serwis (service)
   - Przejdź do: **Settings** → **Service**

2. **Ustaw konfigurację:**
   - **Start Command:**
     ```
     uvicorn api.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Healthcheck Path:** `/docs` lub `/health`
   - **Healthcheck Timeout:** 100

3. **Jeśli nie masz jeszcze folderu `api/`:**
   - Railway może nie wykryć automatycznie
   - Musisz ręcznie skonfigurować

### Krok 2.4: Dodaj zmienne środowiskowe

**W Railway: Settings → Variables, dodaj:**

```bash
# Database
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres

# API Configuration
FRAMER_BASE_URL=https://www.framer.com
RATE_LIMIT=1.0
MAX_RETRIES=3
LOG_LEVEL=INFO

# CORS (dodaj URL frontendu po wdrożeniu)
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000

# Optional
ENVIRONMENT=production
```

**Jak dodać:**
1. Kliknij "New Variable"
2. Wpisz nazwę (np. `DATABASE_URL`)
3. Wpisz wartość
4. Kliknij "Add"

### Krok 2.5: Utwórz plik konfiguracyjny (Opcjonalnie)

**Utwórz `railway.json` w root projektu:**

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/docs",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Lub utwórz `Procfile` w root:**

```
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Krok 2.6: Sprawdź deployment

1. **Railway automatycznie:**
   - Zbuduje projekt
   - Wdroży API
   - Pokaże logi w czasie rzeczywistym

2. **Sprawdź logi:**
   - W Railway dashboard: **Deployments** → **View Logs**
   - Szukaj błędów (czerwone linie)
   - Sprawdź czy uvicorn się uruchomił

3. **Po udanym wdrożeniu:**
   - Railway wygeneruje URL: `https://your-api.railway.app`
   - URL znajdziesz w: **Settings** → **Networking** → **Public Domain**

4. **Test API:**
   ```bash
   # Sprawdź czy API działa
   curl https://your-api.railway.app/docs
   
   # Lub otwórz w przeglądarce:
   # https://your-api.railway.app/docs
   ```

### Krok 2.7: Dodaj custom domain (Opcjonalnie)

1. **W Railway:**
   - **Settings** → **Networking**
   - Kliknij **"Generate Domain"** (automatyczny)
   - Lub **"Custom Domain"** (własna domena)

2. **Zapisz URL API:**
   - Będziesz potrzebować w następnym kroku
   - Przykład: `https://api-framer-scraper.railway.app`

### Krok 2.8: Sprawdź limity darmowego planu

**Railway Free Plan:**
- ✅ $5 kredytu miesięcznie
- ✅ Wystarczy na mały projekt
- ⚠️ Po wyczerpaniu kredytu: projekt się zatrzyma

**Dla Twojego projektu:** Wystarczy na start (API zużywa ~$2-3/miesiąc)

---

## Faza 3: Vercel (Frontend) - 15-20 minut

### Krok 3.1: Utwórz konto Vercel

1. **Przejdź na:** https://vercel.com
2. **Kliknij:** "Sign Up"
3. **Zaloguj się** używając GitHub
4. **Zaakceptuj** uprawnienia

### Krok 3.2: Połącz repozytorium

1. **W Vercel dashboard:**
   - Kliknij **"Add New Project"**
   - Wybierz repozytorium: `Scraper V2`

2. **Vercel automatycznie wykryje:**
   - Framework: Next.js (jeśli jest w `frontend/`)
   - Root Directory: może wykryć automatycznie

3. **Jeśli nie wykryje automatycznie, ustaw ręcznie:**
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build` (lub `yarn build`)
   - **Output Directory:** `.next`
   - **Install Command:** `npm install` (lub `yarn install`)

### Krok 3.3: Skonfiguruj zmienne środowiskowe

**W Vercel: Settings → Environment Variables, dodaj:**

```bash
# API URL (użyj URL z Railway)
NEXT_PUBLIC_API_URL=https://your-api.railway.app

# Optional
NEXT_PUBLIC_ENVIRONMENT=production
```

**Jak dodać:**
1. Przejdź do projektu w Vercel
2. **Settings** → **Environment Variables**
3. Kliknij **"Add New"**
4. Wpisz:
   - **Key:** `NEXT_PUBLIC_API_URL`
   - **Value:** URL z Railway (krok 2.7)
   - **Environment:** Production, Preview, Development (zaznacz wszystkie)
5. Kliknij **"Save"**

### Krok 3.4: Utwórz `vercel.json` (jeśli potrzebne)

**Utwórz `frontend/vercel.json`:**

```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["iad1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "@next_public_api_url"
  }
}
```

**Lub jeśli używasz `package.json` w root:**

**Utwórz `vercel.json` w root projektu:**

```json
{
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ]
}
```

### Krok 3.5: Deploy

1. **Kliknij:** "Deploy"
2. **Vercel automatycznie:**
   - Zainstaluje zależności
   - Zbuduje projekt
   - Wdroży frontend
   - Pokaże logi w czasie rzeczywistym

3. **Po udanym wdrożeniu:**
   - Vercel wygeneruje URL: `https://your-project.vercel.app`
   - URL znajdziesz w dashboardzie projektu

4. **Test frontendu:**
   - Otwórz URL w przeglądarce
   - Sprawdź czy strona się ładuje
   - Sprawdź czy API calls działają (DevTools → Network)

### Krok 3.6: Dodaj custom domain (Opcjonalnie)

1. **W Vercel:**
   - **Settings** → **Domains**
   - Dodaj własną domenę (jeśli masz)
   - Lub użyj darmowego `.vercel.app` domain

### Krok 3.7: Sprawdź limity darmowego planu

**Vercel Free Plan (Hobby):**
- ✅ Unlimited deployments
- ✅ 100 GB bandwidth
- ✅ Serverless Functions: 100 GB-hours
- ✅ Edge Functions: Unlimited
- ✅ Builds: Unlimited

**Dla Twojego projektu:** Wystarczy na start

---

## Faza 4: Konfiguracja Połączeń - 10 minut

### Krok 4.1: Zaktualizuj CORS w API

**W `api/main.py` (FastAPI):**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# CORS Configuration
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reszta kodu...
```

**Lub jeśli używasz settings:**

```python
from src.config.settings import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(",") if hasattr(settings, 'cors_origins') else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Zaktualizuj zmienną środowiskową w Railway:**
```bash
CORS_ORIGINS=https://your-project.vercel.app,http://localhost:3000
```

### Krok 4.2: Zaktualizuj API URL w frontend

**W `frontend/src/lib/api.ts` (lub podobny plik):**

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchProducts(params?: {
  type?: string;
  limit?: number;
  offset?: number;
}) {
  const queryParams = new URLSearchParams();
  if (params?.type) queryParams.append('type', params.type);
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());

  const url = `${API_BASE_URL}/api/products${queryParams.toString() ? `?${queryParams}` : ''}`;
  
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch products: ${response.statusText}`);
  }
  
  return response.json();
}
```

### Krok 4.3: Testuj połączenia

**1. Test API → Database:**
```bash
# Sprawdź czy API łączy się z bazą
curl https://your-api.railway.app/api/products?limit=5

# Powinieneś otrzymać JSON z produktami
```

**2. Test Frontend → API:**
```bash
# Otwórz frontend w przeglądarce
# Otwórz DevTools (F12) → Network
# Sprawdź czy requesty do API przechodzą
# Sprawdź czy nie ma błędów CORS
```

**3. Test end-to-end:**
- Otwórz frontend: `https://your-project.vercel.app`
- Sprawdź czy produkty się ładują
- Sprawdź czy filtry działają
- Sprawdź czy paginacja działa

### Krok 4.4: Sprawdź logi

**Railway:**
- Dashboard → Deployments → View Logs
- Sprawdź czy nie ma błędów połączenia z bazą

**Vercel:**
- Dashboard → Deployments → View Logs
- Sprawdź czy build przeszedł pomyślnie

**Supabase:**
- Dashboard → Database → Logs
- Sprawdź czy są zapytania do bazy

---

## Faza 5: GitHub Actions - Aktualizacja (5 minut)

### Krok 5.1: Zaktualizuj workflow scrapowania

**W `.github/workflows/scrape.yml`, możesz dodać opcjonalnie:**

```yaml
name: Daily Scrape

on:
  schedule:
    - cron: '0 2 * * *'  # Codziennie o 2:00 UTC
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run scraper
        env:
          FRAMER_BASE_URL: ${{ secrets.FRAMER_BASE_URL || 'https://www.framer.com' }}
          RATE_LIMIT: ${{ secrets.RATE_LIMIT || '1.0' }}
          MAX_RETRIES: ${{ secrets.MAX_RETRIES || '3' }}
          LOG_LEVEL: ${{ secrets.LOG_LEVEL || 'INFO' }}
          CHECKPOINT_ENABLED: ${{ secrets.CHECKPOINT_ENABLED || 'true' }}
        run: |
          python -m src.main
      
      # Opcjonalnie: Push do bazy danych
      - name: Sync to Database (Optional)
        if: success()
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          # Jeśli masz skrypt do sync do bazy
          python scripts/sync_to_db.py || echo "Sync script not found, skipping"
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: scraped-data
          path: |
            data/
            logs/
          retention-days: 7
```

### Krok 5.2: Dodaj secrets do GitHub

**W GitHub: Settings → Secrets and variables → Actions:**

**Dodaj następujące secrets:**

1. **`DATABASE_URL`**
   - Value: connection string z Supabase (krok 1.2)
   - Używane do: opcjonalnego sync do bazy po scrapowaniu

2. **`RAILWAY_API_TOKEN`** (Opcjonalnie)
   - Jeśli chcesz triggerować redeploy z GitHub Actions
   - Pobierz z: Railway → Settings → API Tokens

3. **`VERCEL_TOKEN`** (Opcjonalnie)
   - Jeśli chcesz triggerować redeploy z GitHub Actions
   - Pobierz z: Vercel → Settings → Tokens

**Jak dodać secret:**
1. Przejdź do repozytorium na GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Kliknij **"New repository secret"**
4. Wpisz nazwę i wartość
5. Kliknij **"Add secret"**

---

## Faza 6: Monitoring i Testy - 10 minut

### Krok 6.1: Health Checks

**1. API Health:**
```bash
# Sprawdź health endpoint (jeśli masz)
curl https://your-api.railway.app/health

# Lub sprawdź Swagger UI
# https://your-api.railway.app/docs
```

**2. Frontend:**
- Otwórz: `https://your-project.vercel.app`
- Sprawdź czy strona się ładuje
- Sprawdź czy nie ma błędów w konsoli (F12)

**3. Database:**
- Supabase Dashboard → Database → Table Editor
- Sprawdź czy tabele istnieją (jeśli używasz bazy)
- Lub sprawdź connection w Settings → Database

### Krok 6.2: Testy End-to-End

**1. Test ładowania danych:**
- Otwórz frontend
- Sprawdź czy produkty się ładują
- Sprawdź DevTools → Network → czy requesty do API przechodzą

**2. Test funkcjonalności:**
- Sprawdź czy filtry działają
- Sprawdź czy paginacja działa
- Sprawdź czy sortowanie działa
- Sprawdź czy wyszukiwanie działa (jeśli masz)

**3. Test błędów:**
- Sprawdź czy błędy są obsługiwane gracefully
- Sprawdź czy są user-friendly error messages
- Sprawdź czy loading states działają

### Krok 6.3: Monitoring

**Railway:**
- Dashboard → Metrics
- Sprawdź: CPU usage, Memory usage, Request count
- Sprawdź logi: Deployments → View Logs

**Vercel:**
- Dashboard → Analytics
- Sprawdź: Page views, Performance metrics
- Sprawdź logi: Deployments → View Logs

**Supabase:**
- Dashboard → Database → Logs
- Sprawdź: Query performance, Connection count
- Sprawdź: Database → Table Editor (dane)

### Krok 6.4: Performance Test

**1. Test API response time:**
```bash
# Test pojedynczego requestu
time curl https://your-api.railway.app/api/products?limit=10

# Powinno być < 500ms
```

**2. Test frontend load time:**
- Otwórz DevTools → Network
- Sprawdź Time to First Byte (TTFB)
- Sprawdź Load time
- Powinno być < 2s

**3. Test database queries:**
- Supabase Dashboard → Database → Query Performance
- Sprawdź czy queries są szybkie (< 100ms)

---

## Checklist Wdrożenia

### ✅ Supabase
- [ ] Projekt utworzony
- [ ] Connection string skopiowany
- [ ] Hasło zapisane bezpiecznie
- [ ] `.env` zaktualizowany z `DATABASE_URL`
- [ ] Test połączenia (opcjonalnie) - działa
- [ ] Limity darmowego planu sprawdzone

### ✅ Railway
- [ ] Konto utworzone
- [ ] Repozytorium połączone z GitHub
- [ ] Start command skonfigurowany
- [ ] Zmienne środowiskowe dodane:
  - [ ] `DATABASE_URL`
  - [ ] `CORS_ORIGINS`
  - [ ] `FRAMER_BASE_URL`
  - [ ] `RATE_LIMIT`
  - [ ] `MAX_RETRIES`
  - [ ] `LOG_LEVEL`
- [ ] Deployment zakończony pomyślnie
- [ ] API URL zapisany
- [ ] Swagger UI działa (`/docs`)
- [ ] Health check działa
- [ ] Logi sprawdzone (brak błędów)

### ✅ Vercel
- [ ] Konto utworzone
- [ ] Repozytorium połączone z GitHub
- [ ] Root directory ustawiony na `frontend/`
- [ ] Framework wykryty (Next.js)
- [ ] Zmienne środowiskowe dodane:
  - [ ] `NEXT_PUBLIC_API_URL`
- [ ] Build command skonfigurowany
- [ ] Deployment zakończony pomyślnie
- [ ] Frontend URL zapisany
- [ ] Frontend działa (strona się ładuje)
- [ ] Logi sprawdzone (brak błędów)

### ✅ Konfiguracja
- [ ] CORS skonfigurowany w API (FastAPI)
- [ ] `CORS_ORIGINS` zawiera URL frontendu
- [ ] API URL ustawiony w frontend (`NEXT_PUBLIC_API_URL`)
- [ ] Połączenie Frontend → API działa
- [ ] Połączenie API → Database działa
- [ ] Wszystkie zmienne środowiskowe ustawione

### ✅ GitHub Actions
- [ ] Secrets dodane do GitHub:
  - [ ] `DATABASE_URL` (opcjonalnie)
  - [ ] `RAILWAY_API_TOKEN` (opcjonalnie)
  - [ ] `VERCEL_TOKEN` (opcjonalnie)
- [ ] Workflow zaktualizowany (jeśli potrzebne)
- [ ] Test workflow (opcjonalnie)

### ✅ Testy
- [ ] API odpowiada (`/docs` działa)
- [ ] Frontend łączy się z API (Network tab)
- [ ] Dane się ładują w frontend
- [ ] Filtry działają
- [ ] Paginacja działa
- [ ] Błędy są obsługiwane gracefully
- [ ] Loading states działają
- [ ] Performance jest akceptowalna (< 2s load time)

### ✅ Monitoring
- [ ] Railway metrics sprawdzone
- [ ] Vercel analytics sprawdzone
- [ ] Supabase logs sprawdzone
- [ ] Wszystkie serwisy działają

---

## Troubleshooting

### Problem: Railway nie wykrywa Python

**Objawy:**
- Railway pokazuje błąd "No buildpack detected"
- Deployment się nie uruchamia

**Rozwiązanie:**

1. **Dodaj `Procfile` w root projektu:**
   ```
   web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```

2. **Lub dodaj `railway.json`:**
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT"
     }
   }
   ```

3. **Lub ustaw ręcznie w Railway:**
   - Settings → Service → Start Command
   - Wpisz: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

### Problem: Vercel nie buduje frontendu

**Objawy:**
- Build fails w Vercel
- Błędy w logach

**Rozwiązanie:**

1. **Sprawdź `package.json` w `frontend/`:**
   ```json
   {
     "scripts": {
       "build": "next build",
       "dev": "next dev"
     }
   }
   ```

2. **Sprawdź czy `frontend/` ma `next.config.js`:**
   ```javascript
   /** @type {import('next').NextConfig} */
   const nextConfig = {
     // config
   }
   
   module.exports = nextConfig
   ```

3. **Sprawdź root directory w Vercel:**
   - Settings → General → Root Directory
   - Powinno być: `frontend`

4. **Sprawdź logi w Vercel:**
   - Deployments → View Logs
   - Szukaj błędów kompilacji

### Problem: CORS errors

**Objawy:**
- W konsoli przeglądarki: `CORS policy: No 'Access-Control-Allow-Origin'`
- Requesty z frontendu nie przechodzą

**Rozwiązanie:**

1. **Sprawdź `CORS_ORIGINS` w Railway:**
   ```bash
   CORS_ORIGINS=https://your-project.vercel.app,http://localhost:3000
   ```

2. **Sprawdź CORS middleware w `api/main.py`:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=cors_origins,  # Musi zawierać URL frontendu
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Redeploy API po zmianach:**
   - Railway automatycznie redeployuje po zmianie zmiennych środowiskowych
   - Lub ręcznie: Deployments → Redeploy

### Problem: Database connection failed

**Objawy:**
- API zwraca 500 error
- W logach Railway: "connection refused" lub "authentication failed"

**Rozwiązanie:**

1. **Sprawdź connection string:**
   - Format: `postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres`
   - Upewnij się, że hasło jest poprawne
   - Upewnij się, że nie ma spacji

2. **Sprawdź IP whitelist w Supabase:**
   - Settings → Database → Connection Pooling
   - Sprawdź czy Railway IP jest dozwolony
   - Dla Supabase: zazwyczaj nie trzeba whitelistować (public access)

3. **Sprawdź czy baza działa:**
   - Supabase Dashboard → Database → Table Editor
   - Sprawdź czy możesz połączyć się przez dashboard

4. **Test połączenia lokalnie:**
   ```bash
   psql "postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres"
   ```

### Problem: API nie odpowiada

**Objawy:**
- `curl` zwraca timeout
- Frontend nie może połączyć się z API

**Rozwiązanie:**

1. **Sprawdź czy Railway service działa:**
   - Dashboard → Deployments
   - Sprawdź czy ostatni deployment jest "Active"
   - Sprawdź logi: View Logs

2. **Sprawdź health check:**
   ```bash
   curl https://your-api.railway.app/docs
   ```

3. **Sprawdź czy port jest poprawny:**
   - Railway używa `$PORT` environment variable
   - Upewnij się, że start command używa `$PORT`

4. **Sprawdź czy uvicorn się uruchomił:**
   - Logi powinny pokazywać: "Uvicorn running on..."

### Problem: Frontend nie ładuje danych

**Objawy:**
- Frontend się ładuje, ale dane nie
- Błędy w konsoli przeglądarki

**Rozwiązanie:**

1. **Sprawdź `NEXT_PUBLIC_API_URL`:**
   - Vercel → Settings → Environment Variables
   - Upewnij się, że wartość jest poprawna
   - Upewnij się, że jest dostępna w Production, Preview, Development

2. **Sprawdź Network tab w DevTools:**
   - F12 → Network
   - Sprawdź czy requesty do API są wysyłane
   - Sprawdź status code (powinno być 200)

3. **Sprawdź CORS:**
   - Jeśli widzisz CORS error, zobacz sekcję "CORS errors" wyżej

4. **Sprawdź API response:**
   ```bash
   curl https://your-api.railway.app/api/products?limit=5
   ```

### Problem: Build fails w Vercel

**Objawy:**
- Deployment fails w Vercel
- Błędy w build logs

**Rozwiązanie:**

1. **Sprawdź logi:**
   - Vercel → Deployments → View Logs
   - Szukaj błędów kompilacji

2. **Sprawdź zależności:**
   - Upewnij się, że `package.json` ma wszystkie zależności
   - Sprawdź czy nie ma błędów w `package-lock.json`

3. **Sprawdź TypeScript errors:**
   - Jeśli używasz TypeScript, sprawdź czy nie ma błędów typów
   - Uruchom lokalnie: `npm run build`

4. **Sprawdź environment variables:**
   - Upewnij się, że wszystkie wymagane zmienne są ustawione
   - Sprawdź czy nie ma błędów w użyciu `process.env`

---

## Następne Kroki po Wdrożeniu

### 1. Monitoring i Alerty

**Railway:**
- Skonfiguruj alerty przy wysokim użyciu zasobów
- Monitoruj logi pod kątem błędów

**Vercel:**
- Włącz Analytics (jeśli potrzebne)
- Monitoruj performance metrics

**Supabase:**
- Skonfiguruj alerty przy zbliżaniu się do limitów
- Monitoruj query performance

### 2. Backup Strategy

**Supabase:**
- Automatyczne backupy (wbudowane w Supabase)
- Sprawdź częstotliwość backupów w Settings

**GitHub Actions:**
- Dane scrapowane są zapisywane jako artifacts
- Rozważ backup do external storage (S3, etc.)

### 3. Performance Optimization

**API:**
- Dodaj caching (Redis/Upstash)
- Optymalizuj database queries
- Dodaj database indexes

**Frontend:**
- Dodaj image optimization (Next.js Image)
- Dodaj static generation gdzie możliwe
- Optymalizuj bundle size

### 4. Security

**API:**
- Dodaj rate limiting (jeśli jeszcze nie ma)
- Dodaj authentication (jeśli potrzebne)
- Skonfiguruj HTTPS (automatyczne w Railway/Vercel)

**Database:**
- Używaj connection pooling (Supabase ma wbudowane)
- Nie commituj connection strings
- Rotuj hasła regularnie

### 5. Scaling

**Kiedy rozważyć upgrade:**

- **Supabase:** Gdy przekroczysz 500 MB storage
- **Railway:** Gdy przekroczysz $5 kredytu/miesiąc
- **Vercel:** Gdy przekroczysz 100 GB bandwidth

**Opcje:**
- Upgrade do paid plans
- Alternatywne platformy (AWS, GCP, Azure)
- Self-hosted solutions

---

## Przydatne Linki

### Dokumentacja
- **Supabase:** https://supabase.com/docs
- **Railway:** https://docs.railway.app
- **Vercel:** https://vercel.com/docs
- **FastAPI:** https://fastapi.tiangolo.com
- **Next.js:** https://nextjs.org/docs

### Dashboardy
- **Supabase Dashboard:** https://app.supabase.com
- **Railway Dashboard:** https://railway.app/dashboard
- **Vercel Dashboard:** https://vercel.com/dashboard

### Support
- **Supabase Discord:** https://discord.supabase.com
- **Railway Discord:** https://discord.gg/railway
- **Vercel Community:** https://github.com/vercel/vercel/discussions

---

## Notatki

**Zapisz tutaj swoje wartości:**

- **Supabase Connection String:** `_________________________________`
- **Railway API URL:** `https://_________________________________`
- **Vercel Frontend URL:** `https://_________________________________`
- **Database Password:** `_________________________________` (zapisz bezpiecznie!)

---

**Ostatnia aktualizacja:** 2025-01-06  
**Status:** Gotowy do użycia ✅

