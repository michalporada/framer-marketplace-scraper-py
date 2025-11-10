# Plan Testów - Stabilizacja Scrapera

## 📋 Przegląd zmian do przetestowania

### Zadanie 1: Usunięcie błędnej logiki sitemapa ✅
- [ ] Test: Marketplace sitemap zwraca 5xx → scraper kończy się z exit code 2
- [ ] Test: Marketplace sitemap zwraca inne błędy → używa cache (jeśli dostępny)
- [ ] Test: Marketplace sitemap działa → zapisuje do cache

### Zadanie 2: Twarde zabezpieczenia na wyniki ✅
- [ ] Test: < 50 URL-i z sitemapa → scraper kończy się błędem
- [ ] Test: products_scraped == 0 → CSV export zablokowany
- [ ] Test: products_scraped == 0 → DB write zablokowany
- [ ] Test: Duplikaty wykryte → DB write zablokowany dla duplikatów

### Zadanie 3: Naprawa problemów z wydłużaniem czasu scrapów ✅
- [ ] Test: Exponential backoff + jitter działa (5 retry, max 5 min)
- [ ] Test: Timeout per request (25s) działa
- [ ] Test: Globalny timeout (15 min) przerywa scraper
- [ ] Test: Slow requests (>10s) są logowane

### Zadanie 4: Blokowanie duplikatów ✅
- [ ] Test: Deduplikacja po product ID działa
- [ ] Test: Deduplikacja po product URL działa
- [ ] Test: Deduplikacja po creator username działa
- [ ] Test: Duplikaty są logowane

### Zadanie 5: Naprawa artefaktów GitHub Actions ✅
- [ ] Test: Artifact upload działa (scraped-data-latest)
- [ ] Test: Sync workflow pobiera artefakt poprawnie
- [ ] Test: Sprawdzenie artefaktu przed sync działa

### Zadanie 6: Naprawa zmiennego czasu działania scraperów ✅
- [ ] Test: Jitter cron działa (0-60s delay)
- [ ] Test: Cache sitemapa zapisuje się poprawnie
- [ ] Test: Cache sitemapa używa się przy błędach non-5xx
- [ ] Test: Metrics.log zapisuje się poprawnie

### Zadanie 7: Stabilność pipeline ✅
- [ ] Test: Exit code 2 przy upstream 5xx
- [ ] Test: Exit code 1 przy innych błędach
- [ ] Test: Webhook notification działa (jeśli skonfigurowany)

### Zadanie 8: Dodatkowe poprawki jakościowe ✅
- [ ] Test: Weryfikacja sitemap parsowania (puste URL → błąd)
- [ ] Test: Logowanie liczby rekordów przed zapisaniem

---

## 🧪 Szczegółowe testy

### Test 1: Sitemap - brak fallback, przerwanie przy 5xx

**Cel:** Sprawdzić, że scraper nie używa fallback do main sitemap i przerywa przy 5xx

**Kroki:**
1. Uruchom scraper lokalnie
2. Sprawdź logi - powinien próbować tylko marketplace sitemap
3. Jeśli marketplace sitemap zwraca 5xx → scraper kończy się z exit code 2

**Oczekiwany wynik:**
- Brak prób pobrania main sitemap
- Exit code 2 przy 5xx
- Log: "upstream_unavailable" lub "sitemap_fetch_failed_5xx"

**Komenda testowa:**
```bash
python -m src.main 10  # Test z limitem 10 produktów
```

---

### Test 2: Minimalny próg danych (50 URL-i)

**Cel:** Sprawdzić, że scraper kończy się błędem, jeśli < 50 URL-i

**Kroki:**
1. Tymczasowo ustaw `MIN_URLS_THRESHOLD=1000` w `.env`
2. Uruchom scraper
3. Jeśli sitemap zwraca < 1000 URL-i → scraper powinien zakończyć się błędem

**Oczekiwany wynik:**
- Scraper kończy się przed rozpoczęciem scrapowania produktów
- Log: "insufficient_urls" z found i required
- Exit code != 0

**Komenda testowa:**
```bash
# W .env ustaw: MIN_URLS_THRESHOLD=1000
python -m src.main
```

---

### Test 3: Blokowanie eksportu przy products_scraped == 0

**Cel:** Sprawdzić, że CSV export i DB write są zablokowane przy braku produktów

**Kroki:**
1. Uruchom scraper, który nie znajdzie żadnych produktów (np. błędny sitemap)
2. Sprawdź logi - powinien być błąd "no_products_scraped"
3. Sprawdź, że nie powstał plik CSV
4. Sprawdź, że nie było zapisów do DB

**Oczekiwany wynik:**
- Log: "no_products_scraped" z message
- Log: "csv_export_blocked" z reason="no_products_scraped"
- Brak pliku CSV w `data/exports/`
- Brak zapisów do DB

**Komenda testowa:**
```bash
# Symulacja: ustaw błędny sitemap URL w .env
# FRAMER_BASE_URL=https://invalid-url.com
python -m src.main
```

---

### Test 4: Deduplikacja produktów

**Cel:** Sprawdzić, że duplikaty są wykrywane i blokowane

**Kroki:**
1. Uruchom scraper normalnie
2. Sprawdź logi - powinny być warningi o duplikatach (jeśli występują)
3. Sprawdź, że duplikaty nie są zapisywane do DB
4. Sprawdź, że liczba duplikatów jest logowana na końcu

**Oczekiwany wynik:**
- Log: "duplicate_product_id" lub "duplicate_product_url" dla każdego duplikatu
- Log: "db_write_skipped_duplicate" dla duplikatów
- Log: "duplicates_found" na końcu z count
- Brak duplikatów w DB

**Komenda testowa:**
```bash
python -m src.main 100  # Test z większą liczbą produktów
```

---

### Test 5: Exponential backoff + jitter

**Cel:** Sprawdzić, że retry używa exponential backoff z jitter

**Kroki:**
1. Uruchom scraper z limitem
2. Sprawdź logi retry - powinny pokazywać base_wait i jitter
3. Sprawdź, że czasy oczekiwania rosną wykładniczo (2s, 4s, 8s, 16s, 32s...)
4. Sprawdź, że jitter jest dodawany (0-20% base wait)

**Oczekiwany wynik:**
- Log: "retry_attempt" z wait_time, base_wait, jitter
- Czas oczekiwania rośnie wykładniczo
- Jitter jest losowy (0-20% base wait)
- Max 5 retry

**Komenda testowa:**
```bash
# Uruchom z limitem i obserwuj logi
python -m src.main 50
# Sprawdź logi w logs/scraper.log
```

---

### Test 6: Timeout per request (25s)

**Cel:** Sprawdzić, że timeout per request działa

**Kroki:**
1. Uruchom scraper
2. Sprawdź, że requesty kończą się po 25s (jeśli timeout)
3. Sprawdź logi - powinny być timeout errors

**Oczekiwany wynik:**
- Requesty kończą się po ~25s przy timeout
- Log: "TimeoutError" lub podobny
- Retry po timeout

**Komenda testowa:**
```bash
# Można symulować wolne requesty przez proxy lub rate limiting
python -m src.main 10
```

---

### Test 7: Globalny timeout (15 min)

**Cel:** Sprawdzić, że globalny timeout przerywa scraper

**Kroki:**
1. Tymczasowo ustaw `GLOBAL_SCRAPING_TIMEOUT=60` (1 minuta) w `.env`
2. Uruchom scraper z dużą liczbą produktów
3. Sprawdź, że scraper kończy się po 1 minucie

**Oczekiwany wynik:**
- Scraper kończy się po ~60s
- Log: "global_scraping_timeout" z elapsed i timeout
- Exit code != 0
- TimeoutError raised

**Komenda testowa:**
```bash
# W .env ustaw: GLOBAL_SCRAPING_TIMEOUT=60
python -m src.main 1000  # Duża liczba produktów
```

---

### Test 8: Slow requests logging

**Cel:** Sprawdzić, że wolne requesty (>10s) są logowane

**Kroki:**
1. Uruchom scraper
2. Sprawdź logi - powinny być warningi dla requestów >10s

**Oczekiwany wynik:**
- Log: "slow_request" z url, duration, status_code
- Duration > 10.0s
- Message z threshold

**Komenda testowa:**
```bash
python -m src.main 50
# Sprawdź logi w logs/scraper.log dla "slow_request"
```

---

### Test 9: Cache sitemapa

**Cel:** Sprawdzić, że cache sitemapa działa

**Kroki:**
1. Uruchom scraper normalnie (zapisze cache)
2. Sprawdź, że plik `data/sitemap_cache.xml` został utworzony
3. Symuluj błąd non-5xx (np. 404) - scraper powinien użyć cache
4. Sprawdź logi - powinien być "using_cached_sitemap"

**Oczekiwany wynik:**
- Plik `data/sitemap_cache.xml` istnieje po udanym scrapowaniu
- Cache jest używany przy błędach non-5xx
- Log: "sitemap_cache_saved" przy zapisie
- Log: "sitemap_cache_loaded" przy użyciu
- Log: "using_cached_sitemap" przy użyciu cache

**Komenda testowa:**
```bash
# Pierwszy run - zapisze cache
python -m src.main 10

# Sprawdź cache
ls -lh data/sitemap_cache.xml

# Drugi run - użyje cache jeśli upstream nie działa
python -m src.main 10
```

---

### Test 10: Metrics.log zapis

**Cel:** Sprawdzić, że metryki są zapisywane do metrics.log

**Kroki:**
1. Uruchom scraper
2. Sprawdź, że plik `data/metrics.log` został utworzony
3. Sprawdź, że zawiera JSON Lines z metrykami

**Oczekiwany wynik:**
- Plik `data/metrics.log` istnieje
- Zawiera JSON Lines (jeden obiekt JSON per linia)
- Każdy wpis ma timestamp i pełne metryki
- Format: `{"timestamp": "...", "duration_seconds": ..., ...}`

**Komenda testowa:**
```bash
python -m src.main 10
cat data/metrics.log | jq .  # Jeśli masz jq
```

---

### Test 11: Deduplikacja przed eksportem CSV

**Cel:** Sprawdzić, że CSV export deduplikuje produkty

**Kroki:**
1. Utwórz ręcznie kilka zduplikowanych plików JSON w `data/products/`
2. Uruchom export do CSV
3. Sprawdź, że CSV nie zawiera duplikatów

**Oczekiwany wynik:**
- Log: "duplicates_removed_before_export" z count
- CSV zawiera tylko unikalne produkty
- Brak duplikatów w CSV

**Komenda testowa:**
```bash
# Ręcznie skopiuj plik produktu jako duplikat
cp data/products/templates/product1.json data/products/templates/product1_duplicate.json

# Export do CSV
python scripts/export_data.py

# Sprawdź CSV - nie powinien zawierać duplikatów
```

---

### Test 12: Weryfikacja parsowania sitemapa

**Cel:** Sprawdzić, że scraper kończy się błędem, jeśli sitemap nie zawiera URL-i

**Kroki:**
1. Tymczasowo zmodyfikuj `parse_sitemap()` aby zwracała pusty dict
2. Uruchom scraper
3. Sprawdź, że scraper kończy się błędem

**Oczekiwany wynik:**
- Log: "sitemap_parse_verification_failed"
- ValueError raised: "Sitemap parsing returned empty result"
- Exit code != 0

**Komenda testowa:**
```bash
# Test wymaga tymczasowej modyfikacji kodu
# Lub symulacji pustego sitemap
```

---

### Test 13: Logowanie liczby rekordów przed zapisaniem

**Cel:** Sprawdzić, że liczba rekordów jest logowana przed eksportem

**Kroki:**
1. Uruchom scraper
2. Sprawdź logi - powinien być log "records_before_export"

**Oczekiwany wynik:**
- Log: "records_before_export" z:
  - products_scraped
  - products_failed
  - creators_scraped
  - duplicates
  - total_products

**Komenda testowa:**
```bash
python -m src.main 50
# Sprawdź logi w logs/scraper.log dla "records_before_export"
```

---

### Test 14: Jitter cron w GitHub Actions

**Cel:** Sprawdzić, że jitter działa w workflow

**Kroki:**
1. Uruchom workflow ręcznie (workflow_dispatch)
2. Sprawdź logi - powinien być log o jitterze

**Oczekiwany wynik:**
- Log: "⏱️ Adding Xs jitter before scraping..."
- X jest losową liczbą 0-60
- Scraper startuje po jitterze

**Komenda testowa:**
```bash
# W GitHub Actions - workflow_dispatch
# Sprawdź logi workflow
```

---

### Test 15: Exit codes

**Cel:** Sprawdzić, że exit codes są poprawne

**Kroki:**
1. Uruchom scraper normalnie → exit code 0
2. Uruchom scraper z błędem upstream 5xx → exit code 2
3. Uruchom scraper z innym błędem → exit code 1

**Oczekiwany wynik:**
- Success: exit code 0
- Upstream 5xx: exit code 2
- Inne błędy: exit code 1

**Komenda testowa:**
```bash
# Normal run
python -m src.main 10
echo $?  # Powinno być 0

# Test upstream error (wymaga symulacji)
# Sprawdź exit code
```

---

## 🚀 Szybki test end-to-end

**Kompleksowy test wszystkich funkcji:**

```bash
# 1. Wyczyść stare dane
rm -rf data/products/* data/creators/* data/exports/* data/*.log data/sitemap_cache.xml

# 2. Uruchom scraper z limitem
python -m src.main 20

# 3. Sprawdź wyniki
echo "=== Sprawdzenie wyników ==="
echo "Produkty:"
find data/products -name "*.json" | wc -l
echo "Kreatorzy:"
find data/creators -name "*.json" | wc -l
echo "Cache sitemapa:"
ls -lh data/sitemap_cache.xml 2>/dev/null || echo "Brak cache"
echo "Metryki:"
tail -1 data/metrics.log | jq . 2>/dev/null || tail -1 data/metrics.log
echo "Logi:"
grep -E "(insufficient_urls|no_products_scraped|duplicates_found|slow_request|global_scraping_timeout)" logs/*.log | tail -10

# 4. Test export CSV
python scripts/export_data.py
echo "CSV export:"
ls -lh data/exports/*.csv | tail -1

# 5. Sprawdź exit code
echo "Exit code ostatniego runu: $?"
```

---

## 📊 Checklist przed commitem

- [ ] Wszystkie testy lokalne przeszły
- [ ] Brak błędów lintera
- [ ] Logi są czytelne i informatywne
- [ ] Exit codes są poprawne
- [ ] Cache sitemapa działa
- [ ] Metrics.log zapisuje się poprawnie
- [ ] Deduplikacja działa
- [ ] Zabezpieczenia działają (min próg, blokowanie eksportu)
- [ ] Timeouty działają (per request i globalny)
- [ ] Retry z jitter działa

---

## 🔍 Monitoring po wdrożeniu

Po wdrożeniu zmian, monitoruj:

1. **Czas trwania runów** - sprawdź `data/metrics.log`
   - Czy czas jest stabilny?
   - Czy nie ma ekstremalnie długich runów (>15 min)?

2. **Liczba duplikatów** - sprawdź logi
   - Czy są duplikaty?
   - Jeśli tak, dlaczego?

3. **Slow requests** - sprawdź logi
   - Ile jest slow requests?
   - Które URL-e są wolne?

4. **Exit codes** - sprawdź GitHub Actions
   - Czy exit codes są poprawne?
   - Czy pipeline nie jest zielony przy błędach?

5. **Cache sitemapa** - sprawdź użycie
   - Czy cache jest używany?
   - Czy TTL jest odpowiedni?

---

## 📝 Notatki testowe

**Data testów:** _______________

**Tester:** _______________

**Wyniki:**
- [ ] Test 1: Sitemap fallback - PASSED / FAILED
- [ ] Test 2: Minimalny próg - PASSED / FAILED
- [ ] Test 3: Blokowanie eksportu - PASSED / FAILED
- [ ] Test 4: Deduplikacja - PASSED / FAILED
- [ ] Test 5: Exponential backoff - PASSED / FAILED
- [ ] Test 6: Timeout per request - PASSED / FAILED
- [ ] Test 7: Globalny timeout - PASSED / FAILED
- [ ] Test 8: Slow requests - PASSED / FAILED
- [ ] Test 9: Cache sitemapa - PASSED / FAILED
- [ ] Test 10: Metrics.log - PASSED / FAILED
- [ ] Test 11: Deduplikacja CSV - PASSED / FAILED
- [ ] Test 12: Weryfikacja sitemap - PASSED / FAILED
- [ ] Test 13: Logowanie rekordów - PASSED / FAILED
- [ ] Test 14: Jitter cron - PASSED / FAILED
- [ ] Test 15: Exit codes - PASSED / FAILED

**Uwagi:**
_________________________________________________
_________________________________________________

