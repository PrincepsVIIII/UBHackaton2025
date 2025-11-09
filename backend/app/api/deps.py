"""
FastAPI dependency utilities.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models import RoleEnum, User
from app.models import crud

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Retrieves the authenticated user by validating the session JWT sent in the
    Authorization header.
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials.",
        )

    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
        ) from exc

    user = crud.get_user_by_id(db, user_id_int)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user


async def get_current_elder(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != RoleEnum.ELDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Elder role required.",
        )
    return current_user


async def get_current_volunteer(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != RoleEnum.VOLUNTEER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Volunteer role required.",
        )
    return current_user


async def require_admin_user(
    current_user: User = Depends(get_current_user),
    admin_secret: Optional[str] = Header(default=None, alias="X-Admin-Secret"),
) -> User:
    """
    Validates that the caller has admin privileges either by email allowlist or
    providing the configured admin secret.
    """

    if current_user.email.lower() in settings.admin_email_allowlist:
        return current_user

    if settings.admin_secret and admin_secret == settings.admin_secret:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin privileges required.",
    )
