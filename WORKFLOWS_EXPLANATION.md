# Wyjaśnienie GitHub Actions Workflows

## 🔍 CI Workflow (Continuous Integration)

### Kiedy się uruchamia:
- ✅ **Automatycznie** przy każdym `push` do brancha `main` lub `develop`
- ✅ **Automatycznie** przy każdym `pull request` do brancha `main` lub `develop`
- 🔘 **NIE** uruchamia się automatycznie według harmonogramu

### Co robi:
1. **Testy jednostkowe** (`pytest`)
   - Uruchamia wszystkie 36 testów
   - Sprawdza coverage (pokrycie kodem)
   - Uploaduje coverage do Codecov

2. **Linting** (`ruff check`)
   - Sprawdza czy kod jest zgodny ze standardami
   - Wykrywa błędy, nieużywane importy, problemy stylistyczne

3. **Formatowanie** (`ruff format --check`)
   - Sprawdza czy kod jest poprawnie sformatowany
   - Nie formatuje, tylko sprawdza

4. **Type checking** (`mypy`)
   - Sprawdza typy w kodzie
   - Wykrywa potencjalne błędy typów

### Cel:
- ✅ **Weryfikacja jakości kodu** przed merge
- ✅ **Zapobieganie bugom** - testy wykrywają problemy wcześnie
- ✅ **Zgodność ze standardami** - kod musi być czysty i czytelny
- ✅ **Spójność** - wszyscy używają tego samego stylu kodu

### Przykład:
```bash
# Robisz zmiany lokalnie
git add .
git commit -m "Add new feature"
git push

# → CI workflow automatycznie się uruchamia
# → Sprawdza czy wszystko działa
# → Jeśli testy/linting fail → możesz naprawić przed merge
```

---

## 🤖 Daily Scrape Workflow (Automatyczne Scrapowanie)

### Kiedy się uruchamia:
- ⏰ **Automatycznie codziennie o 2:00 UTC** (3:00 CET / 4:00 CEST)
- 🔘 **Ręcznie** przez "Run workflow" w GitHub Actions
- ❌ **NIE** uruchamia się przy push/PR

### Co robi:
1. **Uruchamia scraper**
   - Pobiera listę produktów z sitemap
   - Scrapuje produkty z Framer Marketplace
   - Zapisuje dane do plików JSON

2. **Zapisuje artifacts**
   - `scraped-data` - wszystkie zscrapowane dane (JSON, checkpoint)
   - `scraper-logs` - logi z scrapowania
   - Artifacts są dostępne przez **7 dni**

### Cel:
- 📊 **Zbieranie danych** - automatyczne aktualizowanie bazy danych
- 🔄 **Aktualizacja** - codzienne pobieranie nowych produktów
- 📁 **Backup** - dane są zapisywane jako artifacts
- ⏱️ **Automatyzacja** - nie musisz ręcznie uruchamiać scrapera

### Przykład:
```
Codziennie o 2:00 UTC:
→ Workflow się uruchamia automatycznie
→ Scraper scrapuje produkty
→ Dane są zapisywane jako artifacts
→ Możesz pobrać artifacts z GitHub Actions
```

---

## 📊 Porównanie

| Cecha | CI Workflow | Daily Scrape Workflow |
|-------|-------------|----------------------|
| **Trigger** | Push/PR | Schedule (codziennie) + ręczne |
| **Częstotliwość** | Przy każdej zmianie kodu | Raz dziennie |
| **Czas wykonania** | ~1-2 minuty | ~kilka minut do godzin (zależnie od liczby produktów) |
| **Co robi** | Testuje i sprawdza kod | Scrapuje dane z Framer |
| **Wymagane zależności** | requirements.txt + requirements-dev.txt | requirements.txt |
| **Artifacts** | Brak (tylko coverage) | scraped-data, scraper-logs |
| **Cel** | Jakość kodu | Zbieranie danych |

---

## 🎯 Kiedy używać którego?

### Użyj CI Workflow gdy:
- ✅ Chcesz sprawdzić czy kod działa przed merge
- ✅ Chcesz zweryfikować jakość kodu
- ✅ Chcesz upewnić się że testy przechodzą
- ✅ Chcesz sprawdzić linting/formatowanie

### Użyj Daily Scrape Workflow gdy:
- ✅ Chcesz scrapować dane automatycznie
- ✅ Chcesz zaktualizować bazę danych produktów
- ✅ Chcesz pobrać najnowsze dane z Framer Marketplace
- ✅ Chcesz uruchomić scraper ręcznie (bez czekania do 2:00 UTC)

---

## 🔧 Konfiguracja

### CI Workflow:
- **Brak konfiguracji** - działa automatycznie przy push/PR
- **Wymaga**: requirements-dev.txt (dla testów, lintingu)

### Daily Scrape Workflow:
- **Secrets** (opcjonalne):
  - `DATABASE_URL` - jeśli używasz bazy danych
  - `FRAMER_BASE_URL` - domyślnie `https://www.framer.com`
  - `RATE_LIMIT` - domyślnie `1.0`
  - `MAX_RETRIES` - domyślnie `3`
  - `LOG_LEVEL` - domyślnie `INFO`
  - `CHECKPOINT_ENABLED` - domyślnie `true`

---

## 📝 Podsumowanie

**CI = Kontrola jakości kodu** (testy, linting, type checking)  
**Daily Scrape = Zbieranie danych** (scrapowanie produktów)

Oba workflow są ważne, ale służą do różnych celów:
- **CI** → zapewnia że kod jest dobry
- **Daily Scrape** → zapewnia że dane są aktualne

