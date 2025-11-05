# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added `.env.example` file with all environment variables documented
- Added `src/utils/constants.py` for centralized constant management
  - `PROGRESS_MILESTONES` - progress logging milestones
  - `PROGRESS_LOG_INTERVAL` - progress logging interval
  - Retry and HTTP configuration constants
- Added configuration validation in `Settings` class:
  - Field validators for `rate_limit`, `max_concurrent_requests`, `timeout`, `max_retries`
  - Validators for `log_level`, `log_format`, `output_format`
- Added `.pre-commit-config.yaml` with:
  - Black code formatter
  - Ruff linter and formatter
  - MyPy type checker
  - General file checks (trailing whitespace, end-of-file, YAML/JSON/TOML validation)
- Enhanced CI/CD workflow (`.github/workflows/ci.yml`):
  - Separated code quality checks and tests into separate jobs
  - Added Black formatting check
  - Added coverage threshold checking (60% minimum)
  - Added coverage report upload as artifact
  - Improved error messages and workflow structure
- Added test coverage configuration:
  - Coverage settings in `pyproject.toml` and `pytest.ini`
  - Coverage threshold: 60% minimum
  - Coverage reports: HTML, XML, and terminal output
  - Excluded test files and type checking code from coverage

### Changed
- Refactored `marketplace_scraper.py` to use constants from `constants.py`:
  - Replaced hard-coded milestone percentages with `PROGRESS_MILESTONES`
  - Replaced hard-coded progress interval (50) with `PROGRESS_LOG_INTERVAL`
- Updated `requirements.txt` to clarify that `pyproject.toml` is the single source of truth
- Enhanced `Settings` class with Pydantic `Field` validators for better validation
- Improved CI workflow to use `pip install -e ".[dev]"` instead of separate requirements files

### Fixed
- All imports are now at the top of files (PEP 8 compliance)
- Configuration validation now prevents invalid values (e.g., negative rate limits, zero timeouts)

### Documentation
- Added `CHANGELOG.md` to track project changes
- Updated `README.md` documentation (already existed)

## [0.1.0] - 2025-01-XX

### Added
- Initial release of Scraper V2
- Sitemap scraping with fallback to marketplace pages
- Product scraping (templates, components, vectors, plugins)
- Creator profile scraping
- Category scraping
- Checkpoint system for resuming scrapes
- File storage (JSON/CSV)
- Structured logging with structlog
- Retry logic with exponential backoff
- Rate limiting and concurrency control

[Unreleased]: https://github.com/yourusername/scraper-v2/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/scraper-v2/releases/tag/v0.1.0

