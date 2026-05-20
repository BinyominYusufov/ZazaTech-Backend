"""Public ambassadors listing. Sync SQLModel session.

Only active ambassadors are visible to the public.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.ambassador import Ambassador
from app.schemas.ambassador import AmbassadorResponse

router = APIRouter(prefix="/api/ambassadors", tags=["ambassadors"])

SessionDep = Annotated[Session, Depends(get_session)]


def _serialize(obj: Ambassador) -> AmbassadorResponse:
    return AmbassadorResponse.model_validate(obj, from_attributes=True)


@router.get("")
def list_ambassadors(
    session: SessionDep,
    is_featured: bool | None = None,
) -> dict:
    stmt = select(Ambassador).where(Ambassador.is_active == True)  # noqa: E712
    if is_featured is not None:
        stmt = stmt.where(Ambassador.is_featured == is_featured)
    stmt = stmt.order_by(
        Ambassador.is_featured.desc(),
        Ambassador.created_at.desc(),
    )
    items = session.exec(stmt).all()
    return {"success": True, "data": [_serialize(i) for i in items]}


@router.get("/{ambassador_id}")
def get_ambassador(ambassador_id: int, session: SessionDep) -> dict:
    ambassador = session.get(Ambassador, ambassador_id)
    if ambassador is None or not ambassador.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not found"
        )
    return {"success": True, "data": _serialize(ambassador)}
