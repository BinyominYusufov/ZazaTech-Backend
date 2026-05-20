"""Admin moderation of ambassador applications. Sync SQLModel session.

All endpoints require the super_admin or admin role. Approving an
application deliberately does NOT create an Ambassador.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies.auth import require_role
from app.models.ambassador_application import AmbassadorApplication
from app.schemas.ambassador_application import AmbassadorApplicationResponse

router = APIRouter(
    prefix="/api/admin/ambassador-applications",
    tags=["admin-ambassador-applications"],
    dependencies=[Depends(require_role("super_admin", "admin"))],
)

SessionDep = Annotated[Session, Depends(get_session)]

# Exposed to clients as `?status=` but bound to `status_filter` so it does
# not shadow the imported `status` module.
StatusFilter = Annotated[str | None, Query(alias="status")]


def _serialize(obj: AmbassadorApplication) -> AmbassadorApplicationResponse:
    return AmbassadorApplicationResponse.model_validate(
        obj, from_attributes=True
    )


def _get_or_404(
    application_id: int, session: Session
) -> AmbassadorApplication:
    application = session.get(AmbassadorApplication, application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not found"
        )
    return application


@router.get("")
def list_ambassador_applications(
    session: SessionDep,
    status_filter: StatusFilter = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    page = max(page, 1)
    limit = max(limit, 1)

    count_stmt = select(func.count()).select_from(AmbassadorApplication)
    stmt = select(AmbassadorApplication)
    if status_filter is not None:
        count_stmt = count_stmt.where(
            AmbassadorApplication.status == status_filter
        )
        stmt = stmt.where(AmbassadorApplication.status == status_filter)

    total = session.exec(count_stmt).one()
    stmt = (
        stmt.order_by(AmbassadorApplication.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    items = session.exec(stmt).all()

    pages = (total + limit - 1) // limit

    return {
        "success": True,
        "data": {
            "items": [_serialize(i) for i in items],
            "total": total,
            "page": page,
            "pages": pages,
        },
    }


@router.get("/{application_id}")
def get_ambassador_application(
    application_id: int, session: SessionDep
) -> dict:
    application = _get_or_404(application_id, session)
    return {"success": True, "data": _serialize(application)}


@router.patch("/{application_id}/approve")
def approve_ambassador_application(
    application_id: int, session: SessionDep
) -> dict:
    application = _get_or_404(application_id, session)
    if application.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application already reviewed",
        )
    application.status = "approved"
    session.add(application)
    session.commit()
    session.refresh(application)
    return {"success": True, "data": _serialize(application)}


@router.patch("/{application_id}/reject")
def reject_ambassador_application(
    application_id: int, session: SessionDep
) -> dict:
    application = _get_or_404(application_id, session)
    if application.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application already reviewed",
        )
    application.status = "rejected"
    session.add(application)
    session.commit()
    session.refresh(application)
    return {"success": True, "data": _serialize(application)}
