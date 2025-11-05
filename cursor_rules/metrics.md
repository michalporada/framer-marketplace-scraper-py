# Metrics Rules

**Cel:** Zapewnić spójność metryk.

## System Metryk

### ScraperMetrics Class

Główna klasa do trackowania metryk scrapowania znajduje się w `src/utils/metrics.py`.

### Wymagane Metryki

#### 1. Counters

- **Products**
  - `products_scraped`: Liczba pomyślnie scrapowanych produktów
  - `products_failed`: Liczba nieudanych prób scrapowania produktów

- **Creators**
  - `creators_scraped`: Liczba pomyślnie scrapowanych twórców
  - `creators_failed`: Liczba nieudanych prób scrapowania twórców

- **Categories**
  - `categories_scraped`: Liczba pomyślnie scrapowanych kategorii
  - `categories_failed`: Liczba nieudanych prób scrapowania kategorii

#### 2. Timing

- `total_requests`: Całkowita liczba requestów HTTP
- `total_wait_time`: Całkowity czas oczekiwania (rate limiting)
- `total_retries`: Całkowita liczba retry

#### 3. Errors

- `errors_by_type`: Słownik błędów według typu (np. `{"TimeoutError": 5, "HTTPError": 2}`)
- `errors_by_url`: Słownik błędów według URL (dla debugowania)

#### 4. Duration

- `start_time`: Czas rozpoczęcia scrapowania
- `end_time`: Czas zakończenia scrapowania
- Obliczane: `duration`, `products_per_second`, `success_rate`

## Użycie

### Inicjalizacja

```python
from src.utils.metrics import get_metrics

metrics = get_metrics()
metrics.start()  # Na początku scrapowania
```

### Recording Events

```python
# Sukces
metrics.record_product_scraped()
metrics.record_creator_scraped()
metrics.record_category_scraped()

# Błędy
metrics.record_product_failed(error_type="TimeoutError", url=url)
metrics.record_creator_failed(error_type="HTTPError", url=url)
metrics.record_category_failed(error_type="ParsingError", url=url)

# Requesty
metrics.record_request(wait_time=1.5)  # wait_time w sekundach

# Retry
metrics.record_retry()
```

### Zakończenie

```python
metrics.stop()  # Na końcu scrapowania
metrics.log_summary()  # Loguj podsumowanie
```

## Zasady Trackowania

### 1. Always Track

- Zawsze trackuj sukcesy i błędy
- Zawsze trackuj requesty (z wait_time)
- Zawsze trackuj retry

### 2. Error Context

- Zawsze podawaj `error_type` przy błędzie
- Podawaj `url` dla błędów requestów (opcjonalnie, dla debugowania)
- Używaj standardowych nazw błędów:
  - `TimeoutError`
  - `HTTPError`
  - `ParsingError`
  - `ValidationError`
  - `ConnectionError`

### 3. Timing

- `start()` na początku scrapowania (w `main()` lub na początku `scrape()`)
- `stop()` na końcu scrapowania (po zakończeniu wszystkich operacji)
- `wait_time` w sekundach (float)

## Obliczane Metryki

### Success Rate

```python
success_rate = products_scraped / (products_scraped + products_failed)
```

- Zwraca wartość między 0.0 a 1.0
- 0.0 jeśli brak prób

### Products Per Second

```python
products_per_second = products_scraped / duration
```

- Obliczane na podstawie `duration`
- 0.0 jeśli brak produktów lub duration = 0

### Average Wait Time

```python
average_wait_time = total_wait_time / total_requests
```

- Średni czas oczekiwania na request
- 0.0 jeśli brak requestów

## Logging

### Strukturalne Logowanie

```python
metrics.log_summary()  # Loguje pełne podsumowanie
```

### Format Summary

```python
{
  "duration_seconds": 3600.5,
  "duration_formatted": "1h 0m",
  "start_time": "2024-01-01T00:00:00",
  "end_time": "2024-01-01T01:00:00",
  "products": {
    "scraped": 1000,
    "failed": 50,
    "total": 1050,
    "success_rate": 0.952,
    "per_second": 0.278
  },
  "creators": {
    "scraped": 500,
    "failed": 10,
    "total": 510
  },
  "categories": {
    "scraped": 50,
    "failed": 0,
    "total": 50
  },
  "requests": {
    "total": 2000,
    "total_wait_time": 1800.0,
    "average_wait_time": 0.9
  },
  "retries": {
    "total": 25
  },
  "errors": {
    "by_type": {
      "TimeoutError": 20,
      "HTTPError": 30
    },
    "total_unique_urls_failed": 45
  }
}
```

## Best Practices

### 1. Consistency

- Używaj zawsze `get_metrics()` do dostępu do metryk
- Nie tworz wielu instancji `ScraperMetrics`
- Trackuj wszystkie ważne operacje

### 2. Performance

- Metryki są lightweight - nie wpływają na wydajność
- Nie trackuj każdego małego kroku (overhead)
- Trackuj tylko znaczące operacje

### 3. Error Tracking

- Zawsze kategoryzuj błędy przez `error_type`
- Używaj standardowych nazw błędów
- Nie trackuj każdego retry jako błąd (używaj `record_retry()`)

### 4. Context

- Dodawaj kontekst w logach (nie w metrykach)
- Metryki = liczby i statystyki
- Logi = szczegóły i kontekst

## Integration z Scraperami

### MarketplaceScraper

```python
class MarketplaceScraper:
    async def scrape(self, ...):
        metrics = get_metrics()
        metrics.start()
        
        try:
            # Scrapowanie
            metrics.record_product_scraped()
        except Exception as e:
            metrics.record_product_failed(error_type=type(e).__name__, url=url)
        finally:
            metrics.stop()
            metrics.log_summary()
```

### ProductScraper

```python
class ProductScraper:
    async def scrape_product(self, url: str):
        metrics = get_metrics()
        
        try:
            # Scrapowanie
            metrics.record_product_scraped()
        except Exception as e:
            metrics.record_product_failed(
                error_type=type(e).__name__,
                url=url
            )
```

## Export Metryk

### JSON Export (Opcjonalnie)

```python
summary = metrics.get_summary()
with open('metrics.json', 'w') as f:
    json.dump(summary, f, indent=2)
```

### CSV Export (Opcjonalnie)

- Można dodać export do CSV dla analizy
- Format: timestamp, metric_name, value

## Monitoring

### GitHub Actions

- Metryki logowane w GitHub Actions logs
- Można dodać summary do workflow
- Alerty przy niskim success rate

### External Monitoring (Opcjonalnie)

- Sentry dla error tracking
- Custom dashboard dla metryk
- Alerty przy problemach

## Checklist

- [ ] Metryki inicjalizowane na początku (`start()`)
- [ ] Wszystkie sukcesy trackowane (`record_*_scraped()`)
- [ ] Wszystkie błędy trackowane (`record_*_failed()`)
- [ ] Requesty trackowane z wait_time
- [ ] Retry trackowane
- [ ] Metryki zakończone (`stop()`)
- [ ] Summary zalogowane (`log_summary()`)
- [ ] Error types są standardowe
- [ ] Duration jest mierzony poprawnie

---

**Uwaga:** Te reguły są draftem i mogą być rozszerzone/zmodyfikowane w przyszłości.

