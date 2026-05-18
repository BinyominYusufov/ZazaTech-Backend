"""Blog entity: table + Create / Update / Response schemas.

`tags` is stored as a JSON string and exposed as list[str].
"""

from __future__ import annotations

from datetime import datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.models.json_field import dumps_list, loads_list


class Blog(SQLModel, table=True):
    __tablename__ = "blogs"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True, description="Post title")
    slug: str = Field(unique=True, index=True, description="URL slug")
    content: str = Field(description="Post body (markdown/html)")
    cover_image: str | None = Field(default=None, description="Cover image URL/path")
    tags: str = Field(default="[]", description="JSON-encoded list[str] of tags")
    published: bool = Field(default=False, description="Visible to the public")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def tags_list(self) -> list[str]:
        return loads_list(self.tags)

    @tags_list.setter
    def tags_list(self, value: list[str]) -> None:
        self.tags = dumps_list(value)


class BlogCreate(SQLModel):
    title: str = Field(description="Post title")
    slug: str = Field(description="URL slug (unique)")
    content: str = Field(description="Post body (markdown/html)")
    cover_image: str | None = Field(default=None, description="Cover image URL/path")
    tags: list[str] = Field(default_factory=list, description="List of tags")
    published: bool = Field(default=False, description="Visible to the public")


class BlogUpdate(SQLModel):
    title: str | None = Field(default=None)
    slug: str | None = Field(default=None)
    content: str | None = Field(default=None)
    cover_image: str | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    published: bool | None = Field(default=None)


class BlogResponse(SQLModel):
    id: int
    title: str
    slug: str
    content: str
    cover_image: str | None = None
    tags: list[str] = Field(default_factory=list)
    published: bool
    created_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def _tags_to_list(cls, v: object) -> list[str]:
        return loads_list(v)
