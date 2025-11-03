"""Pydantic model for creator/profile data."""

from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class CreatorStats(BaseModel):
    """Statistics for a creator."""

    total_products: int = Field(default=0, ge=0, description="Total number of published products")
    templates_count: int = Field(default=0, ge=0, description="Number of templates")
    components_count: int = Field(default=0, ge=0, description="Number of components")
    vectors_count: int = Field(default=0, ge=0, description="Number of vectors")
    plugins_count: int = Field(default=0, ge=0, description="Number of plugins")
    total_sales: Optional[int] = Field(None, ge=0, description="Total sales count if available")
    average_rating: Optional[float] = Field(None, ge=0, le=5, description="Average product rating")


class Creator(BaseModel):
    """Model for a creator/profile."""

    username: str = Field(..., description="Creator username (without @, may contain special characters like -790ivi)")
    name: Optional[str] = Field(None, description="Creator display name")
    profile_url: HttpUrl = Field(..., description="URL to creator's profile")
    avatar_url: Optional[HttpUrl] = Field(None, description="Avatar/profile image URL")
    bio: Optional[str] = Field(None, description="Creator bio/description")
    website: Optional[HttpUrl] = Field(None, description="Creator's website")
    social_media: dict[str, str] = Field(
        default_factory=dict,
        description="Social media links (twitter, linkedin, instagram, etc.)",
    )
    stats: CreatorStats = Field(default_factory=CreatorStats, description="Creator statistics")

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "johndoe",
                "name": "John Doe",
                "profile_url": "https://www.framer.com/@johndoe",
                "avatar_url": "https://...",
                "bio": "Designer and developer",
                "website": "https://johndoe.com",
                "social_media": {
                    "twitter": "https://twitter.com/johndoe",
                    "linkedin": "https://linkedin.com/in/johndoe",
                },
                "stats": {
                    "total_products": 10,
                    "templates_count": 5,
                    "components_count": 3,
                    "vectors_count": 2,
                    "plugins_count": 1,
                    "total_sales": 150,
                    "average_rating": 4.5,
                },
            }
        }
    }

