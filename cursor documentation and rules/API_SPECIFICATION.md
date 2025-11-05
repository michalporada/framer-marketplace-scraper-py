# Amonit API — Specification & Implementation Guide

**Cel:** Kompleksowa dokumentacja API dla Amonit — od Foundation do Prediction & Automation.

**Status:** Foundation (ETAP 1) → Intelligence (ETAP 2) → Prediction (ETAP 3)

**Ostatnia aktualizacja:** 2025-01-XX

---

## 📋 Spis Treści

1. [Architektura API](#architektura-api)
2. [Authentication & Authorization](#authentication--authorization)
3. [Endpointy — ETAP 1 (Foundation)](#endpointy--etap-1-foundation)
4. [Endpointy — ETAP 2 (Intelligence)](#endpointy--etap-2-intelligence)
5. [Endpointy — ETAP 3 (Prediction)](#endpointy--etap-3-prediction)
6. [Market Context Integration](#market-context-integration)
7. [Rate Limiting & Quotas](#rate-limiting--quotas)
8. [Error Handling](#error-handling)
9. [Response Formats](#response-formats)
10. [Implementation Roadmap](#implementation-roadmap)

---

## 🏗️ Architektura API

### Stack Techniczny

- **Framework:** FastAPI (Python) lub Next.js API Routes (TypeScript) — [patrz wyjaśnienie](#api-structure-decision)
- **Database:** PostgreSQL (Supabase) z time-series snapshots
- **Authentication:** Supabase Auth (JWT-based, gotowe rozwiązanie)
- **Caching:** Redis (opcjonalne) lub in-memory cache — [patrz wyjaśnienie](#caching-strategy)
- **Documentation:** Swagger/OpenAPI (automatyczna z FastAPI)

### Struktura Projektu

```
api/
├── main.py                    # FastAPI app entry point
├── dependencies.py            # Auth, DB session, rate limiting
├── config.py                  # App configuration
│
├── routes/
│   ├── auth.py               # Authentication endpoints
│   ├── templates.py          # Template data endpoints
│   ├── categories.py         # Category analytics
│   ├── creators.py           # Creator profiles & analytics
│   ├── insights.py           # Insight generation (ETAP 2+)
│   ├── watchlist.py          # Watchlist management (ETAP 2+)
│   ├── alerts.py             # Alert management (ETAP 2+)
│   ├── market.py             # Market context & trends
│   └── predictions.py         # Predictive analytics (ETAP 3)
│
├── models/
│   ├── schemas.py            # Pydantic response models
│   ├── requests.py           # Request validation models
│   └── database.py           # SQLAlchemy models
│
├── services/
│   ├── insight_engine.py     # Insight generation logic
│   ├── metrics_calculator.py # Derived metrics (Difficulty, Opportunity)
│   ├── trend_detector.py     # Trend detection & analysis
│   └── market_context.py     # Market payout data integration
│
└── utils/
    ├── cache.py              # Caching utilities
    └── validators.py         # Input validation
```

---

## 🔐 Authentication & Authorization

### Authentication Flow

**ETAP 1 (Foundation):** Public API (read-only), bez authentication  
**ETAP 2+ (Intelligence):** Supabase Auth (JWT-based) dla watchlist, alerts, personal insights

#### Supabase Authentication

Supabase Auth zapewnia gotowe rozwiązanie dla:
- Email/password authentication
- OAuth (Google, GitHub) — opcjonalne
- JWT token management
- User session management

**Przykład użycia w API:**

```python
from supabase import create_client, Client
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)) -> dict:
    """Verify Supabase JWT token and return user."""
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        user = supabase.auth.get_user(token.credentials)
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Endpoint logowania** (obsługiwany przez Supabase Auth):
- Frontend używa Supabase client SDK do logowania
- API otrzymuje JWT token w headerze `Authorization: Bearer {token}`
- Token jest weryfikowany przy każdym requestcie wymagającym auth

#### Subscription Tiers & Access

| Tier | ETAP 1 | ETAP 2 | ETAP 3 |
|------|--------|--------|--------|
| **Free** | Public data, CSV export | Basic insights, 1 watchlist | Limited predictions |
| **Pro** ($9/m) | Historical data | Watchlist, alerts, full insights | Predictive dashboard |
| **Team** ($49/m) | - | CSV exports, email alerts, API access | - |
| **Studio** ($149/m) | - | - | Multi-marketplace, custom reports |

---

## 📊 Endpointy — ETAP 1 (Foundation)

### 1. Categories

#### `GET /api/categories`

Lista wszystkich kategorii z podstawowymi metrykami.

**Query Parameters:**
- `sort` (optional): `views`, `templates_count`, `name` (default: `views`)
- `order` (optional): `asc`, `desc` (default: `desc`)
- `limit` (optional): number (default: 100)
- `offset` (optional): number (default: 0)

**Response:**
```json
{
  "categories": [
    {
      "slug": "business",
      "name": "Business",
      "templates_count": 245,
      "total_views": 2840000,
      "avg_price": 89,
      "difficulty": "Medium",
      "first_seen_at": "2024-01-15T00:00:00Z",
      "last_seen_at": "2025-01-15T00:00:00Z"
    }
  ],
  "total": 45,
  "limit": 100,
  "offset": 0
}
```

#### `GET /api/categories/{slug}`

Szczegóły kategorii z podstawowymi statystykami.

**Response:**
```json
{
  "slug": "business",
  "name": "Business",
  "description": "Business templates for SaaS, startups, and companies",
  "templates_count": 245,
  "total_views": 2840000,
  "avg_views_per_template": 11591,
  "avg_price": 89,
  "difficulty": "Medium",
  "difficulty_score": 0.65,
  "estimated_revenue": 142000,
  "first_seen_at": "2024-01-15T00:00:00Z",
  "last_seen_at": "2025-01-15T00:00:00Z"
}
```

---

### 2. Templates

#### `GET /api/templates`

Lista szablonów z filtrowaniem i sortowaniem.

**Query Parameters:**
- `category` (optional): category slug
- `creator` (optional): creator handle
- `sort` (optional): `views`, `price`, `updated`, `rank` (default: `views`)
- `order` (optional): `asc`, `desc` (default: `desc`)
- `min_price` (optional): number
- `max_price` (optional): number
- `min_views` (optional): number
- `limit` (optional): number (default: 50)
- `offset` (optional): number (default: 0)

**Response:**
```json
{
  "templates": [
    {
      "slug": "calisto",
      "title": "Calisto — SaaS Template",
      "category_slug": "business",
      "creator_handle": "aster-themes",
      "creator_name": "Aster Themes",
      "price_cents": 9900,
      "price_currency": "USD",
      "price_display": "$99",
      "views": 28400,
      "pages": 12,
      "updated_label": "3 days ago",
      "updated_normalized": "2025-01-12T00:00:00Z",
      "rank_in_category": 3,
      "estimated_revenue": 141.24,
      "framer_url": "https://www.framer.com/marketplace/templates/calisto/",
      "affiliate_url": "https://framer.link/xxxxx?url=https://www.framer.com/marketplace/templates/calisto/"
    }
  ],
  "total": 1234,
  "limit": 50,
  "offset": 0
}
```

#### `GET /api/templates/{slug}`

Szczegóły szablonu.

**Response:**
```json
{
  "slug": "calisto",
  "title": "Calisto — SaaS Template",
  "description": "Modern SaaS template with...",
  "category_slug": "business",
  "categories": ["business", "saas"],
  "creator_handle": "aster-themes",
  "creator_name": "Aster Themes",
  "price_cents": 9900,
  "price_currency": "USD",
  "price_display": "$99",
  "views": 28400,
  "pages": 12,
  "updated_label": "3 days ago",
  "updated_normalized": "2025-01-12T00:00:00Z",
  "rank_in_category": 3,
  "category_positions": {
    "business": 3,
    "saas": 5
  },
  "estimated_revenue": 141.24,
  "features": ["Responsive", "Dark mode", "CMS"],
  "framer_url": "https://www.framer.com/marketplace/templates/calisto/",
  "affiliate_url": "https://framer.link/xxxxx?url=https://www.framer.com/marketplace/templates/calisto/",
  "first_seen_at": "2024-06-15T00:00:00Z",
  "last_seen_at": "2025-01-15T00:00:00Z"
}
```

---

### 3. Creators

#### `GET /api/creators`

Lista twórców z podstawowymi statystykami.

**Query Parameters:**
- `sort` (optional): `templates_count`, `total_views`, `name` (default: `total_views`)
- `order` (optional): `asc`, `desc` (default: `desc`)
- `min_templates` (optional): number
- `limit` (optional): number (default: 50)
- `offset` (optional): number (default: 0)

**Response:**
```json
{
  "creators": [
    {
      "handle": "aster-themes",
      "name": "Aster Themes",
      "templates_count": 12,
      "total_views": 450000,
      "avg_price": 89,
      "profile_url": "https://www.framer.com/@aster-themes/"
    }
  ],
  "total": 234,
  "limit": 50,
  "offset": 0
}
```

#### `GET /api/creators/{handle}`

Szczegóły twórcy z listą szablonów.

**Response:**
```json
{
  "handle": "aster-themes",
  "name": "Aster Themes",
  "bio": "Designer and developer creating...",
  "profile_url": "https://www.framer.com/@aster-themes/",
  "avatar_url": "https://...",
  "social_media": {
    "twitter": "https://twitter.com/asterthemes",
    "linkedin": "https://linkedin.com/in/asterthemes"
  },
  "templates_count": 12,
  "total_views": 450000,
  "avg_price": 89,
  "estimated_revenue": 2250,
  "templates": [
    {
      "slug": "calisto",
      "title": "Calisto — SaaS Template",
      "views": 28400,
      "price_cents": 9900
    }
  ],
  "first_seen_at": "2024-01-15T00:00:00Z",
  "last_seen_at": "2025-01-15T00:00:00Z"
}
```

---

## 📈 Endpointy — ETAP 2 (Intelligence)

### 4. Insights

#### `GET /api/insights`

Lista insightów z filtrowaniem.

**Query Parameters:**
- `category` (optional): category slug
- `type` (optional): `opportunity`, `warning`, `trend`, `performance` (default: all)
- `level` (optional): `high_opportunity`, `opportunity`, `warning` (default: all)
- `limit` (optional): number (default: 20)
- `offset` (optional): number (default: 0)

**Response:**
```json
{
  "insights": [
    {
      "id": "uuid",
      "type": "category_growth",
      "level": "opportunity",
      "title": "Real Estate category grew +26%",
      "subtitle": "Demand up, average price down",
      "action": "Consider creating a template in Real Estate with competitive pricing",
      "trend": "+26%",
      "category_slug": "real-estate",
      "metric": "views_growth",
      "data": {
        "growth_percent": 26,
        "avg_price_change": -11,
        "views_change": 45000
      },
      "generated_at": "2025-01-15T10:30:00Z"
    },
    {
      "id": "uuid",
      "type": "position_gain",
      "level": "high_opportunity",
      "title": "Your template Calisto gained 8 positions",
      "subtitle": "Moved from #45 to #28 in Business category",
      "action": "Analyze what caused the improvement and replicate",
      "trend": "+8",
      "template_slug": "calisto",
      "category_slug": "business",
      "metric": "rank_change",
      "data": {
        "previous_rank": 45,
        "current_rank": 28,
        "days": 7
      },
      "generated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

#### `GET /api/insights/personal`

Personalizowane insighty dla użytkownika (wymaga authentication).

**Query Parameters:**
- `type` (optional): insight type filter
- `limit` (optional): number (default: 10)

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "insights": [
    {
      "id": "uuid",
      "type": "personal_performance",
      "level": "warning",
      "title": "Your templates underperform vs market median",
      "subtitle": "Average views: 2.1K vs market median: 3.4K",
      "action": "Increase page count or improve SEO title",
      "trend": "-38%",
      "metric": "views_comparison",
      "data": {
        "your_avg_views": 2100,
        "market_median": 3400,
        "difference_percent": -38
      },
      "generated_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

#### `GET /api/categories/{slug}/insights`

Insighty dla konkretnej kategorii.

**Response:**
```json
{
  "category_slug": "business",
  "insights": [
    {
      "id": "uuid",
      "type": "category_growth",
      "title": "Business category grew +15% this month",
      "subtitle": "Views increased while average price stabilized",
      "action": "Consider entering this category",
      "trend": "+15%",
      "level": "opportunity"
    }
  ]
}
```

#### `GET /api/templates/{slug}/insights`

Insighty dla konkretnego szablonu.

**Response:**
```json
{
  "template_slug": "calisto",
  "insights": [
    {
      "id": "uuid",
      "type": "update_impact",
      "title": "Recent update improved rank significantly",
      "subtitle": "Rank improved from #45 → #28 after last update",
      "action": "Plan regular updates to maintain visibility",
      "trend": "+17",
      "level": "opportunity"
    }
  ]
}
```

---

### 5. Trends & Analytics

#### `GET /api/categories/{slug}/trends`

Wykresy trendów dla kategorii.

**Query Parameters:**
- `metric` (required): `views`, `templates_count`, `avg_price`, `revenue`
- `days` (optional): number (default: 30)
- `granularity` (optional): `day`, `week`, `month` (default: `day`)

**Response:**
```json
{
  "category_slug": "business",
  "metric": "views",
  "period": {
    "start": "2024-12-15T00:00:00Z",
    "end": "2025-01-15T00:00:00Z",
    "days": 30
  },
  "data": [
    {
      "date": "2024-12-15T00:00:00Z",
      "value": 2700000,
      "change_percent": 0
    },
    {
      "date": "2024-12-16T00:00:00Z",
      "value": 2720000,
      "change_percent": 0.74
    }
  ],
  "summary": {
    "current": 2840000,
    "previous": 2700000,
    "change_percent": 5.19,
    "growth_rate": "+15%"
  }
}
```

#### `GET /api/templates/{slug}/history`

Historia zmian szablonu w czasie.

**Query Parameters:**
- `days` (optional): number (default: 30)
- `fields` (optional): comma-separated list: `views,price,rank` (default: all)

**Response:**
```json
{
  "template_slug": "calisto",
  "period": {
    "start": "2024-12-15T00:00:00Z",
    "end": "2025-01-15T00:00:00Z"
  },
  "history": [
    {
      "date": "2024-12-15T00:00:00Z",
      "views": 26500,
      "price_cents": 9900,
      "rank_in_category": 5,
      "category_slug": "business"
    },
    {
      "date": "2025-01-15T00:00:00Z",
      "views": 28400,
      "price_cents": 9900,
      "rank_in_category": 3,
      "category_slug": "business"
    }
  ],
  "deltas": {
    "views": {
      "change": 1900,
      "change_percent": 7.17
    },
    "rank": {
      "change": -2,
      "direction": "up"
    }
  }
}
```

#### `GET /api/metrics/top-gainers`

Top templates gaining views/rank.

**Query Parameters:**
- `category` (optional): category slug
- `metric` (optional): `views`, `rank` (default: `views`)
- `days` (optional): number (default: 7)
- `limit` (optional): number (default: 10)

**Response:**
```json
{
  "metric": "views",
  "period_days": 7,
  "gainers": [
    {
      "template_slug": "calisto",
      "title": "Calisto — SaaS Template",
      "views_delta": 1900,
      "views_growth_percent": 7.17,
      "previous_views": 26500,
      "current_views": 28400,
      "rank_change": -2
    }
  ]
}
```

---

### 6. Watchlist

#### `POST /api/watchlist`

Dodaj element do watchlist (wymaga authentication).

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Request Body:**
```json
{
  "type": "template",  // "template", "creator", "category"
  "target_id": "calisto"  // template_slug, creator_handle, category_slug
}
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "type": "template",
  "target_id": "calisto",
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### `GET /api/watchlist`

Lista elementów w watchlist użytkownika (wymaga authentication).

**Query Parameters:**
- `type` (optional): `template`, `creator`, `category`
- `limit` (optional): number (default: 50)

**Response:**
```json
{
  "watchlist": [
    {
      "id": "uuid",
      "type": "template",
      "target_id": "calisto",
      "target": {
        "slug": "calisto",
        "title": "Calisto — SaaS Template",
        "views": 28400,
        "rank_in_category": 3
      },
      "created_at": "2025-01-15T10:30:00Z",
      "recent_changes": {
        "rank_delta": -2,
        "views_delta": 1900,
        "last_change": "2025-01-15T08:00:00Z"
      }
    }
  ],
  "total": 12
}
```

#### `DELETE /api/watchlist/{id}`

Usuń element z watchlist (wymaga authentication).

---

### 7. Alerts

#### `GET /api/alerts`

Lista alertów dla użytkownika (wymaga authentication).

**Query Parameters:**
- `status` (optional): `unread`, `read`, `all` (default: `unread`)
- `type` (optional): alert type filter
- `limit` (optional): number (default: 20)

**Response:**
```json
{
  "alerts": [
    {
      "id": "uuid",
      "type": "position_change",
      "message": "Template Calisto moved 2 positions up in Business category",
      "data": {
        "template_slug": "calisto",
        "category_slug": "business",
        "previous_rank": 5,
        "current_rank": 3,
        "delta": -2
      },
      "created_at": "2025-01-15T08:00:00Z",
      "read_at": null,
      "status": "unread"
    }
  ],
  "total": 5
}
```

#### `POST /api/alerts/rules`

Utwórz regułę alertu (wymaga authentication).

**Request Body:**
```json
{
  "watchlist_id": "uuid",
  "rule_type": "position_change",  // "position_change", "views_drop", "new_template"
  "threshold_value": 5,  // e.g., position change > 5
  "enabled": true
}
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "watchlist_id": "uuid",
  "rule_type": "position_change",
  "threshold_value": 5,
  "enabled": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

## 🔮 Endpointy — ETAP 3 (Prediction)

### 8. Predictive Analytics

#### `GET /api/categories/{slug}/forecast`

Przewidywanie trendów dla kategorii (wymaga Pro+ subscription).

**Query Parameters:**
- `days_ahead` (optional): number (default: 30)
- `metric` (optional): `views`, `revenue` (default: `views`)

**Response:**
```json
{
  "category_slug": "business",
  "metric": "views",
  "forecast": {
    "predicted_value": 3000000,
    "confidence_interval": {
      "lower": 2850000,
      "upper": 3150000
    },
    "trend": "increasing",
    "confidence": 0.85
  },
  "historical_data": [
    {
      "date": "2024-12-15T00:00:00Z",
      "value": 2700000
    }
  ],
  "predicted_data": [
    {
      "date": "2025-02-15T00:00:00Z",
      "value": 3000000
    }
  ]
}
```

#### `GET /api/metrics/heatmap`

Category heatmap z opportunity/difficulty scores (wymaga Pro+ subscription).

**Response:**
```json
{
  "heatmap": [
    {
      "category_slug": "business",
      "category_name": "Business",
      "opportunity_score": 0.75,
      "difficulty_score": 0.65,
      "recommendation": "enter",
      "data": {
        "views_growth": 15,
        "avg_price": 89,
        "templates_count": 245
      }
    }
  ]
}
```

---

### 9. AI Insights

#### `POST /api/insights/generate-ai`

Wygeneruj AI-powered insight (wymaga Pro+ subscription).

**Request Body:**
```json
{
  "category_slug": "business",
  "context": "user wants to understand market dynamics"
}
```

**Response:**
```json
{
  "insight": "Category Business grew 23% in views this month — while average template price rose by 14%. This suggests strong demand with pricing power. Consider entering with a template priced competitively between $79-$99.",
  "supporting_data": {
    "views_growth": 23,
    "price_growth": 14,
    "recommended_price_range": [79, 99]
  },
  "generated_at": "2025-01-15T10:30:00Z"
}
```

---

## 📊 Market Context Integration

### 10. Market Data

#### `GET /api/market/context`

Globalne dane rynkowe (Framer Marketplace payouts).

**Response:**
```json
{
  "latest_payout": {
    "month": "2025-09",
    "total_payout_usd": 737000,
    "source": "twitter:@framer"
  },
  "historical_payouts": [
    {
      "month": "2025-02",
      "total_payout_usd": 322348,
      "source": "twitter:@framer"
    },
    {
      "month": "2025-09",
      "total_payout_usd": 737000,
      "source": "twitter:@framer"
    }
  ],
  "summary": {
    "avg_monthly_payout": 525000,
    "annual_run_rate": 6300000,
    "growth_since_february": 128.5,
    "trend": "increasing"
  }
}
```

#### `GET /api/market/trends`

Trendy rynku z wizualizacją.

**Query Parameters:**
- `months` (optional): number (default: 12)

**Response:**
```json
{
  "trends": [
    {
      "month": "2025-02",
      "total_payout_usd": 322348,
      "change_percent": 0
    },
    {
      "month": "2025-09",
      "total_payout_usd": 737000,
      "change_percent": 128.5
    }
  ],
  "insights": [
    "Market revenue up +128% since February",
    "Average monthly creator payout now exceeds half a million USD"
  ]
}
```

#### `GET /api/categories/{slug}/revenue-share`

Udział kategorii w przychodach rynku.

**Response:**
```json
{
  "category_slug": "business",
  "category_views": 2840000,
  "total_marketplace_views": 50000000,
  "revenue_share_percent": 5.68,
  "estimated_revenue": 41872,
  "latest_market_payout": 737000
}
```

---

## 🔗 Affiliate Links Integration

### 11. Affiliate Management

#### `GET /api/templates/{slug}/affiliate-url`

Pobierz affiliate URL dla szablonu.

**Query Parameters:**
- `user_affiliate_code` (optional): user's Framer affiliate code (jeśli dostępny)

**Response:**
```json
{
  "template_slug": "calisto",
  "framer_url": "https://www.framer.com/marketplace/templates/calisto/",
  "affiliate_url": "https://framer.link/xxxxx?url=https://www.framer.com/marketplace/templates/calisto/",
  "affiliate_source": "amonit",  // "amonit" (default) or "user" (if user_affiliate_code provided)
  "disclosure": "Clicking this link supports Amonit and the template creator"
}
```

**Logika:**
- Jeśli użytkownik ma własny affiliate code → użyj jego
- W przeciwnym razie → użyj domyślnego Amonit affiliate link
- Wszystkie linki w API responses zawierają `affiliate_url` field

#### `POST /api/user/affiliate-code`

Zapisz affiliate code użytkownika (wymaga authentication).

**Request Body:**
```json
{
  "affiliate_code": "framer.link/xxxxx"  // User's Framer affiliate code
}
```

**Response:**
```json
{
  "user_id": "uuid",
  "affiliate_code": "framer.link/xxxxx",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

## ⚡ Rate Limiting & Quotas

### Rate Limits by Tier

| Tier | Requests/min | Requests/hour | Requests/day |
|------|---------------|---------------|--------------|
| **Free** | 10 | 100 | 1000 |
| **Pro** | 30 | 500 | 5000 |
| **Team** | 60 | 2000 | 20000 |
| **Studio** | 120 | 10000 | 100000 |

### Rate Limit Headers

```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1642248000
```

### Response (429 Too Many Requests)

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```

---

## ❌ Error Handling

### Standard Error Response

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "additional error details"
  },
  "request_id": "uuid"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `not_found` | 404 | Resource not found |
| `unauthorized` | 401 | Authentication required |
| `forbidden` | 403 | Insufficient permissions |
| `rate_limit_exceeded` | 429 | Too many requests |
| `validation_error` | 422 | Invalid input data |
| `server_error` | 500 | Internal server error |

### Example Error Responses

**404 Not Found:**
```json
{
  "error": "not_found",
  "message": "Template 'invalid-slug' not found",
  "request_id": "uuid"
}
```

**401 Unauthorized:**
```json
{
  "error": "unauthorized",
  "message": "Authentication required. Please provide a valid JWT token.",
  "request_id": "uuid"
}
```

**422 Validation Error:**
```json
{
  "error": "validation_error",
  "message": "Invalid input data",
  "details": {
    "category": "Invalid category slug format"
  },
  "request_id": "uuid"
}
```

---

## 📝 Response Formats

### Standard Response Wrapper

```json
{
  "data": { ... },
  "meta": {
    "total": 100,
    "limit": 50,
    "offset": 0,
    "has_more": true
  },
  "links": {
    "self": "/api/templates?limit=50&offset=0",
    "next": "/api/templates?limit=50&offset=50",
    "prev": null
  }
}
```

### Pagination

Wszystkie list endpoints wspierają paginację:
- `limit`: liczba elementów (max 100)
- `offset`: przesunięcie (0-indexed)

---

## 🗺️ Implementation Roadmap

### Faza 1: Foundation API (ETAP 1) — 2-3 tygodnie

**Priorytet:** Public endpoints dla podstawowych danych

- [ ] `GET /api/categories` — lista kategorii
- [ ] `GET /api/categories/{slug}` — szczegóły kategorii
- [ ] `GET /api/templates` — lista szablonów
- [ ] `GET /api/templates/{slug}` — szczegóły szablonu
- [ ] `GET /api/creators` — lista twórców
- [ ] `GET /api/creators/{handle}` — szczegóły twórcy
- [ ] `GET /api/market/context` — market context data
- [ ] Basic error handling & rate limiting
- [ ] Swagger/OpenAPI documentation

**Szacowany czas:** 2-3 tygodnie

---

### Faza 2: Intelligence API (ETAP 2) — 3-4 tygodnie

**Priorytet:** Insights, trends, watchlist, alerts

- [ ] `GET /api/insights` — lista insightów
- [ ] `GET /api/insights/personal` — personalizowane insighty
- [ ] `GET /api/categories/{slug}/insights` — insighty kategorii
- [ ] `GET /api/templates/{slug}/insights` — insighty szablonu
- [ ] `GET /api/categories/{slug}/trends` — trendy kategorii
- [ ] `GET /api/templates/{slug}/history` — historia szablonu
- [ ] `GET /api/metrics/top-gainers` — top gainers
- [ ] `POST /api/watchlist` — dodaj do watchlist
- [ ] `GET /api/watchlist` — lista watchlist
- [ ] `DELETE /api/watchlist/{id}` — usuń z watchlist
- [ ] `GET /api/alerts` — lista alertów
- [ ] `POST /api/alerts/rules` — utwórz regułę alertu
- [ ] Authentication & authorization
- [ ] User management endpoints

**Szacowany czas:** 3-4 tygodnie

---

### Faza 3: Prediction API (ETAP 3) — 2-3 tygodnie

**Priorytet:** AI insights, predictive analytics

- [ ] `GET /api/categories/{slug}/forecast` — przewidywania
- [ ] `GET /api/metrics/heatmap` — category heatmap
- [ ] `POST /api/insights/generate-ai` — AI-powered insights
- [ ] LLM integration (OpenAI/Claude)
- [ ] Time-series forecasting (Prophet)
- [ ] Advanced caching dla predictions

**Szacowany czas:** 2-3 tygodnie

---

## 🔧 Technical Implementation Notes

### Database Queries

**Time-series queries:**
```sql
-- Get template history
SELECT * FROM template_snapshots 
WHERE template_slug = 'calisto' 
  AND captured_at >= NOW() - INTERVAL '30 days'
ORDER BY captured_at DESC;

-- Calculate rank deltas
WITH ranked AS (
  SELECT 
    template_slug,
    rank_in_category,
    captured_at,
    LAG(rank_in_category) OVER (PARTITION BY template_slug ORDER BY captured_at) as prev_rank
  FROM template_snapshots
  WHERE category_slug = 'business'
)
SELECT * FROM ranked WHERE rank_in_category != prev_rank;
```

### Caching Strategy

- **Categories list:** Cache 1 hour (rarely changes)
- **Template details:** Cache 15 minutes (changes daily)
- **Insights:** Cache 30 minutes (regenerated daily)
- **Trends:** Cache 1 hour (computed daily)
- **Predictions:** Cache 6 hours (expensive computation)

### Market Context Data

**Storage:**
```json
// data/market_context.json
[
  {
    "month": "2025-02",
    "total_payout_usd": 322348,
    "source": "twitter:@framer"
  },
  {
    "month": "2025-09",
    "total_payout_usd": 737000,
    "source": "twitter:@framer"
  }
]
```

**Helper function:**
```python
def get_latest_market_payout() -> float:
    """Get latest Framer Marketplace payout from market_context.json."""
    with open("data/market_context.json") as f:
        context = json.load(f)
    latest = max(context, key=lambda x: x["month"])
    return latest["total_payout_usd"]
```

**Revenue estimation:**
```python
def estimate_template_revenue(template_views: int, total_market_views: int) -> float:
    """Estimate template revenue based on market payout."""
    payout = get_latest_market_payout()
    return (template_views / total_market_views) * payout if total_market_views > 0 else 0
```

---

## 📚 Additional Resources

### API Documentation

- **Swagger UI:** `/docs` (automatyczna z FastAPI)
- **ReDoc:** `/redoc` (alternatywna dokumentacja)
- **OpenAPI Schema:** `/openapi.json`

### Testing

- **Unit tests:** `tests/api/`
- **Integration tests:** `tests/integration/`
- **Postman collection:** `docs/postman_collection.json`

---

**Wersja:** 1.0  
**Ostatnia aktualizacja:** 2025-01-XX  
**Status:** Foundation (ETAP 1) — Ready for Implementation

