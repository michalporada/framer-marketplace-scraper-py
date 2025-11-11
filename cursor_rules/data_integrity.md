# Backup & Data Integrity Rules

**Cel:** Ochrona danych historycznych i bezpieczeństwo scrapera.

## Zasady Integralności Danych

### 1. Immutable History

- Dane historyczne NIE powinny być modyfikowane
- Każdy scrap tworzy nową wersję danych
- Zachowaj pełną historię zmian
- **Product History Table (`product_history`):**
  - Tabela w PostgreSQL przechowująca pełną historię zmian produktów
  - Każdy scrap tworzy nowy wpis (INSERT only, nigdy UPDATE)
  - Timestamp `scraped_at` pozwala śledzić zmiany w czasie
  - Automatyczne zapisywanie przez `save_product_history_db()` przy każdym scrapowaniu
  - Umożliwia analizę trendów i porównywanie danych między scrapami
  - Endpoint `/api/products/{id}/changes` używa tej tabeli (priorytet)

### 2. Data Validation

- Wszystkie dane muszą przejść walidację Pydantic przed zapisem
- Nie zapisuj nieprawidłowych danych
- Loguj błędy walidacji

### 3. Consistency

- Zapewnij spójność danych między różnymi źródłami
- Synchronizuj dane między produktami a twórcami
- Sprawdzaj referential integrity

## Backup Strategy

### 1. Automated Backups

#### GitHub Actions Artifacts

- Automatyczny backup po każdym scrapowaniu
- Zapisuj jako GitHub Actions artifacts
- Przechowuj przez 90 dni (default)

#### GitHub Releases

- Backup danych jako release assets
- Tagowane wersje danych
- Długoterminowe przechowywanie

#### Local Backups

- Backup przed dużymi zmianami
- Backup przed eksperymentalnymi scrapami
- Przechowuj w `data/backups/`

### 2. Backup Frequency

- **Daily**: Automatyczny backup po scheduled scrapowaniu
- **Before major changes**: Manual backup przed zmianami
- **On error**: Backup przed rollback

### 3. Backup Content

- Wszystkie pliki z `data/products/`
- Wszystkie pliki z `data/creators/`
- Wszystkie pliki z `data/categories/` (jeśli dostępne)
- Checkpoint file (`data/checkpoint.json`)
- Exports (`data/exports/`)
- **Database backup:**
  - Tabela `products` - najnowsze wersje
  - Tabela `product_history` - pełna historia zmian (WAŻNE!)
  - Tabela `creators` - dane twórców

## Checkpoint System

### Zasady

1. **Checkpoint Location**
   - Plik: `data/checkpoint.json`
   - Format: JSON
   - Zawiera: last_scraped_urls, progress, metadata

2. **Checkpoint Updates**
   - Update po każdej partii produktów (np. co 10-50 produktów)
   - Update po każdym błędzie (dla resume capability)
   - Update na końcu scrapowania

3. **Checkpoint Structure**
   ```json
   {
     "last_update": "2024-01-01T00:00:00Z",
     "products": {
       "scraped": ["url1", "url2", ...],
       "failed": ["url3", ...],
       "current_index": 100
     },
     "creators": {
       "scraped": ["@creator1", ...],
       "failed": ["@creator2", ...]
     },
     "metadata": {
       "start_time": "2024-01-01T00:00:00Z",
       "total_urls": 1000
     }
   }
   ```

### Resume Capability

1. **On Startup**
   - Sprawdź checkpoint file
   - Jeśli istnieje, zapytaj użytkownika czy resume
   - Skip już scrapowane URL

2. **On Error**
   - Zapisz checkpoint przed exit
   - Umożliwij resume po naprawie błędu
   - Loguj checkpoint location

## Data Validation

### Pre-save Validation

1. **Pydantic Models**
   ```python
   # Zawsze waliduj przed zapisem
   try:
       product = Product(**data)
   except ValidationError as e:
       logger.error("validation_failed", error=str(e), data=data)
       return None  # Nie zapisuj
   ```

2. **Required Fields**
   - Sprawdź czy wszystkie required fields są obecne
   - Sprawdź czy typy są poprawne
   - Sprawdź czy wartości są w dozwolonych zakresach

3. **Data Completeness**
   - Sprawdź czy dane są kompletne
   - Loguj missing fields (jako warning)
   - Nie zapisuj jeśli brak critical fields

### Post-save Validation

1. **File Integrity**
   - Sprawdź czy plik został zapisany poprawnie
   - Sprawdź czy można odczytać plik
   - Verify JSON validity

2. **Data Consistency**
   - Sprawdź czy creator istnieje dla produktu
   - Sprawdź czy product_id jest unikalny
   - Sprawdź czy referencje są poprawne

## Data Recovery

### Rollback Strategy

1. **Identify Issue**
   - Zidentyfikuj problematyczne dane
   - Sprawdź logi dla błędów
   - Zidentyfikuj zakres problemu

2. **Restore from Backup**
   - Znajdź ostatni poprawny backup
   - Przywróć dane z backupu
   - Verify integrity

3. **Re-scrape**
   - Re-scrape problematyczne dane
   - Verify poprawne dane
   - Update checkpoint

### Error Recovery

1. **Partial Failures**
   - Jeśli część danych się nie powiodła, kontynuuj z resztą
   - Zapisz checkpoint
   - Re-try failed items później

2. **Complete Failure**
   - Backup przed zmianami
   - Rollback do ostatniego backupu
   - Investigate root cause

## Data Storage

### File Organization

```
data/
├── products/
│   ├── templates/      # {product_id}.json
│   ├── components/    # {product_id}.json
│   ├── vectors/       # {product_id}.json
│   └── plugins/       # {product_id}.json
├── creators/          # {username}.json
├── categories/        # {category_name}.json (opcjonalnie)
├── exports/           # CSV exports
├── backups/           # Manual backups
└── checkpoint.json    # Checkpoint file
```

### Database Organization

```
PostgreSQL Tables:
├── products           # Najnowsze wersje produktów (UPSERT)
├── product_history    # Pełna historia zmian (INSERT only)
│   ├── id (SERIAL PRIMARY KEY)
│   ├── product_id (VARCHAR)
│   ├── scraped_at (TIMESTAMP) - kluczowy dla analizy trendów
│   ├── views_normalized, pages_normalized, users_normalized, etc.
│   └── Indexes: product_id, scraped_at, (product_id, scraped_at)
└── creators           # Dane twórców
```

### File Naming

1. **Products**
   - Format: `{product_id}.json`
   - product_id: slug z URL (np. `template-name`)

2. **Creators**
   - Format: `{username}.json`
   - username: bez `@` (np. `creator-name`)

3. **Backups**
   - Format: `backup-{timestamp}.tar.gz`
   - Timestamp: ISO 8601 (np. `backup-2024-01-01T00-00-00.tar.gz`)

## Data Integrity Checks

### Automated Checks

1. **Validation Script**
   ```python
   # scripts/validate_data.py
   def validate_all_data():
       # Check all products
       # Check all creators
       # Check referential integrity
       # Report issues
   ```

2. **Regular Validation**
   - Run po każdym scrapowaniu
   - Run przed backup
   - Run przed release

### Manual Checks

1. **Before Major Changes**
   - Validate data integrity
   - Create backup
   - Document changes

2. **After Changes**
   - Verify data integrity
   - Check for regressions
   - Update documentation

## Security

### Data Protection

1. **No Sensitive Data**
   - Nie przechowuj API keys w danych
   - Nie przechowuj passwords
   - Nie przechowuj PII

2. **Access Control**
   - `.gitignore` dla `data/` (opcjonalnie)
   - Backup encryption (jeśli potrzebne)
   - Secure storage dla backupów

### Backup Security

1. **GitHub Artifacts**
   - Automatyczne szyfrowanie
   - Access control przez GitHub
   - Retention policy

2. **External Backups**
   - Encrypt jeśli wrażliwe
   - Secure storage
   - Access logs

## Monitoring

### Data Quality Metrics

1. **Completeness**
   - % produktów z pełnymi danymi
   - Missing fields tracking
   - Data quality score

2. **Accuracy**
   - Validation errors rate
   - Parsing errors rate
   - Data consistency checks

3. **Timeliness**
   - Last update timestamp
   - Stale data detection
   - Update frequency

### Alerts

1. **Data Issues**
   - High validation error rate
   - Data integrity failures
   - Backup failures

2. **Storage Issues**
   - Disk space warnings
   - Backup failures
   - File system errors

## Checklist

### Przed Scrapowaniem

- [ ] Checkpoint file sprawdzony (jeśli resume)
- [ ] Backup wykonany (jeśli potrzeba)
- [ ] Storage space available
- [ ] Validation scripts ready

### Po Scrapowaniu

- [ ] Checkpoint zaktualizowany
- [ ] Wszystkie dane zwalidowane
- [ ] Produkty zapisane do `products` table
- [ ] Produkty zapisane do `product_history` table (automatycznie)
- [ ] Backup wykonany (w tym `product_history`!)
- [ ] Data integrity checked
- [ ] Metrics logged

### Przed Release

- [ ] Full data validation
- [ ] Backup created
- [ ] Documentation updated
- [ ] Data integrity verified

---

**Uwaga:** Te reguły są draftem i mogą być rozszerzone/zmodyfikowane w przyszłości.

