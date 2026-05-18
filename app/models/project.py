"""Project entity: table + Create / Update / Response schemas.

`technologies` is stored as a JSON string and exposed as list[str].
"""

from __future__ import annotations

from datetime import datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.models.json_field import dumps_list, loads_list


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True, description="Project title")
    description: str = Field(description="Full description")
    category: str = Field(index=True, description="Project category")
    image: str | None = Field(default=None, description="Image URL or path")
    technologies: str = Field(
        default="[]", description="JSON-encoded list[str] of technologies"
    )
    github_url: str | None = Field(default=None, description="GitHub repo URL")
    live_url: str | None = Field(default=None, description="Live demo URL")
    featured: bool = Field(default=False, description="Show on landing page")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def technologies_list(self) -> list[str]:
        return loads_list(self.technologies)

    @technologies_list.setter
    def technologies_list(self, value: list[str]) -> None:
        self.technologies = dumps_list(value)


class ProjectCreate(SQLModel):
    title: str = Field(description="Project title")
    description: str = Field(description="Full description")
    category: str = Field(description="Project category")
    image: str | None = Field(default=None, description="Image URL or path")
    technologies: list[str] = Field(
        default_factory=list, description="List of technologies"
    )
    github_url: str | None = Field(default=None, description="GitHub repo URL")
    live_url: str | None = Field(default=None, description="Live demo URL")
    featured: bool = Field(default=False, description="Show on landing page")


class ProjectUpdate(SQLModel):
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    category: str | None = Field(default=None)
    image: str | None = Field(default=None)
    technologies: list[str] | None = Field(default=None)
    github_url: str | None = Field(default=None)
    live_url: str | None = Field(default=None)
    featured: bool | None = Field(default=None)


class ProjectResponse(SQLModel):
    id: int
    title: str
    description: str
    category: str
    image: str | None = None
    technologies: list[str] = Field(default_factory=list)
    github_url: str | None = None
    live_url: str | None = None
    featured: bool
    created_at: datetime

    @field_validator("technologies", mode="before")
    @classmethod
    def _tech_to_list(cls, v: object) -> list[str]:
        return loads_list(v)
