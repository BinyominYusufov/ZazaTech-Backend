"""Auth dependencies: resolve the current User from a Bearer JWT, gate by role.

Synchronous: the project uses sync SQLAlchemy (no aiosqlite/AsyncSession).
FastAPI runs these sync dependencies in a threadpool, so the event loop is
never blocked.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import decode_token
from app.models.user import User

bearer_scheme = HTTPBearer(bearerFormat="JWT", auto_error=False)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _credentials_exception
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise _credentials_exception

    # Reject refresh tokens used as Bearer creds. Tokens issued before the
    # type claim existed (`type` missing) are treated as access for compat.
    if payload.get("type", "access") != "access":
        raise _credentials_exception

    raw_sub = payload.get("sub")
    if raw_sub is None:
        raise _credentials_exception
    try:
        user_id = int(raw_sub)
    except (TypeError, ValueError):
        raise _credentials_exception

    user = session.get(User, user_id)
    if user is None:
        raise _credentials_exception
    return user


def require_role(*roles: str):
    """Dependency factory: `Depends(require_role("super_admin"))`."""

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        return current_user

    return role_checker
