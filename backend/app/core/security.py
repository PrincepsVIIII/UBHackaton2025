"""
Security helpers for JWT creation and validation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import HTTPException, status

from app.core.config import settings


ALGORITHM = "HS256"


def _create_token(data: Dict[str, Any], expires_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()
    now = datetime.now(tz=timezone.utc)
    to_encode.update(
        {
            "iat": now,
            "nbf": now,
            "exp": now + expires_delta,
            "type": token_type,
        }
    )
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def create_access_token(payload: Dict[str, Any]) -> str:
    """
    Generates the session JWT returned after a successful login.
    """

    expires = timedelta(minutes=settings.access_token_expire_minutes)
    return _create_token(payload, expires, token_type="access")


def decode_token(token: str) -> Dict[str, Any]:
    """
    Validates the provided JWT and returns its payload.
    """

    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid.",
        ) from exc

