# Amonit — Product Roadmap & Strategy

**Cel:** Stać się inteligentnym dashboardem dla twórców Framer Marketplace, który pokazuje trendy, przewiduje szanse i pomaga zwiększyć sprzedaż szablonów i komponentów.

**Filozofia:** Nie sprzedajemy danych — sprzedajemy przewagę informacyjną. Produktem nie jest wykres, tylko lepsze decyzje.

---

## 🚀 Roadmap — 3 Etapy Rozwoju

### ETAP 1: Foundation (0 → 1) | 1–2 miesiące

**Cel:** Zbierać i prezentować dane w czytelny sposób

**Zakres:**
- ✅ Stabilny scraper z codziennymi aktualizacjami:
  - Kategorie, autorzy, ceny, views, pozycje w rankingu, liczba stron, data aktualizacji
- ✅ Baza historyczna (SQLite/Supabase) — dane zachowują ciągłość
- ✅ Dashboard MVP:
  - Lista kategorii, tabela szablonów
  - Filtry: sortowanie po views/price/update
  - Wskaźniki: Difficulty, Total Views, Est. Revenue (0.5–0.7% conversion)

**Wartość:** "W końcu mogę zobaczyć, które kategorie mają największy ruch i kto w nich dominuje."

**Monetyzacja:**
- Darmowa wersja z CSV exportem
- $9/m Pro plan — zapis danych historycznych + porównanie między dniami

---

### ETAP 2: Intelligence (1 → 10) | 2–3 miesiące

**Cel:** Pokazywać wnioski, a nie dane

**Zakres:**
- 📈 **Trend Detection**
  - Wykresy "views growth / category", "position change / template"
  - Raport "Top 10 templates gaining views this week"
- 🧮 **New Metrics**
  - **Opportunity Score** = (średni views / liczba szablonów) × CTR trend
  - **Revenue Potential** = estymowany na podstawie cen + views
- 🔔 **Watchlist & Alerts**
  - Obserwuj konkurenta lub kategorię
  - Powiadomienia: awans/spadek w rankingu, nowy szablon w kategorii, nowy template autora
- 📊 **History View** — Timeline zmian w pozycji, views, revenue

**Wartość:** "Nie muszę już zgadywać, co budować — Amonit pokazuje, gdzie rośnie popyt."

**Monetyzacja:**
- $19/m Pro plan — watchlist i metryki trendowe
- $49/m Team plan — raporty CSV + alerty mailowe + API access

---

### ETAP 3: Prediction & Automation (10 → 100) | 3–6 miesięcy

**Cel:** Dawać konkretne rekomendacje i przewidywać trendy

**Zakres:**
- 🧠 **AI Insight Engine**
  - Generuje zdania: "Category Real Estate grew 23% in views this month — while average template price rose by 14%."
  - "Templates with 6–8 pages perform 30% better in engagement."
- 🔮 **Predictive Analytics**
  - Model trenowany na danych historycznych → przewidywanie trendów per category
  - Automatyczna "Category Heatmap"
- 💌 **Weekly Digest**
  - Raport mailowy z 3 kluczowymi zmianami
  - "Your templates performance summary"


**Wartość:** "Amonit sam pokazuje mi, co będzie się sprzedawać w przyszłym miesiącu."

**Monetyzacja:**
- $79/m Pro+ plan — predictive dashboard + category forecasts
- $149/m Studio plan — multi-marketplace access + team seats + custom reports

---

## 📊 Kluczowe Metryki & Insighty

### Performance Insights (per category)

| Metryka | Insight | Akcja |
|---------|---------|-------|
| **Category growth** | "Views in Real Estate grew +26% last month, while average template price dropped 11% — demand rising, pricing pressure." | Stwórz nowy szablon Real Estate z mniejszą ceną wejścia |
| **Views-per-template ratio** | "AI Tools category has the highest engagement per template (4.3K views/template)." | Mniej konkurencji, lepsza widoczność — dobra nisza |
| **Revenue potential** | "Templates in Portfolio category generate ~2.3x higher estimated revenue than average." | Skup się na Portfolio — tam popyt spotyka płacących klientów |
| **Update frequency** | "Templates updated within last 3 weeks have +38% higher average rank." | Aktualizuj częściej, nawet kosmetycznie |

### Competition Insights (per creator)

| Metryka | Insight | Akcja |
|---------|---------|-------|
| **Templates per creator** | "Top 10 creators own 45% of marketplace views." | Twoja konkurencja to kilka dominujących twórców |
| **Rank movement** | "Your template Calisto gained 8 positions in 7 days — likely featured or trend-related." | Zidentyfikuj, co to spowodowało |
| **Average price** | "Creators with >5 templates tend to price 25% lower." | Duzi gracze optymalizują przez wolumen — wygraj unikalnością |

### Market Dynamics (macro level)

| Metryka | Insight | Akcja |
|---------|---------|-------|
| **Total marketplace views** | "Marketplace traffic grew +42% YoY, but number of templates doubled — competition intensifies." | Wybieraj rosnące nisze |
| **Difficulty vs Opportunity** | "Membership is oversaturated, while Events is emerging (low difficulty, high opportunity)." | Szukaj wczesnych trendów |
| **Launch rate** | "New templates dropped by 17% in the last 2 months — creators slowing down." | Dobra okazja, by się wybić |

### Behavioral Insights

| Metryka | Insight | Akcja |
|---------|---------|-------|
| **Your templates vs median** | "Your average template gets 2.1K views — market median is 3.4K." | Zwiększ page count lub popraw SEO tytułu |
| **Update impact** | "After last update, rank improved from #45 → #28." | Planuj cykliczne odświeżanie |
| **Watchlist changes** | "2 watched competitors lost >15% traffic last week." | Ich spadek to Twoja szansa |

### Strategic Insights

| Metryka | Insight | Akcja |
|---------|---------|-------|
| **Price vs Views correlation** | "Templates priced between $49–$79 achieve best balance." | Zoptymalizuj ceny |
| **Page count vs Performance** | "Optimal page count seems to be 7–10." | Projektuj w tym zakresie |
| **Feature keywords** | "Templates mentioning AI or Notion get +22% more clicks." | Używaj tych słów w tytule |

**Format Insight Block:**
```typescript
<InsightCard
  title="Real Estate category grew +26%"
  subtitle="Demand up, average price down"
  action="Consider creating a template priced under $79"
  trend="+26%"
  level="opportunity"
/>
```

---

## 🧱 Architektura Scrapera — Kluczowe Zasady

### Compliance & Safety
- **Rate limit:** 1 request / 1.2–1.8s (jittered), burst do 2/s dla HTML
- **Backoff:** Exponential (2^n × 1s, cap 60s) na HTTP 429/5xx
- **Circuit breaker:** >20% błędów w ostatnich 100 requestach → pause 10 min
- **UA string:** `Mozilla/5.0 (compatible; AmonitBot/1.0; +https://amonit.app/bot-info)`
- **Retry:** 3 próby per URL, potem `status=permanent_fail`

### Discovery Strategy
1. Seed kategorii przez Marketplace top "Templates" page
2. Na każdej kategorii: scroll/paginate do końca
3. Queue detail URLs; dedupe po slug
4. **Revisit cadence:**
   - Category pages: daily
   - Template detail: co 3 dni (staggered); daily dla watchlist
   - Creator pages: weekly

### Rendering Rules
- Preferuj static HTTP (GET) dla detail pages
- Playwright tylko gdy: category wymaga JS do pełnej listy, price/views widoczne tylko po hydracji
- Viewport: 1366×900, timezone UTC, disable images/video jeśli możliwe

### Data Model (normalized + history)

**Tables:**
- `categories` — slug, name, first_seen_at, last_seen_at
- `templates` — slug (unique), title, category_slug, creator_handle, is_active
- `template_snapshots` — time-series, append-only: views, pages, updated_label, price_cents, rank_in_category, captured_at
- `creators` — handle (pk), name, profile_url
- `creator_snapshots` — templates_count, captured_at
- `jobs_runs` — job_name, started_at, status, urls_fetched, urls_failed

**Why:** Clean facts (current entities) + history (snapshots) dla trendów i rank deltas.

### Incremental Updates
- Compute `page_hash = sha1(strip_html(main_section))`
- Jeśli hash niezmieniony → skip parse+store
- Store field-level deltas dla views, price, pages
- Re-calculate `rank_in_category` sortując dzisiejszą listę kategorii po views

### Derived Metrics
- **Category Volume** = sum of today's views per category
- **Difficulty** (dynamic) = quantile-based:
  - `difficulty_score = qnorm(templates_count) × 0.6 + qnorm(views_per_template) × 0.4`
  - Buckets: Low / Medium / High / Very High
- **Opportunity Score** (per category):
  - `O = normalized_growth × 0.5 + normalized_views_per_template × 0.3 + normalized_price_headroom × 0.2`

---

## 📅 Harmonogram (sugestia)

| Etap | Zakres | Czas | Cel |
|------|--------|------|-----|
| **Q4 2025** | Foundation MVP + Pro beta | 6–8 tyg | Ustabilizować scraper i dashboard |
| **Q1 2026** | Trendy, watchlist, metryki | 8–10 tyg | Zebrać dane do modelu AI |
| **Q2 2026** | Insight engine + raporty | 12 tyg | Wersja 2.0 z predykcjami |

---

## 🎯 Strategic Principles

### Co robić
- ✅ Buduj bazę danych i reputację przed monetyzacją
- ✅ Rób screenshoty trendów, wykresy, raporty → paliwo do marketingu na X
- ✅ Zmieniaj metryki w insighty — każdy wykres odpowiada na "so what?"
- ✅ Buduj mailing/community wokół Framer performance → potem SaaS

### Czego unikać
- ❌ Monetyzacja za wcześnie — najpierw lock-in przez wartość
- ❌ Tylko liczby — zawsze pokazuj dynamikę zmian (Δ +12%)
- ❌ Statyczne dane — zawsze pokazuj trend i kontekst

---

## 🌐 Dodatkowe Warstwy Wartości

| Warstwa | Funkcja | Przewaga |
|---------|---------|----------|
| **Public API** | Dostęp do danych z Framer Marketplace | Można zbudować integracje (np. wtyczki, boty) |
| **Community Reports** | Wspólne raporty trendów | Virality i social proof |
| **Creator Profiles** | Ranking autorów i analiz ich performance | Użyteczne dla agencji i klientów |
| **Affiliate Loop** | Z linkami do Framera | Możliwość revenue share |

---

## 🧭 TL;DR — Kluczowe Decyzje

1. **Nie monetyzuj za wcześnie** — zbuduj bazę danych i reputację, potem zrobisz produkt z lock-inem
2. **Rób screenshoty trendów** — paliwo do marketingu na X i newslettera
3. **Zmieniaj metryki w insighty** — każdy wykres powinien odpowiadać na "so what?"
4. **Buduj mailing/community** — wokół Framer performance, potem zmonetyzujesz przez SaaS

---

**Wersja:** 1.0  
**Ostatnia aktualizacja:** 2025-01-XX  
**Status:** Foundation (ETAP 1)

