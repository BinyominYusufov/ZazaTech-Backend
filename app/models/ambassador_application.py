"""AmbassadorApplication table model.

An intentionally standalone entity: approving an application does NOT create
an Ambassador. Schemas live in app/schemas/ambassador_application.py.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel

ALLOWED_STATUSES = ("pending", "approved", "rejected")


class AmbassadorApplication(SQLModel, table=True):
    __tablename__ = "ambassador_applications"

    # table=True models skip Pydantic validation by default; enable it so the
    # `status` @field_validator below actually runs on construction/assignment.
    model_config = {"validate_assignment": True}  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    full_name: str = Field(description="Applicant full name")
    email: str = Field(index=True, description="Applicant email")
    phone: str = Field(description="Applicant phone")
    profession: str = Field(description="Applicant profession")
    organization: str | None = Field(default=None, description="Organization")
    message: str | None = Field(default=None, description="Free-form message")
    status: str = Field(
        default="pending",
        index=True,
        description='One of: "pending" | "approved" | "rejected"',
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        if v not in ALLOWED_STATUSES:
            raise ValueError(
                f"status must be one of {', '.join(ALLOWED_STATUSES)}"
            )
        return v
