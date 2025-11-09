"""
Administrative endpoints for request lifecycle overrides and user management.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin_user
from app.api.requests import _help_request_to_schema
from app.db.session import get_db
from app.models import RequestStatusEnum, User, crud
from app.schemas import HelpRequestResponse, UserResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/requests/{request_id}/force-close",
    response_model=HelpRequestResponse,
)
async def force_close_request(
    request_id: int,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    help_request = crud.get_help_request_by_id(db, request_id=request_id)
    if help_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help request not found.",
        )

    help_request = db.merge(help_request)
    now = datetime.utcnow()

    # Mark any active assignments as completed so volunteers are released.
    for assignment in help_request.assignments:
        if assignment.completed_at is None:
            assignment.completed_at = now
            db.add(assignment)

    help_request.status = RequestStatusEnum.CANCELLED
    help_request.cancelled_at = now
    help_request.completed_at = help_request.completed_at or now

    try:
        crud.log_event(
            db,
            event_type="admin_force_close",
            user_id=admin_user.id,
            request_id=help_request.id,
            metadata={"admin_email": admin_user.email},
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - defensive rollback
        db.rollback()
        raise exc

    db.refresh(help_request)
    return _help_request_to_schema(help_request)


@router.post(
    "/users/{user_id}/suspend",
    response_model=UserResponse,
)
async def suspend_user(
    user_id: int,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user = db.merge(user)
    user.is_suspended = True
    db.add(user)

    crud.log_event(
        db,
        event_type="admin_suspend_user",
        user_id=admin_user.id,
        request_id=None,
        metadata={"suspended_user_id": user.id},
    )
    db.commit()
    db.refresh(user)

    return UserResponse.from_orm(user)

