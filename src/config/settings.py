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
    timeout: int = 30  # seconds
    max_retries: int = 3

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text

    # Output Settings
    output_format: str = "json"  # json, csv, both
    data_dir: str = "data"

    # Database (optional)
    database_url: str = ""

    # Checkpoint & Resume
    checkpoint_enabled: bool = True
    checkpoint_file: str = "data/checkpoint.json"

    # GitHub Actions
    github_actions: bool = False

    # Scraping options - which types to scrape
    scrape_templates: bool = True
    scrape_components: bool = True
    scrape_vectors: bool = True
    scrape_plugins: bool = True  # New product type
    scrape_categories: bool = False  # Optional
    scrape_profiles: bool = False  # Optional

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
