# Następne Kroki - Implementacja Dashboardu

**Data:** 2025-01-12  
**Status:** Refaktoring zakończony - gotowe do implementacji logiki

---

## ✅ Co jest gotowe

### 1. Infrastruktura
- ✅ Konfiguracja Tailwind CSS + shadcn/ui
- ✅ Wszystkie komponenty shadcn z MCP serwera (Card, Table, Button, Badge, Skeleton, Avatar)
- ✅ Struktura dashboardu (6 bloków)
- ✅ Responsywny layout (grid: 1/2/3 kolumny)
- ✅ Time Period Selector (1d/7d/30d)
- ✅ API client functions (`lib/api.ts`)
- ✅ TypeScript types (`lib/types.ts`)

### 2. UI Components
- ✅ Card z CardHeader, CardTitle, CardAction, CardContent
- ✅ Table z pełną strukturą
- ✅ Button dla selektora okresu
- ✅ Badge dla zmian procentowych
- ✅ Skeleton dla loading states
- ✅ Avatar dla kreatorów

---

## 🎯 Następne Kroki - Priorytet

### **KROK 1: Implementacja logiki pobierania danych** 🔴 WYSOKI

#### 1.1. Top Creators by Total Views (Priorytet 1)

**⚠️ WAŻNE: Najpierw stworzyć dedykowany endpoint w API!**

**Nowy endpoint do stworzenia:**
```
GET /api/creators/top-by-template-views?limit=10&period_hours=24
```

**Korzyści:**
- ✅ Jeden query zamiast N+1 queries (1 + liczba kreatorów)
- ✅ Szybsze (agregacja po stronie bazy danych)
- ✅ Mniej obciążające dla API
- ✅ Łatwiejsze w użyciu z frontendu
- ✅ Możliwość obliczenia % change po stronie backendu

**Alternatywa (jeśli nie możemy stworzyć endpointu):**
```
GET /api/creators?limit=1000&sort=username
GET /api/creators/{username}/products?type=template
```

**Logika (jeśli użyjemy nowego endpointu):**
1. Wywołaj `GET /api/creators/top-by-template-views?limit=10&period_hours=24`
2. Otrzymaj już przetworzone dane z % change
3. Wyświetl w tabeli:
   - Rank (#)
   - Creator (avatar + name + templates count)
   - Total Views (sformatowane)
   - Percentage Change

**Kod do dodania w `TopCreatorsByViews` (z nowym endpointem):**
```typescript
const [loading, setLoading] = useState(true)
const [data, setData] = useState<any[]>([])
const [error, setError] = useState<string | undefined>()

useEffect(() => {
  async function fetchData() {
    setLoading(true)
    setError(undefined)
    
    try {
      const periodHours = periodToHours(period)
      const response = await fetch(
        `${API_BASE_URL}/api/creators/top-by-template-views?limit=10&period_hours=${periodHours}`
      )
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`)
      }
      
      const result = await response.json()
      const creators = result.data || []
      
      setData(creators.map((creator: any, index: number) => ({
        id: creator.username,
        rank: index + 1,
        name: creator.name || creator.username,
        avatar: creator.avatar_url,
        views: creator.total_views,
        templatesCount: creator.templates_count,
        change: creator.views_change_percent ? {
          value: Math.abs(creator.views_change_percent),
          isPositive: creator.views_change_percent >= 0
        } : undefined
      })))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }
  
  fetchData()
}, [period])
```

**Kod do dodania w API (`api/routes/creators.py`):**
```python
@router.get("/top-by-template-views")
async def get_top_creators_by_template_views(
    limit: int = Query(10, ge=1, le=100, description="Number of creators to return"),
    period_hours: int = Query(24, ge=1, le=168, description="Period in hours for % change"),
):
    """Get top creators by total views of their templates.
    
    Returns creators sorted by sum of views_normalized for all their templates,
    with percentage change calculated for the specified period.
    """
    # SQL query to aggregate template views per creator
    # Join products with creators, filter by type=template
    # Calculate total views and % change using product_history
    # ... (implementacja SQL query)
```

**Szacowany czas:** 
- Stworzenie endpointu w API: 1-2 godziny
- Implementacja w frontendzie: 30 minut
- **RAZEM: 1.5-2.5 godziny**

---

#### 1.2. Most Popular Templates (Priorytet 2)

**Endpoint:**
```
GET /api/products?type=template&sort=views_normalized&order=desc&limit=10
```

**Logika:**
1. Pobierz top 10 template'ów
2. Dla każdego template'a:
   - Pobierz dane o zmianach (jeśli dostępne)
   - Oblicz % change
3. Wyświetl w tabeli:
   - Rank (#)
   - Template name
   - Creator username
   - Views count
   - Price (Free/Paid badge)
   - Percentage Change

**Kod do dodania:**
```typescript
useEffect(() => {
  async function fetchData() {
    setLoading(true)
    try {
      const response = await getProducts({
        type: 'template',
        sort: 'views_normalized',
        order: 'desc',
        limit: 10
      })
      
      const templates = response.data || []
      
      // TODO: Dla każdego template'a pobierz changes i oblicz % change
      const templatesWithChanges = await Promise.all(
        templates.map(async (template: Product, index: number) => {
          // Pobierz changes jeśli endpoint dostępny
          // Oblicz % change
          
          return {
            id: template.product_id,
            rank: index + 1,
            name: template.name,
            creator: template.creator_username,
            views: template.views_normalized || 0,
            isFree: template.is_free,
            price: template.price,
            change: undefined // TODO
          }
        })
      )
      
      setData(templatesWithChanges)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }
  
  fetchData()
}, [period])
```

**Szacowany czas:** 1 godzina

---

#### 1.3. Most Popular Components (Priorytet 3)

**Endpoint:**
```
GET /api/products?type=component&sort=views_normalized&order=desc&limit=10
```

**Logika:** Podobna do Most Popular Templates

**Szacowany czas:** 30 minut (kopiowanie i modyfikacja)

---

#### 1.4. Most Popular Categories (Priorytet 4)

**Problem:** Brak bezpośredniego endpointu

**Rozwiązanie:**
1. Pobierz wszystkie produkty: `GET /api/products?limit=1000`
2. Agreguj po kategoriach:
   - Sumuj `views_normalized` dla każdej kategorii
   - Policz liczbę produktów w kategorii
3. Posortuj po total views
4. Weź top 10

**Kod do dodania:**
```typescript
useEffect(() => {
  async function fetchData() {
    setLoading(true)
    try {
      // Pobierz wszystkie produkty
      const response = await getProducts({ limit: 1000 })
      const products = response.data || []
      
      // Agreguj po kategoriach
      const categoryMap = new Map<string, { views: number; count: number }>()
      
      products.forEach((product: Product) => {
        const views = product.views_normalized || 0
        const categories = product.categories || []
        
        categories.forEach((category: string) => {
          const current = categoryMap.get(category) || { views: 0, count: 0 }
          categoryMap.set(category, {
            views: current.views + views,
            count: current.count + 1
          })
        })
      })
      
      // Konwertuj do array, sortuj i weź top 10
      const topCategories = Array.from(categoryMap.entries())
        .map(([name, stats]) => ({
          id: name,
          name,
          views: stats.views,
          productsCount: stats.count,
          change: undefined // TODO
        }))
        .sort((a, b) => b.views - a.views)
        .slice(0, 10)
      
      setData(topCategories)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }
  
  fetchData()
}, [period])
```

**Szacowany czas:** 1-2 godziny

---

#### 1.5. Most Popular Free Templates (Priorytet 5)

**Endpoint:**
```
GET /api/products?type=template&sort=views_normalized&order=desc&limit=1000
```

**Logika:**
1. Pobierz wszystkie template'y (lub dużo, np. 1000)
2. Filtruj po `is_free === true`
3. Sortuj po views
4. Weź top 10

**Szacowany czas:** 30 minut

---

#### 1.6. Creators with Most Templates (Priorytet 6)

**Endpoint:**
```
GET /api/creators?sort=total_products&order=desc&limit=100
```

**Logika:**
1. Pobierz kreatorów posortowanych po total_products
2. Filtruj po `stats.templates_count` (tylko template'y)
3. Weź top 10
4. Wyświetl:
   - Rank
   - Creator (avatar + name)
   - Templates count
   - Total products count
   - Percentage Change (zmiana liczby template'ów)

**Szacowany czas:** 1 godzina

---

### **KROK 2: Implementacja obliczania % Change** 🟡 ŚREDNI

#### 2.1. Helper function do obliczania % change

**Plik:** `frontend/src/lib/utils.ts` (rozszerzyć)

```typescript
export function calculatePercentageChange(
  current: number,
  previous: number | null | undefined
): { value: number; isPositive: boolean } | null {
  if (previous === null || previous === undefined || previous === 0) {
    return null // Brak danych historycznych
  }
  
  const change = ((current - previous) / previous) * 100
  return {
    value: Math.abs(change),
    isPositive: change >= 0
  }
}
```

#### 2.2. Integracja z API endpoints dla changes

**Dla każdego bloku:**
- Sprawdź czy endpoint `/api/products/{id}/changes` zwraca dane
- Jeśli tak, użyj do obliczenia % change
- Jeśli nie, pokaż "N/A" lub "-"

**Szacowany czas:** 2-3 godziny (dla wszystkich bloków)

---

### **KROK 3: Obsługa błędów i edge cases** 🟢 NISKI

#### 3.1. Error handling
- ✅ Już zaimplementowane (error state w każdym komponencie)
- Dodać retry logic (opcjonalnie)

#### 3.2. Edge cases
- Pusta lista danych → pokaż "No data available"
- Brak danych historycznych → pokaż "-" zamiast % change
- previousValue === 0 → pokaż "New" badge
- Timeout → pokaż error message

**Szacowany czas:** 1 godzina

---

### **KROK 4: Optymalizacja i performance** 🟢 NISKI

#### 4.1. Caching
- Rozważyć React Query lub SWR dla cache'owania danych
- Cache na poziomie komponentu (useMemo)

#### 4.2. Loading states
- ✅ Już zaimplementowane (Skeleton)
- Dodać progressive loading (opcjonalnie)

#### 4.3. Debouncing
- Jeśli będzie real-time updates, dodać debouncing

**Szacowany czas:** 2-3 godziny (opcjonalne)

---

### **KROK 5: Styling i UX improvements** 🟢 NISKI

#### 5.1. Responsywność
- ✅ Już zaimplementowane (grid responsive)
- Przetestować na różnych rozdzielczościach

#### 5.2. Animacje
- Dodać smooth transitions (opcjonalnie)
- Loading animations

#### 5.3. Accessibility
- Dodać ARIA labels
- Keyboard navigation
- Screen reader support

**Szacowany czas:** 2-3 godziny

---

## 📋 Checklist Implementacji

### Faza 1: Podstawowa funkcjonalność (Priorytet WYSOKI)
- [ ] **Top Creators by Total Views** - pełna implementacja
- [ ] **Most Popular Templates** - pełna implementacja
- [ ] **Most Popular Components** - pełna implementacja
- [ ] **Most Popular Categories** - pełna implementacja
- [ ] **Most Popular Free Templates** - pełna implementacja
- [ ] **Creators with Most Templates** - pełna implementacja

### Faza 2: % Change (Priorytet ŚREDNI)
- [ ] Helper function do obliczania % change
- [ ] Integracja z API endpoints dla changes
- [ ] Obsługa edge cases (brak danych, previousValue === 0)

### Faza 3: Polish (Priorytet NISKI)
- [ ] Error handling improvements
- [ ] Loading states improvements
- [ ] Styling refinements
- [ ] Accessibility improvements

---

## 🎯 Rekomendowana Kolejność

### Faza 0: Stworzenie endpointów w API (jeśli potrzebne)
1. **Najpierw:** Stwórz endpoint `/api/creators/top-by-template-views` w API
2. **Opcjonalnie:** Stwórz inne dedykowane endpointy dla pozostałych bloków

### Faza 1: Implementacja frontendu
1. **Najpierw:** Top Creators by Total Views (używając nowego endpointu)
2. **Potem:** Most Popular Templates (prosty endpoint)
3. **Potem:** Most Popular Components (podobny do Templates)
4. **Potem:** Most Popular Free Templates (filtrowanie po stronie frontendu)
5. **Potem:** Most Popular Categories (agregacja po stronie frontendu lub endpoint)
6. **Na końcu:** Creators with Most Templates (filtrowanie lub endpoint)

---

## 📝 Uwagi Techniczne

### API Endpoints - Status
- ✅ `/api/creators` - dostępny
- ✅ `/api/creators/{username}/products` - dostępny
- ✅ `/api/products` - dostępny
- ✅ `/api/creators/{username}/products-growth` - dostępny (zwraca growth dla produktów kreatora)
- ❓ `/api/products/{id}/changes` - sprawdzić czy dostępny
- ❌ `/api/creators/top-by-template-views` - **DO STWORZENIA** (rekomendowane)
- ❌ `/api/products/top-templates` - opcjonalnie (dla Most Popular Templates)
- ❌ `/api/categories/top-by-views` - opcjonalnie (dla Most Popular Categories)

### Performance Considerations
- Top Creators wymaga wielu API calls (1 + N gdzie N = liczba kreatorów)
- Rozważyć debouncing/throttling
- Rozważyć pagination dla kreatorów

### Error Handling
- Każdy komponent ma już error state
- Dodać retry logic (opcjonalnie)
- Logować błędy do console (dla development)

---

## 🚀 Szacowany Czas Całkowity

### Opcja A: Z dedykowanymi endpointami (REKOMENDOWANE)
- **Faza 0 (Stworzenie endpointów w API):** 2-4 godziny
- **Faza 1 (Podstawowa funkcjonalność):** 3-4 godziny (szybsze dzięki endpointom)
- **Faza 2 (% Change):** 0-1 godzina (już w endpointach)
- **Faza 3 (Polish):** 3-4 godziny
- **RAZEM:** ~8-13 godzin pracy

### Opcja B: Bez dedykowanych endpointów (alternatywa)
- **Faza 1 (Podstawowa funkcjonalność):** 6-8 godzin (wolniejsze, N+1 queries)
- **Faza 2 (% Change):** 2-3 godziny
- **Faza 3 (Polish):** 3-4 godziny
- **RAZEM:** ~11-15 godzin pracy

**Rekomendacja:** Stwórz dedykowane endpointy - oszczędność czasu i lepsza wydajność!

---

**Następny krok:** Rozpocząć implementację Top Creators by Total Views

