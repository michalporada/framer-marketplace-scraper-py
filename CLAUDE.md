# CLAUDE.md - AI Assistant Guide

**Last Updated**: 2026-01-13
**Project**: Framer Marketplace Scraper
**Python Version**: 3.11+

This document provides comprehensive guidance for AI assistants (like Claude, GPT-4, etc.) working on this codebase. It explains the project structure, architecture patterns, conventions, and best practices to help you work effectively and maintain code quality.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Design Philosophy](#architecture--design-philosophy)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [Development Workflow](#development-workflow)
6. [Key Conventions](#key-conventions)
7. [Working with the Codebase](#working-with-the-codebase)
8. [Common Tasks](#common-tasks)
9. [Testing Strategy](#testing-strategy)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

---

## Project Overview

### What is this project?

This is an advanced web scraper for the Framer Marketplace that collects data about:
- **Products**: Templates, Components, Vectors, and Plugins
- **Creators**: User profiles with social media and product statistics
- **Categories**: Product categories and their metadata

The system includes:
- **Scraper** (Python): Async web scraping with checkpoint/resume capability
- **API** (FastAPI): RESTful API for accessing scraped data
- **Database** (PostgreSQL/Supabase): Product history tracking and trend analysis
- **Frontend** (Next.js): Dashboard for data visualization (separate repo)

### Key Features

- ✅ Async web scraping with rate limiting
- ✅ Checkpoint system for resumable scraping
- ✅ Product history tracking for trend analysis
- ✅ FastAPI REST API with caching
- ✅ GitHub Actions automation (daily scraping)
- ✅ Data normalization (raw + normalized formats)
- ✅ Type-safe data validation with Pydantic v2

### Tech Stack

**Backend**: Python 3.11+, httpx (async), BeautifulSoup4, Pydantic v2
**API**: FastAPI, SQLAlchemy, cachetools
**Storage**: JSON/CSV files, PostgreSQL (Supabase)
**Automation**: GitHub Actions
**Tools**: structlog, tenacity, fake-useragent, tqdm

---

## Architecture & Design Philosophy

### Core Principles

#### 1. **"Option B" Data Normalization**

All dates and statistics are stored in **two formats**:
- `raw`: Original format from HTML (e.g., "5 months ago", "19.8K Views")
- `normalized`: Standardized format (ISO 8601 dates, integer statistics)

```json
{
  "views": {
    "raw": "19.8K Views",
    "normalized": 19800
  },
  "published_date": {
    "raw": "5 months ago",
    "normalized": "2024-10-15T00:00:00Z"
  }
}
```

**Why?** Provides flexibility in analysis and enables verification of source data.

#### 2. **Type Safety First**

- All data models use **Pydantic v2** with full type hints
- Type hints are **mandatory** throughout the codebase
- Validation happens at data boundaries (scraping → parsing → storage)

#### 3. **Async Throughout**

- Full async/await implementation with `asyncio`
- Async context managers for resource management
- Semaphore-based concurrency control (15 concurrent requests)
- Non-blocking I/O with `httpx` and `aiofiles`

#### 4. **Graceful Degradation**

- Continue on individual failures, track errors
- Checkpoint system enables resume after interruption
- Fallback strategies (e.g., cached sitemap on 502 errors)
- Error aggregation by type and URL

#### 5. **Separation of Concerns**

```
Scraper → Parser → Model → Storage
   ↓         ↓       ↓        ↓
 Fetch    Extract  Validate  Persist
  HTML     Data     Data      Data
```

Each layer has a single, well-defined responsibility.

### Design Patterns

#### **Observer Pattern** - Metrics Tracking
```python
from src.utils.metrics import get_metrics

metrics = get_metrics()  # Singleton
metrics.record_product_scraped()
metrics.log_summary()
```

#### **Factory Pattern** - Utility Singletons
```python
get_logger(__name__)      # Logger factory
get_rate_limiter()        # Rate limiter singleton
get_metrics()             # Metrics singleton
```

#### **Strategy Pattern** - Type-Specific Parsing
Different product types have different parsing strategies:
- Templates: pages + views
- Plugins: version + users + changelog
- Components: installs
- Vectors: users + views + vectors count

#### **Repository Pattern** - Storage Abstraction
```python
# FileStorage and DatabaseStorage provide consistent interfaces
storage.save_product(product)
storage.save_products_batch(products)
```

#### **Async Context Managers** - Resource Cleanup
```python
async def __aenter__(self):
    self.client = httpx.AsyncClient(timeout=settings.timeout)
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb):
    if self.client:
        await self.client.aclose()
```

---

## Project Structure

```
framer-marketplace-scraper-py/
├── src/                         # Core application code
│   ├── config/                  # Configuration & settings
│   │   └── settings.py          # Pydantic settings (env vars)
│   ├── models/                  # Pydantic data models
│   │   ├── product.py           # Product model (with nested Stats/Metadata)
│   │   ├── creator.py           # Creator/profile model
│   │   └── category.py          # Category model
│   ├── scrapers/                # Web scraping components
│   │   ├── marketplace_scraper.py   # Main orchestrator
│   │   ├── sitemap_scraper.py       # Sitemap fetching & parsing
│   │   ├── product_scraper.py       # Product page scraping
│   │   ├── creator_scraper.py       # Creator profile scraping
│   │   └── category_scraper.py      # Category scraping
│   ├── parsers/                 # HTML parsing logic
│   │   ├── product_parser.py    # Product data extraction
│   │   ├── creator_parser.py    # Creator data extraction
│   │   └── category_parser.py   # Category data extraction
│   ├── storage/                 # Data persistence
│   │   ├── file_storage.py      # JSON/CSV file operations
│   │   └── database.py          # PostgreSQL/Supabase operations
│   ├── utils/                   # Utility modules
│   │   ├── logger.py            # Structured logging (structlog)
│   │   ├── rate_limiter.py      # Rate limiting logic
│   │   ├── retry.py             # Retry with exponential backoff
│   │   ├── normalizers.py       # Data normalization functions
│   │   ├── checkpoint.py        # Checkpoint/resume system
│   │   └── metrics.py           # Metrics tracking
│   └── main.py                  # Entry point
├── api/                         # FastAPI application
│   ├── main.py                  # FastAPI app initialization
│   ├── cache.py                 # Caching utilities (TTLCache)
│   ├── dependencies.py          # Dependency injection
│   └── routes/                  # API route handlers
│       ├── products.py          # Product endpoints
│       ├── creators.py          # Creator endpoints
│       └── metrics.py           # Metrics endpoints
├── tests/                       # Unit & integration tests
│   ├── test_models/
│   ├── test_parsers/
│   ├── test_scrapers/
│   └── test_utils/
├── scripts/                     # Utility scripts
│   ├── export_data.py           # CSV export script
│   ├── setup_db.py              # Database setup
│   ├── sync_json_to_db.py       # Sync JSON → DB
│   └── sync_existing_to_history.py  # Migrate to history
├── data/                        # Scraped data (gitignored)
│   ├── products/                # Product JSON files
│   │   ├── templates/
│   │   ├── components/
│   │   ├── vectors/
│   │   └── plugins/
│   ├── creators/                # Creator JSON files ({username}.json)
│   ├── categories/              # Category data
│   ├── exports/                 # CSV exports
│   └── checkpoint.json          # Resume state
├── docs/                        # Technical documentation
│   ├── API_ENDPOINTS_LIST.md
│   ├── DEPLOYMENT_PLAN.md
│   └── ...
├── cursor_rules/                # AI assistant guidelines
│   ├── project.md               # Project philosophy
│   ├── scraper.md               # Scraper-specific rules
│   ├── api.md                   # API development rules
│   └── dev_workflow.md          # Git workflow
├── .github/workflows/           # CI/CD pipelines
│   ├── ci.yml                   # Linting, testing, type checking
│   ├── scrape.yml               # Scheduled daily scraping
│   └── sync_to_db.yml           # Sync data to database
├── frontend/                    # Next.js dashboard (separate)
├── .env.example                 # Environment variable template
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml               # Project metadata & tool config
├── .pre-commit-config.yaml      # Pre-commit hooks
└── README.md                    # User-facing documentation
```

### Key Files Reference

| File | Purpose | Line Reference |
|------|---------|----------------|
| `src/main.py` | Entry point, CLI argument parsing | [Link](src/main.py:1) |
| `src/scrapers/marketplace_scraper.py` | Main orchestrator, batch scraping | [Link](src/scrapers/marketplace_scraper.py:1) |
| `src/parsers/product_parser.py` | Product HTML parsing logic | [Link](src/parsers/product_parser.py:1) |
| `src/storage/database.py` | Database operations, history tracking | [Link](src/storage/database.py:1) |
| `src/config/settings.py` | Configuration management | [Link](src/config/settings.py:1) |
| `api/main.py` | FastAPI app, CORS, health checks | [Link](api/main.py:1) |
| `api/routes/products.py` | Product API endpoints | [Link](api/routes/products.py:1) |

---

## Core Components

### 1. Configuration (`src/config/settings.py`)

**Pattern**: Pydantic Settings with environment variable loading

```python
from src.config.settings import settings

# Access configuration
settings.rate_limit          # 2.0 (requests per second)
settings.max_concurrent_requests  # 15
settings.timeout             # 12 seconds
settings.max_retries         # 3
settings.checkpoint_enabled  # True/False
```

**Key Settings**:
- `RATE_LIMIT`: Requests per second (default: 2.0, optimized from 1.0)
- `MAX_CONCURRENT_REQUESTS`: Concurrent scraping tasks (default: 15)
- `TIMEOUT`: Per-request timeout in seconds (default: 12s)
- `MAX_RETRIES`: Retry attempts (default: 3)
- `GLOBAL_SCRAPING_TIMEOUT`: Overall timeout (default: 0 = disabled)
- `SCRAPE_TEMPLATES`, `SCRAPE_COMPONENTS`, etc.: Product type toggles
- `DATABASE_URL`: PostgreSQL/Supabase connection string

**Note**: Currently, only `SCRAPE_TEMPLATES=true` is enabled. Components, vectors, and plugins are disabled.

### 2. Models (`src/models/`)

**Pattern**: Pydantic v2 with nested models and type hints

#### Product Model Structure
```python
Product
├── id: str
├── url: str
├── name: str
├── type: str (template/component/vector/plugin)
├── stats: ProductStats
│   ├── views: NormalizedStatistic | None
│   ├── pages: NormalizedStatistic | None
│   ├── users: NormalizedStatistic | None
│   ├── installs: NormalizedStatistic | None
│   ├── vectors: NormalizedStatistic | None
│   └── version: str | None
├── metadata: ProductMetadata
│   ├── creator_name: str
│   ├── creator_url: str
│   ├── price: NormalizedPrice
│   ├── published_date: NormalizedDate
│   ├── last_updated: NormalizedDate | None
│   └── description: str | None
├── features: ProductFeatures
│   ├── categories: list[str]
│   ├── tags: list[str]
│   └── attributes: dict[str, Any]
└── media: ProductMedia
    ├── thumbnail: str | None
    ├── images: list[str]
    └── video: str | None
```

#### Normalized Types
```python
class NormalizedStatistic(BaseModel):
    raw: str                    # "19.8K Views"
    normalized: int             # 19800

class NormalizedDate(BaseModel):
    raw: str                    # "5 months ago"
    normalized: str             # "2024-10-15T00:00:00Z" (ISO 8601)

class NormalizedPrice(BaseModel):
    raw: str                    # "$49"
    normalized: float           # 49.0
    currency: str               # "USD"
```

### 3. Scrapers (`src/scrapers/`)

#### Hierarchy
```
MarketplaceScraper (orchestrator)
  ├── SitemapScraper          # Fetch product URLs from sitemap.xml
  ├── ProductScraper          # Scrape individual product pages
  ├── CreatorScraper          # Scrape creator profiles
  └── CategoryScraper         # Scrape category pages (optional)
```

#### MarketplaceScraper (`marketplace_scraper.py`)

**Responsibilities**:
- Orchestrates the entire scraping process
- Manages concurrency with semaphore (15 concurrent tasks)
- Implements checkpoint/resume capability
- Handles deduplication
- Tracks metrics and progress

**Key Methods**:
```python
async with MarketplaceScraper() as scraper:
    await scraper.scrape(limit=None, product_types=None)
    await scraper.scrape_creators(limit=None)
    await scraper.scrape_categories(limit=None)
```

**Checkpoint System**:
- Saves progress to `data/checkpoint.json`
- Tracks processed URLs and failed URLs
- Enables resume after interruption

**Sitemap Refresh Strategy**:
- If cache is stale (>6h), attempts refresh at milestones (25%, 50%, 75%, 100%)
- New products discovered are scraped in background (non-blocking)
- Uses asyncio.Lock to prevent concurrent refresh attempts

#### SitemapScraper (`sitemap_scraper.py`)

**Responsibilities**:
- Fetch and parse `sitemap.xml`
- Filter URLs by product type
- Cache sitemap for fallback

**Retry Strategy** (Fibonacci sequence):
```
Attempt 1: 0s
Attempt 2: 1s
Attempt 3: 1s (2s total)
Attempt 4: 2s (4s total)
Attempt 5: 3s (7s total)
...
Attempt 15: 377s (~16.4 min total)
```

**Fallback**: Uses cached sitemap (TTL: 1 hour, 6 hours for 502 errors)

**URL Filtering**:
- Templates: `/marketplace/templates/{name}/`
- Components: `/marketplace/components/{name}/`
- Vectors: `/marketplace/vectors/{name}/`
- Plugins: `/marketplace/plugins/{name}/`

#### ProductScraper (`product_scraper.py`)

**Responsibilities**:
- Fetch HTML for individual product pages
- Call ProductParser to extract data
- Handle retries and rate limiting

**Type Detection**:
1. From URL (primary)
2. From HTML structure (fallback)
3. From Next.js JSON data (if available)

### 4. Parsers (`src/parsers/`)

**Pattern**: Pure HTML → Model conversion (no I/O)

#### ProductParser (`product_parser.py`)

**Key Extraction Methods**:
- `_extract_product_stats()`: Type-specific statistics
- `_extract_metadata()`: Creator, price, dates
- `_extract_categories()`: Multiple categories supported
- `_extract_features()`: Tags and attributes
- `_extract_media()`: Thumbnail, images, video
- `_extract_json_data()`: Next.js SSR data from `<script id="__NEXT_DATA__">`

**Next.js Data Extraction**:
```python
# Extract JSON from <script id="__NEXT_DATA__" type="application/json">
json_data = parser._extract_json_data(soup)
# Used for: avatars, social media, install counts, etc.
```

**Performance Optimizations**:
- Limited CSS selector iterations (first 3 elements)
- Cached BeautifulSoup selectors
- Early returns on missing data

### 5. Storage (`src/storage/`)

#### FileStorage (`file_storage.py`)

**Pattern**: Async file operations with `aiofiles`

```python
from src.storage.file_storage import FileStorage

storage = FileStorage()

# Save single product
await storage.save_product(product)

# Save batch
await storage.save_products_batch(products)

# Export to CSV
await storage.export_to_csv(output_path, product_type=None)

# Creator-specific
await storage.save_creator(creator)
await storage.export_creators_to_csv(output_path)
```

**Organization**:
- Products: `data/products/{type}/{id}.json`
- Creators: `data/creators/{username}.json`
- Categories: `data/categories/{name}.json`

#### DatabaseStorage (`database.py`)

**Pattern**: SQLAlchemy with NullPool (serverless-friendly)

**Key Features**:
- **Upsert**: `INSERT ... ON CONFLICT DO UPDATE`
- **History Tracking**: Every save appends to `product_history` table
- **Batch Operations**: Transactions with chunking (>1000 items)
- **Prepared Statements**: SQL injection protection
- **Connection Pooling**: NullPool for Railway deployment

**Tables**:
- `products`: Latest product data (upserted)
- `product_history`: Full history with `scraped_at` timestamp
- `creators`: Creator profiles

**Example**:
```python
from src.storage.database import DatabaseStorage

db = DatabaseStorage()

# Save with history
await db.save_product(product)  # Updates products + appends to product_history

# Batch save
await db.save_products_batch(products)  # Transactional with history

# Query history
history = await db.get_product_history(product_id, limit=10)
```

### 6. Utilities (`src/utils/`)

#### Logger (`logger.py`)

**Pattern**: Structured logging with `structlog`

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Structured logging with context
logger.info("product_scraped",
    product_id=product.id,
    product_type=product.type,
    duration=elapsed_time
)

# Error logging
logger.error("scraping_failed",
    url=url,
    error=str(e),
    error_type=type(e).__name__,
    retry_count=retry
)
```

**Log Levels**:
- `INFO`: Normal operations
- `WARNING`: Non-critical issues (e.g., product not found)
- `ERROR`: Critical failures requiring attention

#### RateLimiter (`rate_limiter.py`)

**Pattern**: Token bucket with randomization

```python
from src.utils.rate_limiter import get_rate_limiter

limiter = get_rate_limiter()

# Wait before request
wait_time = await limiter.wait()
response = await client.get(url)
```

**Features**:
- Randomization: 0.5x-2x base delay (prevents patterns)
- Configurable rate: `settings.rate_limit` (default: 2.0 req/s)

#### Retry Logic (`retry.py`)

**Pattern**: Exponential backoff + jitter (tenacity)

```python
from src.utils.retry import retry_async

result = await retry_async(
    fetch_function,
    max_retries=3,
    initial_wait=2.0,
    max_wait=300.0  # 5 minutes
)
```

**Features**:
- Exponential backoff: `initial_wait * 2^attempt`
- Jitter: Random 0-20% variation
- Max wait: 5 minutes per retry

#### Metrics (`metrics.py`)

**Pattern**: Singleton metrics tracker

```python
from src.utils.metrics import get_metrics

metrics = get_metrics()
metrics.start()
metrics.record_product_scraped()
metrics.record_request(wait_time=1.5)
metrics.record_product_failed(error_type="TimeoutError", url=url)
metrics.log_summary()  # End of scraping
```

**Tracked Metrics**:
- Products scraped/failed
- Total requests
- Rate limiting wait time
- Error counts by type
- Success rate
- Scraping duration

**Output**: `data/metrics.log` (JSON Lines format)

---

## Development Workflow

### Git Workflow

#### Branch Strategy

- `main`: Production-ready code (protected)
- `feature/{name}`: New features (e.g., `feature/add-product-filter`)
- `fix/{name}`: Bug fixes (e.g., `fix/rate-limiting-bug`)
- `refactor/{name}`: Code refactoring

#### Commit Message Convention

**Format**: `{type}: {description}`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring (no behavior change)
- `chore`: Build/config changes
- `docs`: Documentation updates
- `test`: Test additions/changes

**Examples**:
```
feat: add product filter by type
fix: handle timeout errors in scraper
refactor: simplify product parser logic
docs: update API documentation
test: add tests for product insights
```

**Breaking Changes**:
```
feat: change API response format

BREAKING CHANGE: API now returns normalized data by default.
Update clients to handle new format.
```

### Pre-commit Hooks (MANDATORY)

**Install hooks**:
```bash
pre-commit install
```

**What hooks do**:
- Fix unused imports (`ruff --fix`)
- Format code (`ruff-format`, `black`)
- Check YAML, JSON, TOML syntax
- Remove trailing whitespace
- Detect merge conflicts
- Check for large files (>1000KB)
- Type check with `mypy` (non-blocking)

**If hooks make changes**:
```bash
# Hooks modify files, you must re-stage
git add .
git commit -m "fix: your message"
```

**Manual run**:
```bash
pre-commit run --all-files  # Check all files
pre-commit run              # Check staged files only
```

### Local Development Setup

#### 1. Environment Setup
```bash
# Clone repo
git clone <repo-url>
cd framer-marketplace-scraper-py

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt        # Production
pip install -r requirements-dev.txt   # Development

# Install pre-commit hooks (MANDATORY)
pre-commit install
```

#### 2. Configuration
```bash
cp .env.example .env
# Edit .env with your configuration
```

**Required Variables**:
- `DATABASE_URL`: PostgreSQL connection string (if using database)
- `RATE_LIMIT`: Requests per second (default: 2.0)
- `SCRAPE_TEMPLATES`: Enable template scraping (default: true)

#### 3. Development Commands

```bash
# Run scraper
python -m src.main              # All products (templates only)
python -m src.main 10           # First 10 products
python -m src.main --templates-only 10
python -m src.main --creators-only
python -m src.main --categories-only

# Run tests
pytest                          # All tests
pytest --cov=src --cov-report=html  # With coverage

# Linting & formatting
ruff check .                    # Lint
ruff check . --fix              # Lint + fix
ruff format .                   # Format
black .                         # Format (alternative)

# Type checking
mypy src/                       # Type check

# Export data
python scripts/export_data.py --type template -o data/exports/templates.csv

# Database setup
python scripts/setup_db.py --db-type postgresql

# API server
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### CI/CD Pipeline

#### CI Workflow (`.github/workflows/ci.yml`)

**Triggers**: Push/PR to main

**Steps**:
1. Setup Python 3.11
2. Install dependencies (with pip cache)
3. Run pytest with coverage
4. Upload to Codecov
5. Lint with ruff
6. Format check with ruff
7. Type check with mypy (non-blocking)

#### Scrape Workflow (`.github/workflows/scrape.yml`)

**Triggers**:
- Scheduled: Daily at 2:00 UTC
- Manual: `workflow_dispatch`

**Features**:
- Resume from checkpoint (downloads from previous failed runs)
- Random jitter (0-60s) to avoid CloudFront edge issues
- Artifact uploads:
  - `scraped-data-{run_number}`: Dated backup (90 days retention)
  - `scraped-data-latest`: Most recent (7 days retention)
  - `scraper-logs`: Debug logs (7 days retention)
- Webhook notifications on failure
- Timeout: 360 minutes (6 hours)

#### Sync to DB Workflow (`.github/workflows/sync_to_db.yml`)

**Purpose**: Syncs scraped JSON data to Supabase database

---

## Key Conventions

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files | `snake_case` | `product_scraper.py` |
| Classes | `PascalCase` | `ProductScraper` |
| Functions | `snake_case` | `scrape_product()` |
| Variables | `snake_case` | `product_id` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_TTL` |
| Private methods | `_leading_underscore` | `_extract_stats()` |

### Import Organization

```python
# Standard library (alphabetical)
import asyncio
import json
from pathlib import Path

# Third-party packages (alphabetical)
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

# Local imports (alphabetical)
from src.config.settings import settings
from src.models.product import Product
from src.utils.logger import get_logger
```

### Code Style

**Line Length**: 100 characters (configured in `pyproject.toml`)

**Type Hints**: Mandatory for all functions
```python
def scrape_product(url: str, timeout: int = 30) -> Product | None:
    """Scrape product from URL.

    Args:
        url: Product URL
        timeout: Request timeout in seconds

    Returns:
        Product object or None if failed
    """
    ...
```

**Docstrings**: Google style
```python
def parse_statistics(html: str, product_type: str) -> dict[str, Any]:
    """Parse product statistics from HTML.

    Args:
        html: HTML content
        product_type: Type of product (template/component/vector/plugin)

    Returns:
        Dictionary of statistics with raw and normalized values

    Raises:
        ValueError: If product type is invalid
    """
    ...
```

### Error Handling Pattern

```python
try:
    result = await operation()
    logger.info("operation_success", result=result)
    return result
except SpecificError as e:
    logger.error("operation_failed",
        error=str(e),
        url=url,
        retry_count=retry
    )
    return None
except Exception as e:
    logger.error("unexpected_error",
        error=str(e),
        error_type=type(e).__name__
    )
    raise  # Re-raise unexpected errors
```

### Async Context Manager Pattern

```python
class Scraper:
    async def __aenter__(self):
        """Initialize resources."""
        self.client = httpx.AsyncClient(
            timeout=settings.timeout,
            follow_redirects=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources."""
        if self.client:
            await self.client.aclose()
```

---

## Working with the Codebase

### Before Starting Work

#### 1. Read Documentation
- `README.md` - User-facing documentation
- `CLAUDE.md` - This file (AI assistant guide)
- `docs/` - Technical documentation
- `cursor_rules/` - Domain-specific guidelines

#### 2. Understand Context
- What files are affected?
- What are the dependencies?
- Does this require documentation updates?

#### 3. Check Existing Tests
- Are there tests for the code you're changing?
- Do tests pass before your changes?
- Do you need to add new tests?

### During Work

#### 1. Maintain Consistency
- Follow existing patterns
- Don't introduce new libraries without justification
- Match the code style of surrounding code

#### 2. Test Locally
```bash
# Run affected tests
pytest tests/test_scrapers/test_product_scraper.py

# Run all tests
pytest

# Check linting
ruff check .

# Format code
ruff format .
```

#### 3. Use Structured Logging
```python
logger.info("event_name",
    product_id=product.id,
    duration=elapsed_time,
    status="success"
)
```

**Don't**:
```python
print(f"Scraped product {product.id}")  # ❌ No print statements
logger.info(f"Scraped product {product.id}")  # ❌ No f-strings in logs
```

### After Work

#### 1. Update Documentation (if needed)
- **Always ask user first** before updating documentation
- Document breaking changes
- Update examples if API changes

#### 2. Run Pre-commit Hooks
```bash
pre-commit run --all-files
```

#### 3. Commit with Conventions
```bash
git add .
git commit -m "feat: add product type filter"
```

#### 4. Create Pull Request
- Use PR template
- Ensure CI checks pass
- Request review

---

## Common Tasks

### Adding a New Product Type

**Example: Adding "Guides" product type**

#### 1. Update Settings (`src/config/settings.py`)
```python
class Settings(BaseSettings):
    # Existing types...
    scrape_guides: bool = Field(default=False, env="SCRAPE_GUIDES")
```

#### 2. Update Product Model (`src/models/product.py`)
```python
# Add to ProductType enum if exists, or update type validation
```

#### 3. Update SitemapScraper (`src/scrapers/sitemap_scraper.py`)
```python
def _filter_urls_by_type(self, urls: list[str]) -> dict[str, list[str]]:
    # Add guide URL pattern
    if "/marketplace/guides/" in url:
        filtered_urls["guide"].append(url)
```

#### 4. Update ProductParser (`src/parsers/product_parser.py`)
```python
def _extract_product_stats(self, soup: BeautifulSoup, product_type: str) -> ProductStats:
    if product_type == "guide":
        # Extract guide-specific stats
        ...
```

#### 5. Add Tests
```python
# tests/test_parsers/test_product_parser.py
def test_parse_guide_product():
    html = """..."""
    product = ProductParser.parse(html, url, "guide")
    assert product.type == "guide"
    # Assert guide-specific fields
```

### Adding a New API Endpoint

**Example: GET /api/products/top-rated**

#### 1. Add Route Handler (`api/routes/products.py`)
```python
@router.get("/top-rated")
async def get_top_rated_products(
    limit: int = Query(10, ge=1, le=100),
    product_type: str | None = Query(None),
    db = Depends(get_database)
) -> list[Product]:
    """Get top-rated products by views or installs."""
    # Implementation
    ...
```

#### 2. Update Database Storage (`src/storage/database.py`)
```python
async def get_top_rated_products(
    self,
    limit: int = 10,
    product_type: str | None = None
) -> list[Product]:
    """Query top-rated products from database."""
    query = """
        SELECT * FROM products
        WHERE ($1::text IS NULL OR type = $1)
        ORDER BY (stats->>'views')::int DESC
        LIMIT $2
    """
    # Execute query...
```

#### 3. Add Caching (`api/cache.py`)
```python
@cache_result(ttl=300, max_size=100)
async def get_top_rated_products_cached(*args, **kwargs):
    return await get_top_rated_products(*args, **kwargs)
```

#### 4. Update Documentation (`docs/API_ENDPOINTS_LIST.md`)
```markdown
### GET /api/products/top-rated

Returns top-rated products by views or installs.

**Query Parameters**:
- `limit` (int, optional): Number of products (default: 10, max: 100)
- `product_type` (str, optional): Filter by type

**Example**:
```bash
curl "https://api.example.com/api/products/top-rated?limit=20&product_type=template"
```
```

#### 5. Add Tests
```python
# tests/test_api/test_products.py
def test_top_rated_products(client):
    response = client.get("/api/products/top-rated?limit=5")
    assert response.status_code == 200
    assert len(response.json()) <= 5
```

### Debugging Scraping Issues

#### 1. Enable Debug Logging
```bash
LOG_LEVEL=DEBUG python -m src.main 5
```

#### 2. Check Checkpoint State
```bash
cat data/checkpoint.json | jq
```

#### 3. Test Single Product
```python
# scripts/test_single_product.py
import asyncio
from src.scrapers.product_scraper import ProductScraper

async def main():
    url = "https://www.framer.com/marketplace/templates/example/"
    async with ProductScraper() as scraper:
        product = await scraper.scrape(url)
        print(product.model_dump_json(indent=2))

asyncio.run(main())
```

#### 4. Inspect HTML
```python
import httpx
from bs4 import BeautifulSoup

url = "..."
response = httpx.get(url)
soup = BeautifulSoup(response.text, "lxml")

# Check for expected elements
print(soup.select("div.product-stats"))
```

#### 5. Clear Checkpoint (Force Re-scrape)
```bash
rm data/checkpoint.json
python -m src.main
```

---

## Testing Strategy

### Test Structure

```
tests/
├── test_models/              # Pydantic model validation
│   ├── test_product.py
│   └── test_creator.py
├── test_parsers/             # HTML parsing logic
│   ├── test_product_parser.py
│   └── test_creator_parser.py
├── test_scrapers/            # Scraper components
│   ├── test_sitemap_scraper.py
│   └── test_product_scraper.py
├── test_utils/               # Utility functions
│   ├── test_normalizers.py
│   └── test_rate_limiter.py
└── test_api/                 # API endpoints
    ├── test_products.py
    └── test_creators.py
```

### Test Markers

```python
import pytest

@pytest.mark.unit
def test_normalize_statistic():
    """Unit test - fast, no I/O."""
    ...

@pytest.mark.integration
async def test_scrape_product():
    """Integration test - involves I/O."""
    ...

@pytest.mark.slow
async def test_full_scraping_pipeline():
    """Slow test - full end-to-end."""
    ...
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_parsers/test_product_parser.py

# Specific test function
pytest tests/test_parsers/test_product_parser.py::test_parse_template

# Stop on first failure
pytest -x

# Verbose output
pytest -v

# Show print statements
pytest -s
```

### Writing Tests

#### Unit Test Example
```python
from src.utils.normalizers import normalize_statistic

def test_normalize_statistic_with_k_suffix():
    """Test normalizing statistics with K suffix."""
    result = normalize_statistic("19.8K Views")
    assert result == {"raw": "19.8K Views", "normalized": 19800}

def test_normalize_statistic_with_m_suffix():
    """Test normalizing statistics with M suffix."""
    result = normalize_statistic("1.2M Users")
    assert result == {"raw": "1.2M Users", "normalized": 1200000}
```

#### Async Test Example
```python
import pytest
from src.scrapers.product_scraper import ProductScraper

@pytest.mark.asyncio
async def test_scrape_product_success():
    """Test scraping a product successfully."""
    url = "https://www.framer.com/marketplace/templates/example/"

    async with ProductScraper() as scraper:
        product = await scraper.scrape(url)

    assert product is not None
    assert product.type == "template"
    assert product.stats.views.normalized > 0
```

#### Mocking External Requests
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_scrape_with_mocked_response():
    """Test scraping with mocked HTTP response."""
    mock_html = """<html>...</html>"""

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.text = mock_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        async with ProductScraper() as scraper:
            product = await scraper.scrape("https://example.com")

        assert product is not None
```

---

## Deployment

### Production Environments

#### 1. API (Railway)

**URL**: https://framer-marketplace-scraper-py-production.up.railway.app

**Configuration**:
- Platform: Railway
- Runtime: Python 3.11
- Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- Environment variables:
  - `DATABASE_URL`: Supabase connection string
  - `CORS_ORIGINS`: Frontend URL (Vercel)
  - `API_BASE_URL`: Railway URL

**Database**: Supabase PostgreSQL (connection pooling with NullPool)

#### 2. Frontend (Vercel)

**URL**: https://framer-marketplace-scraper-py.vercel.app

**Configuration**:
- Platform: Vercel
- Framework: Next.js
- Build command: `npm run build`
- Environment variables:
  - `NEXT_PUBLIC_API_URL`: Railway API URL

#### 3. Database (Supabase)

**Configuration**:
- PostgreSQL 14+
- Tables: `products`, `product_history`, `creators`
- Connection string in `DATABASE_URL`

#### 4. GitHub Actions (Scraping)

**Schedule**: Daily at 2:00 UTC

**Workflow**:
1. Checkout repo
2. Setup Python 3.11
3. Install dependencies
4. Download checkpoint (if exists)
5. Run scraper: `python -m src.main`
6. Upload artifacts (90 days retention)
7. Sync to database (Supabase)

**Artifacts**:
- `scraped-data-{run_number}`: Dated backup
- `scraped-data-latest`: Most recent run
- `scraper-logs`: Debug logs

### Deployment Checklist

#### Before Deployment

- [ ] All tests passing (`pytest`)
- [ ] Linting/formatting OK (`ruff check .`, `ruff format .`)
- [ ] Environment variables configured
- [ ] Database migrations applied (if any)
- [ ] API documentation updated
- [ ] Frontend API URL updated

#### After Deployment

- [ ] API health check: `GET /health`
- [ ] Database connectivity verified
- [ ] CORS headers working
- [ ] GitHub Actions running successfully
- [ ] Monitoring/logging working

---

## Troubleshooting

### Common Issues

#### 1. Scraping Failures

**Symptom**: Products fail to scrape with timeout errors

**Diagnosis**:
```bash
# Check logs
tail -f logs/scraper.log

# Check metrics
cat data/metrics.log | jq

# Test single product
python scripts/test_single_product.py
```

**Solutions**:
- Increase `TIMEOUT` in `.env` (default: 12s → try 20s)
- Decrease `RATE_LIMIT` (default: 2.0 → try 1.0)
- Decrease `MAX_CONCURRENT_REQUESTS` (default: 15 → try 10)

#### 2. Database Connection Errors

**Symptom**: `psycopg2.OperationalError: could not connect to server`

**Diagnosis**:
```bash
# Test connection
python -c "from src.storage.database import DatabaseStorage; db = DatabaseStorage(); print('OK')"
```

**Solutions**:
- Check `DATABASE_URL` format: `postgresql://user:pass@host:port/db`
- Verify Supabase connection string is correct
- Check firewall rules (Supabase allows all IPs by default)
- Test with `psql` directly: `psql $DATABASE_URL`

#### 3. GitHub Actions Failing

**Symptom**: Workflow fails with "No products scraped"

**Diagnosis**:
```bash
# Check workflow logs in GitHub Actions UI
# Look for errors in scraper output
```

**Solutions**:
- Check if sitemap is accessible: `curl https://www.framer.com/marketplace/sitemap.xml`
- Verify CloudFront isn't blocking (502 errors)
- Check if checkpoint is corrupted (delete artifact)
- Increase `GLOBAL_SCRAPING_TIMEOUT` if hitting timeout

#### 4. API Rate Limiting (429 Errors)

**Symptom**: Framer returns 429 Too Many Requests

**Diagnosis**:
```bash
# Check logs for 429 errors
grep "429" logs/scraper.log
```

**Solutions**:
- Decrease `RATE_LIMIT` in `.env` (e.g., 2.0 → 0.5)
- Increase `DELAY_BETWEEN_REQUESTS` (e.g., 1.0 → 2.0)
- Wait 5-10 minutes before retrying
- Consider rotating IP addresses (use proxy)

#### 5. Parsing Errors (Pydantic ValidationError)

**Symptom**: `pydantic.ValidationError: X validation errors for Product`

**Diagnosis**:
```bash
# Enable debug logging
LOG_LEVEL=DEBUG python -m src.main 5

# Inspect HTML structure
python scripts/inspect_html.py <product_url>
```

**Solutions**:
- Check if Framer changed HTML structure
- Update CSS selectors in `product_parser.py`
- Make fields optional if data isn't always present
- Add fallback extraction methods

#### 6. Pre-commit Hooks Failing

**Symptom**: Commit blocked by pre-commit hooks

**Diagnosis**:
```bash
# Run hooks manually to see errors
pre-commit run --all-files
```

**Solutions**:
```bash
# Fix linting errors
ruff check . --fix

# Format code
ruff format .

# Fix type errors
mypy src/

# Add fixed files
git add .
git commit -m "fix: address pre-commit issues"
```

### Performance Optimization

#### Slow Scraping

**Check**:
- Are you hitting rate limits? (check `data/metrics.log` for wait times)
- Is the timeout too high? (default: 12s)
- Are there many retries? (check error counts)

**Optimize**:
```bash
# Increase concurrency (default: 15)
MAX_CONCURRENT_REQUESTS=20

# Decrease timeout (default: 12s)
TIMEOUT=10

# Increase rate limit (default: 2.0, be careful!)
RATE_LIMIT=3.0
```

**Note**: Current production settings are optimized (RATE_LIMIT=2.0, MAX_CONCURRENT=15, TIMEOUT=12s)

#### Database Slow Queries

**Check**:
```sql
-- Check for missing indexes
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE tablename IN ('products', 'product_history', 'creators');

-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 10;
```

**Optimize**:
```sql
-- Add indexes
CREATE INDEX IF NOT EXISTS idx_products_type ON products(type);
CREATE INDEX IF NOT EXISTS idx_product_history_product_id ON product_history(product_id);
CREATE INDEX IF NOT EXISTS idx_product_history_scraped_at ON product_history(scraped_at DESC);
```

### Debug Mode

Enable debug mode for verbose output:

```bash
# Debug logging
LOG_LEVEL=DEBUG python -m src.main

# Debug with limited products
LOG_LEVEL=DEBUG python -m src.main 10

# Debug API
LOG_LEVEL=DEBUG uvicorn api.main:app --reload

# Debug tests
pytest -v -s
```

---

## Additional Resources

### Documentation

- **User Documentation**: `README.md`
- **API Documentation**: `docs/API_ENDPOINTS_LIST.md`
- **Deployment Guide**: `docs/DEPLOYMENT_PLAN.md`
- **Tech Stack**: `documentation_sources/STACK_TECHNICZNY.md`
- **Architecture**: `documentation_sources/PROPOZYCJA_ARCHITEKTURY.md`

### AI Assistant Guidelines

- **Project Philosophy**: `cursor_rules/project.md`
- **Scraper Rules**: `cursor_rules/scraper.md`
- **API Development**: `cursor_rules/api.md`
- **Development Workflow**: `cursor_rules/dev_workflow.md`
- **Metrics & Analytics**: `cursor_rules/metrics.md`

### External Links

- **Framer Marketplace**: https://www.framer.com/marketplace
- **Framer Robots.txt**: https://www.framer.com/robots.txt
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **httpx Documentation**: https://www.python-httpx.org/

---

## Summary: Key Points for AI Assistants

### Philosophy

1. **"Option B" Data Strategy**: Always preserve raw + normalized data
2. **Type Safety**: Pydantic models with full type hints
3. **Async All The Way**: Use async/await for I/O operations
4. **Graceful Degradation**: Continue on failures, track errors
5. **Resume Capability**: Checkpoint system for long-running scrapes

### Working Effectively

1. **Read docs first**: Check `docs/`, `cursor_rules/`, `CLAUDE.md`
2. **Follow patterns**: Match existing code style and architecture
3. **Test locally**: Run `pytest` before committing
4. **Structured logging**: Use context-rich logging, avoid print statements
5. **Pre-commit hooks**: Install and use them (`pre-commit install`)

### Common Patterns

- **Singleton Utilities**: `get_logger()`, `get_metrics()`, `get_rate_limiter()`
- **Async Context Managers**: For resource cleanup (HTTP clients, file handles)
- **Prepared Statements**: For all SQL queries (security + performance)
- **Batch Operations**: For database writes (with transactions)
- **Deduplication**: Track seen IDs/URLs to prevent duplicates

### Quick Navigation

| Component | File | Line |
|-----------|------|------|
| Entry Point | `src/main.py` | [Link](src/main.py:1) |
| Main Orchestrator | `src/scrapers/marketplace_scraper.py` | [Link](src/scrapers/marketplace_scraper.py:1) |
| Product Parser | `src/parsers/product_parser.py` | [Link](src/parsers/product_parser.py:1) |
| Database Storage | `src/storage/database.py` | [Link](src/storage/database.py:1) |
| Settings | `src/config/settings.py` | [Link](src/config/settings.py:1) |
| API Main | `api/main.py` | [Link](api/main.py:1) |

---

**Version**: 1.0
**Last Updated**: 2026-01-13
**Maintained By**: Project maintainers + AI assistants

For questions or improvements to this guide, please open an issue or PR on GitHub.
