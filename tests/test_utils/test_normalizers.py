"""Tests for normalizers."""

from datetime import datetime

from src.utils.normalizers import parse_relative_date, parse_statistic, extract_statistic_label


class TestParseRelativeDate:
    """Tests for parse_relative_date function."""

    def test_parse_months_ago(self):
        """Test parsing 'X months ago' format."""
        result = parse_relative_date("5 months ago")
        assert result["raw"] == "5 months ago"
        assert result["normalized"] is not None
        assert isinstance(result["normalized"], str)
        # Check it's a valid ISO 8601 date
        datetime.fromisoformat(result["normalized"].replace("Z", "+00:00"))

    def test_parse_month_ago(self):
        """Test parsing 'X month ago' format."""
        result = parse_relative_date("1 month ago")
        assert result["raw"] == "1 month ago"
        assert result["normalized"] is not None

    def test_parse_mo_ago(self):
        """Test parsing 'Xmo ago' format."""
        result = parse_relative_date("3mo ago")
        assert result["raw"] == "3mo ago"
        assert result["normalized"] is not None

    def test_parse_weeks_ago(self):
        """Test parsing 'X weeks ago' format."""
        result = parse_relative_date("2 weeks ago")
        assert result["raw"] == "2 weeks ago"
        assert result["normalized"] is not None

    def test_parse_days_ago(self):
        """Test parsing 'X days ago' format."""
        result = parse_relative_date("6 days ago")
        assert result["raw"] == "6 days ago"
        assert result["normalized"] is not None


class TestParseStatistic:
    """Tests for parse_statistic function."""

    def test_parse_k_format(self):
        """Test parsing 'XK' format."""
        result = parse_statistic("19.8K Views")
        assert result["raw"] == "19.8K Views"
        assert result["normalized"] == 19800

    def test_parse_k_format_integer(self):
        """Test parsing 'XK' format with integer."""
        result = parse_statistic("5K Views")
        assert result["normalized"] == 5000

    def test_parse_m_format(self):
        """Test parsing 'XM' format."""
        result = parse_statistic("1.5M Views")
        assert result["normalized"] == 1500000

    def test_parse_number_with_commas(self):
        """Test parsing number with commas."""
        result = parse_statistic("1,200 Views")
        assert result["normalized"] == 1200

    def test_parse_simple_number(self):
        """Test parsing simple number."""
        result = parse_statistic("500 Views")
        assert result["normalized"] == 500

    def test_parse_pages(self):
        """Test parsing pages count."""
        result = parse_statistic("8 Pages")
        assert result["normalized"] == 8


class TestExtractStatisticLabel:
    """Tests for extract_statistic_label function."""

    def test_extract_views_label(self):
        """Test extracting 'Views' label."""
        label = extract_statistic_label("19.8K Views")
        assert label == "Views"  # Function returns original case

    def test_extract_pages_label(self):
        """Test extracting 'Pages' label."""
        label = extract_statistic_label("8 Pages")
        assert label == "Pages"  # Function returns original case

    def test_extract_users_label(self):
        """Test extracting 'Users' label."""
        label = extract_statistic_label("1.2K Users")
        assert label == "Users"  # Function returns original case

