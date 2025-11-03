"""Tests for SitemapScraper."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.scrapers.sitemap_scraper import SitemapScraper


class TestSitemapScraper:
    """Tests for SitemapScraper."""

    def test_filter_urls_by_type(self):
        """Test filtering URLs by product type."""
        scraper = SitemapScraper()
        
        parsed_sitemap = {
            "products": {
                "templates": [
                    "https://www.framer.com/marketplace/templates/viral/",
                    "https://www.framer.com/marketplace/templates/test/",
                ],
                "components": [
                    "https://www.framer.com/marketplace/components/glass/",
                ],
                "vectors": [],
                "plugins": [],
            },
            "categories": [],
            "profiles": [],
            "help_articles": [],
        }
        
        # Filter for templates only
        urls = scraper.filter_urls_by_type(parsed_sitemap, ["template"])
        assert len(urls) == 2
        assert "viral" in urls[0]
        assert "test" in urls[1]
        
        # Filter for multiple types
        urls = scraper.filter_urls_by_type(parsed_sitemap, ["template", "component"])
        assert len(urls) == 3
        
        # Filter for all types
        urls = scraper.filter_urls_by_type(parsed_sitemap, ["template", "component", "vector", "plugin"])
        assert len(urls) == 3

    def test_parse_sitemap_product_urls(self):
        """Test parsing product URLs from sitemap XML."""
        scraper = SitemapScraper()
        
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://www.framer.com/marketplace/templates/viral/</loc>
            </url>
            <url>
                <loc>https://www.framer.com/marketplace/components/glass/</loc>
            </url>
            <url>
                <loc>https://www.framer.com/marketplace/vectors/test/</loc>
            </url>
            <url>
                <loc>https://www.framer.com/marketplace/plugins/test/</loc>
            </url>
            <url>
                <loc>https://www.framer.com/@johndoe/</loc>
            </url>
            <url>
                <loc>https://www.framer.com/marketplace/category/templates/</loc>
            </url>
        </urlset>"""
        
        result = scraper.parse_sitemap(xml_content.encode())
        
        assert len(result["products"]["templates"]) == 1
        assert len(result["products"]["components"]) == 1
        assert len(result["products"]["vectors"]) == 1
        assert len(result["products"]["plugins"]) == 1
        assert len(result["profiles"]) == 1
        assert len(result["categories"]) == 1

