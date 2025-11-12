# Plan Implementacji Dashboardu - Framer Marketplace Analytics

## 📋 Przegląd

Dashboard składa się z **6 bloków**, każdy zawierający **tabelę z 10 elementami**. Każdy blok ma możliwość zmiany widoku na okresy czasowe: **1d, 7d, 30d** (7d i 30d disabled na razie).

Każdy element tabeli pokazuje **wzrost procentowy** względem wybranego okresu czasu.

---

## 🎯 Wymagane Bloki Dashboardu

### 1. **Top Creators by Total Views of Their Templates**
- **Opis**: Top 10 kreatorów posortowanych po sumie views wszystkich ich template'ów
- **Dane**: 
  - Creator name/username
  - Total views (suma views wszystkich template'ów)
  - Percentage change (wzrost % względem okresu)
  - Avatar (opcjonalnie)

### 2. **Most Popular Templates**
- **Opis**: Top 10 template'ów po views
- **Dane**:
  - Template name
  - Creator username
  - Views count
  - Percentage change
  - Price (free/paid)

### 3. **Most Popular Components**
- **Opis**: Top 10 komponentów po views/installs
- **Dane**:
  - Component name
  - Creator username
  - Views/Installs count
  - Percentage change
  - Price (free/paid)

### 4. **Most Popular Categories**
- **Opis**: Top 10 kategorii po total views
- **Dane**:
  - Category name
  - Total views (suma views wszystkich produktów w kategorii)
  - Products count
  - Percentage change

### 5. **Most Popular Free Templates**
- **Opis**: Top 10 darmowych template'ów po views
- **Dane**:
  - Template name
  - Creator username
  - Views count
  - Percentage change
  - Status: Free

### 6. **Creators with the Most Amount of Templates**
- **Opis**: Top 10 kreatorów po liczbie template'ów
- **Dane**:
  - Creator name/username
  - Templates count
  - Percentage change (zmiana liczby template'ów)
  - Total products count

---

## 🏗️ Architektura Techniczna

### Stack Techniczny
- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn/ui **TYLKO** (bez innych bibliotek UI)
- **Type Safety**: TypeScript
- **Data Fetching**: React Query (opcjonalnie) lub fetch API
- **State Management**: React useState/useContext (lokalne state)

### Struktura Plików

```
frontend/src/
├── app/
│   ├── dashboard/
│   │   └── page.tsx              # Główna strona dashboardu
│   ├── layout.tsx                 # Root layout
│   └── globals.css                # Globalne style
├── components/
│   ├── ui/                        # Shadcn components
│   │   ├── table.tsx              # Tabela (shadcn)
│   │   ├── button.tsx              # Przycisk (shadcn)
│   │   ├── card.tsx                # Karta (shadcn)
│   │   ├── badge.tsx               # Badge (shadcn)
│   │   └── skeleton.tsx            # Loading skeleton (shadcn)
│   ├── dashboard/
│   │   ├── DashboardBlock.tsx      # Wrapper dla każdego bloku
│   │   ├── TimePeriodSelector.tsx # Selektor okresu (1d/7d/30d)
│   │   ├── PercentageChange.tsx   # Komponent pokazujący % change
│   │   └── blocks/
│   │       ├── TopCreatorsByViews.tsx
│   │       ├── MostPopularTemplates.tsx
│   │       ├── MostPopularComponents.tsx
│   │       ├── MostPopularCategories.tsx
│   │       ├── MostPopularFreeTemplates.tsx
│   │       └── CreatorsMostTemplates.tsx
│   └── layout/
│       └── Header.tsx              # Header z nawigacją (opcjonalnie)
├── lib/
│   ├── api.ts                      # API client functions
│   ├── utils.ts                    # Helper functions
│   └── types.ts                    # TypeScript types/interfaces
└── hooks/
    └── useDashboardData.ts         # Custom hook dla danych dashboardu
```

---

## 📊 API Endpoints - Mapowanie

### 1. Top Creators by Total Views of Templates
**Problem**: Brak bezpośredniego endpointu.

**Rozwiązanie**: 
- Pobierz wszystkich kreatorów: `GET /api/creators?limit=1000&sort=username`
- Dla każdego kreatora pobierz produkty typu template: `GET /api/creators/{username}/products?type=template`
- Oblicz sumę `views_normalized` dla wszystkich template'ów
- Posortuj i weź top 10
- Dla obliczenia % change: użyj `/api/creators/{username}/products-growth?product_type=template&period_hours=24`

**Alternatywa (lepsza)**: Stwórz nowy endpoint w API:
```
GET /api/creators/top-by-template-views?limit=10&period_hours=24
```

### 2. Most Popular Templates
**Endpoint**: `GET /api/products?type=template&sort=views_normalized&order=desc&limit=10`

**% Change**: 
- Użyj `/api/products/{product_id}/changes` dla każdego produktu
- Lub stwórz endpoint agregujący: `GET /api/products/top-templates?limit=10&period_hours=24`

### 3. Most Popular Components
**Endpoint**: `GET /api/products?type=component&sort=views_normalized&order=desc&limit=10`

**% Change**: Podobnie jak templates

### 4. Most Popular Categories
**Problem**: Brak endpointu zwracającego listę top kategorii.

**Rozwiązanie**: 
- Pobierz wszystkie produkty: `GET /api/products?limit=1000`
- Agreguj po kategoriach i sumuj views
- Dla % change: użyj `/api/products/categories/comparison?product_type=template`

**Alternatywa**: Stwórz endpoint:
```
GET /api/categories/top-by-views?limit=10&product_type=template&period_hours=24
```

### 5. Most Popular Free Templates
**Endpoint**: `GET /api/products?type=template&sort=views_normalized&order=desc&limit=1000`
**Filtrowanie**: Po stronie frontendu - filtruj `is_free === true`, weź top 10

**% Change**: Podobnie jak templates

**Uwaga**: Jeśli API nie wspiera filtrowania po `is_free`, trzeba będzie pobrać wszystkie i filtrować po stronie frontendu.

### 6. Creators with Most Templates
**Endpoint**: `GET /api/creators?sort=total_products&order=desc&limit=10`

**Filtrowanie**: Po stronie frontendu - sprawdź `stats.templates_count` dla każdego kreatora

**% Change**: 
- Porównaj `stats.templates_count` między scrapami
- Użyj `/api/creators/{username}` i porównaj z historią (jeśli dostępna)

---

## 🎨 Design & UI Components

### Shadcn Components do Zainstalowania

1. **Table** (`@/components/ui/table`)
   - Dla wyświetlania danych w tabelach
   - Responsive, sortable (opcjonalnie)

2. **Card** (`@/components/ui/card`)
   - Wrapper dla każdego bloku dashboardu
   - Card header z tytułem
   - Card content z tabelą

3. **Button** (`@/components/ui/button`)
   - Dla selektora okresu czasu
   - Variants: outline, ghost

4. **Badge** (`@/components/ui/badge`)
   - Dla statusów (Free, Paid)
   - Dla pokazania wzrostu/spadku

5. **Skeleton** (`@/components/ui/skeleton`)
   - Loading states podczas fetchowania danych

### Layout Dashboardu

```
┌─────────────────────────────────────────────────────────┐
│                    Dashboard Header                      │
│              (Title + Time Period Selector)            │
└─────────────────────────────────────────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐
│  Block 1             │  │  Block 2             │
│  Top Creators        │  │  Popular Templates   │
│  [1d] [7d] [30d]    │  │  [1d] [7d] [30d]    │
│  ┌────────────────┐ │  │  ┌────────────────┐ │
│  │ Table (10 rows)│ │  │  │ Table (10 rows)│ │
│  └────────────────┘ │  │  └────────────────┘ │
└──────────────────────┘  └──────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐
│  Block 3             │  │  Block 4             │
│  Popular Components  │  │  Popular Categories  │
│  [1d] [7d] [30d]    │  │  [1d] [7d] [30d]    │
│  ┌────────────────┐ │  │  ┌────────────────┐ │
│  │ Table (10 rows)│ │  │  │ Table (10 rows)│ │
│  └────────────────┘ │  │  └────────────────┘ │
└──────────────────────┘  └──────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐
│  Block 5             │  │  Block 6             │
│  Free Templates      │  │  Creators Most Temp. │
│  [1d] [7d] [30d]    │  │  [1d] [7d] [30d]    │
│  ┌────────────────┐ │  │  ┌────────────────┐ │
│  │ Table (10 rows)│ │  │  │ Table (10 rows)│ │
│  └────────────────┘ │  │  └────────────────┘ │
└──────────────────────┘  └──────────────────────┘
```

### Responsive Design
- **Desktop**: 3 kolumny (grid-cols-3)
- **Tablet**: 2 kolumny (grid-cols-2)
- **Mobile**: 1 kolumna (stack vertical)

---

## 🔄 Logika Obliczania % Change

### Wzór
```typescript
percentageChange = ((currentValue - previousValue) / previousValue) * 100
```

### Obsługa Edge Cases
- **previousValue === 0**: Jeśli poprzednia wartość to 0, pokaż "New" lub "∞"
- **previousValue === null**: Jeśli brak danych historycznych, pokaż "N/A"
- **Negative change**: Pokazuj z minusem i czerwonym kolorem
- **Positive change**: Pokazuj z plusem i zielonym kolorem

### Formatowanie
- **Dodatnie**: `+5.2%` (zielony)
- **Ujemne**: `-3.1%` (czerwony)
- **Zero**: `0%` (szary)
- **Brak danych**: `N/A` (szary)

---

## 📝 Implementacja Krok po Kroku

### Krok 1: Setup Shadcn/ui
```bash
cd frontend
npx shadcn-ui@latest init
npx shadcn-ui@latest add table
npx shadcn-ui@latest add card
npx shadcn-ui@latest add button
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add skeleton
```

### Krok 2: Instalacja Zależności
```bash
npm install @tanstack/react-query  # Opcjonalnie dla data fetching
npm install date-fns               # Dla formatowania dat
```

### Krok 3: Konfiguracja API Client
Stwórz `frontend/src/lib/api.ts`:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchProducts(params: {
  type?: string;
  sort?: string;
  order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}) {
  // Implementation
}

export async function fetchCreators(params: {
  sort?: string;
  order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}) {
  // Implementation
}

// ... inne funkcje API
```

### Krok 4: TypeScript Types
Stwórz `frontend/src/lib/types.ts`:
```typescript
export type TimePeriod = '1d' | '7d' | '30d';

export interface DashboardItem {
  id: string;
  name: string;
  value: number;
  percentageChange: number | null;
  // ... inne pola w zależności od bloku
}

export interface DashboardBlockData {
  title: string;
  items: DashboardItem[];
  loading: boolean;
  error: string | null;
}
```

### Krok 5: Komponenty

#### TimePeriodSelector.tsx
```typescript
interface TimePeriodSelectorProps {
  value: TimePeriod;
  onChange: (period: TimePeriod) => void;
  disabled?: TimePeriod[];
}

export function TimePeriodSelector({ value, onChange, disabled = ['7d', '30d'] }: TimePeriodSelectorProps) {
  // Implementation z shadcn Button
}
```

#### PercentageChange.tsx
```typescript
interface PercentageChangeProps {
  value: number | null;
  showIcon?: boolean;
}

export function PercentageChange({ value, showIcon = true }: PercentageChangeProps) {
  // Implementation z kolorami i formatowaniem
}
```

#### DashboardBlock.tsx
```typescript
interface DashboardBlockProps {
  title: string;
  children: React.ReactNode;
  timePeriod: TimePeriod;
  onTimePeriodChange: (period: TimePeriod) => void;
  loading?: boolean;
}

export function DashboardBlock({ title, children, timePeriod, onTimePeriodChange, loading }: DashboardBlockProps) {
  // Implementation z shadcn Card
}
```

### Krok 6: Implementacja Bloków

Każdy blok będzie:
1. Fetchować dane z API
2. Obliczać % change (jeśli dostępne dane historyczne)
3. Renderować tabelę z 10 elementami
4. Obsługiwać loading i error states

### Krok 7: Strona Dashboardu

`frontend/src/app/dashboard/page.tsx`:
```typescript
export default function DashboardPage() {
  const [timePeriod, setTimePeriod] = useState<TimePeriod>('1d');
  
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <TopCreatorsByViewsBlock timePeriod={timePeriod} />
        <MostPopularTemplatesBlock timePeriod={timePeriod} />
        {/* ... pozostałe bloki */}
      </div>
    </div>
  );
}
```

---

## 🚨 Uwagi i Ograniczenia

### Obecne Ograniczenia
1. **7d i 30d disabled**: Brak danych historycznych dla tych okresów
2. **Brak niektórych endpointów**: Trzeba będzie stworzyć nowe endpointy w API lub obliczać po stronie frontendu
3. **Performance**: Pobieranie danych dla wielu kreatorów może być wolne - rozważyć caching

### Rozwiązania
1. **Caching**: Użyj React Query dla automatycznego cache'owania
2. **Loading States**: Zawsze pokazuj skeleton podczas ładowania
3. **Error Handling**: Graceful error handling z możliwością retry
4. **Pagination**: Jeśli potrzeba więcej niż 10 elementów, rozważyć paginację

---

## 📋 Checklist Implementacji

### Setup
- [ ] Zainstalować Shadcn/ui
- [ ] Dodać wymagane komponenty Shadcn (table, card, button, badge, skeleton)
- [ ] Skonfigurować Tailwind CSS
- [ ] Stworzyć strukturę folderów

### API & Types
- [ ] Stworzyć API client (`lib/api.ts`)
- [ ] Zdefiniować TypeScript types (`lib/types.ts`)
- [ ] Przetestować dostępność endpointów API

### Komponenty Podstawowe
- [ ] TimePeriodSelector
- [ ] PercentageChange
- [ ] DashboardBlock wrapper
- [ ] Table component (shadcn)

### Bloki Dashboardu
- [ ] Top Creators by Total Views
- [ ] Most Popular Templates
- [ ] Most Popular Components
- [ ] Most Popular Categories
- [ ] Most Popular Free Templates
- [ ] Creators with Most Templates

### Strona Dashboardu
- [ ] Layout strony
- [ ] Grid layout (responsive)
- [ ] Integracja wszystkich bloków
- [ ] Loading states
- [ ] Error handling

### Styling & UX
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Loading skeletons
- [ ] Error messages
- [ ] Hover states
- [ ] Accessibility (ARIA labels)

### Testing
- [ ] Testowanie na różnych rozdzielczościach
- [ ] Testowanie z różnymi danymi (empty, loading, error)
- [ ] Testowanie przełączania okresów czasu

---

## 🎯 Następne Kroki

1. **Zacznij od Setup**: Zainstaluj Shadcn/ui i wymagane komponenty
2. **Stwórz API Client**: Zaimplementuj funkcje do pobierania danych
3. **Zbuduj Podstawowe Komponenty**: TimePeriodSelector, PercentageChange, DashboardBlock
4. **Zaimplementuj Jeden Blok**: Zacznij od najprostszego (np. Most Popular Templates)
5. **Iteruj**: Dodawaj kolejne bloki jeden po drugim
6. **Refine**: Popraw UX, dodaj loading states, error handling

---

## 📚 Dokumentacja Shadcn/ui

- [Shadcn/ui Documentation](https://ui.shadcn.com/)
- [Table Component](https://ui.shadcn.com/docs/components/table)
- [Card Component](https://ui.shadcn.com/docs/components/card)
- [Button Component](https://ui.shadcn.com/docs/components/button)
- [Badge Component](https://ui.shadcn.com/docs/components/badge)

---

## 🔗 Przydatne Linki

- [Next.js App Router](https://nextjs.org/docs/app)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript](https://www.typescriptlang.org/docs/)
- [React Query](https://tanstack.com/query/latest) (opcjonalnie)

---

**Data utworzenia**: 2024-01-XX
**Status**: Plan gotowy do implementacji
**Autor**: AI Assistant

