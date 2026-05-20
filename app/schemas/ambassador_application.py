"""AmbassadorApplication request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.models.ambassador_application import ALLOWED_STATUSES


class AmbassadorApplicationCreate(SQLModel):
    full_name: str = Field(description="Applicant full name")
    email: str = Field(description="Applicant email")
    phone: str = Field(description="Applicant phone")
    profession: str = Field(description="Applicant profession")
    organization: str | None = Field(default=None, description="Organization")
    message: str | None = Field(default=None, description="Free-form message")


class AmbassadorApplicationStatusUpdate(SQLModel):
    status: str = Field(description='"approved" or "rejected"')

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        if v not in ALLOWED_STATUSES:
            raise ValueError(
                f"status must be one of {', '.join(ALLOWED_STATUSES)}"
            )
        return v


class AmbassadorApplicationResponse(SQLModel):
    id: int
    full_name: str
    email: str
    phone: str
    profession: str
    organization: str | None = None
    message: str | None = None
    status: str
    created_at: datetime
