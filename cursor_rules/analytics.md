# Product Analytics Rules

**Cel:** Spójne trackowanie zachowań użytkowników.

## Definicja Analytics

Product Analytics to trackowanie interakcji użytkowników z aplikacją/frontendem, które pozwala zrozumieć jak użytkownicy korzystają z produktu.

## Zasady Trackowania

### 1. Event-based Tracking

- Trackuj wydarzenia (events), nie page views
- Każde wydarzenie ma: `name`, `properties`, `timestamp`
- Używaj strukturalnych nazw eventów

### 2. Privacy-first

- Nie trackuj PII (Personally Identifiable Information)
- Respektuj GDPR/privacy regulations
- Anonimizuj dane gdzie możliwe

### 3. Consistency

- Używaj spójnych nazw eventów
- Spójne property names
- Spójne formaty danych

## Event Naming

### Konwencja

- Format: `{category}_{action}_{object}`
- Używaj snake_case
- Bądź opisowy ale zwięzły

### Przykłady

```
# Product interactions
product_viewed
product_clicked
product_shared
product_filtered

# Creator interactions
creator_viewed
creator_products_clicked
creator_followed

# Navigation
page_viewed
navigation_clicked
search_performed

# User actions
filter_applied
sort_changed
export_clicked
```

## Event Properties

### Standardowe Properties

Każde wydarzenie powinno zawierać:

```typescript
{
  event: "product_viewed",
  properties: {
    // Context
    product_id: string,
    product_type: "template" | "component" | "vector" | "plugin",
    product_name: string,
    
    // User context (anonimizowane)
    session_id: string,
    user_id?: string,  // Opcjonalnie, jeśli użytkownik zalogowany
    
    // Technical
    timestamp: string,  // ISO 8601
    url: string,
    referrer?: string,
    
    // Custom
    [key: string]: any
  }
}
```

### Product Events

```typescript
// Product viewed
{
  event: "product_viewed",
  properties: {
    product_id: "template-name",
    product_type: "template",
    product_name: "Template Name",
    creator_username: "creator-name",
    price: 49.99,
    is_free: false
  }
}

// Product clicked (from list)
{
  event: "product_clicked",
  properties: {
    product_id: "template-name",
    product_type: "template",
    position: 5,  // Position in list
    list_type: "popular" | "recent" | "search"
  }
}

// Product shared
{
  event: "product_shared",
  properties: {
    product_id: "template-name",
    share_method: "twitter" | "facebook" | "copy_link"
  }
}
```

### Creator Events

```typescript
// Creator viewed
{
  event: "creator_viewed",
  properties: {
    creator_username: "creator-name",
    products_count: 10,
    source: "product_page" | "direct" | "search"
  }
}

// Creator products clicked
{
  event: "creator_products_clicked",
  properties: {
    creator_username: "creator-name",
    product_type?: "template" | "component" | "vector" | "plugin"
  }
}
```

### Navigation Events

```typescript
// Page viewed
{
  event: "page_viewed",
  properties: {
    page: "/products" | "/creators" | "/product/[id]",
    page_title: string
  }
}

// Search performed
{
  event: "search_performed",
  properties: {
    query: string,
    results_count: number,
    filters_applied: string[]
  }
}
```

### Filter/Sort Events

```typescript
// Filter applied
{
  event: "filter_applied",
  properties: {
    filter_type: "product_type" | "price" | "category",
    filter_value: string,
    active_filters: string[]
  }
}

// Sort changed
{
  event: "sort_changed",
  properties: {
    sort_by: "popularity" | "price" | "date",
    sort_order: "asc" | "desc"
  }
}
```

## Implementation

### Frontend (Next.js)

#### Analytics Provider

```typescript
// lib/analytics.ts
type AnalyticsEvent = {
  event: string;
  properties?: Record<string, any>;
};

export function track(event: string, properties?: Record<string, any>) {
  // Implementation (Google Analytics, Mixpanel, etc.)
  if (typeof window !== 'undefined') {
    // Track event
    window.gtag?.('event', event, properties);
  }
}
```

#### Usage in Components

```typescript
// components/ProductCard.tsx
import { track } from '@/lib/analytics';

export function ProductCard({ product }: ProductCardProps) {
  const handleClick = () => {
    track('product_clicked', {
      product_id: product.id,
      product_type: product.type,
      position: product.position,
    });
  };

  return (
    <Card onClick={handleClick}>
      {/* Content */}
    </Card>
  );
}
```

### Backend (API) - Opcjonalnie

#### Track API Usage

```python
# api/middleware.py
from fastapi import Request
import time

async def track_api_usage(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Track API call
    track_event("api_request", {
        "endpoint": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "duration_ms": duration * 1000,
    })
    
    return response
```

## Analytics Providers

### Google Analytics 4 (GA4)

```typescript
// lib/analytics.ts
export function track(event: string, properties?: Record<string, any>) {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', event, properties);
  }
}
```

### Mixpanel

```typescript
import mixpanel from 'mixpanel-browser';

export function track(event: string, properties?: Record<string, any>) {
  mixpanel.track(event, properties);
}
```

### Custom Analytics

```typescript
// lib/analytics.ts
export async function track(event: string, properties?: Record<string, any>) {
  // Send to custom endpoint
  await fetch('/api/analytics', {
    method: 'POST',
    body: JSON.stringify({
      event,
      properties: {
        ...properties,
        timestamp: new Date().toISOString(),
      },
    }),
  });
}
```

## Best Practices

### 1. Don't Over-track

- Trackuj tylko znaczące wydarzenia
- Nie trackuj każdego kliknięcia
- Fokus na business metrics

### 2. Consistent Naming

- Używaj słownika eventów
- Dokumentuj wszystkie eventy
- Review eventy regularnie

### 3. Error Handling

- Analytics nie powinny blokować aplikacji
- Obsługuj błędy gracefully
- Loguj błędy analytics

### 4. Performance

- Analytics powinny być async
- Nie blokuj renderowania
- Batch events jeśli możliwe

## Privacy & Compliance

### GDPR Compliance

1. **Consent**
   - Zbieraj zgodę przed trackowaniem
   - Pozwól użytkownikom opt-out
   - Respektuj Do Not Track

2. **Data Minimization**
   - Zbieraj tylko potrzebne dane
   - Nie zbieraj PII
   - Anonimizuj dane

3. **Transparency**
   - Informuj użytkowników o trackowaniu
   - Privacy policy
   - Clear opt-out mechanism

## Testing

### Unit Tests

```typescript
// lib/__tests__/analytics.test.ts
import { track } from '@/lib/analytics';

describe('analytics', () => {
  it('tracks events', () => {
    const mockGtag = jest.fn();
    window.gtag = mockGtag;
    
    track('product_viewed', { product_id: 'test' });
    
    expect(mockGtag).toHaveBeenCalledWith(
      'event',
      'product_viewed',
      { product_id: 'test' }
    );
  });
});
```

### E2E Tests

- Testuj trackowanie w E2E tests
- Verify events są wysyłane
- Testuj opt-out functionality

## Documentation

### Event Dictionary

Dokumentuj wszystkie eventy w `docs/analytics-events.md`:

```markdown
## Product Events

### product_viewed
**Description:** User viewed a product detail page

**Properties:**
- `product_id` (string, required): Product identifier
- `product_type` (string, required): template | component | vector | plugin
- `product_name` (string, required): Product name
- `creator_username` (string, required): Creator username
- `price` (number, optional): Product price
- `is_free` (boolean, required): Is product free
```

## Checklist

- [ ] Event naming convention zdefiniowany
- [ ] Analytics provider wybrany/implementowany
- [ ] Trackowanie zaimplementowane w komponentach
- [ ] Privacy compliance (GDPR)
- [ ] Error handling zaimplementowany
- [ ] Performance zoptymalizowana (async)
- [ ] Testy napisane
- [ ] Dokumentacja eventów stworzona
- [ ] Opt-out mechanism zaimplementowany

---

**Uwaga:** Te reguły są draftem i mogą być rozszerzone/zmodyfikowane w przyszłości.

