"""Configuration settings for the scraper using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, List
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Framer Marketplace URLs
    framer_base_url: str = "https://www.framer.com"
    marketplace_url: str = "https://www.framer.com/marketplace"
    sitemap_url: str = "https://www.framer.com/marketplace/sitemap.xml"
    main_sitemap_url: str = (
        "https://www.framer.com/sitemap.xml"  # Fallback if marketplace sitemap fails
    )
    robots_url: str = "https://www.framer.com/robots.txt"

    # Rate Limiting
    rate_limit: float = 1.0  # requests per second
    delay_between_requests: float = 1.0  # seconds
    max_concurrent_requests: int = 5

    # HTTP Settings
    timeout: int = 25  # seconds per request (20-30s range)
    max_retries: int = 5  # 5-6 retries with exponential backoff
    retry_initial_wait: float = 2.0  # Initial wait time in seconds
    retry_max_wait: float = 300.0  # Max wait time (5 minutes)
    retry_jitter: bool = True  # Add random jitter to retry delays

    # Global scraping timeout
    global_scraping_timeout: int = 900  # 15 minutes in seconds

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    log_file: str = "scraper.log"  # Log file name (saved in logs/ directory)

    # Output Settings
    output_format: str = "both"  # json, csv, both
    data_dir: str = "data"

    # Database (optional)
    database_url: str = ""

    # Checkpoint & Resume
    checkpoint_enabled: bool = True
    checkpoint_file: str = "data/checkpoint.json"

    # Sitemap cache
    sitemap_cache_enabled: bool = True
    sitemap_cache_file: str = "data/sitemap_cache.xml"
    sitemap_cache_max_age: int = 3600  # 1 hour in seconds
    sitemap_cache_max_age_on_502: int = 86400  # 24 hours for 502 errors (CloudFront issues)
    use_cache_on_502: bool = True  # Use cache even for 502 errors (CloudFront problem, not origin)

    # GitHub Actions
    github_actions: bool = False

    # Alerting
    webhook_url: str = ""  # Webhook URL for alerts (Slack, Discord, etc.)
    alert_on_consecutive_failures: bool = (
        True  # Alert if two consecutive runs fail with upstream errors
    )

    # Scraping options - which types to scrape
    scrape_templates: bool = True
    scrape_components: bool = True
    scrape_vectors: bool = True
    scrape_plugins: bool = True  # New product type
    scrape_categories: bool = True  # Optional
    scrape_profiles: bool = False  # Optional

    # Data validation thresholds
    min_urls_threshold: int = 50  # Minimum URLs required from sitemap to proceed
    min_products_scraped: int = 0  # Minimum products scraped to allow export/DB write

    @property
    def base_url(self) -> str:
        """Alias for framer_base_url."""
        return self.framer_base_url

    @property
    def data_path(self) -> Path:
        """Get Path object for data directory."""
        return Path(self.data_dir)

    @property
    def checkpoint_path(self) -> Path:
        """Get Path object for checkpoint file."""
        return Path(self.checkpoint_file)

    def get_product_types(self) -> List[str]:
        """Get list of product types to scrape based on settings."""
        types = []
        if self.scrape_templates:
            types.append("template")
        if self.scrape_components:
            types.append("component")
        if self.scrape_vectors:
            types.append("vector")
        if self.scrape_plugins:
            types.append("plugin")
        return types

    def get_selectors(self) -> Dict[str, str]:
        """Get CSS selectors for HTML parsing."""
        return {
            # Product card selectors (from marketplace list)
            "product_card": "div.card-module-scss-module__P62yvW__card",
            "product_link": "a.card-module-scss-module__P62yvW__images",
            "product_name": "a.text-h6",
            "product_price": "div.card-module-scss-module__P62yvW__normalMeta span",
            "creator_link": "div.card-module-scss-module__P62yvW__hoverMeta a[href^='/@']",
            "product_image": "img.card-module-scss-module__P62yvW__image",
            "product_hover_image": "img.card-module-scss-module__P62yvW__hoverImage",
            "product_type": "span.card-module-scss-module__P62yvW__capitalize",
            "workshop_badge": "button.card-module-scss-module__P62yvW__badge",
        }

    def get_default_user_agents(self) -> List[str]:
        """Get default user agents for rotation."""
        return [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]


# Global settings instance
settings = Settings()
