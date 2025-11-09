"""
Email-based one-time passcode authentication flow.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models import RoleEnum, User, crud
from app.schemas import OTPRequest, OTPVerify, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _validate_edu_email(email: str) -> None:
    if not email.endswith(".edu"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .edu email addresses are eligible for login.",
        )


@router.post(
    "/request-code",
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_code(
    payload: OTPRequest,
    db: Session = Depends(get_db),
):
    """
    Generates and stores a one-time passcode for the specified email.
    """

    normalized_email = _normalize_email(payload.email)
    _validate_edu_email(normalized_email)

    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = datetime.utcnow() + timedelta(minutes=settings.otp_expire_minutes)

    crud.upsert_email_otp(
        db,
        email=normalized_email,
        code_hash=_hash_code(code),
        role=payload.role,
        expires_at=expires_at,
    )

    print(f"[auth][otp] Send code to {normalized_email}: {code}")

    return {"ok": True}


@router.post("/verify-code", response_model=TokenResponse)
async def verify_code(
    payload: OTPVerify,
    db: Session = Depends(get_db),
):
    """
    Verifies the submitted passcode and returns a session JWT.
    """

    normalized_email = _normalize_email(payload.email)
    _validate_edu_email(normalized_email)

    otp_entry = crud.get_email_otp(db, normalized_email)
    if otp_entry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code.",
        )

    if otp_entry.expires_at < datetime.utcnow():
        crud.delete_email_otp(db, otp_entry)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code.",
        )

    if _hash_code(payload.code) != otp_entry.code_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code.",
        )

    role: RoleEnum = otp_entry.role
    crud.delete_email_otp(db, otp_entry)

    user = crud.get_user_by_email(db, normalized_email)
    if user is None:
        user = crud.create_user(db, email=normalized_email, role=role)
    else:
        try:
            crud.ensure_user_role(db, user, role)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

    crud.touch_user_last_login(db, user)

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value if user.role else None,
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user),
    )


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's information using JWT bearer auth.
    """

    return UserResponse.from_orm(current_user)

