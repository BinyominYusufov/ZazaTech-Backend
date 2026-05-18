"""Contact entity: table + Create / Update / Response schemas."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class Contact(SQLModel, table=True):
    __tablename__ = "contacts"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(description="Sender name")
    email: str = Field(index=True, description="Sender email")
    subject: str = Field(description="Message subject")
    message: str = Field(description="Message body")
    read: bool = Field(default=False, description="Marked as read by staff")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContactCreate(SQLModel):
    name: str = Field(description="Sender name")
    email: str = Field(description="Sender email")
    subject: str = Field(description="Message subject")
    message: str = Field(description="Message body")


class ContactUpdate(SQLModel):
    name: str | None = Field(default=None)
    email: str | None = Field(default=None)
    subject: str | None = Field(default=None)
    message: str | None = Field(default=None)
    read: bool | None = Field(default=None, description="Mark as read/unread")


class ContactResponse(SQLModel):
    id: int
    name: str
    email: str
    subject: str
    message: str
    read: bool
    created_at: datetime
