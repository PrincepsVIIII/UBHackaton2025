"""
Passwordless email login flow.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_login_token, decode_token
from app.db.session import get_db
from app.models import RoleEnum, crud
from app.schemas import LoginRequest, LoginRequestResponse, TokenResponse, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _send_login_email(to_email: str, login_url: str) -> None:
    """
    Sends the magic login link to the provided email.

    For hackathon/demo use-cases we default to printing the link to the console.
    To integrate a production-ready service (e.g. SendGrid, Mailgun), replace the
    console output with the provider SDK/API call below.
    """

    subject = f"{settings.app_name} login link"
    body = (
        f"Hello,\n\n"
        f"Click the link below to finish signing in. "
        f"This link will expire in {settings.login_token_expire_minutes} minutes.\n\n"
        f"{login_url}\n\n"
        f"If you did not request this link you can ignore this message."
    )

    if settings.use_console_email or not settings.smtp_host:
        logger.info("Magic link for %s -> %s", to_email, login_url)
        print(f"[passwordless] Send to {to_email}: {login_url}")
        return

    # SMTP configuration is optional. Provide SMTP_HOST/SMTP_PORT/SMTP_USERNAME/SMTP_PASSWORD
    # to send real emails. Replace this block with your email provider SDK as needed.
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.email_from
        msg["To"] = to_email
        msg.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
    except Exception:  # pragma: no cover - best effort for demo
        logger.exception("Failed to send login email via SMTP; falling back to console output.")
        print(f"[passwordless] Send to {to_email}: {login_url}")


@router.post(
    "/login-request",
    response_model=LoginRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def login_request(
    payload: LoginRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Accepts an email + role and sends a one-time login link.
    """

    role = payload.role
    user = crud.get_user_by_email(db, payload.email)

    if user:
        try:
            crud.ensure_user_role(db, user, role)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    else:
        user = crud.create_user(db, email=payload.email, role=role)

    login_token = create_login_token({"email": payload.email, "role": role.value})
    login_url = f"{settings.app_base_url.rstrip('/')}/auth/login?token={login_token}"

    background_tasks.add_task(_send_login_email, payload.email, login_url)

    # Returning the URL helps during hackathon demos where email may not be configured yet.
    return LoginRequestResponse(
        message="Login link sent. Check your inbox.",
        login_url=login_url if settings.use_console_email else None,
    )


@router.get("/login", response_model=TokenResponse)
async def complete_login(
    token: str = Query(..., description="Magic link token"),
    db: Session = Depends(get_db),
):
    """
    Validates the magic link token and returns a session JWT.
    """

    payload = decode_token(token)
    if payload.get("type") != "login":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid login token.")

    email: Optional[str] = payload.get("email")
    role_value: Optional[str] = payload.get("role")

    if not email or not role_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token payload incomplete.")

    try:
        role = RoleEnum(role_value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role in token.") from exc

    user = crud.get_user_by_email(db, email=email)
    if user is None:
        user = crud.create_user(db, email=email, role=role)
    else:
        try:
            crud.ensure_user_role(db, user, role)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

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

