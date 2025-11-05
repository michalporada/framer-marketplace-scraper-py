# Scraper Rules

**Cel:** Zapewnić stabilność, bezpieczeństwo i zgodność z Framer Marketplace.

## Podstawowe Zasady

### Respektowanie Framer Marketplace

1. **Rate Limiting**
   - Zawsze używaj `RateLimiter` z `src/utils/rate_limiter.py`
   - Limit: 1-2 requesty na sekundę (domyślnie 1.0 req/s)
   - Randomizuj opóźnienia między requestami (0.5-2s)
   - NIE przekraczaj limitów - grozi to blokadą IP

2. **User-Agent Rotation**
   - Zawsze używaj rotacji User-Agent
   - Używaj `src/utils/user_agents.py` do pobierania User-Agent
   - Nie używaj domyślnego User-Agent biblioteki

3. **Robots.txt**
   - Sprawdzaj robots.txt przed scrapowaniem
   - Respektuj reguły z robots.txt
   - Nie scrapuj stron zabronionych

4. **Error Handling**
   - Implementuj retry logic z exponential backoff
   - Używaj `src/utils/retry.py` dla retry
   - Max retries: 3 (domyślnie)
   - Timeout: 30 sekund (domyślnie)

## Struktura Scraperów

### Hierarchia Scraperów

```
MarketplaceScraper (orchestrator)
  ├── SitemapScraper (pobieranie listy URL)
  ├── ProductScraper (scrapowanie produktów)
  ├── CreatorScraper (scrapowanie twórców)
  └── CategoryScraper (scrapowanie kategorii)
```

### Zasady Implementacji

1. **Async Context Manager**
   - Wszystkie scrapery używają `async with` pattern
   - Implementuj `__aenter__` i `__aexit__`
   - Zarządzaj sesją HTTP wewnątrz context managera

2. **Separacja Odpowiedzialności**
   - Scraper: tylko pobieranie HTML
   - Parser: tylko ekstrakcja danych z HTML
   - Model: tylko walidacja danych

3. **Checkpoint System**
   - Wszystkie scrapery obsługują checkpoint/resume
   - Zapisuj checkpoint po każdej partii produktów
   - Używaj `src/utils/checkpoint.py` do zarządzania checkpointami

## SitemapScraper

### Zasady

1. **Priorytet sitemap**
   - Próbuj najpierw: `/marketplace/sitemap.xml`
   - Fallback: `/sitemap.xml` (główny sitemap)
   - Obsługuj błędy gracefully

2. **Filtrowanie URL**
   - Wyodrębnij tylko produkty marketplace:
     - Templates: `/marketplace/templates/{name}/`
     - Components: `/marketplace/components/{name}/`
     - Vectors: `/marketplace/vectors/{name}/`
     - Plugins: `/marketplace/plugins/{name}/`
   - Profile: `/@{username}/` (wszystko z `@`)
   - Kategorie: `/marketplace/category/{name}/`

3. **Deduplikacja**
   - Usuń duplikaty URL
   - Sortuj URL dla spójności

## ProductScraper

### Zasady

1. **Obsługa wszystkich typów produktów**
   - Templates: `/marketplace/templates/{name}/`
   - Components: `/marketplace/components/{name}/`
   - Vectors: `/marketplace/vectors/{name}/`
   - Plugins: `/marketplace/plugins/{name}/`

2. **Identyfikacja typu produktu**
   - Z URL (priorytet)
   - Z HTML (fallback)
   - Z JSON danych Next.js (jeśli dostępne)

3. **Pobieranie danych**
   - Pobierz stronę produktu
   - Wywołaj odpowiedni parser (`product_parser.py`)
   - Waliduj dane przez Pydantic model

4. **Error Handling**
   - Jeśli produkt nie istnieje: skip, loguj warning
   - Jeśli timeout: retry z exponential backoff
   - Jeśli błąd parsowania: loguj error, skip produkt

## CreatorScraper

### Zasady

1. **Obsługa username z znakami specjalnymi**
   - Username może zawierać znaki specjalne (np. `/@-790ivi/`)
   - URL-encode username jeśli potrzebne
   - Obsługuj wszystkie profile zaczynające się od `@`

2. **Pobieranie danych**
   - Pobierz profil twórcy (`/@username/`)
   - Wywołaj `creator_parser.py`
   - Zbierz wszystkie produkty twórcy

3. **Zapis danych**
   - Zapisuj profil jako osobny plik: `data/creators/{username}.json`
   - NIE duplikuj danych twórcy w plikach produktów
   - Linkuj produkty przez username

4. **Avatar i Social Media**
   - Avatar: wyciągnij z JSON danych Next.js (priorytet)
   - Pomijaj placeholdery API
   - Social Media: filtruj linki Framer automatycznie
   - Obsługuj: Twitter/X, LinkedIn, Instagram, GitHub, Dribbble, Behance, YouTube

## CategoryScraper

### Zasady

1. **Opcjonalny scraper**
   - Domyślnie wyłączony (`scrape_categories: false`)
   - Można włączyć przez konfigurację

2. **Pobieranie danych**
   - Pobierz stronę kategorii
   - Wyodrębnij listę produktów w kategorii
   - Zbierz metadane kategorii (nazwa, opis, liczba produktów)

## Rate Limiting Implementation

### Wymagania

```python
# Zawsze używaj RateLimiter
from src.utils.rate_limiter import RateLimiter

async with RateLimiter(rate_limit=1.0) as limiter:
    await limiter.wait()  # Przed każdym requestem
    response = await client.get(url)
```

### Best Practices

1. **Timing**
   - Czekaj PRZED requestem, nie po
   - Mierz czas oczekiwania dla metryk
   - Loguj nadmierne opóźnienia

2. **Randomizacja**
   - Dodaj losowe opóźnienie (0.1-0.5s) do base delay
   - Unikaj przewidywalnych wzorców

3. **Respect Rate Limits**
   - Jeśli otrzymasz 429 (Too Many Requests):
     - Zwiększ opóźnienie
     - Zatrzymaj scrapowanie na 5-10 minut
     - Loguj warning

## Error Handling

### Retry Logic

```python
from src.utils.retry import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=1.0)
async def scrape_product(url: str):
    # Scrapowanie produktu
    pass
```

### Error Types

1. **TimeoutError**
   - Retry z exponential backoff
   - Max 3 retry
   - Po 3 retry: skip, loguj error

2. **HTTPError (404, 403, 429)**
   - 404: skip, loguj warning (produkt nie istnieje)
   - 403: skip, loguj error (może być blokada)
   - 429: zwiększ opóźnienie, retry po dłuższym czasie

3. **ParsingError**
   - Loguj error z kontekstem
   - Skip produkt
   - Nie retry - błąd parsowania nie jest recoverable

4. **ValidationError (Pydantic)**
   - Loguj error z szczegółami walidacji
   - Skip produkt
   - Może wskazywać na zmianę struktury HTML

## Metrics Tracking

### Wymagane Metryki

1. **Dla każdego scrapera:**
   - Liczba scrapowanych produktów/twórców/kategorii
   - Liczba błędów
   - Success rate
   - Czas scrapowania

2. **Dla requestów:**
   - Liczba requestów
   - Total wait time (rate limiting)
   - Liczba retry

3. **Dla błędów:**
   - Błędy według typu
   - Błędy według URL

### Użycie

```python
from src.utils.metrics import get_metrics

metrics = get_metrics()
metrics.start()
metrics.record_product_scraped()
metrics.record_request(wait_time=1.5)
metrics.record_product_failed(error_type="TimeoutError", url=url)
metrics.log_summary()  # Na końcu
```

## Logging

### Strukturalne Logowanie

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("product_scraped", product_id=product_id, product_type=type)
logger.warning("product_not_found", url=url)
logger.error("scraping_failed", error=str(e), url=url, retry_count=retry)
```

### Poziomy Logowania

- **INFO**: Normalne operacje (scrapowanie rozpoczęte, produkt scrapowany)
- **WARNING**: Niestandardowe sytuacje (produkt nie znaleziony, timeout)
- **ERROR**: Błędy wymagające uwagi (parsing error, validation error)

## Checklist przed Implementacją

- [ ] Rate limiting zaimplementowany
- [ ] User-Agent rotation działa
- [ ] Retry logic z exponential backoff
- [ ] Checkpoint system obsługiwany
- [ ] Metrics tracking zaimplementowany
- [ ] Strukturalne logowanie
- [ ] Error handling dla wszystkich przypadków
- [ ] Walidacja danych przez Pydantic
- [ ] Testy jednostkowe napisane
- [ ] Dokumentacja zaktualizowana (jeśli potrzebne)

---

**Uwaga:** Te reguły są draftem i mogą być rozszerzone/zmodyfikowane w przyszłości.

