# 🚀 Uruchamianie GitHub Actions z lokalnego środowiska

## Opcja 1: Użyj skryptów (wymaga GitHub Token)

### 1. Utwórz GitHub Personal Access Token

1. Przejdź do: https://github.com/settings/tokens
2. Kliknij **"Generate new token (classic)"**
3. Nadaj tokenowi nazwę (np. "Scraper Workflows")
4. Wybierz uprawnienia:
   - ✅ `repo` (pełny dostęp do repozytorium)
   - ✅ `workflow` (uruchamianie workflow)
5. Kliknij **"Generate token"**
6. **Skopiuj token** (zostanie pokazany tylko raz!)

### 2. Ustaw token w zmiennej środowiskowej

```bash
export GITHUB_TOKEN='twoj_token_tutaj'
```

### 3. Uruchom workflow

**Daily Scrape:**
```bash
cd "/Users/michalporada/Desktop/Scraper V2 "
./run_workflow.sh
```

**CI Workflow:**
```bash
cd "/Users/michalporada/Desktop/Scraper V2 "
./run_workflow_ci.sh
```

**Lub w jednej linii:**
```bash
GITHUB_TOKEN='twoj_token' ./run_workflow.sh
```

## Opcja 2: Użyj GitHub CLI (gh)

### Instalacja GitHub CLI

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install gh

# Fedora
sudo dnf install gh
```

**Windows:**
```bash
# Chocolatey
choco install gh

# lub pobierz z: https://cli.github.com/
```

### Konfiguracja

```bash
gh auth login
```

### Uruchom workflow

```bash
# Daily Scrape
gh workflow run "Daily Scrape" --repo michalporada/framer-marketplace-scraper-py

# CI
gh workflow run "CI" --repo michalporada/framer-marketplace-scraper-py
```

## Opcja 3: Użyj GitHub API bezpośrednio (curl)

### 1. Pobierz workflow ID

```bash
curl -H "Authorization: token TWOJ_TOKEN" \
  https://api.github.com/repos/michalporada/framer-marketplace-scraper-py/actions/workflows
```

### 2. Uruchom workflow

```bash
curl -X POST \
  -H "Authorization: token TWOJ_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/michalporada/framer-marketplace-scraper-py/actions/workflows/WORKFLOW_ID/dispatches \
  -d '{"ref":"main"}'
```

## Opcja 4: Przez interfejs GitHub (najprostsze)

1. Przejdź do: https://github.com/michalporada/framer-marketplace-scraper-py/actions
2. Wybierz workflow (np. "Daily Scrape")
3. Kliknij **"Run workflow"** → **"Run workflow"**

## 🔍 Sprawdzanie statusu workflow

### Przez skrypt

```bash
# Po uruchomieniu workflow, sprawdź status:
open "https://github.com/michalporada/framer-marketplace-scraper-py/actions"
```

### Przez GitHub CLI

```bash
gh run list --repo michalporada/framer-marketplace-scraper-py
```

### Przez API

```bash
curl -H "Authorization: token TWOJ_TOKEN" \
  https://api.github.com/repos/michalporada/framer-marketplace-scraper-py/actions/runs
```

## ⚠️ Troubleshooting

### Problem: "GITHUB_TOKEN nie jest ustawiony"
**Rozwiązanie**: Ustaw token w zmiennej środowiskowej lub użyj opcji 4 (interfejs GitHub)

### Problem: "403 Forbidden"
**Rozwiązanie**: Sprawdź czy token ma uprawnienia `repo` i `workflow`

### Problem: "404 Not Found"
**Rozwiązanie**: Sprawdź czy nazwa repozytorium jest poprawna

### Problem: "Workflow not found"
**Rozwiązanie**: Upewnij się że workflow są włączone w Settings → Actions → General

## 📝 Bezpieczeństwo

**⚠️ Nigdy nie commituj tokenu do repozytorium!**

- Używaj zmiennych środowiskowych
- Dodaj `.env` do `.gitignore` (już jest)
- Tokeny można przechowywać w `~/.zshrc` lub `~/.bashrc`:
  ```bash
  export GITHUB_TOKEN='twoj_token'
  ```

