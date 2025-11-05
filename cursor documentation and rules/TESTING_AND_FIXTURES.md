# Dokumentacja Testów i Fixture'ów - Scraper Framer Marketplace

## 📋 Cel dokumentu

Ten dokument jest **źródłem prawdy** (Single Source of Truth) dla struktury testów, fixture'ów i konwencji testowych w projekcie. Wszystkie decyzje dotyczące testów, struktury fixture'ów i best practices są tutaj dokumentowane i powinny być przestrzegane przez cały zespół.

**Data ostatniej aktualizacji:** 2025-01-XX

---

## 🏗️ Struktura testów

### Organizacja folderów

```
tests/
├── fixtures/                          # Pliki danych testowych (HTML, JSON, XML)
│   ├── html/                          # HTML fixtures dla różnych typów stron
│   │   ├── products/                  # Strony produktów
│   │   ├── creators/                  # Profile twórców
│   │   ├── categories/                # Strony kategorii
│   │   └── sitemap/                   # Pliki sitemap.xml
│   ├── json/                          # JSON fixtures dla różnych scenariuszy
│   │   ├── products/                  # Dane produktów
│   │   ├── creators/                  # Dane twórców
│   │   └── categories/                # Dane kategorii
│   └── README.md                      # Dokumentacja fixture'ów (jak używać)
│
├── conftest.py                        # Główne fixture'y współdzielone
│
├── test_models/                       # Testy modeli Pydantic
│   ├── conftest.py                    # Fixture'y specyficzne dla models
│   ├── test_product.py               # ✅ Istnieje
│   ├── test_creator.py                # Do utworzenia
│   └── test_category.py               # Do utworzenia
│
├── test_parsers/                      # Testy parserów HTML
│   ├── conftest.py                    # Fixture'y specyficzne dla parsers
│   ├── test_product_parser.py         # ✅ Istnieje
│   ├── test_creator_parser.py        # Do utworzenia
│   └── test_category_parser.py        # Do utworzenia
│
├── test_scrapers/                     # Testy scraperów
│   ├── conftest.py                    # Fixture'y specyficzne dla scrapers
│   ├── test_sitemap_scraper.py        # ✅ Istnieje
│   ├── test_product_scraper.py        # Do utworzenia
│   ├── test_creator_scraper.py        # Do utworzenia
│   └── test_category_scraper.py       # Do utworzenia
│
├── test_utils/                        # Testy narzędzi pomocniczych
│   ├── conftest.py                    # Fixture'y specyficzne dla utils
│   ├── test_normalizers.py           # ✅ Istnieje
│   ├── test_rate_limiter.py           # Do utworzenia
│   ├── test_retry.py                  # Do utworzenia
│   ├── test_checkpoint.py             # Do utworzenia
│   └── test_user_agents.py            # Do utworzenia
│
└── test_storage/                      # Testy storage (opcjonalnie)
    ├── conftest.py                    # Fixture'y specyficzne dla storage
    └── test_file_storage.py           # Do utworzenia
```

### Konwencje nazewnictwa

#### Pliki testowe:
- Format: `test_<moduł>_<nazwa>.py`
- Przykład: `test_product_parser.py`, `test_creator_scraper.py`

#### Klasy testowe:
- Format: `Test<ClassName>`
- Przykład: `TestProductParser`, `TestCreatorScraper`

#### Funkcje testowe:
- Format: `test_<co_testujemy>`
- Przykład: `test_parse_template_complete`, `test_extract_categories`

#### Fixture'y:
- Format: `[nazwa]_fixture` lub opisowy (np. `html_template_omicorn`)
- Przykład: `html_template_omicorn`, `product_data_complete`

---

## 🎯 Typy fixture'ów

### A. HTML Fixtures (dla parserów)

**Lokalizacja:** `tests/fixtures/html/`

#### 1. Products (`products/`)

| Fixture | Opis | Użycie |
|---------|------|--------|
| `template_omicorn.html` | Pełna strona template Omicorn (wszystkie features, kategorie, strony) | Testy parsowania kompletnego template |
| `template_1936redcliff.html` | Template 1936Redcliff (real estate) | Testy parsowania z tytułem strony |
| `template_free.html` | Darmowy template z przyciskiem "Preview" | Testy parsowania darmowych produktów |
| `component_animated_gradient.html` | Komponent z instalacjami | Testy parsowania komponentów |
| `component_with_installs.html` | Komponent z "7.4K Installs" | Testy ekstrakcji instalacji (JSON + HTML) |
| `vector_solar_duotone.html` | Zestaw wektorów (Users, Views, Vectors) | Testy parsowania wektorów |
| `plugin_rive.html` | Plugin Rive (Version, Users, Changelog) | Testy parsowania pluginów |
| `product_minimal.html` | Minimalny HTML (tylko podstawowe tagi) | Testy odporności na brakujące dane |

**Wymagania dla HTML fixtures:**
- ✅ Pochodzą z rzeczywistych stron (pobrane przez `curl` lub zapisane z przeglądarki)
- ✅ Zawierają wszystkie istotne elementy (features, kategorie, statystyki)
- ✅ Kodowane w UTF-8
- ✅ Zawierają komentarz na początku z opisem i datą pobrania

**Przykład struktury:**
```html
<!--
  Fixture: template_omicorn.html
  Źródło: https://www.framer.com/marketplace/templates/omicorn/
  Data pobrania: 2025-01-XX
  Opis: Pełna strona template Omicorn z wszystkimi features, kategoriami i stronami
-->
<!DOCTYPE html>
<html>
  ...
</html>
```

#### 2. Creators (`creators/`)

| Fixture | Opis | Użycie |
|---------|------|--------|
| `creator_kunal_bats.html` | Profil Kunal Bats (kompletny) | Testy parsowania profilu twórcy |
| `creator_with_social.html` | Profil z linkami do social media | Testy ekstrakcji social media |
| `creator_minimal.html` | Minimalny profil (bez bio, avatar) | Testy odporności na brakujące dane |

#### 3. Categories (`categories/`)

| Fixture | Opis | Użycie |
|---------|------|--------|
| `category_saas.html` | Kategoria SaaS z listą produktów | Testy parsowania kategorii |
| `category_with_products.html` | Kategoria z produktami (pozycje) | Testy ekstrakcji pozycji w kategorii |

#### 4. Sitemap (`sitemap/`)

| Fixture | Opis | Użycie |
|---------|------|--------|
| `sitemap_marketplace.xml` | Marketplace sitemap (pełny) | Testy parsowania sitemap |
| `sitemap_main.xml` | Główny sitemap (fallback) | Testy fallback mechanism |

### B. JSON Fixtures (dla modeli)

**Lokalizacja:** `tests/fixtures/json/`

#### 1. Products (`products/`)

| Fixture | Opis | Użycie |
|---------|------|--------|
| `product_template_complete.json` | Kompletne dane template (wszystkie pola) | Testy tworzenia modelu Product |
| `product_template_minimal.json` | Minimalne dane (tylko wymagane pola) | Testy walidacji wymaganych pól |
| `product_component_complete.json` | Kompletne dane komponentu | Testy różnic między typami |
| `product_with_categories.json` | Produkt z wieloma kategoriami | Testy parsowania kategorii |
| `product_with_creator.json` | Produkt z danymi twórcy | Testy relacji Product-Creator |

**Struktura przykładu:**
```json
{
  "id": "omicorn",
  "name": "Omicorn",
  "type": "template",
  "categories": ["SaaS", "Agency", "Landing Page"],
  "price": 75.0,
  "is_free": false,
  "features": {
    "pages_list": ["Home", "Contact", "404", "Case studies"],
    "pages_count": 4
  }
}
```

#### 2. Creators (`creators/`)

| Fixture | Opis | Użycie |
|---------|------|--------|
| `creator_complete.json` | Kompletne dane twórcy | Testy tworzenia modelu Creator |
| `creator_minimal.json` | Minimalne dane | Testy walidacji |

#### 3. Categories (`categories/`)

| Fixture | Opis | Użycie |
|---------|------|--------|
| `category_complete.json` | Kompletne dane kategorii | Testy tworzenia modelu Category |

### C. HTTP Mock Fixtures (dla scraperów)

**Lokalizacja:** Fixture'y w `conftest.py` (nie pliki)

Fixture'y HTTP mock są tworzone programatycznie w `tests/conftest.py` i `tests/test_scrapers/conftest.py`:

| Fixture | Opis | Użycie |
|---------|------|--------|
| `mock_httpx_client` | Mock httpx.AsyncClient | Testy scraperów bez rzeczywistych requestów |
| `mock_product_response` | Mock response dla produktu | Testy ProductScraper |
| `mock_creator_response` | Mock response dla profilu | Testy CreatorScraper |
| `mock_sitemap_response` | Mock response dla sitemap | Testy SitemapScraper |
| `mock_error_404` | Mock 404 response | Testy obsługi błędów |
| `mock_error_500` | Mock 500 response | Testy obsługi błędów |
| `mock_timeout` | Mock timeout | Testy obsługi timeoutów |
| `mock_rate_limit` | Mock rate limit (429) | Testy obsługi rate limiting |

**Narzędzie:** `pytest-httpx` lub `pytest-mock` z `httpx.AsyncClient`

### D. File System Fixtures (dla storage)

**Lokalizacja:** Fixture'y w `conftest.py` (nie pliki)

| Fixture | Opis | Użycie |
|---------|------|--------|
| `temp_data_dir` | Tymczasowy katalog danych | Testy FileStorage |
| `mock_file_storage` | Mock storage (opcjonalnie) | Testy bez zapisu na dysk |

**Narzędzie:** Wbudowany `pytest` fixture `tmp_path`

---

## 📝 Struktura conftest.py

### Główne conftest.py (`tests/conftest.py`)

**Zawartość:**
- Fixture'y współdzielone przez wszystkie testy
- Factory fixture'y do ładowania plików
- Ścieżki do katalogów fixture'ów
- Mock'i dla logger, rate_limiter, checkpoint_manager

**Przykład struktury:**
```python
# tests/conftest.py
"""
Główne fixture'y współdzielone dla wszystkich testów.
"""

import pytest
from pathlib import Path
from typing import Dict
import json

# ===== Ścieżki do fixture'ów =====

@pytest.fixture
def fixtures_dir() -> Path:
    """Zwraca ścieżkę do katalogu z fixture'ami."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def html_fixtures_dir(fixtures_dir) -> Path:
    """Zwraca ścieżkę do katalogu z HTML fixture'ami."""
    return fixtures_dir / "html"

@pytest.fixture
def json_fixtures_dir(fixtures_dir) -> Path:
    """Zwraca ścieżkę do katalogu z JSON fixture'ami."""
    return fixtures_dir / "json"

# ===== Factory fixture'y do ładowania plików =====

@pytest.fixture
def load_html_fixture(html_fixtures_dir):
    """Factory fixture do ładowania HTML fixture'ów."""
    def _load(name: str) -> str:
        path = html_fixtures_dir / name
        if not path.exists():
            pytest.fail(f"HTML fixture not found: {name}")
        return path.read_text(encoding="utf-8")
    return _load

@pytest.fixture
def load_json_fixture(json_fixtures_dir):
    """Factory fixture do ładowania JSON fixture'ów."""
    def _load(name: str) -> Dict:
        path = json_fixtures_dir / name
        if not path.exists():
            pytest.fail(f"JSON fixture not found: {name}")
        return json.loads(path.read_text(encoding="utf-8"))
    return _load

# ===== HTML Fixtures dla produktów =====

@pytest.fixture
def html_template_omicorn(load_html_fixture) -> str:
    """HTML strony template Omicorn (pełna)."""
    return load_html_fixture("products/template_omicorn.html")

@pytest.fixture
def html_template_free(load_html_fixture) -> str:
    """HTML darmowego template."""
    return load_html_fixture("products/template_free.html")

# ... więcej HTML fixtures

# ===== JSON Fixtures dla modeli =====

@pytest.fixture
def product_data_template(load_json_fixture) -> Dict:
    """Kompletne dane template dla modelu Product."""
    return load_json_fixture("products/product_template_complete.json")

# ... więcej JSON fixtures

# ===== Mock'i dla utilities =====

@pytest.fixture
def mock_logger(monkeypatch):
    """Mock logger."""
    # Implementacja mock'a
    pass

@pytest.fixture
def mock_rate_limiter(monkeypatch):
    """Mock rate limiter."""
    # Implementacja mock'a
    pass
```

### Specyficzne conftest.py

#### `tests/test_parsers/conftest.py`
- Fixture'y specyficzne dla parserów
- HTML fixtures dla różnych typów produktów
- Przykładowe URL-e

#### `tests/test_scrapers/conftest.py`
- Mock HTTP fixtures
- Mock httpx client
- Mock responses dla różnych URL-i

#### `tests/test_models/conftest.py`
- JSON fixtures dla modeli
- Przykładowe dane testowe

#### `tests/test_utils/conftest.py`
- Mock'i dla utilities
- Przykładowe dane wejściowe

---

## 🧪 Przykłady użycia fixture'ów

### Test parsera z HTML fixture

```python
# tests/test_parsers/test_product_parser.py
import pytest

class TestProductParser:
    """Tests for ProductParser."""
    
    def test_parse_template_omicorn(self, html_template_omicorn):
        """Test parsowania template Omicorn."""
        from src.parsers.product_parser import ProductParser
        
        parser = ProductParser()
        url = "https://www.framer.com/marketplace/templates/omicorn/"
        
        product = parser.parse(html_template_omicorn, url, "template")
        
        assert product is not None
        assert product.name == "Omicorn"
        assert product.type == "template"
        assert product.price == 75.0
        assert product.is_free is False
        assert len(product.categories) == 8
        assert "SaaS" in product.categories
        assert len(product.features.pages_list) == 4
        assert "Home" in product.features.pages_list
        assert product.features.pages_count == 4
    
    def test_parse_template_free(self, html_template_free):
        """Test parsowania darmowego template."""
        from src.parsers.product_parser import ProductParser
        
        parser = ProductParser()
        url = "https://www.framer.com/marketplace/templates/free-template/"
        
        product = parser.parse(html_template_free, url, "template")
        
        assert product.is_free is True
        assert product.price is None
```

### Test scrapera z mock HTTP

```python
# tests/test_scrapers/test_product_scraper.py
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
class TestProductScraper:
    """Tests for ProductScraper."""
    
    async def test_scrape_product(self, mock_httpx_client, html_template_omicorn):
        """Test scrapowania produktu z mock'iem."""
        from src.scrapers.product_scraper import ProductScraper
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html_template_omicorn
        mock_httpx_client.get.return_value = mock_response
        
        async with ProductScraper(client=mock_httpx_client) as scraper:
            product = await scraper.scrape(
                "https://www.framer.com/marketplace/templates/omicorn/"
            )
            
            assert product is not None
            assert product.name == "Omicorn"
            mock_httpx_client.get.assert_called_once()
```

### Test modelu z JSON fixture

```python
# tests/test_models/test_product.py
import pytest

class TestProduct:
    """Tests for Product model."""
    
    def test_product_from_fixture(self, product_data_template):
        """Test tworzenia Product z fixture."""
        from src.models.product import Product
        
        product = Product(**product_data_template)
        
        assert product.id == product_data_template["id"]
        assert product.name == product_data_template["name"]
        assert product.type == product_data_template["type"]
```

---

## 📊 Markery testowe

### Definicje markerów (w `pytest.ini`):

```ini
markers =
    unit: marks tests as unit tests (deselect with '-m "not unit"')
    integration: marks tests as integration tests (deselect with '-m "not integration"')
    slow: marks tests as slow (deselect with '-m "not slow"')
```

### Użycie markerów:

```python
@pytest.mark.unit
def test_parse_price():
    """Unit test - szybki test jednostkowy."""
    pass

@pytest.mark.integration
@pytest.mark.slow
async def test_full_scraping_flow():
    """Integration test - testuje pełny flow scrapowania."""
    pass
```

### Uruchamianie testów:

```bash
# Tylko unit testy
pytest -m unit

# Tylko integration testy
pytest -m integration

# Bez slow testów
pytest -m "not slow"

# Wszystkie testy
pytest
```

---

## 🎯 Coverage requirements

### Minimalne coverage:

- **Parsers:** 85%+
- **Models:** 90%+
- **Utils:** 80%+
- **Scrapers:** 75%+ (ze względu na mock'i)

### Uruchamianie coverage:

```bash
pytest --cov=src --cov-report=html --cov-report=term
```

---

## 🔄 Aktualizacja fixture'ów

### Kiedy aktualizować fixture'y:

1. **Zmiana struktury HTML** na Framer Marketplace
2. **Nowe funkcjonalności** w parserach/scraperach
3. **Edge cases** odkryte podczas scrapowania
4. **Aktualizacja danych** - okresowo (co 3-6 miesięcy)

### Jak aktualizować:

1. Pobierz nowy HTML z rzeczywistej strony
2. Zastąp stary fixture
3. Zaktualizuj komentarz z datą
4. Uruchom testy - sprawdź czy wszystko działa
5. Commit z opisem zmian

### Wersjonowanie:

- Fixture'y nie są wersjonowane osobno
- Zmiany są commitowane z kodem
- Komentarz w fixture zawiera datę pobrania

---

## 📚 Dokumentacja fixture'ów

### `tests/fixtures/README.md`

Każdy katalog fixture'ów powinien zawierać `README.md` z:

1. **Opisem** - co zawiera katalog
2. **Listą fixture'ów** - co każdy fixture zawiera
3. **Przykładami użycia** - jak używać fixture'ów
4. **Źródłem danych** - skąd pochodzą fixture'y
5. **Datą ostatniej aktualizacji** - kiedy ostatnio aktualizowane

**Przykład:**
```markdown
# HTML Fixtures

## Products

### template_omicorn.html
- **Źródło:** https://www.framer.com/marketplace/templates/omicorn/
- **Data pobrania:** 2025-01-XX
- **Zawartość:** Pełna strona template z wszystkimi features, kategoriami, stronami
- **Użycie:** Testy parsowania kompletnego template

### template_free.html
- **Źródło:** https://www.framer.com/marketplace/templates/[nazwa-free-template]/
- **Data pobrania:** 2025-01-XX
- **Zawartość:** Darmowy template z przyciskiem "Preview"
- **Użycie:** Testy parsowania darmowych produktów
```

---

## ✅ Checklist tworzenia nowego testu

- [ ] Utworzono test w odpowiednim katalogu (`test_*/`)
- [ ] Użyto odpowiednich fixture'ów (jeśli potrzebne)
- [ ] Dodano odpowiednie markery (`@pytest.mark.unit` lub `@pytest.mark.integration`)
- [ ] Test ma opisową nazwę i docstring
- [ ] Test pokrywa happy path + edge cases
- [ ] Test jest niezależny (nie zależy od innych testów)
- [ ] Test jest deterministyczny (te same dane = ten sam wynik)
- [ ] Test używa mock'ów dla zewnętrznych zależności (HTTP, file system)
- [ ] Test przechodzi lokalnie przed commitem
- [ ] Coverage nie spadło poniżej wymagań

---

## 🚀 Best Practices

### 1. Organizacja testów

- ✅ Jeden test = jedna funkcjonalność
- ✅ Testy powinny być niezależne
- ✅ Użyj fixture'ów zamiast duplikować kod
- ✅ Grupuj powiązane testy w klasy

### 2. Fixture'y

- ✅ Użyj fixture'ów dla danych testowych (nie hardcode)
- ✅ Użyj factory fixture'ów dla ładowania plików
- ✅ Użyj mock'ów dla zewnętrznych zależności
- ✅ Użyj `tmp_path` dla testów file system

### 3. Mock'i

- ✅ Mockuj zewnętrzne API (HTTP requests)
- ✅ Mockuj file system operations
- ✅ Mockuj time-sensitive operations (rate limiting)
- ✅ Mockuj logger (opcjonalnie, dla czystych testów)

### 4. Assertions

- ✅ Użyj opisowych assertion messages
- ✅ Testuj zarówno happy path jak i edge cases
- ✅ Testuj walidację (Pydantic models)
- ✅ Testuj error handling

### 5. Async tests

- ✅ Użyj `@pytest.mark.asyncio` dla async testów
- ✅ Użyj `async with` dla context managers
- ✅ Użyj `await` dla async operations
- ✅ Testuj zarówno async jak i sync wersje

---

## 📝 Changelog

### 2025-01-XX - Inicjalna wersja
- Utworzenie dokumentacji testów i fixture'ów
- Definicja struktury folderów
- Definicja typów fixture'ów
- Konwencje nazewnictwa
- Przykłady użycia
- Best practices

---

## 🔗 Linki

- [pytest documentation](https://docs.pytest.org/)
- [pytest-httpx](https://pytest-httpx.readthedocs.io/) - Mock HTTP requests
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) - Async test support
- [pytest-cov](https://pytest-cov.readthedocs.io/) - Coverage plugin

---

**Uwaga:** Ten dokument jest źródłem prawdy i powinien być aktualizowany przy każdej zmianie w strukturze testów lub fixture'ów. Wszystkie decyzje dotyczące testów powinny być tutaj dokumentowane.



