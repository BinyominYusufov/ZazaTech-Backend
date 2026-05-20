"""Ambassador table model.

Standalone entity — never created automatically from an
AmbassadorApplication. Schemas live in app/schemas/ambassador.py.
"""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class Ambassador(SQLModel, table=True):
    __tablename__ = "ambassadors"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(description="Ambassador name")
    role: str = Field(description="Ambassador role / title")
    image: str | None = Field(default=None, description="Image URL or path")
    description: str | None = Field(default=None, description="Bio / description")
    instagram_url: str | None = Field(default=None, description="Instagram URL")
    twitter_url: str | None = Field(default=None, description="Twitter URL")
    linkedin_url: str | None = Field(default=None, description="LinkedIn URL")
    is_featured: bool = Field(default=False, description="Show as featured")
    is_active: bool = Field(default=True, description="Visible to the public")
    created_at: datetime = Field(default_factory=datetime.utcnow)
