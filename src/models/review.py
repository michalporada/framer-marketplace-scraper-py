"""Pydantic model for product reviews."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class Review(BaseModel):
    """Model for a product review."""

    author: str = Field(..., description="Author of the review")
    author_url: Optional[HttpUrl] = Field(None, description="URL to author's profile")
    rating: float = Field(..., ge=0, le=5, description="Rating from 0 to 5")
    content: str = Field(..., description="Review text content")
    date: Optional[datetime] = Field(None, description="Date when review was written")
    attachments: List[str] = Field(default_factory=list, description="Screenshot URLs if available")

    model_config = {
        "json_schema_extra": {
            "example": {
                "author": "John Doe",
                "author_url": "https://framer.com/@johndoe",
                "rating": 4.5,
                "content": "Great template, very useful!",
                "date": "2024-01-15T10:30:00Z",
                "attachments": [],
            }
        }
    }

