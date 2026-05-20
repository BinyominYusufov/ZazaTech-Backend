"""Ambassador request/response schemas."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class AmbassadorCreate(SQLModel):
    name: str = Field(description="Ambassador name")
    role: str = Field(description="Ambassador role / title")
    image: str | None = Field(default=None, description="Image URL or path")
    description: str | None = Field(default=None, description="Bio / description")
    instagram_url: str | None = Field(default=None, description="Instagram URL")
    twitter_url: str | None = Field(default=None, description="Twitter URL")
    linkedin_url: str | None = Field(default=None, description="LinkedIn URL")
    is_featured: bool = Field(default=False, description="Show as featured")
    is_active: bool = Field(default=True, description="Visible to the public")


class AmbassadorUpdate(SQLModel):
    name: str | None = Field(default=None)
    role: str | None = Field(default=None)
    image: str | None = Field(default=None)
    description: str | None = Field(default=None)
    instagram_url: str | None = Field(default=None)
    twitter_url: str | None = Field(default=None)
    linkedin_url: str | None = Field(default=None)
    is_featured: bool | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class AmbassadorResponse(SQLModel):
    id: int
    name: str
    role: str
    image: str | None = None
    description: str | None = None
    instagram_url: str | None = None
    twitter_url: str | None = None
    linkedin_url: str | None = None
    is_featured: bool
    is_active: bool
    created_at: datetime
