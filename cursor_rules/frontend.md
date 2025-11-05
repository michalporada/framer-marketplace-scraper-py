# Front-end Rules

**Cel:** Zapewnić spójny UI w oparciu o Shadcn + Tailwind + Next.js.

## Stack Techniczny

### Core Technologies

- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn/ui
- **Type Safety**: TypeScript
- **State Management**: React Context / Zustand (jeśli potrzebne)
- **Data Fetching**: React Query / SWR (opcjonalnie)

### Struktura Projektu

```
frontend/
├── package.json
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── products/
│   │   ├── creators/
│   │   └── api/                # API routes (jeśli potrzebne)
│   ├── components/            # Reusable components
│   │   ├── ui/                # Shadcn components
│   │   ├── product/           # Product-specific components
│   │   ├── creator/           # Creator-specific components
│   │   └── layout/            # Layout components
│   ├── lib/                   # Utilities
│   │   ├── utils.ts           # Helper functions
│   │   ├── api.ts             # API client
│   │   └── constants.ts       # Constants
│   ├── hooks/                 # Custom React hooks
│   ├── types/                 # TypeScript types
│   └── styles/                # Global styles
└── public/                    # Static assets
```

## Zasady Projektowania UI

### Design System

1. **Shadcn/ui Components**
   - Używaj Shadcn/ui jako bazy dla komponentów
   - Nie modyfikuj bezpośrednio komponentów Shadcn
   - Twórz wrapper components jeśli potrzebne zmiany

2. **Tailwind CSS**
   - Używaj utility classes z Tailwind
   - Unikaj custom CSS gdzie możliwe
   - Używaj Tailwind config dla custom colors/spacing

3. **Responsive Design**
   - Mobile-first approach
   - Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
   - Testuj na różnych rozdzielczościach

### Komponenty

#### Naming Conventions

- **Components**: PascalCase (np. `ProductCard.tsx`)
- **Files**: PascalCase dla komponentów (np. `ProductCard.tsx`)
- **Hooks**: camelCase z prefix `use` (np. `useProduct.ts`)
- **Utils**: camelCase (np. `formatDate.ts`)

#### Struktura Komponentu

```typescript
// ProductCard.tsx
import { Product } from '@/types';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';

interface ProductCardProps {
  product: Product;
  onSelect?: (product: Product) => void;
}

export function ProductCard({ product, onSelect }: ProductCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{product.name}</CardTitle>
      </CardHeader>
      {/* Content */}
    </Card>
  );
}
```

#### Zasady

1. **Single Responsibility**
   - Jeden komponent = jedna funkcjonalność
   - Dziel duże komponenty na mniejsze
   - Używaj composition pattern

2. **Props Interface**
   - Zawsze definiuj interface dla props
   - Używaj TypeScript strict mode
   - Opcjonalne props: `?`

3. **Reusability**
   - Twórz komponenty reusable
   - Nie duplikuj logiki
   - Używaj composition over inheritance

## Styling

### Tailwind CSS

1. **Utility Classes**
   ```tsx
   // ✅ Dobrze
   <div className="flex items-center gap-4 p-6 bg-white rounded-lg shadow-md">
   
   // ❌ Źle
   <div className="custom-card">
   ```

2. **Custom Classes**
   - Tylko dla złożonych przypadków
   - Używaj `@apply` w CSS
   - Dokumentuj custom classes

3. **Colors**
   - Używaj Tailwind color palette
   - Custom colors w `tailwind.config.js`
   - Consistent color usage

### Dark Mode (Opcjonalnie)

1. **Implementation**
   - Używaj `next-themes` dla dark mode
   - Toggle w header/navigation
   - Persist preference

2. **Styling**
   - Używaj `dark:` prefix dla dark mode styles
   - Testuj w obu trybach

## Data Fetching

### API Integration

1. **API Client**
   ```typescript
   // lib/api.ts
   const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';
   
   export async function fetchProduct(id: string): Promise<Product> {
     const response = await fetch(`${API_BASE_URL}/products/${id}`);
     if (!response.ok) throw new Error('Failed to fetch product');
     return response.json();
   }
   ```

2. **Error Handling**
   - Try-catch w komponentach
   - Error boundaries dla błędów React
   - User-friendly error messages

3. **Loading States**
   - Zawsze pokazuj loading state
   - Używaj Skeleton components (Shadcn)
   - Nie pokazuj pustego ekranu

### React Query / SWR (Opcjonalnie)

1. **Benefits**
   - Automatic caching
   - Background refetching
   - Optimistic updates

2. **Usage**
   ```typescript
   import { useQuery } from '@tanstack/react-query';
   
   function useProduct(id: string) {
     return useQuery({
       queryKey: ['product', id],
       queryFn: () => fetchProduct(id),
     });
   }
   ```

## State Management

### Local State

1. **useState**
   - Dla prostego local state
   - Form inputs
   - UI toggles

2. **useReducer**
   - Dla złożonego state logic
   - Form state z walidacją
   - Complex UI state

### Global State

1. **React Context**
   - Dla shared state (theme, user, etc.)
   - Nie nadużywaj - może powodować re-renders

2. **Zustand** (jeśli potrzebne)
   - Dla bardziej złożonego state
   - Lighter niż Redux
   - Easy to use

## Routing

### Next.js App Router

1. **File-based Routing**
   ```
   app/
   ├── page.tsx                 # / (home)
   ├── products/
   │   ├── page.tsx            # /products (list)
   │   └── [id]/
   │       └── page.tsx        # /products/[id] (detail)
   └── creators/
       ├── page.tsx            # /creators (list)
       └── [username]/
           └── page.tsx        # /creators/[username] (detail)
   ```

2. **Dynamic Routes**
   - Używaj `[param]` dla dynamic routes
   - Access param przez `params` prop

3. **Layouts**
   - Shared layout w `layout.tsx`
   - Nested layouts dla sekcji

## Performance

### Optimization

1. **Image Optimization**
   - Używaj `next/image` dla obrazów
   - Lazy loading domyślnie
   - Responsive images

2. **Code Splitting**
   - Automatic z Next.js
   - Dynamic imports dla heavy components
   - Lazy load components

3. **Memoization**
   - `React.memo` dla expensive components
   - `useMemo` dla expensive calculations
   - `useCallback` dla function props

### SEO

1. **Metadata**
   ```typescript
   export const metadata = {
     title: 'Product Name',
     description: 'Product description',
   };
   ```

2. **Open Graph**
   - Social media sharing
   - Og images dla produktów

## Forms

### Form Handling

1. **React Hook Form** (Rekomendowane)
   - Type-safe forms
   - Validation z Zod
   - Performance optimized

2. **Validation**
   - Zod schemas dla validation
   - Client-side + server-side validation
   - User-friendly error messages

### Example

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

const formSchema = z.object({
  email: z.string().email(),
});

function MyForm() {
  const form = useForm({
    resolver: zodResolver(formSchema),
  });
  
  // Form implementation
}
```

## Accessibility

### WCAG Compliance

1. **Semantic HTML**
   - Używaj semantic tags (nav, main, article, etc.)
   - Proper heading hierarchy (h1 → h2 → h3)

2. **ARIA Attributes**
   - `aria-label` dla icon buttons
   - `aria-describedby` dla form errors
   - `role` attributes gdzie potrzebne

3. **Keyboard Navigation**
   - Tab order logical
   - Focus indicators visible
   - Keyboard shortcuts dla actions

4. **Screen Readers**
   - Alt text dla obrazów
   - Descriptive link text
   - ARIA labels gdzie potrzebne

## Testing

### Testing Strategy

1. **Unit Tests**
   - Jest + React Testing Library
   - Test komponentów w izolacji
   - Test utils functions

2. **Integration Tests**
   - Test pełnych flows
   - Mock API calls
   - Test user interactions

3. **E2E Tests** (Opcjonalnie)
   - Playwright / Cypress
   - Critical user flows
   - Cross-browser testing

## Error Handling

### Error Boundaries

1. **Implementation**
   ```typescript
   'use client';
   
   export default function ErrorBoundary({
     error,
     reset,
   }: {
     error: Error;
     reset: () => void;
   }) {
     return (
       <div>
         <h2>Something went wrong!</h2>
         <button onClick={reset}>Try again</button>
       </div>
     );
   }
   ```

2. **User-friendly Messages**
   - Nie pokazuj technical errors użytkownikom
   - Provide recovery options
   - Log errors do monitoring

## Checklist przed Implementacją

- [ ] Komponenty używają Shadcn/ui
- [ ] Styling z Tailwind CSS
- [ ] TypeScript strict mode
- [ ] Responsive design
- [ ] Loading states zaimplementowane
- [ ] Error handling zaimplementowany
- [ ] Accessibility (WCAG) sprawdzone
- [ ] Performance zoptymalizowana
- [ ] SEO metadata dodane
- [ ] Testy napisane (jeśli potrzebne)

---

**Uwaga:** Te reguły są draftem i mogą być rozszerzone/zmodyfikowane w przyszłości.

