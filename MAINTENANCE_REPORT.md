# Raport Konserwacji - Scraper V2

**Data analizy:** 2025-01-XX  
**Status:** Maintenance & Refactoring  
**Cel:** Analiza całego repozytorium i propozycje usprawnień

---

## 📊 Podsumowanie Analizy

### ✅ Mocne Strony

1. **Dobra struktura projektu** - przejrzysta organizacja modułów (scrapers, parsers, models, utils)
2. **Solidne narzędzia** - structlog, pydantic, async/await, retry logic
3. **Dokumentacja** - obszerna dokumentacja w `cursor documentation and rules/`
4. **Testy** - podstawowa struktura testów (pytest)
5. **Type hints** - większość kodu ma type hints
6. **Logging** - strukturalne logowanie z structlog
7. **Error handling** - retry logic, exponential backoff

### ⚠️ Zidentyfikowane Problemy

#### 1. **Duplikacja Zależności**
- **Problem:** `requirements.txt` i `pyproject.toml` mają różne zależności
- **Szczegóły:**
  - `requirements.txt` zawiera `sqlalchemy>=2.0.0` i `psycopg2-binary>=2.9.9` (nie ma w `pyproject.toml`)
  - `pyproject.toml` ma `dev` dependencies, ale `requirements-dev.txt` również je zawiera
- **Rekomendacja:** Ujednolicić zależności - preferować `pyproject.toml` (standard Python)

#### 2. **Brak README.md w Root**
- **Problem:** Brak głównego README.md w katalogu głównym
- **Szczegóły:** Dokumentacja jest w `cursor documentation and rules/README.md`, ale brakuje w root
- **Rekomendacja:** Dodać README.md w root z podstawowymi informacjami

#### 3. **Duże Pliki**
- **Problem:** `sitemap_scraper.py` ma 535 linii - za dużo na jeden plik
- **Szczegóły:** Zawiera logikę fallback scraping, która mogłaby być w osobnym module
- **Rekomendacja:** Wydzielić `_scrape_product_urls_from_marketplace_pages` do osobnego modułu

#### 4. **Niespójności w Importach**
- **Problem:** Niektóre importy są na początku, inne w środku funkcji (np. w `sitemap_scraper.py:54`)
- **Szczegóły:** 
  ```python
  # W środku funkcji:
  from src.utils.retry import retry_async
  ```
- **Rekomendacja:** Wszystkie importy na początku pliku (PEP 8)

#### 5. **Brak Stałych**
- **Problem:** Hard-coded wartości w kodzie (np. milestone percentages w `marketplace_scraper.py`)
- **Szczegóły:** 
  ```python
  int(total * 0.1), int(total * 0.25), int(total * 0.5), ...
  ```
- **Rekomendacja:** Utworzyć plik `src/utils/constants.py` z wszystkimi stałymi

#### 6. **Duplikacja Kodu**
- **Problem:** Podobne bloki kodu w różnych miejscach (progress logging, checkpoint handling)
- **Szczegóły:** 
  - Progress logging w `scrape_products_batch`, `scrape_creators_batch`, `scrape_categories_batch`
  - Checkpoint handling w wielu miejscach
- **Rekomendacja:** Wydzielić do helper functions

#### 7. **Brak Type Hints w Niektórych Miejscach**
- **Problem:** Niektóre funkcje nie mają pełnych type hints
- **Szczegóły:** 
  - `parse_sitemap` zwraca `Dict[str, any]` (powinno być `Dict[str, Any]`)
  - Niektóre funkcje helper nie mają type hints
- **Rekomendacja:** Dodać pełne type hints wszędzie

#### 8. **Brak Walidacji Konfiguracji**
- **Problem:** Settings nie walidują wszystkich wartości
- **Szczegóły:** 
  - `rate_limit` może być 0 lub ujemny
  - `max_concurrent_requests` może być 0
- **Rekomendacja:** Dodać validatory w Pydantic Settings

#### 9. **Niespójne Nazewnictwo**
- **Problem:** Mieszanka angielskiego i polskiego w komentarzach
- **Szczegóły:** 
  - Komentarze po polsku w `sitemap_scraper.py:135` ("Profile użytkowników")
  - Komentarze po angielsku w innych miejscach
- **Rekomendacja:** Ujednolicić do angielskiego (lub polskiego - ale konsekwentnie)

#### 10. **Brak Pre-commit Hooks**
- **Problem:** Brak automatycznego formatowania i lintowania przed commit
- **Szczegóły:** `pre-commit` jest w dependencies, ale brak `.pre-commit-config.yaml`
- **Rekomendacja:** Dodać pre-commit config z black, ruff, mypy

#### 11. **Brak CI/CD dla Code Quality**
- **Problem:** Brak automatycznego sprawdzania jakości kodu w CI
- **Szczegóły:** GitHub Actions prawdopodobnie tylko uruchamia scraper
- **Rekomendacja:** Dodać job do sprawdzania black, ruff, mypy

#### 12. **Test Coverage**
- **Problem:** Brak informacji o pokryciu testami
- **Szczegóły:** Są testy, ale nie wiadomo jak dużo kodu pokrywają
- **Rekomendacja:** Dodać pytest-cov i wymusić minimum coverage

#### 13. **Brak Dokumentacji API (jeśli jest używana)**
- **Problem:** Kod nie ma docstringów w formacie Google/NumPy
- **Szczegóły:** Są docstringi, ale nie są konsekwentne
- **Rekomendacja:** Ujednolicić format docstringów

#### 14. **Brak .env.example**
- **Problem:** Brak przykładowego pliku `.env` dla nowych deweloperów
- **Rekomendacja:** Dodać `.env.example` z wszystkimi zmiennymi

#### 15. **Brak Wersjonowania**
- **Problem:** Wersja w `pyproject.toml` jest `0.1.0`, ale brak changelog
- **Rekomendacja:** Dodać `CHANGELOG.md` i używać semantic versioning

---

## 🔧 Proponowane Usprawnienia

### Priorytet Wysoki (Krytyczne)

1. **Ujednolicić zależności** - usunąć duplikację między `requirements.txt` i `pyproject.toml`
2. **Dodać README.md w root** - podstawowe informacje o projekcie
3. **Naprawić importy** - wszystkie na początku pliku
4. **Dodać .env.example** - dla łatwiejszego setupu

### Priorytet Średni (Ważne)

5. **Refaktoryzacja dużych plików** - podzielić `sitemap_scraper.py`
6. **Wydzielić stałe** - utworzyć `constants.py`
7. **Dodać walidację konfiguracji** - validatory w Settings
8. **Ujednolicić komentarze** - wszystkie po angielsku
9. **Dodać pre-commit hooks** - automatyczne formatowanie

### Priorytet Niski (Nice to Have)

10. **Dodać CI/CD dla code quality** - black, ruff, mypy w GitHub Actions
11. **Dodać test coverage** - pytest-cov z minimum threshold
12. **Ujednolicić docstringi** - format Google/NumPy
13. **Dodać CHANGELOG.md** - tracking zmian
14. **Wydzielić helper functions** - zmniejszyć duplikację kodu

---

## 📝 Szczegółowe Rekomendacje

### 1. Ujednolicenie Zależności

**Aktualny stan:**
- `requirements.txt` - zawiera zależności produkcyjne + SQLAlchemy/PostgreSQL
- `pyproject.toml` - zawiera zależności produkcyjne, ale bez SQLAlchemy
- `requirements-dev.txt` - zawiera dev dependencies

**Proponowane rozwiązanie:**
- Użyć `pyproject.toml` jako single source of truth
- Dodać SQLAlchemy do `pyproject.toml` jako optional dependency
- `requirements.txt` może być generowany z `pyproject.toml` (backward compatibility)

### 2. Refaktoryzacja sitemap_scraper.py

**Proponowana struktura:**
```
src/scrapers/
  ├── sitemap_scraper.py (main logic, ~200 linii)
  └── marketplace_fallback.py (fallback scraping, ~300 linii)
```

### 3. Utworzenie constants.py

**Proponowana zawartość:**
```python
# src/utils/constants.py
PROGRESS_MILESTONES = [0.1, 0.25, 0.5, 0.75, 0.9]
PROGRESS_LOG_INTERVAL = 50
RETRY_EXPONENTIAL_BASE = 2.0
DEFAULT_TIMEOUT = 30
# ... etc
```

### 4. Pre-commit Config

**Proponowana zawartość `.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
```

---

## 🎯 Plan Implementacji

### Faza 1: Quick Wins (1-2 dni)
- [ ] Dodać README.md w root
- [ ] Dodać .env.example
- [ ] Naprawić importy (wszystkie na początku)
- [ ] Ujednolicić komentarze (angielski)

### Faza 2: Refaktoryzacja (3-5 dni)
- [ ] Ujednolicić zależności (pyproject.toml)
- [ ] Wydzielić stałe (constants.py)
- [ ] Podzielić sitemap_scraper.py
- [ ] Dodać walidację konfiguracji

### Faza 3: Code Quality (2-3 dni)
- [ ] Dodać pre-commit hooks
- [ ] Dodać CI/CD dla code quality
- [ ] Dodać test coverage tracking
- [ ] Ujednolicić docstringi

### Faza 4: Dokumentacja (1-2 dni)
- [ ] Dodać CHANGELOG.md
- [ ] Zaktualizować dokumentację
- [ ] Dodać CONTRIBUTING.md (opcjonalnie)

---

## 📊 Metryki Jakości Kodu

### Obecny Stan
- **Linter errors:** 0 ✅
- **Test coverage:** Nieznane ⚠️
- **Type hints coverage:** ~80% ⚠️
- **Docstring coverage:** ~70% ⚠️
- **Code duplication:** Średnia ⚠️

### Docelowy Stan
- **Linter errors:** 0 ✅
- **Test coverage:** >80% 🎯
- **Type hints coverage:** 100% 🎯
- **Docstring coverage:** 90% 🎯
- **Code duplication:** Niska 🎯

---

## 🚀 Dalsze Kroki

1. **Przegląd raportu** - weryfikacja rekomendacji
2. **Priorytetyzacja** - wybór zadań do implementacji
3. **Implementacja** - według planu fazowego
4. **Code review** - przegląd zmian
5. **Testing** - weryfikacja że wszystko działa

---

## 📌 Notatki

- Wszystkie zmiany powinny być backward compatible
- Testy powinny być aktualizowane wraz z refaktoryzacją
- Dokumentacja powinna być aktualizowana na bieżąco
- Preferowane są małe, inkrementalne zmiany nad dużymi rewizjami

---

**Koniec Raportu**

