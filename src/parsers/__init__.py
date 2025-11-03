"""Parsers module - contains HTML parsers for extracting data."""

from src.parsers.category_parser import CategoryParser
from src.parsers.creator_parser import CreatorParser
from src.parsers.product_parser import ProductParser
from src.parsers.review_parser import ReviewParser

__all__ = [
    "ProductParser",
    "CreatorParser",
    "ReviewParser",
    "CategoryParser",
]
