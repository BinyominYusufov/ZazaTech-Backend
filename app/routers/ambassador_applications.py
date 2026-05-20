"""Public ambassador-application submissions. Sync SQLModel session.

POST is public (no auth). A second submission from the same email while a
previous one is still "pending" is rejected with 400.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.ambassador_application import AmbassadorApplication
from app.schemas.ambassador_application import (
    AmbassadorApplicationCreate,
    AmbassadorApplicationResponse,
)

router = APIRouter(
    prefix="/api/ambassador-applications",
    tags=["ambassador-applications"],
)

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_ambassador_application(
    payload: AmbassadorApplicationCreate, session: SessionDep
) -> dict:
    existing = session.exec(
        select(AmbassadorApplication).where(
            AmbassadorApplication.email == payload.email,
            AmbassadorApplication.status == "pending",
        )
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application already pending",
        )

    application = AmbassadorApplication(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        profession=payload.profession,
        organization=payload.organization,
        message=payload.message,
        status="pending",
    )
    session.add(application)
    session.commit()
    session.refresh(application)

    return {
        "success": True,
        "data": AmbassadorApplicationResponse.model_validate(
            application, from_attributes=True
        ),
    }
