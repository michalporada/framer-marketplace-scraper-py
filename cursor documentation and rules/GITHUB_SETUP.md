# Instrukcja wgrania na GitHub

## ✅ Krok 1: Repozytorium jest gotowe!

Repozytorium git zostało zainicjalizowane i wszystkie pliki są zacommitowane.

## 📝 Krok 2: Stwórz repozytorium na GitHub

1. Przejdź na https://github.com/new
2. Wypełnij formularz:
   - **Repository name**: `framer-marketplace-scraper` (lub inna nazwa)
   - **Description**: "Automated scraper for Framer Marketplace products"
   - **Visibility**: Public lub Private (zgodnie z preferencjami)
   - **NIE zaznaczaj** "Initialize this repository with a README" (już mamy pliki)
3. Kliknij **"Create repository"**

## 🔗 Krok 3: Połącz lokalne repo z GitHub

Po utworzeniu repozytorium, GitHub pokaże instrukcje. Użyj tych komend:

```bash
cd "/Users/michalporada/Desktop/Scraper V2 "

# Dodaj remote (zamień YOUR_USERNAME na swoją nazwę użytkownika)
git remote add origin https://github.com/YOUR_USERNAME/framer-marketplace-scraper.git

# Zmień nazwę brancha na main (jeśli potrzeba)
git branch -M main

# Wgraj kod na GitHub
git push -u origin main
```

## ⚙️ Krok 4: Włącz GitHub Actions

1. Przejdź do repozytorium na GitHub
2. Kliknij zakładkę **"Actions"**
3. Jeśli widzisz komunikat o włączeniu Actions, kliknij **"I understand my workflows, go ahead and enable them"**

## 🔐 Krok 5: (Opcjonalnie) Skonfiguruj Secrets

Jeśli chcesz użyć zmiennych środowiskowych w GitHub Actions:

1. Przejdź do **Settings** → **Secrets and variables** → **Actions**
2. Kliknij **"New repository secret"**
3. Dodaj secrets (jeśli potrzebne):
   - `DATABASE_URL` - jeśli używasz bazy danych
   - `FRAMER_BASE_URL` - domyślnie `https://www.framer.com`
   - `RATE_LIMIT` - domyślnie `1.0`
   - `MAX_RETRIES` - domyślnie `3`
   - `LOG_LEVEL` - domyślnie `INFO`

## 🚀 Krok 6: Testuj GitHub Actions

### Test CI workflow:
1. Przejdź do **Actions**
2. Wybierz workflow **"CI"**
3. Kliknij **"Run workflow"** → **"Run workflow"**

### Test Scrape workflow:
1. Przejdź do **Actions**
2. Wybierz workflow **"Daily Scrape"**
3. Kliknij **"Run workflow"** → **"Run workflow"**

## 📊 Workflows

### 1. CI (Continuous Integration)
- **Trigger**: Push i Pull Request na `main` lub `develop`
- **Co robi**: 
  - Uruchamia testy jednostkowe
  - Sprawdza linting (ruff)
  - Sprawdza formatowanie (ruff format)
  - Sprawdza typy (mypy)

### 2. Daily Scrape
- **Trigger**: 
  - Automatycznie codziennie o 2:00 UTC
  - Ręcznie przez "Run workflow"
- **Co robi**:
  - Uruchamia scraper
  - Zapisuje dane jako artifacts
  - Uploaduje logi

## 📁 Artifacts

Po uruchomieniu workflow "Daily Scrape", możesz pobrać artifacts:
1. Przejdź do **Actions**
2. Kliknij na uruchomienie workflow
3. Przewiń w dół do sekcji **"Artifacts"**
4. Pobierz `scraped-data` i `scraper-logs`

## ⚠️ Ważne informacje

- **Dane nie są commitowane** - folder `data/` jest w `.gitignore`
- **Checkpoint nie jest commitowany** - `checkpoint.json` jest w `.gitignore`
- **Artifacts są dostępne przez 7 dni** - jeśli potrzebujesz dłużej, zmień `retention-days` w workflow
- **Scheduled scraping** - workflow uruchamia się codziennie o 2:00 UTC

## 🐛 Troubleshooting

### Problem: "Permission denied" przy push
**Rozwiązanie**: Użyj SSH zamiast HTTPS lub skonfiguruj Personal Access Token

### Problem: GitHub Actions nie działają
**Rozwiązanie**: Sprawdź czy Actions są włączone w Settings → Actions → General

### Problem: Testy nie przechodzą
**Rozwiązanie**: Sprawdź logi w Actions → wybierz workflow → kliknij na failed job

