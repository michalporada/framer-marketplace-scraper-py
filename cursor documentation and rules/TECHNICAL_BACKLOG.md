# Technical Backlog — Amonit

**Cel:** Zidentyfikować luki techniczne i przygotować plan implementacji funkcji generujących insighty, powiadomienia i analitykę dla twórców Framer Marketplace.

**Data:** 2025-01-XX  
**Status:** Foundation → Intelligence (ETAP 1 → ETAP 2)

---

## 📊 Analiza Obecnego Stanu

### ✅ Mocne Strony

#### 1. **Scraper — Solid Foundation**
- ✅ **Stabilny system scrapowania** z rate limiting, retry logic, checkpoint system
- ✅ **Wszystkie typy produktów** — templates, components, vectors, plugins
- ✅ **Normalizacja danych** — raw + normalized formaty (daty, statystyki)
- ✅ **Struktura danych** — Pydantic models z walidacją
- ✅ **Automatyzacja** — GitHub Actions workflow dla codziennego scrapowania
- ✅ **Error handling** — exponential backoff, circuit breaker patterns
- ✅ **Pozycje w kategoriach** — już zbierane dla templates (`category_positions`)

#### 2. **Data Collection — Kompletne**
- ✅ **Produkty** — wszystkie metadane (cena, views, pages, features, kategorie)
- ✅ **Twórcy** — profile, statystyki, social media
- ✅ **Kategorie** — struktura, produkty, opis
- ✅ **History tracking** — `scraped_at` timestamp w każdym produkcie

#### 3. **Infrastructure**
- ✅ **Checkpoint system** — resume capability
- ✅ **Logging** — structlog z structured logging
- ✅ **Metrics tracking** — podstawowe metryki scrapowania
- ✅ **Storage** — JSON/CSV file storage, gotowy setup do PostgreSQL

### ⚠️ Słabe Strony & Luki

#### 1. **Brak Time-Series Database**
- ❌ **Problem:** Dane zapisywane jako pliki JSON — brak historycznej analizy zmian
- ❌ **Brak:** `template_snapshots`, `creator_snapshots` — nie można śledzić trendów
- ❌ **Brak:** Delta tracking — nie wiemy, co się zmieniło między scrapami
- ❌ **Brak:** Rank history — nie można śledzić zmian pozycji w czasie

#### 2. **Brak Systemu Insights**
- ❌ **Brak:** Generowanie insightów z danych
- ❌ **Brak:** Obliczanie metryk pochodnych (Difficulty, Opportunity Score)
- ❌ **Brak:** Trend detection — growth rates, position changes
- ❌ **Brak:** Comparative analytics — porównanie z medianą, top performers

#### 3. **Brak Watchlist & Alerts**
- ❌ **Brak:** System obserwowania konkurentów/kategorii
- ❌ **Brak:** Alert engine — powiadomienia o zmianach
- ❌ **Brak:** User management — brak autentykacji, użytkowników
- ❌ **Brak:** Notification delivery — email/Slack/webhooks

#### 4. **Brak Dashboard/API**
- ❌ **Brak:** Frontend dashboard do prezentacji danych
- ❌ **Brak:** REST API do dostępu do danych
- ❌ **Brak:** Real-time updates — wszystko jest batch-based
- ❌ **Brak:** User interface — brak interfejsu dla użytkowników

#### 5. **Ograniczenia Scrapera**
- ⚠️ **Incremental updates:** Nie ma mechanizmu hash-based change detection (wymagane dla `page_hash`)
- ⚠️ **Revisit cadence:** Nie ma różnicowania częstotliwości scrapowania (watchlist vs normal)
- ⚠️ **Rank calculation:** `rank_in_category` nie jest automatycznie przeliczany przy każdym scrapie
- ⚠️ **Data deduplication:** Brak mechanizmu wykrywania duplikatów w czasie

---

## 🎯 Czy Scraper Jest Wystarczający?

### ✅ **TAK — dla długoterminowego zbierania danych**

**Dlaczego:**
1. **Stabilność** — rate limiting, retry logic, checkpoint system zapewniają ciągłość
2. **Kompletność** — zbiera wszystkie potrzebne dane (views, prices, categories, positions)
3. **Normalizacja** — dane są już znormalizowane, gotowe do analizy
4. **Automatyzacja** — GitHub Actions może działać codziennie przez miesiące

### ⚠️ **NIE — dla generowania insightów**

**Brakuje:**
1. **Time-series storage** — dane historyczne w strukturze umożliwiającej analizę trendów
2. **Change detection** — mechanizm wykrywania zmian między scrapami
3. **Derived metrics** — obliczanie Difficulty, Opportunity Score, growth rates
4. **Rank tracking** — automatyczne śledzenie zmian pozycji w czasie

---

## 🚀 Backlog Techniczny

### PRIORYTET 1: Time-Series Database & History Tracking

**Cel:** Zachować historię zmian, aby móc analizować trendy i generować insighty.

#### 1.1 Migracja do PostgreSQL z Time-Series Schema

**Zakres:**
- [ ] **Rozszerzyć schema** zgodnie z PRODUCT_ROADMAP.md:
  ```sql
  -- Tabele faktów (current state)
  CREATE TABLE categories (
    slug VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP
  );
  
  CREATE TABLE templates (
    slug VARCHAR(255) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    category_slug VARCHAR(255),
    creator_handle VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
  );
  
  CREATE TABLE creators (
    handle VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    profile_url TEXT
  );
  
  -- Time-series snapshots (append-only)
  CREATE TABLE template_snapshots (
    id SERIAL PRIMARY KEY,
    template_slug VARCHAR(255) REFERENCES templates(slug),
    views INTEGER,
    pages INTEGER,
    updated_label VARCHAR(100), -- "3mo ago"
    price_cents INTEGER,
    rank_in_category INTEGER,
    category_slug VARCHAR(255),
    captured_at TIMESTAMP NOT NULL,
    UNIQUE(template_slug, category_slug, captured_at)
  );
  
  CREATE TABLE creator_snapshots (
    id SERIAL PRIMARY KEY,
    creator_handle VARCHAR(255) REFERENCES creators(handle),
    templates_count INTEGER,
    captured_at TIMESTAMP NOT NULL,
    UNIQUE(creator_handle, captured_at)
  );
  
  CREATE TABLE jobs_runs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status VARCHAR(50), -- 'running', 'completed', 'failed'
    urls_fetched INTEGER DEFAULT 0,
    urls_failed INTEGER DEFAULT 0
  );
  ```

- [ ] **Migracja danych** — skrypt do importu istniejących JSON do PostgreSQL
- [ ] **Indexes** — optymalizacja zapytań time-series:
  ```sql
  CREATE INDEX idx_template_snapshots_captured_at ON template_snapshots(captured_at DESC);
  CREATE INDEX idx_template_snapshots_template_slug ON template_snapshots(template_slug);
  CREATE INDEX idx_template_snapshots_category ON template_snapshots(category_slug);
  ```

**Techniczne sugestie:**
- Użyć **Supabase** (PostgreSQL) — łatwe setup, auto-scaling
- Alternatywa: **TimescaleDB** extension dla PostgreSQL (specjalizacja w time-series)
- Storage layer: **SQLAlchemy ORM** + **alembic** dla migracji

**Szacowany czas:** 1-2 tygodnie

---

#### 1.2 Incremental Update System

**Zakres:**
- [ ] **Hash-based change detection:**
  ```python
  def compute_page_hash(html: str) -> str:
      """Compute SHA1 hash of main content section."""
      soup = BeautifulSoup(html, 'lxml')
      main_section = soup.find('main') or soup.find('body')
      # Strip scripts, styles, timestamps
      clean_html = strip_dynamic_content(main_section)
      return hashlib.sha1(clean_html.encode()).hexdigest()
  ```

- [ ] **Delta tracking:**
  ```python
  def detect_changes(current: Product, previous: Product) -> Dict[str, Any]:
      """Detect field-level changes between snapshots."""
      deltas = {}
      if current.stats.views.normalized != previous.stats.views.normalized:
          deltas['views_delta'] = current.stats.views.normalized - previous.stats.views.normalized
      if current.price != previous.price:
          deltas['price_delta'] = current.price - previous.price
      # ... more fields
      return deltas
  ```

- [ ] **Skip parsing jeśli hash niezmieniony:**
  ```python
  if page_hash == last_page_hash:
      logger.info("page_unchanged", url=url)
      return None  # Skip parse+store
  ```

**Szacowany czas:** 1 tydzień

---

#### 1.3 Rank Calculation & Tracking

**Zakres:**
- [ ] **Automatyczne przeliczanie ranków:**
  ```python
  def calculate_ranks(category_slug: str, snapshot_date: date) -> Dict[str, int]:
      """Calculate rank for each template in category based on views."""
      snapshots = db.query(TemplateSnapshot).filter(
          TemplateSnapshot.category_slug == category_slug,
          TemplateSnapshot.captured_at == snapshot_date
      ).order_by(TemplateSnapshot.views.desc()).all()
      
      ranks = {}
      for idx, snapshot in enumerate(snapshots, start=1):
          ranks[snapshot.template_slug] = idx
      return ranks
  ```

- [ ] **Rank delta tracking:**
  ```python
  def calculate_rank_delta(template_slug: str, category_slug: str, 
                          date1: date, date2: date) -> int:
      """Calculate position change between two dates."""
      rank1 = get_rank(template_slug, category_slug, date1)
      rank2 = get_rank(template_slug, category_slug, date2)
      return rank2 - rank1  # Negative = moved up, positive = moved down
  ```

**Szacowany czas:** 3-5 dni

---

### PRIORYTET 2: Insight Generation Engine

**Cel:** Transformować dane w czytelne insighty z akcjami dla użytkowników.

#### 2.1 Derived Metrics Calculator

**Zakres:**
- [ ] **Difficulty Score:**
  ```python
  def calculate_difficulty(category_slug: str) -> float:
      """Calculate category difficulty based on templates count and views/template."""
      templates_count = count_templates_in_category(category_slug)
      avg_views_per_template = calculate_avg_views(category_slug)
      
      # Quantile normalization
      templates_quantile = quantile_normalize(templates_count, all_categories)
      views_quantile = quantile_normalize(avg_views_per_template, all_categories)
      
      difficulty = templates_quantile * 0.6 + views_quantile * 0.4
      return difficulty
  ```

- [ ] **Opportunity Score:**
  ```python
  def calculate_opportunity_score(category_slug: str, days: int = 30) -> float:
      """Calculate opportunity score based on growth, views/template, price headroom."""
      growth = calculate_growth_rate(category_slug, days)
      views_per_template = calculate_avg_views_per_template(category_slug)
      price_headroom = calculate_price_headroom(category_slug)
      
      # Normalize each metric
      normalized_growth = normalize(growth, all_categories)
      normalized_views = normalize(views_per_template, all_categories)
      normalized_price = normalize(price_headroom, all_categories)
      
      opportunity = (normalized_growth * 0.5 + 
                     normalized_views * 0.3 + 
                     normalized_price * 0.2)
      return opportunity
  ```

- [ ] **Revenue Potential:**
  ```python
  def estimate_revenue(category_slug: str, conversion_rate: float = 0.006) -> float:
      """Estimate revenue potential based on views and average price."""
      total_views = sum_views_in_category(category_slug)
      avg_price = calculate_avg_price(category_slug)
      estimated_revenue = total_views * conversion_rate * avg_price
      return estimated_views
  ```

**Szacowany czas:** 1 tydzień

---

#### 2.2 Trend Detection

**Zakres:**
- [ ] **Growth rate calculation:**
  ```python
  def calculate_growth_rate(category_slug: str, metric: str, days: int = 30) -> float:
      """Calculate % growth rate for metric over time period."""
      current = get_latest_metric(category_slug, metric)
      previous = get_metric_at_date(category_slug, metric, 
                                    date.today() - timedelta(days=days))
      if previous == 0:
          return 0.0
      growth = ((current - previous) / previous) * 100
      return growth
  ```

- [ ] **Position change tracking:**
  ```python
  def get_position_changes(template_slug: str, days: int = 7) -> List[Dict]:
      """Get position changes for template across all categories."""
      changes = []
      for category in get_template_categories(template_slug):
          rank_delta = calculate_rank_delta(template_slug, category, 
                                           date.today() - timedelta(days=days),
                                           date.today())
          if rank_delta != 0:
              changes.append({
                  'category': category,
                  'delta': rank_delta,
                  'direction': 'up' if rank_delta < 0 else 'down'
              })
      return changes
  ```

- [ ] **Top gainers/losers:**
  ```python
  def get_top_gainers(category_slug: str, days: int = 7, limit: int = 10) -> List[Dict]:
      """Get top templates gaining views in category."""
      snapshots = get_snapshots_for_period(category_slug, days)
      gainers = []
      for template in get_templates_in_category(category_slug):
          views_delta = calculate_views_delta(template, snapshots)
          gainers.append({
              'template_slug': template,
              'views_delta': views_delta,
              'growth_percent': (views_delta / previous_views) * 100
          })
      return sorted(gainers, key=lambda x: x['views_delta'], reverse=True)[:limit]
  ```

**Szacowany czas:** 1 tydzień

---

#### 2.3 Insight Generator

**Zakres:**
- [ ] **Insight templates:**
  ```python
  INSIGHT_TEMPLATES = {
      'category_growth': {
          'pattern': "Category {category} grew {growth}% in views this {period}",
          'conditions': lambda data: data['growth'] > 20,
          'action': "Consider creating a template in {category} with competitive pricing"
      },
      'position_gain': {
          'pattern': "Your template {template} gained {positions} positions in {category}",
          'conditions': lambda data: data['positions'] > 5,
          'action': "Analyze what caused the improvement and replicate"
      },
      'competitor_new_template': {
          'pattern': "{competitor} added a new template in {category}",
          'conditions': lambda data: data['is_watched'] == True,
          'action': "Monitor their performance and pricing strategy"
      }
  }
  ```

- [ ] **Insight generation logic:**
  ```python
  def generate_insights(category_slug: str, user_context: Dict = None) -> List[Insight]:
      """Generate insights for category based on data analysis."""
      insights = []
      
      # Category growth insight
      growth = calculate_growth_rate(category_slug, 'views', days=30)
      if growth > 20:
          insights.append(Insight(
              title=f"Category {category_slug} grew +{growth:.0f}%",
              subtitle="Demand rising",
              action=f"Consider creating a template in {category_slug}",
              trend=f"+{growth:.0f}%",
              level="opportunity",
              metric="category_growth"
          ))
      
      # Difficulty vs Opportunity
      difficulty = calculate_difficulty(category_slug)
      opportunity = calculate_opportunity_score(category_slug)
      if opportunity > 0.7 and difficulty < 0.5:
          insights.append(Insight(
              title=f"{category_slug} is emerging",
              subtitle="Low difficulty, high opportunity",
              action="Enter this niche early",
              trend="Emerging",
              level="high_opportunity"
          ))
      
      return insights
  ```

**Szacowany czas:** 1-2 tygodnie

---

### PRIORYTET 3: Watchlist & Alerts System

**Cel:** Pozwolić użytkownikom obserwować konkurentów/kategorie i otrzymywać powiadomienia o zmianach.

#### 3.1 User Management & Authentication

**Zakres:**
- [ ] **User schema:**
  ```sql
  CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subscription_tier VARCHAR(50) DEFAULT 'free' -- 'free', 'pro', 'team'
  );
  ```

- [ ] **Authentication system:**
  - [ ] **FastAPI** z JWT authentication
  - [ ] **Password hashing** — bcrypt
  - [ ] **Email verification** — optional dla MVP
  - [ ] **OAuth** — Google/GitHub (opcjonalne)

**Techniczne sugestie:**
- **FastAPI** + **SQLAlchemy** + **JWT** (python-jose)
- Alternatywa: **Supabase Auth** — gotowe rozwiązanie

**Szacowany czas:** 1 tydzień

---

#### 3.2 Watchlist System

**Zakres:**
- [ ] **Watchlist schema:**
  ```sql
  CREATE TABLE watchlists (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    type VARCHAR(50) NOT NULL, -- 'creator', 'category', 'template'
    target_id VARCHAR(255) NOT NULL, -- creator_handle, category_slug, template_slug
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, type, target_id)
  );
  
  CREATE INDEX idx_watchlists_user ON watchlists(user_id);
  CREATE INDEX idx_watchlists_target ON watchlists(type, target_id);
  ```

- [ ] **Watchlist API endpoints:**
  ```python
  @router.post("/watchlist")
  async def add_to_watchlist(
      item: WatchlistItem,
      current_user: User = Depends(get_current_user)
  ):
      """Add creator/category/template to watchlist."""
      # Implementation
      
  @router.get("/watchlist")
  async def get_watchlist(
      current_user: User = Depends(get_current_user)
  ):
      """Get user's watchlist."""
      # Implementation
  ```

- [ ] **Watchlist-aware scraping:**
  ```python
  def get_scrape_priority(url: str) -> int:
      """Get scrape priority based on watchlist."""
      if is_in_watchlist(url):
          return 1  # High priority - scrape daily
      return 3  # Normal priority - scrape every 3 days
  ```

**Szacowany czas:** 1 tydzień

---

#### 3.3 Alert Engine

**Zakres:**
- [ ] **Alert rules schema:**
  ```sql
  CREATE TABLE alert_rules (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    watchlist_id INTEGER REFERENCES watchlists(id),
    rule_type VARCHAR(50) NOT NULL, -- 'new_template', 'position_change', 'views_drop'
    threshold_value INTEGER, -- e.g., position change > 5
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```

- [ ] **Alert detection:**
  ```python
  def check_alert_rules(snapshot: TemplateSnapshot, previous: TemplateSnapshot):
      """Check if snapshot triggers any alert rules."""
      alerts = []
      
      # Position change alert
      if previous.rank_in_category and snapshot.rank_in_category:
          delta = snapshot.rank_in_category - previous.rank_in_category
          rules = get_alert_rules('position_change', threshold=abs(delta))
          for rule in rules:
              if abs(delta) >= rule.threshold_value:
                  alerts.append(Alert(
                      user_id=rule.user_id,
                      type='position_change',
                      message=f"Template {snapshot.template_slug} moved {delta} positions",
                      data={'delta': delta, 'new_rank': snapshot.rank_in_category}
                  ))
      
      return alerts
  ```

- [ ] **Alert delivery:**
  ```python
  async def send_alerts(alerts: List[Alert]):
      """Send alerts via email/Slack/webhook."""
      for alert in alerts:
          user = get_user(alert.user_id)
          
          # Email notification
          if user.email_notifications_enabled:
              await send_email_alert(user.email, alert)
          
          # In-app notification (store in DB)
          await store_in_app_notification(alert)
  ```

**Techniczne sugestie:**
- **Email:** SendGrid, Resend, lub AWS SES
- **Slack:** Slack Webhook API
- **In-app:** Store notifications w DB, fetch via API

**Szacowany czas:** 1-2 tygodnie

---

### PRIORYTET 4: Dashboard & API

**Cel:** Prezentować dane i insighty w czytelny sposób dla użytkowników.

#### 4.1 REST API

**Zakres:**
- [ ] **FastAPI application structure:**
  ```
  src/
  ├── api/
  │   ├── __init__.py
  │   ├── main.py              # FastAPI app
  │   ├── dependencies.py       # Auth, DB session
  │   ├── routes/
  │   │   ├── auth.py          # Authentication endpoints
  │   │   ├── templates.py    # Template data endpoints
  │   │   ├── categories.py   # Category analytics
  │   │   ├── insights.py     # Insight generation
  │   │   ├── watchlist.py    # Watchlist management
  │   │   └── alerts.py       # Alert management
  │   └── models/
  │       ├── schemas.py      # Pydantic response models
  │       └── requests.py     # Request models
  ```

- [ ] **Key endpoints:**
  ```python
  # Templates
  GET /api/templates?category={slug}&sort=views&limit=50
  GET /api/templates/{slug}/history?days=30
  GET /api/templates/{slug}/insights
  
  # Categories
  GET /api/categories
  GET /api/categories/{slug}/analytics
  GET /api/categories/{slug}/insights
  GET /api/categories/{slug}/trends?metric=views&days=30
  
  # Insights
  GET /api/insights?category={slug}&type=opportunity
  GET /api/insights/personal?user_id={id}
  
  # Watchlist
  POST /api/watchlist
  GET /api/watchlist
  DELETE /api/watchlist/{id}
  
  # Alerts
  GET /api/alerts
  POST /api/alerts/rules
  ```

**Szacowany czas:** 2-3 tygodnie

---

#### 4.2 Frontend Dashboard (MVP)

**Zakres:**
- [ ] **Tech stack:**
  - **Next.js 14+** (App Router)
  - **TypeScript**
  - **Tailwind CSS** + **shadcn/ui**
  - **TanStack Query** (React Query) dla data fetching
  - **Recharts** lub **Chart.js** dla wykresów (opcjonalne)

- [ ] **Key pages:**
  ```
  /dashboard
    - Overview z top insights
    - Quick stats (total views, templates, categories)
  
  /categories
    - Lista kategorii z metrykami
    - Difficulty, Opportunity Score
    - Filtry i sortowanie
  
  /categories/[slug]
    - Szczegóły kategorii
    - Trend charts (opcjonalne)
    - Top templates
    - Insights dla kategorii
  
  /templates/[slug]
    - Szczegóły szablonu
    - History timeline
    - Position changes
    - Performance vs median
  
  /watchlist
    - Obserwowane kreatory/kategorie/szablony
    - Recent changes
    - Quick actions
  
  /insights
    - Wszystkie dostępne insighty
    - Filtry (type, category, priority)
    - Action items
  ```

- [ ] **Insight Card component:**
  ```tsx
  <InsightCard
    title="Real Estate category grew +26%"
    subtitle="Demand up, average price down"
    action="Consider creating a template priced under $79"
    trend="+26%"
    level="opportunity"
    metric="category_growth"
  />
  ```

**Szacowany czas:** 3-4 tygodnie

---

### PRIORYTET 5: Advanced Features (ETAP 3)

**Cel:** AI-powered insights, predictive analytics, weekly digest.

#### 5.1 AI Insight Engine

**Zakres:**
- [ ] **LLM integration:**
  ```python
  def generate_ai_insight(category_data: Dict, historical_data: List[Dict]) -> str:
      """Generate natural language insight using LLM."""
      prompt = f"""
      Analyze this Framer Marketplace category data:
      Category: {category_data['name']}
      Growth: {category_data['growth']}%
      Average price: ${category_data['avg_price']}
      Views per template: {category_data['views_per_template']}
      
      Generate a concise insight (1-2 sentences) explaining what this means
      and what action a creator should take.
      """
      
      response = openai.ChatCompletion.create(
          model="gpt-4",
          messages=[{"role": "user", "content": prompt}]
      )
      return response.choices[0].message.content
  ```

- [ ] **Pattern detection:**
  ```python
  def detect_patterns(category_slug: str) -> List[str]:
      """Detect patterns in category performance."""
      patterns = []
      
      # Page count correlation
      optimal_pages = find_optimal_page_count(category_slug)
      if optimal_pages:
          patterns.append(f"Templates with {optimal_pages} pages perform 30% better")
      
      # Price range correlation
      optimal_price_range = find_optimal_price_range(category_slug)
      if optimal_price_range:
          patterns.append(f"Templates priced ${optimal_price_range[0]}-${optimal_price_range[1]} achieve best balance")
      
      return patterns
  ```

**Techniczne sugestie:**
- **OpenAI API** (GPT-4) lub **Anthropic Claude**
- **Caching** — cache insights dla tej samej kategorii/data
- **Rate limiting** — kontrolować koszty API calls

**Szacowany czas:** 2-3 tygodnie

---

#### 5.2 Predictive Analytics

**Zakres:**
- [ ] **Time-series forecasting:**
  ```python
  from prophet import Prophet
  
  def predict_category_trend(category_slug: str, days_ahead: int = 30) -> Dict:
      """Predict category views trend using Prophet."""
      historical_data = get_historical_views(category_slug, days=90)
      
      df = pd.DataFrame({
          'ds': [d['date'] for d in historical_data],
          'y': [d['views'] for d in historical_data]
      })
      
      model = Prophet()
      model.fit(df)
      future = model.make_future_dataframe(periods=days_ahead)
      forecast = model.predict(future)
      
      return {
          'predicted_views': forecast['yhat'].iloc[-1],
          'confidence_interval': forecast[['yhat_lower', 'yhat_upper']].iloc[-1].to_dict(),
          'trend': 'increasing' if forecast['trend'].iloc[-1] > forecast['trend'].iloc[-2] else 'decreasing'
      }
  ```

- [ ] **Category heatmap:**
  ```python
  def generate_heatmap() -> Dict[str, Dict]:
      """Generate opportunity heatmap for all categories."""
      heatmap = {}
      for category in get_all_categories():
          opportunity = calculate_opportunity_score(category.slug)
          difficulty = calculate_difficulty(category.slug)
          heatmap[category.slug] = {
              'opportunity': opportunity,
              'difficulty': difficulty,
              'recommendation': get_recommendation(opportunity, difficulty)
          }
      return heatmap
  ```

**Szacowany czas:** 2-3 tygodnie

---

#### 5.3 Weekly Digest

**Zakres:**
- [ ] **Digest generator:**
  ```python
  def generate_weekly_digest(user_id: UUID) -> Dict:
      """Generate weekly digest email for user."""
      user = get_user(user_id)
      watchlist = get_watchlist(user_id)
      
      digest = {
          'top_insights': get_top_insights(user_id, limit=3),
          'watchlist_changes': get_watchlist_changes(watchlist, days=7),
          'category_trends': get_relevant_category_trends(user_id),
          'personal_performance': get_personal_performance(user_id) if user.creator_handle else None
      }
      
      return digest
  ```

- [ ] **Email template:**
  ```html
  <h1>Your Weekly Amonit Digest</h1>
  
  <h2>Top 3 Insights</h2>
  <!-- Insight cards -->
  
  <h2>Watchlist Updates</h2>
  <!-- Changes in watched items -->
  
  <h2>Category Trends</h2>
  <!-- Relevant category changes -->
  ```

- [ ] **Scheduled job:**
  ```python
  # Celery task lub GitHub Actions scheduled job
  @scheduled_task(cron="0 9 * * 1")  # Every Monday at 9 AM
  async def send_weekly_digests():
      """Send weekly digest to all users."""
      users = get_all_users_with_email_notifications()
      for user in users:
          digest = generate_weekly_digest(user.id)
          await send_email(user.email, digest)
  ```

**Szacowany czas:** 1-2 tygodnie

---

## 📋 Priorytetyzacja & Timeline

### Faza 1: Foundation (Miesiąc 1-2)
**Cel:** Przygotować infrastrukturę do generowania insightów

1. ✅ **Time-Series Database** (2 tygodnie)
   - Migracja do PostgreSQL
   - Schema z snapshots
   - Migracja istniejących danych

2. ✅ **Incremental Updates** (1 tydzień)
   - Hash-based change detection
   - Delta tracking

3. ✅ **Rank Calculation** (3-5 dni)
   - Automatyczne przeliczanie ranków
   - Rank history tracking

**Rezultat:** Mamy pełną historię zmian, możemy śledzić trendy

---

### Faza 2: Intelligence (Miesiąc 3-4)
**Cel:** Generować insighty i metryki pochodne

1. ✅ **Derived Metrics** (1 tydzień)
   - Difficulty, Opportunity Score, Revenue Potential

2. ✅ **Trend Detection** (1 tydzień)
   - Growth rates, position changes, top gainers

3. ✅ **Insight Generator** (1-2 tygodnie)
   - Template-based insight generation
   - Context-aware insights

**Rezultat:** Możemy generować czytelne insighty z akcjami

---

### Faza 3: User Features (Miesiąc 5-6)
**Cel:** Watchlist, alerts, dashboard

1. ✅ **User Management** (1 tydzień)
   - Authentication, user schema

2. ✅ **Watchlist System** (1 tydzień)
   - Watchlist API, watchlist-aware scraping

3. ✅ **Alert Engine** (1-2 tygodnie)
   - Alert rules, detection, delivery

4. ✅ **REST API** (2-3 tygodnie)
   - FastAPI endpoints dla wszystkich funkcji

5. ✅ **Frontend Dashboard** (3-4 tygodnie)
   - Next.js dashboard z insight cards

**Rezultat:** Użytkownicy mogą obserwować konkurentów i otrzymywać powiadomienia

---

### Faza 4: Advanced (Miesiąc 7-9)
**Cel:** AI insights, predictive analytics

1. ✅ **AI Insight Engine** (2-3 tygodnie)
   - LLM integration, pattern detection

2. ✅ **Predictive Analytics** (2-3 tygodnie)
   - Time-series forecasting, heatmap

3. ✅ **Weekly Digest** (1-2 tygodnie)
   - Email digest, scheduled jobs

**Rezultat:** Produkt gotowy do ETAP 3 z PRODUCT_ROADMAP.md

---

## 🔧 Techniczne Decyzje

### Database
- **PostgreSQL** (Supabase) — time-series friendly, relational, skalowalne
- **TimescaleDB** extension — opcjonalne dla zaawansowanych time-series queries

### Backend
- **FastAPI** — szybkie API, async, automatyczna dokumentacja
- **SQLAlchemy** — ORM dla PostgreSQL
- **Alembic** — migracje bazy danych

### Frontend
- **Next.js 14+** — App Router, Server Components, SEO-friendly
- **TypeScript** — type safety
- **shadcn/ui** — komponenty UI
- **TanStack Query** — data fetching i caching

### Infrastructure
- **Supabase** — PostgreSQL + Auth + Storage w jednym
- **Vercel** — hosting frontendu i API (Edge Functions)
- **GitHub Actions** — scheduled jobs (scraping, weekly digest)

### Monitoring
- **Sentry** — error tracking
- **PostHog** lub **Plausible** — analytics
- **Logtail** lub **Datadog** — log aggregation

---

## ❓ Pytania do Rozstrzygnięcia

1. **Database:** Czy użyć Supabase (łatwiejsze) czy własny PostgreSQL (więcej kontroli)?
2. **Authentication:** Supabase Auth (szybkie) czy własne rozwiązanie (więcej kontroli)?
3. **Email:** Który provider? (SendGrid, Resend, AWS SES)
4. **AI:** OpenAI GPT-4 czy Claude? Jaki budżet?
5. **Hosting:** Vercel (frontend + API) czy osobne serwery?
6. **Pricing:** Jak strukturyzować plany? (free, pro, team)
7. **API Rate Limits:** Jakie limity dla różnych planów?

---

## 📝 Notatki

- **Scraper jest wystarczający** — można go używać długoterminowo, potrzebuje tylko rozszerzeń (incremental updates, watchlist-aware scraping)
- **Insighty są kluczowe** — fokus na transformację danych w czytelne, actionable insights
- **Wykresy opcjonalne** — zgodnie z wymaganiami, ale warto mieć podstawowe dla trendów
- **Time-series jest fundamentem** — bez historii zmian nie można generować insightów

---

**Wersja:** 1.0  
**Ostatnia aktualizacja:** 2025-01-XX

