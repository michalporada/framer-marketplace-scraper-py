# Dashboard Performance Optimization

**Data:** 2025-01-12  
**Status:** ✅ Zaimplementowane  
**Cel:** Optymalizacja czasu ładowania dashboardu z ~47s do <5s

---

## 📊 Problem

### Przed optymalizacją:
- **Całkowity czas ładowania:** ~47.57 sekund
- **Preflight requests:** 15.55 sekund każdy (2x)
- **API requests:** Sekwencyjne (6 zapytań jeden po drugim)
- **Timeout:** 30 sekund
- **N+1 queries:** Pętle z zapytaniami do bazy danych

### Analiza z DevTools:
- 75 requests
- 11.3 MB transferred
- Preflight requests blokowały wszystkie kolejne zapytania
- Fetch requests były sekwencyjne zamiast równoległych

---

## ✅ Zaimplementowane Optymalizacje

### 1. Frontend - Równoległe Ładowanie Danych

**Problem:** 6 komponentów ładowało dane sekwencyjnie (jeden po drugim)

**Rozwiązanie:** 
- Główny komponent `DashboardPage` ładuje wszystkie dane równolegle używając `Promise.allSettled()`
- Wszystkie 6 zapytań API wykonuje się jednocześnie
- Komponenty otrzymują dane jako props zamiast ładować je wewnętrznie

**Zmiany:**
- `frontend/src/app/dashboard/page.tsx`:
  - Dodano `useEffect` w głównym komponencie z `Promise.allSettled()`
  - Wszystkie 6 komponentów przyjmują `data`, `loading`, `error` jako props
  - Usunięto `useEffect` z fetchData z każdego komponentu

**Oczekiwany zysk:** 5-6x szybsze ładowanie (z ~15s do ~3s)

---

### 2. API - Optymalizacja CORS

**Problem:** Preflight requests trwały 15.55 sekund

**Rozwiązanie:**
- Dodano `max_age=3600` do CORS middleware (cache preflight na 1 godzinę)
- Explicit methods zamiast `["*"]`
- Dodano `expose_headers`

**Zmiany:**
- `api/main.py`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=cors_origins,
      allow_credentials=True,
      allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
      allow_headers=["*"],
      expose_headers=["*"],
      max_age=3600,  # Cache preflight for 1 hour
  )
  ```

**Oczekiwany zysk:** Preflight requests < 1s zamiast 15.55s (po pierwszym request)

---

### 3. Frontend - Zmniejszenie Timeout

**Problem:** Timeout 30 sekund był zbyt długi

**Rozwiązanie:**
- Zmniejszono timeout z 30s do 10s
- Dodano cache control do fetch requests

**Zmiany:**
- `frontend/src/lib/api.ts`:
  ```typescript
  const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 seconds
  const response = await fetch(url, {
    signal: controller.signal,
    headers: {
      'Content-Type': 'application/json',
    },
    cache: 'default',
  })
  ```

**Oczekiwany zysk:** Szybsze wykrywanie problemów, mniej oczekiwania na timeout

---

## 🔄 Zmienione Komponenty

Wszystkie 6 komponentów zostały zmienione, żeby przyjmować dane jako props:

1. ✅ `TopCreatorsByViews` - zmieniony
2. ✅ `MostPopularTemplates` - zmieniony
3. ✅ `SmallestCategories` - zmieniony
4. ✅ `MostPopularCategories` - zmieniony
5. ✅ `MostPopularFreeTemplates` - zmieniony
6. ✅ `CreatorsMostTemplates` - zmieniony

**Wzorzec zmiany:**
```typescript
// ❌ PRZED
function Component({ period, onPeriodChange }) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState([])
  const [error, setError] = useState()
  
  useEffect(() => {
    async function fetchData() {
      // fetch data...
    }
    fetchData()
  }, [period])
  
  // render...
}

// ✅ PO
function Component({ period, onPeriodChange, data, loading, error }) {
  const mappedData = data?.data || []
  // render...
}
```

---

## 📈 Oczekiwane Rezultaty

### Przed:
- **Czas ładowania:** ~47.57s
- **Preflight:** 15.55s × 2
- **API requests:** Sekwencyjne (~15s)
- **Timeout:** 30s

### Po:
- **Czas ładowania:** ~3-5s (szacunek)
- **Preflight:** < 1s (po pierwszym request)
- **API requests:** Równoległe (~2-3s)
- **Timeout:** 10s

**Szacowany zysk:** **~10x szybsze ładowanie**

---

## 🧪 Testowanie

### Przed wdrożeniem:
1. Otwórz DevTools → Network
2. Odśwież dashboard
3. Zapisz czasy odpowiedzi dla każdego endpointu
4. Sprawdź czy zapytania są sekwencyjne czy równoległe

### Po wdrożeniu:
1. Sprawdź czy wszystkie 6 zapytań ładuje się równolegle (waterfall chart)
2. Sprawdź czy preflight requests są szybsze (< 1s)
3. Porównaj całkowity czas ładowania
4. Sprawdź czy nie ma błędów w konsoli

### Metryki do sprawdzenia:
- **Network tab:**
  - Finish time (powinno być < 5s)
  - Preflight request time (powinno być < 1s)
  - Fetch requests powinny startować równolegle
- **Console:**
  - Brak błędów
  - Logi "Fetching:" dla każdego endpointu

---

## 🔜 Następne Kroki (Opcjonalne)

### Priorytet 2: Eliminacja N+1 Queries

**Problem:** Pętle z zapytaniami do bazy danych w API

**Rozwiązanie:**
- Zamienić pętle na zapytania z `IN` lub `ANY`
- Przykład w `api/routes/creators.py` i `api/routes/products.py`

**Oczekiwany zysk:** 5-10x szybsze zapytania API

### Priorytet 3: Indeksy Bazy Danych

**Problem:** Zapytania z `DISTINCT ON` mogą być wolne bez indeksów

**Rozwiązanie:**
- Dodać indeksy na `product_history`:
  ```sql
  CREATE INDEX idx_product_history_type_scraped 
  ON product_history(type, scraped_at DESC);
  
  CREATE INDEX idx_product_history_product_scraped 
  ON product_history(product_id, scraped_at DESC);
  ```

**Oczekiwany zysk:** 2-3x szybsze zapytania SQL

### Priorytet 4: Optymalizacja Obrazów

**Problem:** Duże obrazy (1.2 MB) spowalniają ładowanie

**Rozwiązanie:**
- Użyć Next.js Image component
- Lazy loading obrazów
- Optymalizacja rozmiaru obrazów

**Oczekiwany zysk:** Szybsze ładowanie obrazów

---

## 📝 Pliki Zmienione

### Frontend:
- ✅ `frontend/src/app/dashboard/page.tsx` - główny komponent + wszystkie 6 komponentów
- ✅ `frontend/src/lib/api.ts` - timeout i cache control

### Backend:
- ✅ `api/main.py` - CORS optimization

---

## 🐛 Znane Problemy

1. **Cold start na Railway:** Pierwsze zapytanie może być wolne (serverless)
2. **Duplikaty obrazów:** Te same obrazy są ładowane wielokrotnie (do optymalizacji)
3. **N+1 queries:** Nadal występują w niektórych endpointach (do naprawy)

---

## 📚 Referencje

- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [Promise.allSettled()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled)
- [Next.js Performance](https://nextjs.org/docs/app/building-your-application/optimizing)

---

## ✅ Checklist Wdrożenia

- [x] Frontend - równoległe ładowanie z Promise.allSettled()
- [x] API - optymalizacja CORS (max_age)
- [x] Frontend - zmniejszenie timeout (30s → 10s)
- [x] Wszystkie 6 komponentów zmienione na props
- [ ] Testowanie na produkcji
- [ ] Monitoring wydajności
- [ ] Eliminacja N+1 queries (opcjonalnie)
- [ ] Dodanie indeksów bazy danych (opcjonalnie)
- [ ] Optymalizacja obrazów (opcjonalnie)

---

**Następny krok:** Testowanie na produkcji i monitoring wydajności

