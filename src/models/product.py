"""Pydantic model for product data."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl

from src.models.creator import Creator


class NormalizedDate(BaseModel):
    """Normalized date format (Option B - raw + normalized)."""

    raw: str = Field(..., description="Raw date format from HTML (e.g., '5 months ago', '3mo ago')")
    normalized: Optional[str] = Field(
        None, description="Normalized ISO 8601 format (e.g., '2024-10-15T00:00:00Z')"
    )


class NormalizedStatistic(BaseModel):
    """Normalized statistic format (Option B - raw + normalized)."""

    raw: str = Field(..., description="Raw statistic format from HTML (e.g., '19.8K Views', '1,200 Vectors')")
    normalized: Optional[int] = Field(None, description="Normalized integer value (e.g., 19800, 1200)")


class ProductStats(BaseModel):
    """Statistics for a product (different for different product types)."""

    # Templates: Pages + Views
    # Plugins: Version + Users
    # Components: Installs
    # Vectors: Users + Views + Vectors (count)
    views: Optional[NormalizedStatistic] = Field(None, description="Views (templates, vectors)")
    pages: Optional[NormalizedStatistic] = Field(None, description="Pages (templates only)")
    users: Optional[NormalizedStatistic] = Field(None, description="Users (plugins, vectors)")
    installs: Optional[NormalizedStatistic] = Field(None, description="Installs (components only)")
    vectors: Optional[NormalizedStatistic] = Field(None, description="Number of vectors (vectors only)")
    remixes: Optional[NormalizedStatistic] = Field(None, description="Remixes (if available)")
    previews: Optional[NormalizedStatistic] = Field(None, description="Previews (if available)")
    sales: Optional[int] = Field(None, ge=0, description="Number of sales if available")
    popularity: Optional[int] = Field(None, description="Popularity ranking/position")


class ProductMetadata(BaseModel):
    """Metadata for a product (Option B - normalized dates)."""

    published_date: Optional[NormalizedDate] = Field(None, description="Publication date")
    last_updated: Optional[NormalizedDate] = Field(None, description="Last update date")
    version: Optional[str] = Field(None, description="Product version number (plugins)")
    status: str = Field(default="active", description="Status: active, archived, suspended")


class ProductMedia(BaseModel):
    """Media files for a product."""

    thumbnail: Optional[HttpUrl] = Field(None, description="Thumbnail image URL")
    screenshots: List[str] = Field(default_factory=list, description="Screenshot URLs")
    gallery: List[str] = Field(default_factory=list, description="All image URLs")
    video_preview: Optional[HttpUrl] = Field(None, description="Video preview URL if available")


class ProductFeatures(BaseModel):
    """Features and characteristics of a product."""

    features: List[str] = Field(default_factory=list, description="List of key features")
    is_responsive: bool = Field(default=False, description="Whether product is responsive")
    has_animations: bool = Field(default=False, description="Whether product has animations")
    cms_integration: bool = Field(default=False, description="CMS integration support")
    pages_count: Optional[int] = Field(None, ge=0, description="Number of pages (for templates)")
    pages_list: List[str] = Field(default_factory=list, description="List of page names (e.g., ['Home', 'Contact', '404', 'Case studies'])")
    components_count: Optional[int] = Field(None, ge=0, description="Number of components")
    requirements: List[str] = Field(default_factory=list, description="Technical requirements")


class ProductReviews(BaseModel):
    """Reviews and ratings for a product."""

    average_rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")
    total_reviews: int = Field(default=0, ge=0, description="Total number of reviews")
    rating_distribution: dict[int, int] = Field(
        default_factory=dict,
        description="Rating distribution (5: count, 4: count, etc.)",
    )
    reviews: List[dict] = Field(default_factory=list, description="List of reviews (dictionaries for JSON compatibility)")


class Product(BaseModel):
    """Model for a product from Framer Marketplace."""

    id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    type: str = Field(..., description="Product type: template, component, vector, plugin")
    category: Optional[str] = Field(None, description="Main product category (first from categories list, for backward compatibility)")
    categories: List[str] = Field(default_factory=list, description="List of all product categories/tags")
    url: HttpUrl = Field(..., description="Product URL")
    price: Optional[float] = Field(None, ge=0, description="Product price")
    currency: str = Field(default="USD", description="Currency code")
    promotional_price: Optional[float] = Field(None, ge=0, description="Promotional price if available")
    is_free: bool = Field(default=False, description="Whether product is free")
    description: Optional[str] = Field(None, description="Full product description")
    short_description: Optional[str] = Field(None, description="Short preview/teaser")
    creator: Optional[Creator] = Field(None, description="Creator information")
    stats: ProductStats = Field(default_factory=ProductStats, description="Product statistics")
    metadata: ProductMetadata = Field(default_factory=ProductMetadata, description="Product metadata")
    features: ProductFeatures = Field(default_factory=ProductFeatures, description="Product features")
    media: ProductMedia = Field(default_factory=ProductMedia, description="Product media")
    # reviews removed - not available on Framer Marketplace
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="Scraping timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "product_123",
                "name": "Modern Portfolio Template",
                "type": "template",
                "category": "portfolio",
                "url": "https://www.framer.com/marketplace/templates/healing/",
                "price": 29.99,
                "currency": "USD",
                "is_free": False,
                "description": "Full description...",
                "short_description": "Preview text...",
                "creator": {
                    "username": "johndoe",
                    "name": "John Doe",
                    "profile_url": "https://www.framer.com/@johndoe",
                },
                "stats": {
                    "views": {"raw": "19.8K Views", "normalized": 19800},
                    "pages": {"raw": "8 Pages", "normalized": 8},
                    "remixes": {"raw": "456", "normalized": 456            },
        }
    },
                "metadata": {
                    "published_date": {"raw": "5 months ago", "normalized": "2024-10-15T00:00:00Z"},
                    "last_updated": {"raw": "3mo ago", "normalized": "2024-12-15T00:00:00Z"},
                    "version": None,
                    "status": "active",
                },
                "features": {
                    "features": ["Responsive", "Animations", "CMS Ready"],
                    "is_responsive": True,
                    "has_animations": True,
                    "cms_integration": True,
                },
                "media": {
                    "thumbnail": "https://...",
                    "screenshots": ["https://...", "https://..."],
                },
                "scraped_at": "2024-03-25T10:30:00Z",
            }
        }

