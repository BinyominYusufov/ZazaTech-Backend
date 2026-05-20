"""Admin CRUD for ambassadors (multipart). Sync SQLModel session.

All endpoints require the super_admin or admin role. Admin sees every
ambassador regardless of active state.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.files import delete_file, save_upload
from app.dependencies.auth import require_role
from app.models.ambassador import Ambassador
from app.schemas.ambassador import AmbassadorResponse

router = APIRouter(
    prefix="/api/admin/ambassadors",
    tags=["admin-ambassadors"],
    dependencies=[Depends(require_role("super_admin", "admin"))],
)

SessionDep = Annotated[Session, Depends(get_session)]


def _serialize(obj: Ambassador) -> AmbassadorResponse:
    return AmbassadorResponse.model_validate(obj, from_attributes=True)


def _get_or_404(ambassador_id: int, session: Session) -> Ambassador:
    ambassador = session.get(Ambassador, ambassador_id)
    if ambassador is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not found"
        )
    return ambassador


@router.get("")
def list_ambassadors_admin(
    session: SessionDep,
    is_active: bool | None = None,
    is_featured: bool | None = None,
) -> dict:
    stmt = select(Ambassador)
    if is_active is not None:
        stmt = stmt.where(Ambassador.is_active == is_active)
    if is_featured is not None:
        stmt = stmt.where(Ambassador.is_featured == is_featured)
    stmt = stmt.order_by(Ambassador.created_at.desc())
    items = session.exec(stmt).all()
    return {"success": True, "data": [_serialize(i) for i in items]}


@router.get("/{ambassador_id}")
def get_ambassador_admin(ambassador_id: int, session: SessionDep) -> dict:
    ambassador = _get_or_404(ambassador_id, session)
    return {"success": True, "data": _serialize(ambassador)}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_ambassador(
    session: SessionDep,
    name: Annotated[str, Form()],
    role: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    instagram_url: Annotated[str | None, Form()] = None,
    twitter_url: Annotated[str | None, Form()] = None,
    linkedin_url: Annotated[str | None, Form()] = None,
    is_featured: Annotated[bool, Form()] = False,
    is_active: Annotated[bool, Form()] = True,
    image: Annotated[UploadFile | None, File()] = None,
) -> dict:
    ambassador = Ambassador(
        name=name,
        role=role,
        description=description,
        instagram_url=instagram_url,
        twitter_url=twitter_url,
        linkedin_url=linkedin_url,
        is_featured=is_featured,
        is_active=is_active,
    )
    if image is not None:
        ambassador.image = save_upload(image, "ambassadors")

    session.add(ambassador)
    session.commit()
    session.refresh(ambassador)
    return {"success": True, "data": _serialize(ambassador)}


@router.patch("/{ambassador_id}")
def update_ambassador(
    ambassador_id: int,
    session: SessionDep,
    name: Annotated[str | None, Form()] = None,
    role: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    instagram_url: Annotated[str | None, Form()] = None,
    twitter_url: Annotated[str | None, Form()] = None,
    linkedin_url: Annotated[str | None, Form()] = None,
    is_featured: Annotated[bool | None, Form()] = None,
    is_active: Annotated[bool | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> dict:
    ambassador = _get_or_404(ambassador_id, session)

    if name is not None:
        ambassador.name = name
    if role is not None:
        ambassador.role = role
    if description is not None:
        ambassador.description = description
    if instagram_url is not None:
        ambassador.instagram_url = instagram_url
    if twitter_url is not None:
        ambassador.twitter_url = twitter_url
    if linkedin_url is not None:
        ambassador.linkedin_url = linkedin_url
    if is_featured is not None:
        ambassador.is_featured = is_featured
    if is_active is not None:
        ambassador.is_active = is_active
    if image is not None:
        if ambassador.image:
            delete_file(ambassador.image)
        ambassador.image = save_upload(image, "ambassadors")

    session.add(ambassador)
    session.commit()
    session.refresh(ambassador)
    return {"success": True, "data": _serialize(ambassador)}


@router.patch("/{ambassador_id}/toggle-active")
def toggle_ambassador_active(
    ambassador_id: int, session: SessionDep
) -> dict:
    ambassador = _get_or_404(ambassador_id, session)
    ambassador.is_active = not ambassador.is_active
    session.add(ambassador)
    session.commit()
    session.refresh(ambassador)
    return {"success": True, "data": _serialize(ambassador)}


@router.patch("/{ambassador_id}/toggle-featured")
def toggle_ambassador_featured(
    ambassador_id: int, session: SessionDep
) -> dict:
    ambassador = _get_or_404(ambassador_id, session)
    ambassador.is_featured = not ambassador.is_featured
    session.add(ambassador)
    session.commit()
    session.refresh(ambassador)
    return {"success": True, "data": _serialize(ambassador)}


@router.delete("/{ambassador_id}")
def delete_ambassador(ambassador_id: int, session: SessionDep) -> dict:
    ambassador = _get_or_404(ambassador_id, session)
    if ambassador.image:
        delete_file(ambassador.image)
    session.delete(ambassador)
    session.commit()
    return {"success": True, "data": {"id": ambassador_id}}
