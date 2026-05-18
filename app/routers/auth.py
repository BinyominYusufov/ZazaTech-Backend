"""Auth router: login (JWT), current user, logout."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRegister, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
) -> dict:
    # OAuth2 form uses `username`; for ZazaTech that field carries the email.
    user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {
        "success": True,
        "token": token,
        "user": UserResponse.model_validate(user),
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegister,
    session: Annotated[Session, Depends(get_session)],
) -> dict:
    existing = session.exec(
        select(User).where(User.email == payload.email)
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    # role is intentionally NOT taken from the request — new users always
    # get the model's default role ("editor"). Privilege escalation guard.
    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {
        "success": True,
        "token": token,
        "user": UserResponse.model_validate(user),
    }


@router.get("/me")
def read_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    return {
        "success": True,
        "data": UserResponse.model_validate(current_user),
    }


@router.post("/logout")
def logout() -> dict:
    # JWT is stateless: the client just drops the token.
    return {"success": True, "message": "Logged out"}
