"""
Google OAuth router scaffolding.

Provides placeholder endpoints for initiating the OAuth flow and handling the
callback. Full user persistence and session management will be added in later
phases.
"""

from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import crud

router = APIRouter(prefix="/auth/google", tags=["auth"])


@router.get("/login", summary="Start Google OAuth flow")
async def google_login() -> RedirectResponse:
    """
    Redirects the user to Google's OAuth consent screen.
    """

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(settings.google_scope_list),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
    }

    authorization_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    )

    return RedirectResponse(url=authorization_url)


@router.get("/callback", summary="Handle Google OAuth callback")
async def google_callback(request: Request) -> dict[str, str]:
    """
    Handles Google's OAuth callback.

    This endpoint will exchange the authorization code for tokens and validate
    the ID token payload. The current implementation returns the parsed token
    claims for inspection. Future phases will persist the authenticated user and
    establish application sessions.
    """

    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # Placeholder for token exchange. The actual exchange requires making a POST
    # request to Google's token endpoint. That implementation will be added in
    # a subsequent phase when persistence is available.

    # Simulate token verification by expecting an "id_token" query parameter.
    token = request.query_params.get("id_token")
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Token exchange not yet implemented. Provide an id_token for testing.",
        )

    try:
        id_info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid ID token") from exc

    email = id_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided in token.")

    name = id_info.get("name")
    phone = id_info.get("phone_number")

    with SessionLocal() as db:
        user = crud.get_user_by_email(db, email=email)
        if user is None:
            user = crud.create_user(db, email=email, name=name, phone=phone)
        else:
            crud.update_user_google_profile(db, user, name=name, phone=phone)

    # In a future phase, replace this with proper user persistence + session handling.
    return {
        "message": "OAuth callback received - persistence pending.",
        "email": id_info.get("email", ""),
        "name": id_info.get("name", ""),
        "sub": id_info.get("sub", ""),
        "role": user.role.value if user.role else None,
    }

