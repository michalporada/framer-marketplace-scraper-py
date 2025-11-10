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
   - Implementuj retry logic z exponential backoff + jitter
   - Używaj `src/utils/retry.py` dla retry
   - Max retries: 5 (domyślnie, z exponential backoff do max 5 min)
   - Timeout per request: 25 sekund (domyślnie, zakres 20-30s)
   - Globalny timeout na cały scraping: 15 minut
   - Jitter: losowe opóźnienie 0-20% do base wait time

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
   - Próbuj tylko: `/marketplace/sitemap.xml` (BRAK fallback do głównego sitemap)
   - Jeśli marketplace sitemap zwraca 5xx: przerwij scraper natychmiast (exit code 2)
   - Jeśli marketplace sitemap zwraca inne błędy (non-5xx): użyj cache sitemapa (jeśli dostępny)
   - Cache sitemapa: zapisywany po każdym udanym pobraniu, TTL: 1 godzina
   - Weryfikacja parsowania: scraper kończy się błędem, jeśli sitemap nie zawiera URL-i

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
from src.utils.retry import retry_async

# Retry z exponential backoff + jitter
html = await retry_async(
    _fetch,
    max_retries=5,  # 5-6 retry
    initial_wait=2.0,  # Start z 2s
    max_wait=300.0  # Max 5 minut
)
```

### Error Types

1. **TimeoutError**
   - Retry z exponential backoff + jitter
   - Max 5 retry (domyślnie)
   - Exponential backoff: initial_wait * 2^attempt (max 5 min)
   - Jitter: losowe 0-20% base wait time
   - Po wyczerpaniu retry: skip, loguj error
   - Logowanie slow requests (>10s)

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
   - Monitoring trwania runów (zapis do `data/metrics.log`)

2. **Dla requestów:**
   - Liczba requestów
   - Total wait time (rate limiting)
   - Liczba retry
   - Slow requests (>10s) - logowanie z warning

3. **Dla błędów:**
   - Błędy według typu
   - Błędy według URL

4. **Globalne timeouty:**
   - Globalny timeout na cały scraping: 15 minut
   - Ostrzeżenie gdy >80% timeoutu wykorzystane
   - Scraper kończy się błędem po przekroczeniu globalnego timeoutu

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

## Zabezpieczenia i Walidacja

### Twarde Zabezpieczenia

1. **Minimalny próg danych**
   - Minimum 50 URL-i z sitemapa (konfigurowalne: `min_urls_threshold`)
   - Jeśli mniej → scraper kończy się błędem przed rozpoczęciem scrapowania

2. **Blokowanie eksportu przy braku danych**
   - Jeśli `products_scraped == 0`: zablokuj eksport CSV i zapis do DB
   - Loguj error i kończ z odpowiednim exit code

3. **Deduplikacja**
   - Deduplikacja po: product ID, product URL, creator username
   - Zablokuj zapis do DB jeśli znaleziono duplikaty
   - Loguj liczbę duplikatów

4. **Walidacja przed zapisem**
   - Walidacja produktu przed zapisem do DB (sprawdzenie ID i URL)
   - Deduplikacja przed eksportem CSV
   - Logowanie liczby rekordów przed zapisaniem

### Cache i Monitoring

1. **Cache sitemapa**
   - Cache ostatniego poprawnego sitemapa (TTL: 1 godzina)
   - Używany jako fallback przy błędach non-5xx
   - Lokalizacja: `data/sitemap_cache.xml`

2. **Monitoring trwania runów**
   - Zapis metryk do `data/metrics.log` (JSON Lines format)
   - Każdy run zapisuje timestamp i pełne metryki
   - Umożliwia analizę trendów i wykrywanie problemów

## Checklist przed Implementacją

- [ ] Rate limiting zaimplementowany
- [ ] User-Agent rotation działa
- [ ] Retry logic z exponential backoff + jitter (5 retry, max 5 min)
- [ ] Globalny timeout na cały scraping (15 min)
- [ ] Timeout per request (25s)
- [ ] Cache sitemapa zaimplementowany
- [ ] Checkpoint system obsługiwany
- [ ] Metrics tracking zaimplementowany (zapis do metrics.log)
- [ ] Strukturalne logowanie
- [ ] Error handling dla wszystkich przypadków
- [ ] Walidacja danych przez Pydantic
- [ ] Twarde zabezpieczenia (min próg, deduplikacja, blokowanie eksportu)
- [ ] Logowanie slow requests
- [ ] Testy jednostkowe napisane
- [ ] Dokumentacja zaktualizowana (jeśli potrzebne)

---

**Uwaga:** Te reguły są draftem i mogą być rozszerzone/zmodyfikowane w przyszłości.

