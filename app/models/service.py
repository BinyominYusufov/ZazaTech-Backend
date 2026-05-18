"""Service entity: table + Create / Update / Response schemas.

`technologies` is stored as a JSON string (SQLite has no array type) and
exposed to clients as list[str].
"""

from __future__ import annotations

from datetime import datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.models.json_field import dumps_list, loads_list


class Service(SQLModel, table=True):
    __tablename__ = "services"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True, description="Service title")
    description: str = Field(description="Full description")
    short_description: str = Field(description="Card / preview text")
    image: str | None = Field(default=None, description="Image URL or path")
    technologies: str = Field(
        default="[]", description="JSON-encoded list[str] of technologies"
    )
    price: float = Field(default=0.0, ge=0, description="Price, must be >= 0")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def technologies_list(self) -> list[str]:
        return loads_list(self.technologies)

    @technologies_list.setter
    def technologies_list(self, value: list[str]) -> None:
        self.technologies = dumps_list(value)


class ServiceCreate(SQLModel):
    title: str = Field(description="Service title")
    description: str = Field(description="Full description")
    short_description: str = Field(description="Card / preview text")
    image: str | None = Field(default=None, description="Image URL or path")
    technologies: list[str] = Field(
        default_factory=list, description="List of technologies"
    )
    price: float = Field(default=0.0, ge=0, description="Price, must be >= 0")


class ServiceUpdate(SQLModel):
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    short_description: str | None = Field(default=None)
    image: str | None = Field(default=None)
    technologies: list[str] | None = Field(default=None)
    price: float | None = Field(default=None, ge=0)


class ServiceResponse(SQLModel):
    id: int
    title: str
    description: str
    short_description: str
    image: str | None = None
    technologies: list[str] = Field(default_factory=list)
    price: float
    created_at: datetime

    @field_validator("technologies", mode="before")
    @classmethod
    def _tech_to_list(cls, v: object) -> list[str]:
        return loads_list(v)
