"""Tests for Product model."""

import pytest
from datetime import datetime

from src.models.product import (
    Product,
    ProductStats,
    ProductMetadata,
    NormalizedDate,
    NormalizedStatistic,
    ProductFeatures,
    ProductMedia,
)


class TestNormalizedDate:
    """Tests for NormalizedDate model."""

    def test_normalized_date_with_raw(self):
        """Test NormalizedDate with raw date."""
        date = NormalizedDate(raw="5 months ago", normalized="2024-10-15T00:00:00Z")
        assert date.raw == "5 months ago"
        assert date.normalized == "2024-10-15T00:00:00Z"

    def test_normalized_date_without_normalized(self):
        """Test NormalizedDate without normalized value."""
        date = NormalizedDate(raw="5 months ago", normalized=None)
        assert date.raw == "5 months ago"
        assert date.normalized is None


class TestNormalizedStatistic:
    """Tests for NormalizedStatistic model."""

    def test_normalized_statistic_with_values(self):
        """Test NormalizedStatistic with values."""
        stat = NormalizedStatistic(raw="19.8K Views", normalized=19800)
        assert stat.raw == "19.8K Views"
        assert stat.normalized == 19800

    def test_normalized_statistic_without_normalized(self):
        """Test NormalizedStatistic without normalized value."""
        stat = NormalizedStatistic(raw="19.8K Views", normalized=None)
        assert stat.raw == "19.8K Views"
        assert stat.normalized is None


class TestProductStats:
    """Tests for ProductStats model."""

    def test_product_stats_template(self):
        """Test ProductStats for template."""
        stats = ProductStats(
            views=NormalizedStatistic(raw="19.8K Views", normalized=19800),
            pages=NormalizedStatistic(raw="8 Pages", normalized=8),
        )
        assert stats.views.normalized == 19800
        assert stats.pages.normalized == 8

    def test_product_stats_plugin(self):
        """Test ProductStats for plugin."""
        stats = ProductStats(
            users=NormalizedStatistic(raw="1.2K Users", normalized=1200),
        )
        assert stats.users.normalized == 1200

    def test_product_stats_component(self):
        """Test ProductStats for component."""
        stats = ProductStats(
            installs=NormalizedStatistic(raw="500 Installs", normalized=500),
        )
        assert stats.installs.normalized == 500


class TestProductMetadata:
    """Tests for ProductMetadata model."""

    def test_product_metadata_with_dates(self):
        """Test ProductMetadata with dates."""
        metadata = ProductMetadata(
            published_date=NormalizedDate(raw="5 months ago", normalized="2024-10-15T00:00:00Z"),
            last_updated=NormalizedDate(raw="3mo ago", normalized="2024-12-15T00:00:00Z"),
        )
        assert metadata.published_date.raw == "5 months ago"
        assert metadata.last_updated.raw == "3mo ago"

    def test_product_metadata_plugin_version(self):
        """Test ProductMetadata for plugin with version."""
        metadata = ProductMetadata(version="2.1")
        assert metadata.version == "2.1"
        assert metadata.status == "active"


class TestProduct:
    """Tests for Product model."""

    def test_product_minimal(self):
        """Test Product with minimal required fields."""
        product = Product(
            id="test-product",
            name="Test Product",
            type="template",
            url="https://www.framer.com/marketplace/templates/test/",
        )
        assert product.id == "test-product"
        assert product.name == "Test Product"
        assert product.type == "template"
        assert product.is_free is False
        assert product.currency == "USD"

    def test_product_with_price(self):
        """Test Product with price."""
        product = Product(
            id="test-product",
            name="Test Product",
            type="template",
            url="https://www.framer.com/marketplace/templates/test/",
            price=49.99,
            is_free=False,
        )
        assert product.price == 49.99
        assert product.is_free is False

    def test_product_free(self):
        """Test Product that is free."""
        product = Product(
            id="test-product",
            name="Test Product",
            type="template",
            url="https://www.framer.com/marketplace/templates/test/",
            is_free=True,
        )
        assert product.price is None
        assert product.is_free is True

    def test_product_with_stats(self):
        """Test Product with statistics."""
        product = Product(
            id="test-product",
            name="Test Product",
            type="template",
            url="https://www.framer.com/marketplace/templates/test/",
            stats=ProductStats(
                views=NormalizedStatistic(raw="19.8K Views", normalized=19800),
                pages=NormalizedStatistic(raw="8 Pages", normalized=8),
            ),
        )
        assert product.stats.views.normalized == 19800
        assert product.stats.pages.normalized == 8

    def test_product_with_metadata(self):
        """Test Product with metadata."""
        product = Product(
            id="test-product",
            name="Test Product",
            type="template",
            url="https://www.framer.com/marketplace/templates/test/",
            metadata=ProductMetadata(
                published_date=NormalizedDate(raw="5 months ago", normalized="2024-10-15T00:00:00Z"),
            ),
        )
        assert product.metadata.published_date.raw == "5 months ago"

    def test_product_json_serialization(self):
        """Test Product JSON serialization."""
        product = Product(
            id="test-product",
            name="Test Product",
            type="template",
            url="https://www.framer.com/marketplace/templates/test/",
        )
        json_data = product.model_dump_json()
        assert "test-product" in json_data
        assert "Test Product" in json_data

