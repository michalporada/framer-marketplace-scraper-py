# Ogólne Reguły Pracy z Projektem

**Cel:** Zapewnić spójność i stabilność całego repo — żeby każdy agent rozumiał filozofię projektu.

## Filozofia Projektu

### Wizja
Projekt to zaawansowany scraper do zbierania danych z Framer Marketplace, który umożliwia automatyzację pobierania informacji o produktach, twórcach, kategoriach i recenzjach. System jest zbudowany z myślą o stabilności, bezpieczeństwie i zgodności z Framer Marketplace.

### Kluczowe Zasady

1. **Normalizacja Danych (Opcja B)**
   - Wszystkie daty i statystyki zapisujemy w dwóch formatach:
     - `raw`: Format surowy z HTML (np. "5 months ago", "19.8K Views")
     - `normalized`: Format znormalizowany (ISO 8601 dla dat, liczby całkowite dla statystyk)
   - Zapewnia to elastyczność analizy i możliwość weryfikacji danych

2. **Type Safety**
   - Używamy Pydantic v2 do walidacji wszystkich danych
   - Wszystkie modele mają pełną typizację
   - Type hints obowiązkowe w całym kodzie

3. **Respektowanie Framer Marketplace**
   - Rate limiting: 1-2 requesty na sekundę
   - Rotacja User-Agent
   - Respektowanie robots.txt
   - Graceful error handling

4. **Checkpoint System**
   - System umożliwia wznowienie scrapowania po przerwie
   - Checkpoint zapisywany w `data/checkpoint.json`
   - Wszystkie scrapery powinny obsługiwać resume capability

## Struktura Projektu

### Organizacja Katalogów

```
scraper-v2/
├── src/
│   ├── scrapers/          # Scrapery (sitemap, product, creator, category)
│   ├── parsers/           # Parsery HTML (product, creator, review, category)
│   ├── models/            # Modele Pydantic (Product, Creator, Review, Category)
│   ├── storage/           # Zapis danych (file_storage, database)
│   ├── utils/             # Narzędzia (logger, rate_limiter, retry, normalizers, checkpoint, metrics)
│   └── config/            # Konfiguracja (settings.py)
├── data/                  # Dane scrapowane (JSON/CSV)
├── tests/                 # Testy jednostkowe
├── scripts/               # Skrypty pomocnicze
├── docs/                  # Dokumentacja techniczna
└── cursor_rules/          # Reguły dla Cursor AI
```

### Zasady Organizacji Kodu

1. **Separacja odpowiedzialności**
   - Scrapers: tylko pobieranie HTML
   - Parsers: tylko ekstrakcja danych z HTML
   - Models: tylko walidacja i struktura danych
   - Storage: tylko zapis/odczyt danych

2. **Naming Conventions**
   - Pliki: snake_case (np. `product_scraper.py`)
   - Klasy: PascalCase (np. `ProductScraper`)
   - Funkcje: snake_case (np. `scrape_product`)
   - Zmienne: snake_case (np. `product_id`)

3. **Import Organization**
   - Standard library
   - Third-party packages
   - Local imports (src/)
   - W każdej sekcji sortowanie alfabetyczne

## Zasady Pracy

### Przed Rozpoczęciem Pracy

1. **Zawsze sprawdź dokumentację**
   - Przeczytaj `README.md`
   - Sprawdź `documentation_sources/` dla szczegółów
   - Zrozum architekturę przed zmianami

2. **Zrozum kontekst zmiany**
   - Jakie pliki są dotknięte?
   - Jakie są zależności?
   - Czy zmiana wymaga aktualizacji dokumentacji?

3. **Sprawdź istniejące testy**
   - Czy są testy dla zmienianego kodu?
   - Czy testy przechodzą przed zmianą?
   - Czy trzeba dodać nowe testy?

### Podczas Pracy

1. **Zachowaj spójność**
   - Używaj istniejących wzorców
   - Nie wprowadzaj nowych bibliotek bez uzasadnienia
   - Zachowaj styl kodu zgodny z resztą projektu

2. **Testuj lokalnie**
   - Uruchom testy przed commitem
   - Sprawdź linting i formatting
   - Przetestuj na małej próbce danych

3. **Loguj odpowiednio**
   - Używaj strukturalnego logowania (structlog)
   - Loguj na odpowiednich poziomach (INFO, WARNING, ERROR)
   - Zawieraj kontekst w logach (product_id, url, error_type)

### Po Zakończeniu Pracy

1. **Aktualizuj dokumentację** (jeśli potrzebne)
   - Zawsze pytaj użytkownika przed aktualizacją dokumentacji
   - Dokumentuj breaking changes
   - Aktualizuj przykłady użycia

2. **Commituj zgodnie z konwencjami**
   - Używaj Conventional Commits
   - Jeden commit = jedna logiczna zmiana
   - Opisuj co zmieniasz i dlaczego

## Współpraca z Agentami

### Delegowanie Zadań

- Każdy agent ma jasno określony zakres odpowiedzialności (patrz `agents.md`)
- Nie podejmuj decyzji poza swoim zakresem
- Jeśli potrzeba zmiany w innym obszarze, zapytaj użytkownika lub deleguj

### Komunikacja

- Bądź precyzyjny w komunikacji
- Zawsze podawaj kontekst zmian
- Wyjaśniaj decyzje techniczne

## Zasady Bezpieczeństwa

1. **Nie commituj wrażliwych danych**
   - Używaj zmiennych środowiskowych
   - Sprawdź `.gitignore`
   - Nie hardcoduj API keys, tokens, passwords

2. **Walidacja danych wejściowych**
   - Zawsze waliduj dane przed zapisem
   - Używaj Pydantic models
   - Obsługuj edge cases

3. **Error Handling**
   - Nie ukrywaj błędów
   - Loguj szczegóły błędów
   - Implementuj graceful degradation

## Zasady Wydajności

1. **Rate Limiting**
   - Zawsze używaj rate limitera
   - Nie przekraczaj limitów Framer Marketplace
   - Randomizuj opóźnienia

2. **Optymalizacja**
   - Używaj async/await gdzie możliwe
   - Nie blokuj głównego wątku
   - Optymalizuj zapytania do bazy danych

3. **Monitoring**
   - Trackuj metryki (patrz `metrics.md`)
   - Monitoruj wydajność
   - Alertuj przy problemach

## Checklist przed Merge

- [ ] Wszystkie testy przechodzą
- [ ] Linting i formatting OK
- [ ] Dokumentacja zaktualizowana (jeśli potrzebne)
- [ ] Commit message zgodny z konwencjami
- [ ] Brak wrażliwych danych w kodzie
- [ ] Logi są odpowiednie
- [ ] Rate limiting działa
- [ ] Error handling zaimplementowany
- [ ] Metryki są trackowane

---

**Uwaga:** Te reguły są draftem i mogą być rozszerzone/zmodyfikowane w przyszłości.

