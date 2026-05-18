"""User entity: table + Create / Update / Response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel

ALLOWED_ROLES: tuple[str, ...] = ("super_admin", "admin", "editor")


def _validate_role(value: str | None) -> str | None:
    if value is None:
        return value
    if value not in ALLOWED_ROLES:
        raise ValueError(f"role must be one of {ALLOWED_ROLES}, got {value!r}")
    return value


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="Display name")
    email: str = Field(unique=True, index=True, description="Login email")
    hashed_password: str = Field(description="Bcrypt hash — never serialized out")
    role: str = Field(default="editor", description="super_admin | admin | editor")
    avatar: str | None = Field(default=None, description="Avatar URL or path")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("role")
    @classmethod
    def _check_role(cls, v: str) -> str:
        return _validate_role(v)


class UserCreate(SQLModel):
    name: str = Field(description="Display name")
    email: str = Field(description="Login email")
    password: str = Field(min_length=8, description="Plain password (will be hashed)")
    role: str = Field(default="editor", description="super_admin | admin | editor")
    avatar: str | None = Field(default=None, description="Avatar URL or path")

    @field_validator("role")
    @classmethod
    def _check_role(cls, v: str) -> str:
        return _validate_role(v)


class UserRegister(SQLModel):
    """Public self-registration input. No `role` on purpose — the server
    forces the default role so a client cannot register as admin."""

    name: str = Field(description="Display name")
    email: str = Field(description="Login email")
    password: str = Field(min_length=8, description="Plain password (will be hashed)")


class UserUpdate(SQLModel):
    name: str | None = Field(default=None)
    email: str | None = Field(default=None)
    password: str | None = Field(default=None, min_length=8)
    role: str | None = Field(default=None, description="super_admin | admin | editor")
    avatar: str | None = Field(default=None)

    @field_validator("role")
    @classmethod
    def _check_role(cls, v: str | None) -> str | None:
        return _validate_role(v)


class UserResponse(SQLModel):
    """Public view of a user — excludes hashed_password."""

    id: int
    name: str
    email: str
    role: str
    avatar: str | None = None
    created_at: datetime
