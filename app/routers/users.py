"""User management. Sync SQLModel session (project is synchronous).

Every endpoint requires an authenticated super_admin (router-level
dependency); handlers that need the caller's identity also inject
get_current_user (cached within the request).
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
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.files import delete_file, save_upload
from app.core.security import hash_password
from app.dependencies.auth import get_current_user, require_role
from app.models.user import ALLOWED_ROLES, User, UserResponse

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    dependencies=[Depends(get_current_user), Depends(require_role("super_admin"))],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _super_admin_count(session: Session) -> int:
    return session.exec(
        select(func.count()).select_from(User).where(User.role == "super_admin")
    ).one()


def _validate_role(role: str) -> None:
    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Allowed: {', '.join(ALLOWED_ROLES)}",
        )


@router.get("", response_model=list[UserResponse])
def list_users(session: SessionDep):
    return session.exec(select(User)).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.post(
    "", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def create_user(
    session: SessionDep,
    name: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    role: Annotated[str, Form()],
    avatar: Annotated[UploadFile | None, File()] = None,
):
    _validate_role(role)

    existing = session.exec(select(User).where(User.email == email)).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        role=role,
    )
    if avatar is not None:
        user.avatar = save_upload(avatar, "avatars")

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    session: SessionDep,
    name: Annotated[str | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
    password: Annotated[str | None, Form()] = None,
    role: Annotated[str | None, Form()] = None,
    avatar: Annotated[UploadFile | None, File()] = None,
):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if name is not None:
        user.name = name

    if email is not None and email != user.email:
        dup = session.exec(select(User).where(User.email == email)).first()
        if dup is not None and dup.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )
        user.email = email

    if password is not None:
        user.hashed_password = hash_password(password)

    if role is not None and role != user.role:
        _validate_role(role)
        if user.role == "super_admin" and _super_admin_count(session) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change role of the last super_admin",
            )
        user.role = role

    if avatar is not None:
        if user.avatar:
            delete_file(user.avatar)
        user.avatar = save_upload(avatar, "avatars")

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int, session: SessionDep, current_user: CurrentUser
) -> dict:
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Safeguard: never leave the system without a super_admin.
    if user.role == "super_admin" and _super_admin_count(session) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the last super_admin",
        )

    if user.avatar:
        delete_file(user.avatar)
    session.delete(user)
    session.commit()
    return {"success": True, "message": "User deleted"}
