"""
FastAPI dependency utilities.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import RoleEnum, User
from app.models import crud

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Retrieves the currently authenticated user by validating a Google ID token.
    The client must send the token in the Authorization header (Bearer scheme).
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials.",
        )

    token = credentials.credentials
    try:
        id_info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google ID token.",
        )

    email = id_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided in token.",
        )

    name = id_info.get("name")
    phone = id_info.get("phone_number")

    user = crud.get_user_by_email(db, email=email)
    if user is None:
        user = crud.create_user(db, email=email, name=name, phone=phone)
    else:
        crud.update_user_google_profile(db, user, name=name, phone=phone)

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

