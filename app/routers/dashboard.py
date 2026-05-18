"""Dashboard stats. Sync SQLModel session (project is synchronous).

The spec mentioned asyncio.gather(); on a sync single-connection SQLite
setup that buys nothing, so counts run as sequential
`SELECT count(*)` queries (as agreed in the sync-conversion step).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies.auth import get_current_user
from app.models import Blog, Contact, Project, Service, User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

SessionDep = Annotated[Session, Depends(get_session)]


def _count(session: Session, model: type) -> int:
    return session.exec(select(func.count()).select_from(model)).one()


@router.get("/stats", dependencies=[Depends(get_current_user)])
def stats(session: SessionDep) -> dict:
    return {
        "success": True,
        "data": {
            "users": _count(session, User),
            "services": _count(session, Service),
            "projects": _count(session, Project),
            "blogs": _count(session, Blog),
            "contacts": _count(session, Contact),
        },
    }
