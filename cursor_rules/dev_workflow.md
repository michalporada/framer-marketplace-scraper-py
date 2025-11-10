# Development Workflow Rules

**Cel:** Zdefiniować sposób pracy z Cursorem i GitHubem.

## Git Workflow

### Branch Strategy

1. **Main Branch**
   - `main`: Production-ready code
   - Protected branch (wymaga PR)
   - Zawsze aktualizuj przed pracą

2. **Feature Branches**
   - Format: `feature/{name}`
   - Przykłady: `feature/add-product-filter`, `feature/api-endpoints`
   - Merge przez Pull Request

3. **Fix Branches**
   - Format: `fix/{name}`
   - Przykłady: `fix/rate-limiting-bug`, `fix/parsing-error`
   - Merge przez Pull Request

4. **Refactor Branches**
   - Format: `refactor/{name}`
   - Przykłady: `refactor/scraper-structure`, `refactor/api-routes`
   - Merge przez Pull Request

### Commit Messages

#### Conventional Commits

Format: `{type}: {description}`

**Types:**
- `feat`: Nowa funkcjonalność
- `fix`: Naprawa błędu
- `refactor`: Refaktoryzacja kodu
- `chore`: Zmiany w build/config
- `docs`: Zmiany w dokumentacji
- `test`: Dodanie/zmiana testów

**Examples:**
```
feat: add product filter by type
fix: handle timeout errors in scraper
refactor: simplify product parser logic
chore: update dependencies
docs: update API documentation
test: add tests for product insights
```

#### Commit Message Rules

1. **Format**
   - Type w lowercase
   - Opis zaczyna się małą literą
   - Bez kropki na końcu
   - Max 72 znaki (jeśli możliwe)

2. **Body** (opcjonalnie)
   - Dla złożonych zmian
   - Wyjaśnij "co" i "dlaczego"
   - Max 72 znaki na linię

3. **Breaking Changes**
   - Dodaj `BREAKING CHANGE:` w footer
   - Opisz impact i migration

**Example:**
```
feat: add product type filter to API

Add new query parameter 'type' to /api/products endpoint
to filter products by type (template, component, vector, plugin).

BREAKING CHANGE: API now requires explicit type parameter
for filtered results. Update clients to include type parameter.
```

## Pull Request Workflow

### Przed Utworzeniem PR

1. **Update main**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Rebase branch**
   ```bash
   git checkout feature/my-feature
   git rebase main
   ```

3. **Test lokalnie**
   - Uruchom testy: `pytest`
   - Sprawdź linting: `ruff check .`
   - Sprawdź formatting: `black --check .`
   - Przetestuj funkcjonalność

4. **Commit changes**
   - Upewnij się, że commity są zgodne z konwencjami
   - Nie commituj wrażliwych danych
   - Sprawdź `.gitignore`

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Refactoring
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] Manual testing performed
- [ ] All tests passing

## Checklist
- [ ] Code follows project conventions
- [ ] Documentation updated (if needed)
- [ ] No sensitive data committed
- [ ] Linting/formatting checks passed
```

### PR Review Process

1. **Self-review**
   - Sprawdź diff przed prośbą o review
   - Upewnij się, że wszystko działa
   - Sprawdź czy nie ma obvious błędów

2. **CI Checks**
   - Wszystkie checks muszą być green
   - Testy muszą przechodzić
   - Linting/formatting musi być OK

3. **Review Feedback**
   - Address wszystkie komentarze
   - Dyskutuj jeśli potrzebne wyjaśnienia
   - Update PR description jeśli potrzebne

4. **Merge**
   - Merge po approval
   - Usuń branch po merge (local + remote)

## Cursor Workflow

### Praca z Agentem

1. **Zdefiniuj zadanie**
   - Bądź precyzyjny w opisie zadania
   - Podaj kontekst i wymagania
   - Wskaż pliki dotknięte zmianami

2. **Deleguj odpowiednio**
   - Używaj odpowiednich agentów (patrz `agents.md`)
   - Nie mieszaj zakresów odpowiedzialności
   - Sprawdzaj czy agent rozumie zadanie

3. **Review zmian**
   - Zawsze review zmian przed commit
   - Sprawdź czy zmiany są zgodne z regułami
   - Testuj lokalnie przed merge

### Komunikacja z Agentem

1. **Precyzyjne instrukcje**
   ```
   ✅ Dobrze: "Dodaj endpoint GET /api/products/{id} który zwraca produkt po ID"
   ❌ Źle: "Dodaj endpoint dla produktów"
   ```

2. **Kontekst**
   - Podaj kontekst zmian
   - Wskaż powiązane pliki
   - Wspomnij o istniejących wzorcach

3. **Feedback**
   - Daj feedback jeśli zmiany nie są OK
   - Wyjaśnij co jest nie tak
   - Poproś o poprawki

## Local Development

### Setup

1. **Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   pip install -r requirements-dev.txt
   ```

2. **Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Pre-commit Hooks** (OBOWIĄZKOWE)
   ```bash
   pre-commit install
   ```
   
   **Pre-commit hooks automatycznie:**
   - Naprawiają nieużywane importy (ruff --fix)
   - Formatują kod (ruff-format, black)
   - Sprawdzają YAML, JSON, TOML
   - Usuwają trailing whitespace
   - Sprawdzają duże pliki
   - Wykrywają merge conflicts
   
   **WAŻNE:** Pre-commit hooks uruchamiają się automatycznie przed każdym commitem.
   Jeśli hook naprawi błędy, musisz dodać poprawione pliki do staging:
   ```bash
   git add .
   git commit -m "fix: ..."
   ```
   
   **Ręczne uruchomienie:**
   ```bash
   # Sprawdź wszystkie pliki
   pre-commit run --all-files
   
   # Sprawdź tylko staged files (domyślnie)
   pre-commit run
   ```

### Development Commands

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Linting
ruff check .

# Formatting
black .

# Type checking
mypy src/

# Run scraper
python src/main.py

# Run scraper with limit
python src/main.py 100  # Scrape first 100 products
```

## CI/CD Workflow

### GitHub Actions

#### CI Workflow (`.github/workflows/ci.yml`)

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
      - name: Format check
        run: black --check .
      - name: Type check
        run: mypy src/
```

### Release Workflow

Zgodnie z `.cursorrules`:
- Release-please automatycznie tworzy PR z version bump
- Po merge PR automatycznie tworzy tag i release
- CHANGELOG.md jest aktualizowany automatycznie

## Code Review Checklist

### Przed Review

- [ ] Wszystkie testy przechodzą
- [ ] Linting/formatting OK
- [ ] Commit messages zgodne z konwencjami
- [ ] Brak wrażliwych danych
- [ ] Dokumentacja zaktualizowana (jeśli potrzebne)

### During Review

- [ ] Kod jest czytelny i zrozumiały
- [ ] Zgodność z projektowymi wzorcami
- [ ] Error handling zaimplementowany
- [ ] Performance zoptymalizowana (jeśli dotyczy)
- [ ] Testy pokrywają nowy kod
- [ ] Brak duplikacji kodu

## Release Process

### Przed Release

1. **Update main**
   - Upewnij się, że main jest aktualny
   - Wszystkie PR merged

2. **Check CI**
   - Wszystkie checks green
   - Testy przechodzą

3. **Release-please**
   - Review auto-PR od release-please
   - Merge jeśli wszystko OK
   - Tag i release tworzone automatycznie

### After Release

1. **Verify**
   - Sprawdź czy tag został utworzony
   - Sprawdź czy release został utworzony
   - Sprawdź CHANGELOG.md

2. **Deploy** (jeśli dotyczy)
   - Deployment powinien być automatyczny (triggered by tag)
   - Verify deployment

## Troubleshooting

### Common Issues

1. **Merge Conflicts**
   ```bash
   git checkout main
   git pull origin main
   git checkout feature/my-feature
   git rebase main
   # Resolve conflicts
   git add .
   git rebase --continue
   ```

2. **Failed CI**
   - Sprawdź logi CI
   - Napraw lokalnie
   - Push poprawki

3. **Pre-commit Hooks Failing**
   ```bash
   # Run manually
   ruff check .
   black .
   # Fix issues
   ```

## Best Practices

### 1. Small PRs

- Małe PRs są łatwiejsze do review
- Szybsze do merge
- Mniejsze ryzyko konfliktów

### 2. Frequent Commits

- Commituj często (logiczne jednostki)
- Nie commituj broken code
- Używaj descriptive commit messages

### 3. Communication

- Komunikuj się jasno w PR descriptions
- Daj feedback szybko
- Bądź konstruktywny w review

### 4. Documentation

- Aktualizuj dokumentację z zmianami
- Dokumentuj breaking changes
- Dodaj przykłady użycia

## Checklist dla Nowych Feature

- [ ] Branch utworzony z main
- [ ] Feature zaimplementowana
- [ ] Testy napisane
- [ ] Dokumentacja zaktualizowana
- [ ] Linting/formatting OK
- [ ] PR utworzony z opisem
- [ ] CI checks green
- [ ] Review otrzymany
- [ ] Feedback zaadresowany
- [ ] PR merged
- [ ] Branch usunięty

---

**Uwaga:** Te reguły są draftem i mogą być rozszerzone/zmodyfikowane w przyszłości.

