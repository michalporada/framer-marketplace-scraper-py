"""Pydantic model for category data."""

from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class Category(BaseModel):
    """Model for a marketplace category."""

    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="Category slug (URL-friendly name)")
    url: HttpUrl = Field(..., description="Category URL")
    description: Optional[str] = Field(None, description="Category description")
    product_count: Optional[int] = Field(None, ge=0, description="Total number of products in category")
    product_types: Optional[List[str]] = Field(
        default_factory=list,
        description="Product types in this category (template, component, vector, plugin)",
    )
    parent_category: Optional[str] = Field(None, description="Parent category name if this is a subcategory")
    subcategories: List[str] = Field(default_factory=list, description="List of subcategory names")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Templates",
                "slug": "templates",
                "url": "https://www.framer.com/marketplace/category/templates/",
                "description": "Browse all templates",
                "product_count": 150,
                "product_types": ["template"],
                "parent_category": None,
                "subcategories": ["portfolio", "business", "landing-page"],
            }
        }
    }

