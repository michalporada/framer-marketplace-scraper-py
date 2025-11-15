# Rozwiązywanie problemów z połączeniem do Supabase z lokalnego środowiska

## Problem

Błąd podczas próby połączenia z Supabase z lokalnego środowiska:
```
could not translate host name "db.xxxxx.supabase.co" to address: nodename nor servname provided, or not known
```

## Przyczyna

Supabase domyślnie używa adresów **IPv6** dla bezpośrednich połączeń z bazą danych. Jeśli Twoje lokalne środowisko nie obsługuje IPv6 lub ma problemy z DNS dla IPv6, połączenie nie zadziała.

## Rozwiązanie: Użyj Session Mode (Supavisor)

Session Mode używa **IPv4** i działa z lokalnych środowisk, które nie obsługują IPv6.

### Krok 1: Pobierz Session Mode Connection String

1. **Przejdź do Supabase Dashboard:**
   - Zaloguj się na https://supabase.com
   - Wybierz swój projekt

2. **Pobierz Connection String:**
   - Przejdź do: **Settings** → **Database**
   - Znajdź sekcję: **Connection string**
   - Wybierz zakładkę: **Session mode** (NIE "URI")
   - Skopiuj connection string

3. **Format Session Mode connection string:**
   ```
   postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
   
   Przykład:
   ```
   postgresql://postgres.qjmdebkihybwxidmljaf:3odbfqhzSoEMqUCv@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
   ```

### Krok 2: Zaktualizuj .env

Zamień `DATABASE_URL` w pliku `.env`:

```bash
# Stary (bezpośrednie połączenie - IPv6, nie działa lokalnie):
# DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres

# Nowy (Session Mode - IPv4, działa lokalnie):
DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

**Ważne:**
- Port zmienia się z `5432` na `6543`
- Host zmienia się z `db.xxxxx.supabase.co` na `aws-0-[REGION].pooler.supabase.com`
- Username zmienia się z `postgres` na `postgres.[PROJECT_REF]`

### Krok 3: Test połączenia

```bash
python3 -c "
from src.storage.database import DatabaseStorage
from sqlalchemy import text

db = DatabaseStorage()
if db.is_available():
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text('SELECT 1 as test'))
            row = result.fetchone()
            print('✅ Database connection: SUCCESS')
            print('Test query result:', row[0])
    except Exception as e:
        print('❌ Database connection: FAILED')
        print('Error:', str(e))
else:
    print('❌ Database engine not available')
"
```

## Alternatywne rozwiązania

### Opcja 1: Zakup dodatku IPv4 w Supabase

1. W Supabase Dashboard: **Settings** → **Add-ons**
2. Kup dodatek **IPv4** (jeśli dostępny)
3. Użyj bezpośredniego connection string (URI)

### Opcja 2: Skonfiguruj IPv6 lokalnie

Jeśli masz kontrolę nad siecią:
- Skonfiguruj router do obsługi IPv6
- Skontaktuj się z dostawcą internetu w celu włączenia IPv6

## Różnice między trybami

| Tryb | Port | Host | IPv4/IPv6 | Użycie |
|------|------|------|-----------|--------|
| **Direct (URI)** | 5432 | `db.xxxxx.supabase.co` | IPv6 | Produkcja (serwery z IPv6) |
| **Session Mode** | 6543 | `aws-0-[REGION].pooler.supabase.com` | IPv4 | Lokalne środowisko, development |

## Uwagi

- **Session Mode** jest przeznaczony do developmentu i lokalnych środowisk
- Dla produkcji (Railway, Vercel) możesz użyć bezpośredniego połączenia (URI)
- Session Mode używa connection pooling, co jest lepsze dla wielu połączeń

## Sprawdzenie regionu

Aby znaleźć region w Session Mode connection string:
1. W Supabase Dashboard: **Settings** → **General**
2. Sprawdź **Region** (np. `eu-central-1`, `us-east-1`)
3. Użyj tego regionu w connection string: `aws-0-[REGION].pooler.supabase.com`




