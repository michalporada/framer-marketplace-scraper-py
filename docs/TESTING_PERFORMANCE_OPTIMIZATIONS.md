# Testowanie Optymalizacji Wydajności Dashboardu

**Data:** 2025-01-12  
**Status:** Gotowe do testowania

---

## 🧪 Plan Testowania

### Cel
Sprawdzić czy optymalizacje działają i zmierzyć rzeczywisty zysk wydajności.

---

## 📋 Krok 1: Uruchomienie Lokalne

### 1.1. Uruchom API Backend

```bash
cd "/Users/michalporada/Desktop/Scraper V2 "
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Sprawdź:**
- API dostępne na: `http://localhost:8000`
- Dokumentacja: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 1.2. Uruchom Frontend

W **nowym terminalu**:

```bash
cd "/Users/michalporada/Desktop/Scraper V2 /frontend"
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

**Sprawdź:**
- Frontend dostępny na: `http://localhost:3000`
- Dashboard: `http://localhost:3000/dashboard`

---

## 📊 Krok 2: Testowanie Wydajności

### 2.1. Otwórz DevTools

1. Otwórz `http://localhost:3000/dashboard` w przeglądarce
2. Otwórz **DevTools** (F12 lub Cmd+Option+I)
3. Przejdź do zakładki **Network**
4. **Ważne:** Odznacz "Disable cache" (żeby zobaczyć prawdziwą wydajność)
5. Kliknij **Clear** (wyczyść poprzednie requesty)

### 2.2. Odśwież Stronę

1. Kliknij **Refresh** (F5 lub Cmd+R)
2. **Obserwuj** Network tab w czasie rzeczywistym

### 2.3. Sprawdź Metryki

**W Network tab sprawdź:**

1. **Preflight Requests (OPTIONS):**
   - Powinny być **< 1 sekunda** (zamiast 15.55s)
   - Po pierwszym request powinny być jeszcze szybsze (cache)

2. **Fetch Requests (API calls):**
   - Powinny **startować równolegle** (wszystkie 6 jednocześnie)
   - W waterfall chart powinny być na tej samej linii czasowej
   - Każdy request: ~200-500ms

3. **Całkowity czas (Finish):**
   - Powinien być **< 5 sekund** (zamiast ~47s)
   - Sprawdź w dolnej belce Network tab

4. **Waterfall Chart:**
   - Wszystkie 6 fetch requests powinny startować **równolegle**
   - Nie powinny być sekwencyjne (jeden po drugim)

---

## ✅ Checklist Testowania

### Podstawowe Funkcjonalności
- [ ] Dashboard się ładuje bez błędów
- [ ] Wszystkie 6 bloków pokazują dane
- [ ] Loading skeletons działają
- [ ] Error handling działa (jeśli API nie odpowiada)
- [ ] Time period selector działa (1d)

### Wydajność
- [ ] Preflight requests < 1s
- [ ] Wszystkie 6 fetch requests startują równolegle
- [ ] Całkowity czas ładowania < 5s
- [ ] Brak timeoutów (10s timeout działa)

### Network Tab - Szczegóły
- [ ] Wszystkie 6 endpointów są wywoływane:
  - `/api/creators/top-by-template-views`
  - `/api/products/top-templates`
  - `/api/products/categories/all-by-count`
  - `/api/products/categories/top-by-views`
  - `/api/products/top-free-templates`
  - `/api/creators/top-by-template-count`
- [ ] Status: 200 OK dla wszystkich
- [ ] Response times: każdy < 1s

---

## 📸 Co Sprawdzić w Network Tab

### Przed Optymalizacją (dla porównania):
- Preflight: 15.55s × 2
- Fetch requests: sekwencyjne (jeden po drugim)
- Finish: ~47.57s

### Po Optymalizacji (oczekiwane):
- Preflight: < 1s (po pierwszym może być cache)
- Fetch requests: **równoległe** (wszystkie 6 jednocześnie)
- Finish: < 5s

### Waterfall Chart - Jak Powinien Wyglądać:

```
PRZED (❌):
[Preflight 1] ████████████████████ (15.55s)
              [Preflight 2] ████████████████████ (15.55s)
                            [Fetch 1] ████ (2s)
                                      [Fetch 2] ████ (2s)
                                                [Fetch 3] ████ (2s)
                                                          ...

PO (✅):
[Preflight 1] █ (< 1s)
[Preflight 2] █ (< 1s)
[Fetch 1]     ████ (2s)  ← wszystkie startują równolegle
[Fetch 2]     ████ (2s)  ←
[Fetch 3]     ████ (2s)  ←
[Fetch 4]     ████ (2s)  ←
[Fetch 5]     ████ (2s)  ←
[Fetch 6]     ████ (2s)  ←
```

---

## 🐛 Troubleshooting

### Problem: Preflight requests nadal wolne (> 1s)

**Możliwe przyczyny:**
- Cold start na Railway (serverless)
- Pierwszy request zawsze wolniejszy
- Problem z CORS configuration

**Rozwiązanie:**
- Sprawdź czy `max_age=3600` jest w `api/main.py`
- Sprawdź logi API czy są błędy
- Drugi request powinien być szybszy (cache)

### Problem: Fetch requests są sekwencyjne

**Możliwe przyczyny:**
- Błąd w kodzie - sprawdź czy `Promise.allSettled()` jest użyte
- Browser limit - niektóre przeglądarki limitują równoległe requesty
- API rate limiting

**Rozwiązanie:**
- Sprawdź kod w `frontend/src/app/dashboard/page.tsx` linia 89
- Sprawdź czy wszystkie 6 zapytań jest w `Promise.allSettled()`
- Sprawdź logi w konsoli przeglądarki

### Problem: Timeout errors

**Możliwe przyczyny:**
- API nie odpowiada
- Baza danych wolna
- Network problem

**Rozwiązanie:**
- Sprawdź czy API działa: `curl http://localhost:8000/health`
- Sprawdź logi API
- Sprawdź czy baza danych jest dostępna

### Problem: Błędy w konsoli

**Sprawdź:**
- Console tab w DevTools
- Czy są błędy JavaScript
- Czy są błędy CORS
- Czy są błędy API

---

## 📈 Metryki do Zapisania

Zapisz następujące metryki **przed** i **po** optymalizacji:

### Network Tab:
- **Finish time:** ___ sekund
- **Preflight request 1:** ___ sekund
- **Preflight request 2:** ___ sekund
- **Fetch request 1:** ___ sekund
- **Fetch request 2:** ___ sekund
- **Fetch request 3:** ___ sekund
- **Fetch request 4:** ___ sekund
- **Fetch request 5:** ___ sekund
- **Fetch request 6:** ___ sekund

### Waterfall Chart:
- Czy fetch requests są równoległe? (TAK/NIE)
- Czy preflight requests są szybkie? (TAK/NIE)

### Console:
- Czy są błędy? (TAK/NIE)
- Jakie błędy? ___

---

## 🎯 Oczekiwane Rezultaty

### Przed:
- Finish: ~47.57s
- Preflight: 15.55s × 2
- Fetch: Sekwencyjne (~15s łącznie)
- **Łącznie:** ~47s

### Po:
- Finish: < 5s ✅
- Preflight: < 1s ✅
- Fetch: Równoległe (~2-3s łącznie) ✅
- **Łącznie:** ~3-5s ✅

**Oczekiwany zysk:** **~10x szybsze ładowanie** 🚀

---

## 📝 Raport z Testów

Po testach wypełnij:

**Data testów:** ___  
**Przeglądarka:** ___  
**Środowisko:** Lokalne / Produkcja

**Metryki:**
- Finish time: ___ sekund
- Preflight requests: ___ sekund
- Fetch requests: Równoległe? (TAK/NIE)
- Błędy: ___

**Wnioski:**
- Czy optymalizacje działają? ___
- Jaki jest rzeczywisty zysk? ___
- Czy są problemy? ___

---

## 🔄 Następne Kroki

Po pozytywnych testach:
1. ✅ Merge PR do main
2. ✅ Deploy na produkcję
3. ✅ Monitoring wydajności
4. ⏭️ Opcjonalnie: Eliminacja N+1 queries

---

**Gotowe do testowania!** 🚀

