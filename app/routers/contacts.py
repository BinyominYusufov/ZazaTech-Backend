"""CRUD for Contacts. Sync SQLModel session (project is synchronous).

POST is public (contact form submissions); the rest require auth.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies.auth import get_current_user
from app.models.contact import Contact, ContactCreate, ContactResponse

router = APIRouter(prefix="/api/contacts", tags=["contacts"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_contact(payload: ContactCreate, session: SessionDep):
    contact = Contact(
        name=payload.name,
        email=payload.email,
        subject=payload.subject,
        message=payload.message,
    )  # read defaults to False on the model
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact


@router.get(
    "",
    response_model=list[ContactResponse],
    dependencies=[Depends(get_current_user)],
)
def list_contacts(
    session: SessionDep,
    read: bool | None = None,
):
    statement = select(Contact)
    if read is not None:
        statement = statement.where(Contact.read == read)
    statement = statement.order_by(Contact.created_at.desc())
    return session.exec(statement).all()


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    dependencies=[Depends(get_current_user)],
)
def get_contact(contact_id: int, session: SessionDep):
    contact = session.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.put(
    "/{contact_id}/read",
    response_model=ContactResponse,
    dependencies=[Depends(get_current_user)],
)
def mark_contact_read(contact_id: int, session: SessionDep):
    contact = session.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    contact.read = True
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact


@router.delete("/{contact_id}", dependencies=[Depends(get_current_user)])
def delete_contact(contact_id: int, session: SessionDep) -> dict:
    contact = session.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    session.delete(contact)
    session.commit()
    return {"success": True, "message": "Contact deleted"}
