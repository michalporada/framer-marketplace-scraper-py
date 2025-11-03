"""Tests for ProductParser."""

from src.parsers.product_parser import ProductParser


class TestProductParser:
    """Tests for ProductParser."""

    def test_decode_nextjs_image_url(self):
        """Test decoding Next.js Image URLs."""
        parser = ProductParser()

        # Test Next.js Image URL
        nextjs_url = (
            "/creators-assets/_next/image/?url=https%3A%2F%2Fexample.com%2Fimage.jpg&w=800&q=100"
        )
        decoded = parser.decode_nextjs_image_url(nextjs_url)
        assert decoded == "https://example.com/image.jpg"

        # Test regular URL (should return as-is)
        regular_url = "https://example.com/image.jpg"
        decoded = parser.decode_nextjs_image_url(regular_url)
        assert decoded == regular_url

    def test_extract_price_free(self):
        """Test extracting price from free product."""
        parser = ProductParser()
        price, is_free = parser.extract_price("Free")
        assert price is None
        assert is_free is True

    def test_extract_price_paid(self):
        """Test extracting price from paid product."""
        parser = ProductParser()
        price, is_free = parser.extract_price("$49")
        assert price == 49.0
        assert is_free is False

        price, is_free = parser.extract_price("$10.99")
        assert price == 10.99
        assert is_free is False

    def test_extract_creator_username(self):
        """Test extracting creator username from URL."""
        parser = ProductParser()

        username = parser.extract_creator_username("/@johndoe/")
        assert username == "johndoe"

        username = parser.extract_creator_username("https://www.framer.com/@johndoe/")
        assert username == "johndoe"

        username = parser.extract_creator_username("/@-790ivi/")
        assert username == "-790ivi"

    def test_parse_minimal_html(self):
        """Test parsing minimal HTML."""
        parser = ProductParser()

        html = """
        <html>
            <head>
                <title>Test Product - Framer Marketplace</title>
                <meta property="og:title" content="Test Product" />
            </head>
            <body>
                <h1>Test Product</h1>
            </body>
        </html>
        """

        url = "https://www.framer.com/marketplace/templates/test/"
        product = parser.parse(html, url, "template")

        assert product is not None
        assert product.id == "test"
        assert product.type == "template"
        assert str(product.url) == url
